"""Runtime settings. Environment variables override the repo .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_DIR = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_DIR / ".env"), str(_BACKEND_DIR / ".env")),
        extra="ignore",
    )

    database_url: str = "sqlite:///./pantrycook.db"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "*"

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key.strip())


def get_settings() -> Settings:
    return Settings()
