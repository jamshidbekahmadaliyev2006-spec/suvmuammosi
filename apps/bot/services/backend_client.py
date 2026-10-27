"""Backend API bilan xavfsiz va xatolarga chidamli muloqot qiluvchi servis.

Timeout, qayta urinish (retry), exponential backoff va heartbeat hisobotlari bilan ta'minlangan.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

log = logging.getLogger("suvnazorat.bot.backend")


class BackendClient:
    def __init__(
        self,
        backend_url: str,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-bot-api-key": self.api_key,
        }

    async def send_message(self, message_payload: dict[str, Any]) -> dict[str, Any] | None:
        """Xabarni backendga uzatadi. Xatolik bo'lsa, qayta urinish mexanizmini qo'llaydi."""
        url = f"{self.backend_url}/api/v1/bot/messages"
        headers = self._headers()

        delay = 0.5
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=message_payload, headers=headers)

                if resp.status_code in (200, 201):
                    return resp.json()

                if resp.status_code == 409:
                    log.info(
                        "Xabar avval saqlangan (idempotent / duplicate): chat_id=%s, msg_id=%s",
                        message_payload.get("chat_id"),
                        message_payload.get("message_id"),
                    )
                    return resp.json()

                if resp.status_code in (400, 404):
                    log.warning(
                        "Backend xabarni rad etdi (status=%d): %s",
                        resp.status_code,
                        resp.text[:200],
                    )
                    return None

                log.warning(
                    "Backend xatolik qaytardi (urinish %d/%d, status=%d): %s",
                    attempt,
                    self.max_retries,
                    resp.status_code,
                    resp.text[:200],
                )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                log.warning(
                    "Backendga ulanishda tarmoq xatoligi (urinish %d/%d): %s",
                    attempt,
                    self.max_retries,
                    str(exc),
                )

            if attempt < self.max_retries:
                await asyncio.sleep(delay)
                delay *= 2

        log.error("Xabarni backendga yetkazish imkoni bo'lmadi: chat_id=%s, msg_id=%s",
                  message_payload.get("chat_id"), message_payload.get("message_id"))
        return None

    async def send_heartbeat(
        self,
        bot_version: str = "0.1.0",
        rules_version: int | None = None,
        rules_loaded: bool = False,
        rules_fetched_at: datetime | None = None,
        watched_sources: int | None = None,
    ) -> bool:
        """Dashboardda bot holati to'g'ri ko'rinishi uchun muntazam heartbeat yuboradi."""
        url = f"{self.backend_url}/api/v1/bot/heartbeat"
        headers = self._headers()

        payload = {
            "bot_version": bot_version,
            "rules_version": rules_version,
            "rules_loaded": rules_loaded,
            "rules_fetched_at": rules_fetched_at.isoformat() if rules_fetched_at else None,
            "watched_sources": watched_sources,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
            return resp.status_code == 200
        except Exception as e:
            log.debug("Heartbeat yuborishda xatolik: %s", str(e))
            return False

    async def register_source(
        self,
        chat_id: int,
        chat_title: str,
        chat_username: str | None = None,
        source_type: str = "GROUP",
    ) -> dict[str, Any] | None:
        """Guruh yoki kanalga bot qo'shilganda uni backendga avtomatik ro'yxatdan o'tkazadi."""
        url = f"{self.backend_url}/api/v1/bot/register-source"
        headers = self._headers()
        payload = {
            "chat_id": chat_id,
            "chat_title": chat_title,
            "chat_username": chat_username,
            "source_type": source_type,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                log.info("Manba backendga ro'yxatga olindi: chat_id=%s, title=%s", chat_id, chat_title)
                return resp.json()
            log.warning("Manbani ro'yxatga olishda xatolik (status=%d): %s", resp.status_code, resp.text)
        except Exception as exc:
            log.warning("Backendga ulanishda xatolik (register_source): %s", exc)
        return None

    async def get_summary(self) -> dict[str, Any] | None:
        """Admin ko'rinishi uchun monitoring statistikasi va so'nggi hodisalar."""
        url = f"{self.backend_url}/api/v1/bot/summary"
        headers = self._headers()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            log.warning("Backend summary so'rovini rad etdi: status=%d", resp.status_code)
        except Exception as exc:
            log.warning("Backend get_summary da xatolik: %s", exc)
        return None

    async def check_admin(self, phone: str) -> bool:
        """Telefon raqam tizim sozlamalaridagi adminlar ro'yxatida borligini tekshiradi."""
        url = f"{self.backend_url}/api/v1/bot/check-admin"
        headers = self._headers()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params={"phone": phone}, headers=headers)
            if resp.status_code == 200:
                return bool(resp.json().get("is_admin", False))
        except Exception as e:
            log.warning("check_admin so'rovida xatolik: %s", e)
        return False

    async def cancel_incident(self, incident_id: int, chat_id: int) -> bool:
        """Foydalanuvchi murojaatini bekor qilganda backendga bildiradi."""
        url = f"{self.backend_url}/api/v1/bot/cancel-incident"
        headers = self._headers()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    url,
                    json={"incident_id": incident_id, "chat_id": chat_id},
                    headers=headers,
                )
            if resp.status_code == 200:
                return bool(resp.json().get("ok", False))
        except Exception as e:
            log.warning("cancel_incident da xatolik: %s", e)
        return False


