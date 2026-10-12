import enum
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Categorie(str, enum.Enum):
    mobile_money = "mobile_money"
    faux_profil = "faux_profil"
    faux_site = "faux_site"
    faux_emploi = "faux_emploi"
    autre = "autre"


class Canal(str, enum.Enum):
    whatsapp = "whatsapp"
    sms = "sms"
    appel = "appel"
    facebook = "facebook"
    site_web = "site_web"
    autre = "autre"


class Statut(str, enum.Enum):
    recu = "recu"
    en_examen = "en_examen"
    valide = "valide"
    rejete = "rejete"


class TypeElement(str, enum.Enum):
    telephone = "telephone"
    site = "site"
    profil = "profil"


class Role(str, enum.Enum):
    agent = "agent"
    admin = "admin"


def _enum(e: type[enum.Enum], name: str) -> Enum:
    return Enum(e, name=name, values_callable=lambda x: [m.value for m in x])


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    nom: Mapped[str] = mapped_column(String(120))
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(_enum(Role, "role_agent"), default=Role.agent)
    actif: Mapped[bool] = mapped_column(default=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Signalement(Base):
    __tablename__ = "signalements"
    __table_args__ = (
        CheckConstraint("montant_perdu IS NULL OR montant_perdu >= 0", name="montant_positif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(16), unique=True)
    # Le code de suivi n'est jamais stocké en clair : seul le déclarant le connaît.
    code_suivi_hash: Mapped[str] = mapped_column(String(255))
    categorie: Mapped[Categorie] = mapped_column(_enum(Categorie, "categorie"), index=True)
    canal: Mapped[Canal] = mapped_column(_enum(Canal, "canal"))
    description: Mapped[str] = mapped_column(Text)
    montant_perdu: Mapped[int | None] = mapped_column(Integer)
    date_faits: Mapped[date | None] = mapped_column(Date)
    # Coordonnées facultatives du déclarant : visibles par les agents seulement.
    contact: Mapped[str | None] = mapped_column(String(254))
    statut: Mapped[Statut] = mapped_column(_enum(Statut, "statut"), default=Statut.recu, index=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    modifie_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    elements: Mapped[list["Element"]] = relationship(
        back_populates="signalement", cascade="all, delete-orphan", order_by="Element.id"
    )
    historique: Mapped[list["Evenement"]] = relationship(
        back_populates="signalement", cascade="all, delete-orphan", order_by="Evenement.id"
    )


class Element(Base):
    """Numéro, site ou profil cité dans un signalement, sous une forme normalisée pour la recherche."""

    __tablename__ = "elements"

    id: Mapped[int] = mapped_column(primary_key=True)
    signalement_id: Mapped[int] = mapped_column(ForeignKey("signalements.id", ondelete="CASCADE"), index=True)
    type: Mapped[TypeElement] = mapped_column(_enum(TypeElement, "type_element"))
    valeur: Mapped[str] = mapped_column(String(300))
    valeur_normalisee: Mapped[str] = mapped_column(String(300), index=True)

    signalement: Mapped[Signalement] = relationship(back_populates="elements")


class Evenement(Base):
    """Journal des changements de statut : qui, quand, pourquoi."""

    __tablename__ = "evenements"

    id: Mapped[int] = mapped_column(primary_key=True)
    signalement_id: Mapped[int] = mapped_column(ForeignKey("signalements.id", ondelete="CASCADE"), index=True)
    ancien_statut: Mapped[Statut | None] = mapped_column(_enum(Statut, "statut"))
    nouveau_statut: Mapped[Statut] = mapped_column(_enum(Statut, "statut"))
    motif: Mapped[str | None] = mapped_column(String(500))
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signalement: Mapped[Signalement] = relationship(back_populates="historique")
    agent: Mapped[Agent | None] = relationship()
