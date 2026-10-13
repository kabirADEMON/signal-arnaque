from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-uniquement-a-remplacer-en-production-0000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres@127.0.0.1:5432/signal_arnaque"
    # Obligatoire en production : 32 caractères aléatoires au moins.
    jwt_secret: str = DEV_SECRET
    # Seul `python dev.py` l'active : autorise la clé de développement, en local uniquement.
    allow_dev_secret: bool = False
    jwt_minutes: int = 8 * 60
    # À activer seulement derrière un proxy de confiance (Nginx, hébergeur) qui écrit
    # X-Forwarded-For. Sinon, n'importe quel visiteur pourrait inventer son adresse.
    trust_proxy: bool = False
    # Documentation interactive de l'API (/api/docs) : utile en développement, masquée par défaut.
    api_docs: bool = False
    # Dossier du front compilé (npm run build) servi par l'API, s'il existe.
    frontend_dist: str = "../frontend/dist"


class InsecureConfig(RuntimeError):
    pass


def check_settings(s: Settings) -> None:
    """Refuse de démarrer avec une clé de signature faible : avec la clé publique du dépôt,
    n'importe qui pourrait fabriquer un jeton d'administrateur."""
    if s.allow_dev_secret:
        return
    if s.jwt_secret == DEV_SECRET or len(s.jwt_secret) < 32:
        raise InsecureConfig("JWT_SECRET manquant ou trop court (32 caractères aléatoires au moins).")


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    check_settings(s)
    return s
