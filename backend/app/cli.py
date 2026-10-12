"""Création d'un compte administrateur : python -m app.cli creer-admin email@exemple.bj "Nom Prénom"."""

import argparse
import getpass
import sys

from sqlalchemy import func, select

from .database import SessionLocal
from .models import Agent, Role
from .security import hash_secret


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="commande", required=True)
    c = sub.add_parser("creer-admin", help="crée un compte administrateur")
    c.add_argument("email")
    c.add_argument("nom")
    args = parser.parse_args(argv)

    mot_de_passe = getpass.getpass("Mot de passe (12 caractères au moins) : ")
    if len(mot_de_passe) < 12:
        print("Mot de passe trop court.", file=sys.stderr)
        return 1
    with SessionLocal() as db:
        if db.scalar(select(Agent).where(func.lower(Agent.email) == args.email.lower())):
            print("Un compte utilise déjà cet email.", file=sys.stderr)
            return 1
        db.add(Agent(email=args.email.lower(), nom=args.nom, mot_de_passe_hash=hash_secret(mot_de_passe), role=Role.admin))
        db.commit()
    print(f"Administrateur créé : {args.email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
