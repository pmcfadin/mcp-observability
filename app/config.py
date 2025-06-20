from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    LOKI_BASE_URL: str = "http://loki:3100"
    PROMETHEUS_BASE_URL: str = "http://prometheus:9090"
    TEMPO_BASE_URL: str = "http://tempo:3200"
    ALERTMANAGER_BASE_URL: str = "http://alertmanager:9093"
    DEFAULT_HTTP_TIMEOUT: float = 5.0
    MCP_TOKEN: str = "testtoken"


@lru_cache()
def get_settings():
    return Settings()
