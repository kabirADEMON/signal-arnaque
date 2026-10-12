import pytest

from app import normalize
from app.models import TypeElement


@pytest.mark.parametrize("raw", [
    "97 12 34 56", "97123456", "+229 97 12 34 56", "0022997123456",
    "01 97 12 34 56", "+229 01 97 12 34 56", "229 01 97 12 34 56", "(+229) 0197-12-34-56",
])
def test_toutes_les_ecritures_d_un_numero_beninois(raw):
    # L'ancien numéro à 8 chiffres et le nouveau à 10 chiffres désignent la même ligne.
    assert normalize.telephone(raw) == "+2290197123456"


def test_numero_etranger_garde_tel_quel():
    assert normalize.telephone("+33 6 12 34 56 78") == "+33612345678"


@pytest.mark.parametrize("raw", ["https://www.Faux-Site.com/login?x=1", "faux-site.com", "http://faux-site.com./"])
def test_site(raw):
    assert normalize.site(raw) == "faux-site.com"


@pytest.mark.parametrize("raw", ["@Mon.Profil", "https://www.facebook.com/Mon.Profil/", "mon.profil"])
def test_profil(raw):
    assert normalize.profil(raw) == "mon.profil"


@pytest.mark.parametrize("raw, attendu", [
    ("+229 97 12 34 56", TypeElement.telephone),
    ("97123456", TypeElement.telephone),
    ("faux-site.com/payer", TypeElement.site),
    ("@arnaqueur", TypeElement.profil),
    ("facebook.com/arnaqueur", TypeElement.profil),
    ("Jean Recruteur", TypeElement.profil),
])
def test_type_devine(raw, attendu):
    assert normalize.guess_type(raw) == attendu


def test_numero_local_commencant_par_00_n_est_pas_international():
    assert normalize.telephone("00 00 00 99") == "+2290100000099"
    assert normalize.telephone("0033 6 12 34 56 78") == "+33612345678"
