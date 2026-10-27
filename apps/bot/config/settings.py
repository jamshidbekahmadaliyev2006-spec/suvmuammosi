from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    telegram_bot_api_key: str = Field(default="", alias="TELEGRAM_BOT_API_KEY")
    detection_rules_refresh_seconds: int = Field(default=20, alias="DETECTION_RULES_REFRESH_SECONDS")
    heartbeat_interval_seconds: int = Field(default=30, alias="HEARTBEAT_INTERVAL_SECONDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_dedup_cache_size: int = Field(default=10000, alias="MAX_DEDUP_CACHE_SIZE")
    app_env: str = Field(default="development", alias="APP_ENV")

    def validate_for_start(self) -> None:
        """Ishga tushirishdan oldin minimal talablarni tekshirish."""
        if not self.telegram_bot_token and self.app_env != "test":
            raise ValueError("TELEGRAM_BOT_TOKEN belgilanmagan. Iltimos .env faylida ko'rsating.")
        if not self.telegram_bot_api_key and self.app_env != "test":
            raise ValueError("TELEGRAM_BOT_API_KEY belgilanmagan. Iltimos .env faylida ko'rsating.")


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
