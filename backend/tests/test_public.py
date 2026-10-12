from datetime import date, timedelta

from sqlalchemy import select

from app import services
from app.models import Signalement, Statut
from tests.conftest import signalement


def test_signaler_renvoie_reference_et_code(client, db):
    r = client.post("/api/signalements", json=signalement(contact="victime@mail.bj"))
    assert r.status_code == 201
    body = r.json()
    assert body["reference"].startswith("SA-") and len(body["reference"]) == 11
    s = db.scalar(select(Signalement))
    assert s.statut == Statut.recu
    assert s.code_suivi_hash != body["code_suivi"]  # jamais stocké en clair
    assert [e.valeur_normalisee for e in s.elements] == ["+2290197123456"]


def test_elements_dedoublonnes(creer, db):
    creer(elements=[
        {"type": "telephone", "valeur": "97 12 34 56"},
        {"type": "telephone", "valeur": "+229 01 97 12 34 56"},
        {"type": "site", "valeur": "https://www.faux.com/x"},
    ])
    s = db.scalar(select(Signalement))
    assert sorted(e.valeur_normalisee for e in s.elements) == ["+2290197123456", "faux.com"]


def test_validation_des_donnees(client):
    demain = (date.today() + timedelta(days=1)).isoformat()
    for invalide in (
        signalement(description="trop court"),
        signalement(date_faits=demain),
        signalement(montant_perdu=-5),
        signalement(categorie="inconnue"),
        signalement(elements=[{"type": "telephone", "valeur": "97123456"}] * 11),
    ):
        assert client.post("/api/signalements", json=invalide).status_code == 422


def test_suivi_avec_le_bon_code(client, creer):
    cree = creer()
    r = client.post("/api/suivi", json={"reference": cree["reference"].lower(), "code": cree["code_suivi"]})
    assert r.status_code == 200
    body = r.json()
    assert body["statut"] == "recu"
    assert [e["statut"] for e in body["historique"]] == ["recu"]


def test_suivi_ne_revele_rien_sans_le_bon_code(client, creer):
    cree = creer()
    mauvais_code = client.post("/api/suivi", json={"reference": cree["reference"], "code": "XXXXXXXXXX"})
    inconnue = client.post("/api/suivi", json={"reference": "SA-AAAAAAAA", "code": cree["code_suivi"]})
    assert mauvais_code.status_code == inconnue.status_code == 404
    assert mauvais_code.json() == inconnue.json()


def test_verifier_ne_compte_que_les_signalements_valides(client, creer, db, agent):
    for _ in range(3):
        creer()
    assert client.get("/api/verifier", params={"valeur": "+229 01 97 12 34 56"}).json()["signalements_valides"] == 0

    s = db.scalars(select(Signalement)).first()
    services.changer_statut(db, s, Statut.en_examen, None, agent)
    services.changer_statut(db, s, Statut.valide, "Numéro confirmé par l'opérateur", agent)

    r = client.get("/api/verifier", params={"valeur": "97123456"}).json()
    assert r["type"] == "telephone"
    assert r["valeur_normalisee"] == "+2290197123456"
    assert r["signalements_valides"] == 1
    assert r["categories"] == ["mobile_money"]


def test_statistiques(client, creer, db, agent):
    creer()
    creer(categorie="faux_site", canal="site_web", montant_perdu=None,
          elements=[{"type": "site", "valeur": "faux.com"}])
    creer(montant_perdu=20000)
    s = db.scalars(select(Signalement).where(Signalement.montant_perdu == 20000)).one()
    services.changer_statut(db, s, Statut.en_examen, None, agent)
    services.changer_statut(db, s, Statut.valide, "Confirmé", agent)

    stats = client.get("/api/statistiques").json()
    assert stats["total"] == 3 and stats["valides"] == 1
    assert stats["montant_perdu_valide"] == 20000  # seuls les montants validés sont additionnés
    mm = next(c for c in stats["par_categorie"] if c["categorie"] == "mobile_money")
    assert (mm["total"], mm["valides"]) == (2, 1)
    assert len(stats["par_categorie"]) == 5  # toutes les catégories, même vides
    assert stats["par_statut"] == {"recu": 2, "en_examen": 0, "valide": 1, "rejete": 0}
    assert stats["par_mois"] == [{"mois": date.today().strftime("%Y-%m"), "total": 3}]


def test_limite_de_signalements_par_visiteur(client):
    codes = [client.post("/api/signalements", json=signalement()).status_code for _ in range(6)]
    assert codes == [201] * 5 + [429]


def test_en_tetes_de_securite(client):
    r = client.get("/api/statistiques")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"
