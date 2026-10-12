"""PostgreSQL local pour le développement et les tests, sans installation ni droits admin.

Utilise pgserver (binaires PostgreSQL embarqués). En CI, TEST_DATABASE_URL pointe vers
un vrai service PostgreSQL et ce module n'est pas utilisé.
"""

import os
from pathlib import Path

import psycopg


def local_database_url(name: str, fresh: bool = False) -> str:
    import pgserver

    data_dir = Path(os.environ.get("TEMP", "/tmp")) / "signal_arnaque_pg"
    server = pgserver.get_server(data_dir, cleanup_mode="stop")
    admin_uri = server.get_uri()
    with psycopg.connect(admin_uri, autocommit=True) as conn:
        if fresh:
            conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            conn.execute(f'CREATE DATABASE "{name}"')
    return admin_uri.replace("postgresql://", "postgresql+psycopg://").rsplit("/", 1)[0] + "/" + name
