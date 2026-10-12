import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

# ---------- Mots de passe et codes de suivi (scrypt, bibliothèque standard) ----------

_N, _R, _P = 2**14, 8, 1


def hash_secret(secret: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(secret.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_secret(secret: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.scrypt(secret.encode(), salt=bytes.fromhex(salt_hex), n=_N, r=_R, p=_P, dklen=32)
    return hmac.compare_digest(digest.hex(), digest_hex)


# Hachage factice : quand l'email est inconnu, on calcule quand même un scrypt pour que
# le temps de réponse ne révèle pas quels comptes existent.
DUMMY_HASH = hash_secret("compte-inexistant")


# ---------- Références et codes de suivi ----------

# Sans 0/O ni 1/I/L : lisibles au téléphone et sans confusion à la saisie.
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def new_reference() -> str:
    return "SA-" + "".join(secrets.choice(ALPHABET) for _ in range(8))


def new_tracking_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(10))


# ---------- Jetons d'accès des agents ----------

def create_token(agent_id: int) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": str(agent_id), "iat": now, "exp": now + timedelta(minutes=s.jwt_minutes)}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def read_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


# ---------- Limitation du nombre de requêtes ----------

class RateLimiter:
    """Fenêtre glissante en mémoire, par clé (adresse du visiteur).

    Suffisant pour une instance ; derrière plusieurs instances, il faudrait un stockage
    partagé (Redis ou PostgreSQL)."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self.lock:
            hits = self.hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self.lock:
            self.hits.clear()
