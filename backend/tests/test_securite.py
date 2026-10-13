"""Tests des protections : chacun rejoue une attaque et vérifie qu'elle échoue."""

import pytest

from app.config import DEV_SECRET, InsecureConfig, Settings, check_settings
from app.security import hash_secret, verify_secret
from tests.conftest import MOT_DE_PASSE, signalement


def test_refuse_de_demarrer_avec_la_cle_publique_du_depot():
    with pytest.raises(InsecureConfig):
        check_settings(Settings(jwt_secret=DEV_SECRET))
    with pytest.raises(InsecureConfig):
        check_settings(Settings(jwt_secret="trop-courte"))
    check_settings(Settings(jwt_secret="x" * 40))  # clé solide : accepté
    check_settings(Settings(jwt_secret=DEV_SECRET, allow_dev_secret=True))  # développement local


def test_adresse_inventee_ne_contourne_pas_les_limites(client):
    # Sans proxy de confiance, X-Forwarded-For est ignoré : changer d'adresse à chaque
    # requête ne permet pas d'envoyer plus de signalements.
    codes = [
        client.post("/api/signalements", json=signalement(), headers={"X-Forwarded-For": f"10.0.0.{i}"}).status_code
        for i in range(6)
    ]
    assert codes == [201] * 5 + [429]


def test_derriere_un_proxy_seule_la_derniere_adresse_compte(monkeypatch):
    from starlette.requests import Request

    from app import deps
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "trust_proxy", True)
    scope = {"type": "http", "client": ("10.1.1.1", 1234),
             "headers": [(b"x-forwarded-for", b"1.2.3.4, 203.0.113.7")]}
    # « 1.2.3.4 » a été écrit par le client ; « 203.0.113.7 » par le proxy.
    assert deps.client_ip(Request(scope)) == "203.0.113.7"


def test_blocage_du_compte_apres_cinq_echecs_meme_depuis_plusieurs_adresses(client, agent):
    for i in range(5):
        r = client.post("/api/auth/connexion", json={"email": agent.email, "mot_de_passe": "faux"},
                        headers={"X-Forwarded-For": f"10.9.9.{i}"})
        assert r.status_code == 401
    # Même le bon mot de passe est refusé pendant le blocage : l'attaquant ne peut plus essayer.
    bloque = client.post("/api/auth/connexion", json={"email": agent.email, "mot_de_passe": MOT_DE_PASSE})
    assert bloque.status_code == 429


def test_requete_trop_volumineuse(client):
    r = client.post("/api/signalements", content=b"{" + b" " * (70 * 1024) + b"}",
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_en_tetes_https_et_csp_stricte(client):
    r = client.get("/api/statistiques")
    assert "max-age=31536000" in r.headers["strict-transport-security"]
    assert "unsafe-inline" not in r.headers["content-security-policy"]


def test_documentation_de_l_api_masquee_par_defaut(client):
    assert client.get("/api/docs").status_code == 404
    assert client.get("/api/openapi.json").status_code == 404


def test_empreinte_scrypt_parametree_et_salee():
    a, b = hash_secret("secret"), hash_secret("secret")
    assert a != b  # sel différent à chaque fois
    assert a.startswith("scrypt$32768$8$1$")
    assert verify_secret("secret", a) and not verify_secret("autre", a)
    assert not verify_secret("secret", "format-invalide")
