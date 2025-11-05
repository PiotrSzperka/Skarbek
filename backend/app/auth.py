from passlib.context import CryptContext
import jwt
import os
from datetime import datetime, timedelta

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALG = "HS256"


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return pwd_ctx.verify(password, hash)


def create_token(data: dict, expires_minutes: int = 60):
    payload = data.copy()
    payload.update({"exp": datetime.utcnow() + timedelta(minutes=expires_minutes)})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None
