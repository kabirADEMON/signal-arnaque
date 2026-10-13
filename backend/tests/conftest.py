"""Les tests tournent sur un vrai PostgreSQL : pgserver en local, un service PostgreSQL en CI
(TEST_DATABASE_URL). Le schéma est créé par les migrations Alembic, comme en production."""

import os

TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_URL:
    from tests.pg import local_database_url

    TEST_URL = local_database_url("signal_arnaque_test", fresh=True)
os.environ["DATABASE_URL"] = TEST_URL
os.environ.setdefault("JWT_SECRET", "cle-de-test-uniquement-0123456789abcdef")
os.environ["FRONTEND_DIST"] = "__pas_de_front_en_test__"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.deps import limits  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Agent, Role  # noqa: E402
from app.security import create_token, hash_secret  # noqa: E402

MOT_DE_PASSE = "un-mot-de-passe-solide"


@pytest.fixture(scope="session", autouse=True)
def schema():
    command.upgrade(Config("alembic.ini"), "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def propre():
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE evenements, elements, signalements, agents RESTART IDENTITY CASCADE"))
    for limiter in limits.values():
        limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _agent(db, email: str, role: Role, actif: bool = True) -> Agent:
    a = Agent(email=email, nom=email.split("@")[0].title(), mot_de_passe_hash=hash_secret(MOT_DE_PASSE), role=role, actif=actif)
    db.add(a)
    db.commit()
    return a


@pytest.fixture
def agent(db):
    return _agent(db, "awa@signal.bj", Role.agent)


@pytest.fixture
def admin(db):
    return _agent(db, "chef@signal.bj", Role.admin)


@pytest.fixture
def entete_agent(agent):
    return {"Authorization": f"Bearer {create_token(agent.id)}"}


@pytest.fixture
def entete_admin(admin):
    return {"Authorization": f"Bearer {create_token(admin.id)}"}


def signalement(**over) -> dict:
    data = {
        "categorie": "mobile_money",
        "canal": "whatsapp",
        "description": "On m'a demandé d'envoyer 50 000 F pour débloquer un prétendu gain.",
        "montant_perdu": 50000,
        "elements": [{"type": "telephone", "valeur": "97 12 34 56"}],
    }
    data.update(over)
    return data


@pytest.fixture
def creer(client):
    def _creer(**over) -> dict:
        r = client.post("/api/signalements", json=signalement(**over))
        assert r.status_code == 201, r.text
        return r.json()

    return _creer
