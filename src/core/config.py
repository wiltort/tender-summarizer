from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Tender Summarizer API"
    app_description: str = "Умный суммаризатор тендерной документации."
    app_version: str = "0.1.0"

    debug: bool = False
    api_prefix: str = "/api/v1"

    server_host: str = "localhost"
    server_port: int = 8765

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")


settings = Settings()
