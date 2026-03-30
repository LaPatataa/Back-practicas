from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "local"

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # Next modules (DB):
    DATABASE_URL: str | None = None

settings = Settings()
