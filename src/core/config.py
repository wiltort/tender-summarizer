from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Tender Summarizer API"
    app_description: str = "Умный суммаризатор тендерной документации."
    app_version: str = "0.1.0"

    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    server_host: str = "localhost"
    server_port: int = 8765

    # OpenAI settings
    openai_api_key: str
    openai_api_base_url: str | None = None
    openai_model: str | None = None

    openai_timeout: float = 120.0

    openai_max_retries: int = 3

    openai_retry_backoff: float = 1.0
    openai_temperature: float = 0.1

    @property
    def openai_client_args(self) -> dict[str, Any]:
        args = {
            "api_key": self.openai_api_key,
            "timeout": self.openai_timeout,
            "max_retries": 0,
        }
        if self.openai_api_base_url:
            args["base_url"] = self.openai_api_base_url
        return args

    # PDF settings
    pdf_max_size: int = 1024 * 1024 * 5
    max_text_length: int = 100_000

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")


settings = Settings()
