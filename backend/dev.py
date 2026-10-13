"""Outils de développement avec un PostgreSQL local embarqué (pgserver).

    python dev.py serveur        # base locale + migrations + API sur http://127.0.0.1:8000
    python dev.py demo [--neuf]  # idem, avec des données fictives (--neuf : repart d'une base vide)
    python dev.py migration "message"   # génère une migration Alembic à partir des modèles
"""

import os
import sys

from tests.pg import local_database_url


def main() -> None:
    os.environ.setdefault("ALLOW_DEV_SECRET", "1")  # en local uniquement
    os.environ.setdefault("API_DOCS", "1")
    os.environ["DATABASE_URL"] = local_database_url("signal_arnaque", fresh="--neuf" in sys.argv)
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    if sys.argv[1:2] == ["migration"]:
        command.upgrade(cfg, "head")
        command.revision(cfg, message=sys.argv[2], autogenerate=True)
        return
    command.upgrade(cfg, "head")
    if sys.argv[1:2] == ["demo"]:
        from app.database import SessionLocal
        from seed import MOT_DE_PASSE_DEMO, seed

        with SessionLocal() as db:
            if seed(db):
                print(f"Données de démonstration créées. Comptes : admin@demo.bj / agent@demo.bj, mot de passe {MOT_DE_PASSE_DEMO}")
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))


if __name__ == "__main__":
    main()
