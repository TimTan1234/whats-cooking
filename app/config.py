"""Application settings, read from environment variables or a .env file."""

import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "What's Cooking"

    # Storage. The SQLite file and the generated session secret live here.
    data_dir: Path = Path("data")
    database_url: str = ""

    # Sessions. Leave SECRET_KEY empty to have one generated and kept in data_dir.
    secret_key: str = ""
    cookie_secure: bool = False

    # AI service. Set AI_BASE_URL and AI_API_KEY to use an OpenAI-compatible endpoint such as
    # the Coarena Model API; leave AI_BASE_URL empty to call Google's Gemini API with GEMINI_API_KEY.
    # Without a key the app runs in demo mode with sample answers.
    ai_base_url: str = ""
    ai_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    # Photos get their own, stronger model: reading a crowded fridge is the hard part.
    gemini_vision_model: str = "gemini-4-hydrogen"
    # Optional thinking effort for photos (low, medium, high). Empty uses the model's default.
    gemini_vision_thinking: str = ""
    ai_mock: bool = False
    ai_timeout_seconds: int = 60

    # Photo uploads.
    max_upload_mb: int = 10
    max_photos: int = 4

    # Used when showing dates such as "last cooked".
    timezone: str = "Asia/Kuala_Lumpur"

    @property
    def use_mock_ai(self) -> bool:
        key = self.ai_api_key if self.ai_base_url.strip() else self.gemini_api_key
        return self.ai_mock or not key.strip()

    @property
    def ai_service(self) -> str:
        """Who reads the photos, as shown to users."""
        if self.ai_base_url.strip():
            from urllib.parse import urlsplit

            return urlsplit(self.ai_base_url).hostname or self.ai_base_url
        return "Google Gemini"

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{(self.data_dir / 'recipie.db').as_posix()}"

    def resolve_secret_key(self) -> str:
        """Return SECRET_KEY, generating and persisting one on first run."""
        if self.secret_key:
            return self.secret_key
        key_file = self.data_dir / ".secret_key"
        if key_file.exists():
            stored = key_file.read_text(encoding="utf-8").strip()
            if stored:
                return stored
        self.data_dir.mkdir(parents=True, exist_ok=True)
        key = secrets.token_urlsafe(48)
        key_file.write_text(key, encoding="utf-8")
        try:
            key_file.chmod(0o600)
        except OSError:
            pass
        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()
