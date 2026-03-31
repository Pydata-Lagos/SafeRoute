import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password123@localhost:5432/saferoute",
    )

    # Expose a sync URL for Alembic which runs migrations synchronously
    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "+pysycopg2")

    model_config = {"env_file": ".env"}


settings = Settings()
