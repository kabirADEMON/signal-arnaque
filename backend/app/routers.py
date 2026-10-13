from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from . import services
from .database import get_db
from .deps import current_admin, current_agent, limits, rate_limit
from .models import Agent, Categorie, Element, Signalement, Statut
from .schemas import (
    AgentIn, AgentOut, ChangementStatutIn, ConnexionIn, EtapeOut, EvenementOut, JetonOut,
    PageSignalements, SignalementCree, SignalementDetail, SignalementIn, SignalementResume,
    StatistiquesOut, SuiviIn, SuiviOut, VerificationOut,
)
from .security import DUMMY_HASH, create_token, hash_secret, verify_secret

public = APIRouter(prefix="/api", tags=["public"])
agents = APIRouter(prefix="/api/agent", tags=["agents"])


# ---------- Public ----------

@public.post("/signalements", response_model=SignalementCree, status_code=201,
             dependencies=[Depends(rate_limit("signalement"))])
def signaler(data: SignalementIn, db: Session = Depends(get_db)):
    s, code = services.creer_signalement(db, data)
    return SignalementCree(reference=s.reference, code_suivi=code)


# POST plutôt que GET : le code de suivi ne doit pas apparaître dans les adresses ni les journaux.
@public.post("/suivi", response_model=SuiviOut, dependencies=[Depends(rate_limit("suivi"))])
def suivi(data: SuiviIn, db: Session = Depends(get_db)):
    s = db.scalar(
        select(Signalement).options(selectinload(Signalement.historique))
        .where(Signalement.reference == data.reference.strip().upper())
    )
    # Même réponse que la référence existe ou non : on ne révèle rien sans le bon code.
    if not verify_secret(data.code.strip().upper(), s.code_suivi_hash if s else DUMMY_HASH) or not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Référence ou code de suivi incorrect")
    return SuiviOut(
        reference=s.reference, categorie=s.categorie, statut=s.statut, cree_le=s.cree_le,
        historique=[EtapeOut(statut=e.nouveau_statut, motif=e.motif, date=e.cree_le) for e in s.historique],
    )


@public.get("/verifier", response_model=VerificationOut, dependencies=[Depends(rate_limit("verifier"))])
def verifier(valeur: str = Query(min_length=3, max_length=300), db: Session = Depends(get_db)):
    return services.verifier(db, valeur)


@public.get("/statistiques", response_model=StatistiquesOut)
def statistiques(db: Session = Depends(get_db)):
    return services.statistiques(db)


@public.post("/auth/connexion", response_model=JetonOut, dependencies=[Depends(rate_limit("connexion"))])
def connexion(data: ConnexionIn, db: Session = Depends(get_db)):
    compte = data.email.lower()
    if limits["echecs_compte"].blocked(compte):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Trop d'échecs pour ce compte. Réessayez dans 15 minutes.")
    agent = db.scalar(select(Agent).where(func.lower(Agent.email) == compte))
    ok = verify_secret(data.mot_de_passe, agent.mot_de_passe_hash if agent else DUMMY_HASH)
    if not agent or not ok or not agent.actif:
        limits["echecs_compte"].hit(compte)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou mot de passe incorrect")
    return JetonOut(access_token=create_token(agent.id), nom=agent.nom, role=agent.role)


# ---------- Agents ----------

@agents.get("/moi", response_model=AgentOut)
def moi(agent: Agent = Depends(current_agent)):
    return agent


@agents.get("/signalements", response_model=PageSignalements)
def lister(
    statut: Statut | None = None,
    categorie: Categorie | None = None,
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    par_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Agent = Depends(current_agent),
):
    query = select(Signalement)
    if statut:
        query = query.where(Signalement.statut == statut)
    if categorie:
        query = query.where(Signalement.categorie == categorie)
    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(
            Signalement.reference.ilike(like),
            Signalement.description.ilike(like),
            Signalement.elements.any(Element.valeur_normalisee.ilike(like)),
            Signalement.elements.any(Element.valeur.ilike(like)),
        ))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(
        query.order_by(Signalement.cree_le.desc(), Signalement.id.desc()).offset((page - 1) * par_page).limit(par_page)
    ).all()
    return PageSignalements(
        total=total, page=page, par_page=par_page,
        elements=[
            SignalementResume(
                id=s.id, reference=s.reference, categorie=s.categorie, canal=s.canal, statut=s.statut,
                montant_perdu=s.montant_perdu, cree_le=s.cree_le,
                extrait=s.description[:140] + ("…" if len(s.description) > 140 else ""),
            )
            for s in rows
        ],
    )


def _detail(s: Signalement) -> SignalementDetail:
    return SignalementDetail(
        id=s.id, reference=s.reference, categorie=s.categorie, canal=s.canal, statut=s.statut,
        description=s.description, montant_perdu=s.montant_perdu, date_faits=s.date_faits,
        contact=s.contact, cree_le=s.cree_le, elements=s.elements,
        historique=[
            EvenementOut(ancien_statut=e.ancien_statut, nouveau_statut=e.nouveau_statut, motif=e.motif,
                         agent=e.agent.nom if e.agent else None, date=e.cree_le)
            for e in s.historique
        ],
        transitions_possibles=sorted(services.TRANSITIONS[s.statut], key=lambda x: x.value),
    )


def _charger(db: Session, signalement_id: int) -> Signalement:
    s = db.scalar(
        select(Signalement)
        .options(selectinload(Signalement.elements), selectinload(Signalement.historique))
        .where(Signalement.id == signalement_id)
    )
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Signalement introuvable")
    return s


@agents.get("/signalements/{signalement_id}", response_model=SignalementDetail)
def detail(signalement_id: int, db: Session = Depends(get_db), _: Agent = Depends(current_agent)):
    return _detail(_charger(db, signalement_id))


@agents.post("/signalements/{signalement_id}/statut", response_model=SignalementDetail)
def changer_statut(signalement_id: int, data: ChangementStatutIn, db: Session = Depends(get_db),
                   agent: Agent = Depends(current_agent)):
    s = _charger(db, signalement_id)
    try:
        services.changer_statut(db, s, data.statut, data.motif, agent)
    except services.TransitionInterdite as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
    return _detail(_charger(db, signalement_id))


@agents.get("/agents", response_model=list[AgentOut])
def lister_agents(db: Session = Depends(get_db), _: Agent = Depends(current_admin)):
    return db.scalars(select(Agent).order_by(Agent.nom)).all()


@agents.post("/agents", response_model=AgentOut, status_code=201)
def creer_agent(data: AgentIn, db: Session = Depends(get_db), _: Agent = Depends(current_admin)):
    if db.scalar(select(Agent).where(func.lower(Agent.email) == data.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Un agent utilise déjà cet email")
    agent = Agent(email=data.email.lower(), nom=data.nom, mot_de_passe_hash=hash_secret(data.mot_de_passe), role=data.role)
    db.add(agent)
    db.commit()
    return agent
