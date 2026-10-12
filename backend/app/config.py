from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres@127.0.0.1:5432/signal_arnaque"
    # À remplacer en production (au moins 32 caractères aléatoires).
    jwt_secret: str = "dev-uniquement-a-remplacer-en-production-0000"
    jwt_minutes: int = 8 * 60
    # Dossier du front compilé (npm run build) servi par l'API, s'il existe.
    frontend_dist: str = "../frontend/dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
