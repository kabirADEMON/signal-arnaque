from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings
from tests.conftest import MOT_DE_PASSE, _agent
from app.models import Role


def test_acces_reserve_aux_agents(client):
    assert client.get("/api/agent/signalements").status_code == 401
    faux = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "mauvaise-cle", algorithm="HS256")
    assert client.get("/api/agent/signalements", headers={"Authorization": f"Bearer {faux}"}).status_code == 401


def test_jeton_expire_refuse(client, agent):
    expire = jwt.encode({"sub": str(agent.id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                        get_settings().jwt_secret, algorithm="HS256")
    assert client.get("/api/agent/moi", headers={"Authorization": f"Bearer {expire}"}).status_code == 401


def test_connexion(client, agent):
    bad = client.post("/api/auth/connexion", json={"email": agent.email, "mot_de_passe": "faux"})
    unknown = client.post("/api/auth/connexion", json={"email": "personne@signal.bj", "mot_de_passe": MOT_DE_PASSE})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()  # on ne révèle pas quels comptes existent

    ok = client.post("/api/auth/connexion", json={"email": "AWA@signal.bj", "mot_de_passe": MOT_DE_PASSE})
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    assert client.get("/api/agent/moi", headers={"Authorization": f"Bearer {token}"}).json()["email"] == agent.email


def test_compte_desactive(client, db):
    _agent(db, "parti@signal.bj", Role.agent, actif=False)
    assert client.post("/api/auth/connexion", json={"email": "parti@signal.bj", "mot_de_passe": MOT_DE_PASSE}).status_code == 401


def test_force_brute_limitee(client, agent):
    codes = [client.post("/api/auth/connexion", json={"email": agent.email, "mot_de_passe": "x"}).status_code for _ in range(11)]
    assert codes[-1] == 429


def test_liste_filtres_et_recherche(client, creer, entete_agent):
    creer()
    creer(categorie="faux_site", canal="site_web", elements=[{"type": "site", "valeur": "https://www.banque-faux.com"}])
    liste = client.get("/api/agent/signalements", headers=entete_agent).json()
    assert liste["total"] == 2

    par_cat = client.get("/api/agent/signalements", params={"categorie": "faux_site"}, headers=entete_agent).json()
    assert par_cat["total"] == 1 and par_cat["elements"][0]["categorie"] == "faux_site"

    # La recherche retrouve un numéro quelle que soit son écriture d'origine.
    par_numero = client.get("/api/agent/signalements", params={"q": "2290197123456"}, headers=entete_agent).json()
    assert par_numero["total"] == 1

    assert client.get("/api/agent/signalements", params={"statut": "valide"}, headers=entete_agent).json()["total"] == 0


def test_detail_visible_par_l_agent_seulement(client, creer, entete_agent):
    creer(contact="victime@mail.bj")
    sid = client.get("/api/agent/signalements", headers=entete_agent).json()["elements"][0]["id"]
    d = client.get(f"/api/agent/signalements/{sid}", headers=entete_agent).json()
    assert d["contact"] == "victime@mail.bj"
    assert d["transitions_possibles"] == ["en_examen", "rejete"]
    assert client.get("/api/agent/signalements/9999", headers=entete_agent).status_code == 404


def test_circuit_d_instruction(client, creer, entete_agent):
    cree = creer()
    sid = client.get("/api/agent/signalements", headers=entete_agent).json()["elements"][0]["id"]
    url = f"/api/agent/signalements/{sid}/statut"

    assert client.post(url, json={"statut": "valide", "motif": "ok"}, headers=entete_agent).status_code == 409  # étape sautée
    assert client.post(url, json={"statut": "en_examen"}, headers=entete_agent).status_code == 200
    sans_motif = client.post(url, json={"statut": "valide"}, headers=entete_agent)
    assert sans_motif.status_code == 409 and "motif" in sans_motif.json()["detail"]
    d = client.post(url, json={"statut": "valide", "motif": "Numéro confirmé"}, headers=entete_agent).json()
    assert d["statut"] == "valide"
    assert [(h["nouveau_statut"], h["agent"]) for h in d["historique"]] == [("recu", None), ("en_examen", "Awa"), ("valide", "Awa")]

    # Le déclarant voit l'avancement et le motif, mais pas le nom de l'agent.
    suivi = client.post("/api/suivi", json={"reference": cree["reference"], "code": cree["code_suivi"]}).json()
    assert suivi["statut"] == "valide"
    assert suivi["historique"][-1]["motif"] == "Numéro confirmé"
    assert "agent" not in suivi["historique"][-1]

    # Une décision peut être revue, en laissant une trace.
    assert client.post(url, json={"statut": "en_examen", "motif": "Nouvel élément"}, headers=entete_agent).status_code == 200


def test_gestion_des_agents_reservee_aux_admins(client, entete_agent, entete_admin):
    nouveau = {"email": "kofi@signal.bj", "nom": "Kofi", "mot_de_passe": "mot-de-passe-long-1"}
    assert client.post("/api/agent/agents", json=nouveau, headers=entete_agent).status_code == 403
    assert client.post("/api/agent/agents", json=nouveau, headers=entete_admin).status_code == 201
    assert client.post("/api/agent/agents", json=nouveau, headers=entete_admin).status_code == 409
    court = dict(nouveau, email="b@signal.bj", mot_de_passe="court")
    assert client.post("/api/agent/agents", json=court, headers=entete_admin).status_code == 422
    noms = [a["nom"] for a in client.get("/api/agent/agents", headers=entete_admin).json()]
    assert "Kofi" in noms
