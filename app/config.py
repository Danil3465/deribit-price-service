from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/deribit"
    redis_url: str = "redis://redis:6379/0"

    deribit_base_url: str = "https://www.deribit.com/api/v2"
    fetch_interval_seconds: int = 60

    tickers: list[str] = ["btc_usd", "eth_usd"]


settings = Settings()