from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://juventum:juventum@localhost:5432/juventum"

    # External data sources
    football_data_api_key: str = ""

    # Match Brief / LLM
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    enable_llm_brief: bool = True
    llm_timeout_seconds: float = 8.0

    # API
    cors_origins: str = "http://localhost:3000"
    admin_token: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
