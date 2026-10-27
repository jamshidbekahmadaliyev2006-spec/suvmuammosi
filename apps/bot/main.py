"""SuvNazorat Telegram Monitoring Botining asosiy kirish nuqtasi."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import get_bot_settings
from handlers import messages_router
from services import BackendClient, MessageDeduplicator, RulesCache

# Windows konsoli uchun UTF-8 kodlashni ta'minlash (emoji va o'zbekcha belgilar xatosiz chiqishi uchun)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Log formatlash (maxfiy ma'lumotlarsiz)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("suvnazorat.bot")


async def heartbeat_loop(
    backend: BackendClient,
    cache: RulesCache,
    interval: int = 30,
) -> None:
    """Muntazam heartbeat xabarlarini backendga yuborib turadi."""
    while True:
        try:
            await backend.send_heartbeat(
                bot_version="0.1.0",
                rules_version=cache.version,
                rules_loaded=cache.rules_loaded,
                rules_fetched_at=cache.last_fetched_at,
            )
        except Exception as e:
            log.debug("Heartbeat yuborishda xatolik: %s", str(e))
        await asyncio.sleep(interval)


async def main() -> None:
    settings = get_bot_settings()
    settings.validate_for_start()

    log.info("SuvNazorat Bot ishga tushirilmoqda...")
    log.info("Backend URL: %s", settings.backend_url)
    log.info("Qoidalar yangilanish intervali: %d soniya", settings.detection_rules_refresh_seconds)

    # 1. Asosiy servislarni inisializatsiya qilish
    rules_cache = RulesCache(
        backend_url=settings.backend_url,
        api_key=settings.telegram_bot_api_key,
        refresh_interval=settings.detection_rules_refresh_seconds,
    )

    backend_client = BackendClient(
        backend_url=settings.backend_url,
        api_key=settings.telegram_bot_api_key,
    )

    deduplicator = MessageDeduplicator(max_size=settings.max_dedup_cache_size)

    # 2. Dastlabki qoidalarni yuklab olish
    log.info("Backenddan boshlang'ich qoidalar olinmoqda...")
    loaded = await rules_cache.fetch_rules()
    if not loaded:
        log.warning(
            "Diqqat: Dastlabki qoidalarni olib bo'lmadi. Backend ishga tushgach, avtomatik yangilanadi."
        )

    # 3. aiogram Dispatcher yaratish
    dp = Dispatcher()

    # Dependencylarni handlerlarga uzatish
    dp["cache"] = rules_cache
    dp["backend"] = backend_client
    dp["dedup"] = deduplicator

    dp.include_router(messages_router)

    # 4. Fonda ishlovchi vazifalarni ishga tushirish
    rules_cache.start_background_task()
    heartbeat_task = asyncio.create_task(
        heartbeat_loop(
            backend_client,
            rules_cache,
            interval=settings.heartbeat_interval_seconds,
        )
    )

    try:
        log.info("Telegram monitoring muvaffaqiyatli boshlandi.")
        # Dastlabki heartbeat yuborish
        await backend_client.send_heartbeat(
            bot_version="0.1.0",
            rules_version=rules_cache.version,
            rules_loaded=rules_cache.rules_loaded,
            rules_fetched_at=rules_cache.last_fetched_at,
        )
        # Pollingni ishga tushirish (xabarlar, kanal postlari, a'zolik va callback query yangilanishlari)
        while True:
            bot = Bot(
                token=settings.telegram_bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            try:
                await dp.start_polling(
                    bot,
                    allowed_updates=["message", "channel_post", "my_chat_member", "callback_query"],
                    handle_signals=False,
                )
                log.info("Polling to'xtadi, 2 soniyadan so'ng qayta ulanmoqda...")
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                log.info("Polling bekor qilindi.")
                break
            except Exception as e:
                log.warning("Telegram aloqasida vaqtinchalik uzilish: %s. 3 soniyadan keyin qayta ulanmoqda...", e)
                await asyncio.sleep(3)
            finally:
                try:
                    await bot.session.close()
                except Exception:
                    pass
    finally:
        log.info("Bot to'xtatilmoqda...")
        await rules_cache.stop()
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        log.info("Bot to'xtatildi.")


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
            break
        except (KeyboardInterrupt, SystemExit):
            log.info("Bot jarayoni foydalanuvchi tomonidan to'xtatildi.")
            break
        except Exception as err:
            log.warning("Botda kutilmagan uzilish: %s. 3 soniyadan so'ng avtomatik qayta ishga tushiriladi...", err)
            import time
            time.sleep(3)
