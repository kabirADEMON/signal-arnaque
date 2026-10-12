from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import Canal, Categorie, Role, Statut, TypeElement


class ElementIn(BaseModel):
    type: TypeElement
    valeur: str = Field(min_length=2, max_length=300)


class SignalementIn(BaseModel):
    categorie: Categorie
    canal: Canal
    description: str = Field(min_length=20, max_length=4000)
    montant_perdu: int | None = Field(default=None, ge=0, le=1_000_000_000)
    date_faits: date | None = None
    elements: list[ElementIn] = Field(default_factory=list, max_length=10)
    contact: str | None = Field(default=None, max_length=254)

    @field_validator("date_faits")
    @classmethod
    def pas_dans_le_futur(cls, v: date | None) -> date | None:
        if v and v > date.today():
            raise ValueError("la date des faits ne peut pas être dans le futur")
        return v

    @field_validator("description", "contact")
    @classmethod
    def sans_espaces_inutiles(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class SignalementCree(BaseModel):
    reference: str
    code_suivi: str


class SuiviIn(BaseModel):
    reference: str = Field(max_length=16)
    code: str = Field(max_length=20)


class EtapeOut(BaseModel):
    statut: Statut
    motif: str | None
    date: datetime


class SuiviOut(BaseModel):
    reference: str
    categorie: Categorie
    statut: Statut
    cree_le: datetime
    historique: list[EtapeOut]


class VerificationOut(BaseModel):
    valeur_normalisee: str
    type: TypeElement
    signalements_valides: int
    categories: list[Categorie]
    dernier_signalement: datetime | None


class CompteCategorie(BaseModel):
    categorie: Categorie
    total: int
    valides: int
    montant_valide: int


class CompteMois(BaseModel):
    mois: str  # « 2026-10 »
    total: int


class StatistiquesOut(BaseModel):
    total: int
    valides: int
    montant_perdu_valide: int
    par_categorie: list[CompteCategorie]
    par_statut: dict[Statut, int]
    par_mois: list[CompteMois]


# ---------- Agents ----------

class ConnexionIn(BaseModel):
    email: EmailStr
    mot_de_passe: str = Field(max_length=200)


class JetonOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nom: str
    role: Role


class AgentIn(BaseModel):
    email: EmailStr
    nom: str = Field(min_length=2, max_length=120)
    mot_de_passe: str = Field(min_length=12, max_length=200)
    role: Role = Role.agent


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nom: str
    role: Role
    actif: bool


class ElementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: TypeElement
    valeur: str
    valeur_normalisee: str


class EvenementOut(BaseModel):
    ancien_statut: Statut | None
    nouveau_statut: Statut
    motif: str | None
    agent: str | None
    date: datetime


class SignalementResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    categorie: Categorie
    canal: Canal
    statut: Statut
    montant_perdu: int | None
    cree_le: datetime
    extrait: str


class PageSignalements(BaseModel):
    total: int
    page: int
    par_page: int
    elements: list[SignalementResume]


class SignalementDetail(BaseModel):
    id: int
    reference: str
    categorie: Categorie
    canal: Canal
    statut: Statut
    description: str
    montant_perdu: int | None
    date_faits: date | None
    contact: str | None
    cree_le: datetime
    elements: list[ElementOut]
    historique: list[EvenementOut]
    transitions_possibles: list[Statut]


class ChangementStatutIn(BaseModel):
    statut: Statut
    motif: str | None = Field(default=None, max_length=500)
