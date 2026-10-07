from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://retail_user:retail_password@postgres:5432/retail_pricing"
    REDIS_URL: str = "redis://redis:6379/0"
    UPLOAD_DIR: str = "/tmp/retail_pricing_uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()