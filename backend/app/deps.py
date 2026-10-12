from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Agent, Role
from .security import RateLimiter, read_token

bearer = HTTPBearer(auto_error=False)

# Limites par visiteur : signaler, se connecter, vérifier.
limits = {
    "signalement": RateLimiter(5, 600),
    "connexion": RateLimiter(10, 600),
    "suivi": RateLimiter(20, 600),
    "verifier": RateLimiter(30, 60),
}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "inconnu")


def rate_limit(name: str):
    def check(request: Request) -> None:
        if not limits[name].allow(client_ip(request)):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Trop de tentatives. Réessayez plus tard.")

    return check


def current_agent(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> Agent:
    agent_id = read_token(creds.credentials) if creds else None
    agent = db.get(Agent, agent_id) if agent_id else None
    if not agent or not agent.actif:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Connexion requise", headers={"WWW-Authenticate": "Bearer"})
    return agent


def current_admin(agent: Agent = Depends(current_agent)) -> Agent:
    if agent.role != Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Réservé aux administrateurs")
    return agent
