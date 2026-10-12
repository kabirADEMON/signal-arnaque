"""Mise en forme commune des numéros, sites et profils, pour retrouver un même escroc
quelle que soit la façon dont chaque victime l'a écrit."""

import re
from urllib.parse import urlsplit

from .models import TypeElement


def telephone(raw: str) -> str:
    """« 97 12 34 56 », « +229 01 97123456 », « 0022997123456 » -> « +2290197123456 ».

    Depuis novembre 2024, les numéros béninois ont 10 chiffres : l'ancien numéro à
    8 chiffres précédé de « 01 ». Les deux formes désignent la même ligne.
    """
    digits = re.sub(r"\D", "", raw)
    # « 00 » n'est un préfixe international que s'il est suivi d'un indicatif et d'un numéro.
    international = digits.startswith("00") and len(digits) > 10
    if raw.strip().startswith("+") or international:
        digits = digits[2:] if international else digits
        if not digits.startswith("229"):
            return "+" + digits  # numéro étranger : gardé tel quel
        digits = digits[3:]
    elif digits.startswith("229") and len(digits) in (11, 13):
        digits = digits[3:]
    if len(digits) == 8:
        digits = "01" + digits
    return "+229" + digits


def site(raw: str) -> str:
    """« https://www.Faux-Site.com/login?x=1 » -> « faux-site.com »."""
    value = raw.strip()
    if "://" not in value:
        value = "http://" + value
    host = (urlsplit(value).hostname or "").rstrip(".").lower()
    return host.removeprefix("www.")


def profil(raw: str) -> str:
    """« @Mon.Profil » ou « facebook.com/Mon.Profil » -> « mon.profil »."""
    value = raw.strip().lower().rstrip("/")
    value = re.sub(r"^(https?://)?(www\.|m\.)?(facebook|instagram|tiktok|x|twitter)\.com/", "", value)
    return value.lstrip("@").strip()


NORMALIZERS = {TypeElement.telephone: telephone, TypeElement.site: site, TypeElement.profil: profil}


def normalize(type_: TypeElement, raw: str) -> str:
    return NORMALIZERS[type_](raw)


def guess_type(raw: str) -> TypeElement:
    """Pour la recherche publique : devine si l'on a saisi un numéro, un site ou un profil."""
    value = raw.strip()
    digits = re.sub(r"\D", "", value)
    if digits and len(digits) >= 8 and re.fullmatch(r"[\d\s+().-]+", value):
        return TypeElement.telephone
    if "." in value and " " not in value and not value.startswith("@") and not re.search(
        r"(facebook|instagram|tiktok|twitter|x)\.com/", value.lower()
    ):
        return TypeElement.site
    return TypeElement.profil
