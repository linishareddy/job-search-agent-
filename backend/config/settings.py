from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    postgres_user: str = "jobsearch"
    postgres_password: str = "jobsearch"
    postgres_db: str = "jobsearch"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Groq
    groq_api_key: str = ""

    # Job source keys
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    jooble_api_key: str = ""

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    # Scheduler
    scheduler_min_interval_minutes: int = 30

    # Relevance threshold for notifications
    notification_score_threshold: float = 7.0


settings = Settings()
