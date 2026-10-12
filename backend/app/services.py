"""Règles métier : création, circuit des statuts, recherche et statistiques."""

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import normalize
from .models import Agent, Categorie, Element, Evenement, Signalement, Statut
from .schemas import SignalementIn
from .security import hash_secret, new_reference, new_tracking_code

# Circuit d'instruction. Une décision (validé ou rejeté) peut être revue par un agent
# qui remet le dossier en examen, mais jamais modifiée sans laisser de trace.
TRANSITIONS: dict[Statut, set[Statut]] = {
    Statut.recu: {Statut.en_examen, Statut.rejete},
    Statut.en_examen: {Statut.valide, Statut.rejete},
    Statut.valide: {Statut.en_examen},
    Statut.rejete: {Statut.en_examen},
}
# Le déclarant doit savoir pourquoi : un motif est obligatoire pour ces décisions.
MOTIF_OBLIGATOIRE = {Statut.rejete, Statut.valide}


class TransitionInterdite(Exception):
    pass


def creer_signalement(db: Session, data: SignalementIn) -> tuple[Signalement, str]:
    code = new_tracking_code()
    elements = []
    seen = set()
    for e in data.elements:
        norm = normalize.normalize(e.type, e.valeur)
        if norm and (e.type, norm) not in seen:
            seen.add((e.type, norm))
            elements.append(Element(type=e.type, valeur=e.valeur.strip(), valeur_normalisee=norm))
    for _ in range(5):  # référence aléatoire : une collision est improbable, mais on la gère
        s = Signalement(
            reference=new_reference(),
            code_suivi_hash=hash_secret(code),
            categorie=data.categorie,
            canal=data.canal,
            description=data.description,
            montant_perdu=data.montant_perdu,
            date_faits=data.date_faits,
            contact=data.contact or None,
            elements=elements,
            historique=[Evenement(ancien_statut=None, nouveau_statut=Statut.recu)],
        )
        db.add(s)
        try:
            db.commit()
            return s, code
        except IntegrityError:
            db.rollback()
    raise RuntimeError("impossible de générer une référence unique")


def changer_statut(db: Session, s: Signalement, nouveau: Statut, motif: str | None, agent: Agent) -> None:
    if nouveau not in TRANSITIONS[s.statut]:
        raise TransitionInterdite(f"passage de « {s.statut.value} » à « {nouveau.value} » impossible")
    motif = (motif or "").strip() or None
    if nouveau in MOTIF_OBLIGATOIRE and not motif:
        raise TransitionInterdite("un motif est obligatoire pour valider ou rejeter un signalement")
    s.historique.append(Evenement(ancien_statut=s.statut, nouveau_statut=nouveau, motif=motif, agent_id=agent.id))
    s.statut = nouveau
    db.commit()


def verifier(db: Session, raw: str) -> dict:
    type_ = normalize.guess_type(raw)
    norm = normalize.normalize(type_, raw)
    # Seuls les signalements validés par un agent comptent : un signalement isolé et non
    # vérifié ne doit pas suffire à désigner quelqu'un comme escroc.
    rows = db.execute(
        select(Signalement.categorie, Signalement.cree_le)
        .join(Element)
        .where(Element.type == type_, Element.valeur_normalisee == norm, Signalement.statut == Statut.valide)
        .distinct()
    ).all()
    return {
        "valeur_normalisee": norm,
        "type": type_,
        "signalements_valides": len(rows),
        "categories": sorted({r.categorie for r in rows}, key=lambda c: c.value),
        "dernier_signalement": max((r.cree_le for r in rows), default=None),
    }


def statistiques(db: Session) -> dict:
    valide = Signalement.statut == Statut.valide
    by_cat = {
        r.categorie: r
        for r in db.execute(
            select(
                Signalement.categorie,
                func.count().label("total"),
                func.count().filter(valide).label("valides"),
                func.coalesce(func.sum(case((valide, Signalement.montant_perdu), else_=0)), 0).label("montant"),
            ).group_by(Signalement.categorie)
        )
    }
    par_categorie = [
        {
            "categorie": c,
            "total": by_cat[c].total if c in by_cat else 0,
            "valides": by_cat[c].valides if c in by_cat else 0,
            "montant_valide": int(by_cat[c].montant) if c in by_cat else 0,
        }
        for c in Categorie
    ]
    par_statut = {st: 0 for st in Statut}
    for st, n in db.execute(select(Signalement.statut, func.count()).group_by(Signalement.statut)):
        par_statut[st] = n
    mois = func.to_char(func.date_trunc("month", Signalement.cree_le), "YYYY-MM")
    par_mois = [
        {"mois": m, "total": n}
        for m, n in db.execute(select(mois, func.count()).group_by(mois).order_by(mois).limit(24))
    ]
    return {
        "total": sum(par_statut.values()),
        "valides": par_statut[Statut.valide],
        "montant_perdu_valide": sum(c["montant_valide"] for c in par_categorie),
        "par_categorie": par_categorie,
        "par_statut": par_statut,
        "par_mois": par_mois[-12:],
    }
