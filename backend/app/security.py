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

# Paramètres stockés avec chaque empreinte : on pourra les durcir plus tard sans casser
# les comptes existants. N = 2^15 : environ 32 Mo et une fraction de seconde par calcul.
_N, _R, _P = 2**15, 8, 1
_MAXMEM = 64 * 1024 * 1024


def _scrypt(secret: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(secret.encode(), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=_MAXMEM)


def hash_secret(secret: str) -> str:
    salt = secrets.token_bytes(16)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${_scrypt(secret, salt, _N, _R, _P).hex()}"


def verify_secret(secret: str, stored: str) -> bool:
    try:
        _, n, r, p, salt_hex, digest_hex = stored.split("$")
        digest = _scrypt(secret, bytes.fromhex(salt_hex), int(n), int(r), int(p))
    except ValueError:
        return False
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

    def _recent(self, key: str, now: float) -> deque[float]:
        hits = self.hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        return hits

    def allow(self, key: str, now: float | None = None) -> bool:
        """Compte une tentative et dit si elle est permise."""
        now = time.monotonic() if now is None else now
        with self.lock:
            hits = self._recent(key, now)
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def blocked(self, key: str, now: float | None = None) -> bool:
        """Dit si la limite est atteinte, sans compter de tentative."""
        now = time.monotonic() if now is None else now
        with self.lock:
            return len(self._recent(key, now)) >= self.limit

    def hit(self, key: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        with self.lock:
            self._recent(key, now).append(now)

    def reset(self) -> None:
        with self.lock:
            self.hits.clear()
