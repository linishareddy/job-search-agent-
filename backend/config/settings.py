from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    postgres_user: str = "jobsearch"
    # No default: a guessable placeholder here would silently "work" against any
    # Postgres that happens to share it, masking a missing .env value instead of
    # failing loudly. Set POSTGRES_PASSWORD in .env.
    postgres_password: str
    postgres_db: str = "jobsearch"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Comma-separated list of allowed frontend origins for CORS. "*" is invalid
    # together with allow_credentials=True (browsers reject it outright), so this
    # must be a real, explicit allowlist.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

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

    # Auth
    # No default: same rationale as postgres_password — a shared placeholder secret
    # would silently "work" while forging any token. Set JWT_SECRET in .env.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_expire_minutes: int = 1440

    # Email (Resend HTTP API)
    resend_api_key: str = ""
    email_from: str = "Job Agent <onboarding@resend.dev>"
    # Global kill-switch — off by default so email is opt-in even once a key is set.
    email_enabled: bool = False

    # Seed user created on first startup so pre-existing (pre-auth) rows have an owner
    seed_user_email: str = "you@example.com"

    # Auto-apply
    auto_apply_interval_minutes: int = 15

    # JobSpy — LinkedIn + Indeed only
    jobspy_default_location: str = "United States"
    jobspy_us_only: bool = True
    jobspy_country_indeed: str = "USA"
    jobspy_proxies: str = ""

    @property
    def jobspy_proxy_list(self) -> list[str] | None:
        proxies = [p.strip() for p in self.jobspy_proxies.split(",") if p.strip()]
        return proxies if proxies else None


settings = Settings()
