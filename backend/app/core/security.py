# Seguridad utilizando JWT y hashing de contraseñas

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Devuelve el hash SHA-256 de un token.

    Se guarda el hash (no el token) en la base de datos para que un acceso
    no autorizado a esta no permita reutilizar los tokens de refresco.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_token(
    subject: str, token_type: TokenType, expires_delta: timedelta, **claims: Any
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        # `jti` (JWT ID) único: garantiza que dos tokens emitidos para el mismo
        # usuario en el mismo segundo no sean idénticos. Sin él, la rotación de
        # tokens de refresco podría reemitir exactamente el mismo token.
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + expires_delta,
        **claims,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, **claims: Any) -> str:
    return create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        **claims,
    )


def create_refresh_token(subject: str, **claims: Any) -> str:
    return create_token(
        subject,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        **claims,
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise JWTError(f"Expected token type {expected_type}")
    return payload
