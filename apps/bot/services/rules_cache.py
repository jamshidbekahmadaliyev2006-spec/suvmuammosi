"""Dinamik qoidalarni xotirada keshlovchi va fonda yangilovchi servis.

Bot restart qilinmasdan, veb-saytda kiritilgan yangi qoidalar va o'zgarishlarni avtomatik qabul qiladi.
Backend vaqtincha ishlamasa, oxirgi muvaffaqiyatli keshdan foydalanishda davom etadi.
"""
import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

log = logging.getLogger("suvnazorat.bot.cache")


class RulesCache:
    def __init__(
        self,
        backend_url: str,
        api_key: str,
        refresh_interval: int = 20,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.refresh_interval = max(5, refresh_interval)

        self._rules: list[dict[str, Any]] = []
        self._version: int = 0
        self._rules_loaded: bool = False
        self._last_fetched_at: datetime | None = None
        self._is_stale: bool = False
        self._running: bool = False
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    @property
    def rules(self) -> list[dict[str, Any]]:
        return list(self._rules)

    @property
    def version(self) -> int:
        return self._version

    @property
    def rules_loaded(self) -> bool:
        return self._rules_loaded

    @property
    def last_fetched_at(self) -> datetime | None:
        return self._last_fetched_at

    @property
    def is_stale(self) -> bool:
        return self._is_stale

    async def fetch_rules(self) -> bool:
        """Backenddan faol qoidalarni oladi va keshni yangilaydi."""
        url = f"{self.backend_url}/api/v1/detection-rules/active"
        headers = {"x-bot-api-key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                new_version = data.get("version", 0)
                new_rules = data.get("rules", [])

                async with self._lock:
                    self._rules = new_rules
                    self._version = new_version
                    self._rules_loaded = True
                    self._last_fetched_at = datetime.now(UTC)
                    self._is_stale = False

                log.info(
                    "Qoidalar muvaffaqiyatli yuklandi: versiya=%d, qoidalar soni=%d",
                    new_version,
                    len(new_rules),
                )
                return True
            else:
                log.warning(
                    "Backend qoidalarni bermadi (status=%d). Oxirgi keshdan foydalaniladi.",
                    resp.status_code,
                )
                self._is_stale = True
                return False

        except Exception as exc:
            log.warning(
                "Qoidalarni yuklashda xatolik: %s. Oxirgi kesh saqlanib qoladi.",
                str(exc),
            )
            self._is_stale = True
            return False

    async def check_and_update(self) -> bool:
        """Versiyani tekshirib, yangilanish bo'lsa yangi qoidalarni yuklaydi."""
        version_url = f"{self.backend_url}/api/v1/detection-rules/version"
        headers = {"x-bot-api-key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(version_url, headers=headers)

            if resp.status_code == 200:
                remote_version = resp.json().get("version", 0)
                if remote_version != self._version or not self._rules_loaded:
                    log.info(
                        "Yangi qoidalar versiyasi aniqlandi: %d -> %d. Yuklanmoqda...",
                        self._version,
                        remote_version,
                    )
                    return await self.fetch_rules()
                self._is_stale = False
                return True
            else:
                # Agar version endpointi bo'lmasa, to'g'ridan-to'g'ri faol qoidalarni olish
                return await self.fetch_rules()
        except Exception:
            self._is_stale = True
            return False

    async def _loop(self) -> None:
        """Doimiy fonda qoidalar yangilanishini tekshirish tsikli."""
        while self._running:
            try:
                await self.check_and_update()
            except Exception as e:
                log.error("Qoidalar tsiklida xatolik: %s", str(e))
            await asyncio.sleep(self.refresh_interval)

    def start_background_task(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        log.info("Qoidalar keshi fon vazifasi boshlandi (interval=%ds)", self.refresh_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("Qoidalar keshi fon vazifasi to'xtatildi")
