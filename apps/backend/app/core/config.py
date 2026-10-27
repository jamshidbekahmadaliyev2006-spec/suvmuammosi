"""Ilova sozlamalari — faqat environment orqali (maxfiy qiymatlar kodda yo'q)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env", "../.env"),
        extra="ignore",
    )

    app_env: str = "development"
    app_secret_key: str = "change_me"  # noqa: S105 (production'da rad etiladi)
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/suvnazorat"
    frontend_url: str = "http://localhost:3000"
    telegram_bot_api_key: str = ""
    telegram_bot_token: str = ""
    app_timezone: str = "Asia/Tashkent"
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    login_max_attempts: int = 5
    login_window_seconds: int = 60
    bot_heartbeat_ttl_seconds: int = 90
    log_level: str = "INFO"
    groq_api_key: str = "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"
    groq_model: str = "openai/gpt-oss-20b"
    ai_analysis_enabled: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_for_production(self) -> None:
        """Production rejimida zaif yoki bo'sh maxfiy qiymatlar bilan ishga tushmaydi."""
        if not self.is_production:
            return
        problems = []
        if self.app_secret_key in ("", "change_me") or len(self.app_secret_key) < 32:
            problems.append("APP_SECRET_KEY kamida 32 belgili bo'lishi kerak")
        if len(self.telegram_bot_api_key) < 24:
            problems.append("TELEGRAM_BOT_API_KEY kamida 24 belgili bo'lishi kerak")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE=true bo'lishi kerak (HTTPS)")
        if problems:
            raise RuntimeError("Production konfiguratsiyasi xato: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
