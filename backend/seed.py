"""Données de démonstration, entièrement fictives.

Les numéros (+229 01 00 00 00 xx) et les sites (.example, extension réservée) ne
désignent personne : aucune vraie ligne ne doit apparaître comme « arnaque confirmée ».
"""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent, Canal, Categorie, Role, Signalement, Statut, TypeElement
from app.schemas import ElementIn, SignalementIn
from app.security import hash_secret
from app.services import changer_statut, creer_signalement

MOT_DE_PASSE_DEMO = "demo-signal-2026"

CAS = [
    (Categorie.mobile_money, Canal.sms, "Un SMS m'annonçait un bonus de 150 000 F. On m'a demandé d'envoyer 5 000 F de frais de déblocage puis mon code secret.", 5000, [(TypeElement.telephone, "01 00 00 00 11")]),
    (Categorie.mobile_money, Canal.appel, "Un homme se disant agent de l'opérateur m'a appelé pour une « mise à jour du compte » et a obtenu mon code. 80 000 F ont été retirés.", 80000, [(TypeElement.telephone, "+229 01 00 00 00 12")]),
    (Categorie.mobile_money, Canal.whatsapp, "On m'a envoyé 25 000 F « par erreur » puis on m'a supplié de les renvoyer. Le premier transfert était faux.", 25000, [(TypeElement.telephone, "00 00 00 13")]),
    (Categorie.faux_profil, Canal.whatsapp, "Quelqu'un utilise la photo de mon oncle sur WhatsApp et demande de l'argent à toute la famille pour une urgence à l'hôpital.", 30000, [(TypeElement.telephone, "01 00 00 00 21"), (TypeElement.profil, "@tonton.urgence")]),
    (Categorie.faux_profil, Canal.facebook, "Faux profil d'une ONG qui promet des bourses d'études contre des frais d'inscription de 15 000 F.", 15000, [(TypeElement.profil, "facebook.com/bourses.afrique.demo")]),
    (Categorie.faux_site, Canal.site_web, "Site qui copie le portail d'une banque et demande l'identifiant, le mot de passe et le code reçu par SMS.", None, [(TypeElement.site, "https://banque-securite.example/connexion")]),
    (Categorie.faux_site, Canal.sms, "Lien reçu par SMS pour « payer une amende » sur un site qui imite un service public.", 12000, [(TypeElement.site, "amende-paiement.example")]),
    (Categorie.faux_emploi, Canal.facebook, "Offre d'emploi dans une société pétrolière : il fallait payer 40 000 F de visite médicale avant l'embauche.", 40000, [(TypeElement.telephone, "01 00 00 00 41"), (TypeElement.profil, "Recrutement Pétrole Bénin")]),
    (Categorie.faux_emploi, Canal.whatsapp, "On m'a proposé un travail à domicile « liker des vidéos » ; il fallait déposer de l'argent pour débloquer les gains.", 60000, [(TypeElement.telephone, "01 00 00 00 42")]),
    (Categorie.autre, Canal.facebook, "Vente d'une moto sur Facebook : j'ai payé l'avance de 100 000 F et le vendeur a disparu.", 100000, [(TypeElement.profil, "@motos.pas.cheres")]),
]


def seed(db: Session) -> bool:
    if db.scalar(select(Signalement.id).limit(1)):
        return False
    admin = Agent(email="admin@demo.bj", nom="Admin Démo", role=Role.admin, mot_de_passe_hash=hash_secret(MOT_DE_PASSE_DEMO))
    agent = Agent(email="agent@demo.bj", nom="Awa Agent", role=Role.agent, mot_de_passe_hash=hash_secret(MOT_DE_PASSE_DEMO))
    db.add_all([admin, agent])
    db.commit()

    rng = random.Random(2026)
    now = datetime.now(timezone.utc)
    for i in range(36):
        categorie, canal, texte, montant, elements = CAS[i % len(CAS)]
        s, _ = creer_signalement(db, SignalementIn(
            categorie=categorie, canal=canal, description=texte, montant_perdu=montant,
            elements=[ElementIn(type=t, valeur=v) for t, v in elements],
        ))
        # Répartis sur les six derniers mois, pour des statistiques réalistes.
        s.cree_le = now - timedelta(days=rng.randint(0, 175), hours=rng.randint(0, 23))
        s.historique[0].cree_le = s.cree_le
        db.commit()
        tirage = rng.random()
        if tirage < 0.75:
            changer_statut(db, s, Statut.en_examen, None, agent)
        if tirage < 0.55:
            changer_statut(db, s, Statut.valide, "Arnaque confirmée : plusieurs signalements concordants.", agent)
        elif 0.55 <= tirage < 0.65:
            changer_statut(db, s, Statut.rejete, "Informations insuffisantes pour confirmer l'arnaque.", agent)
    return True
