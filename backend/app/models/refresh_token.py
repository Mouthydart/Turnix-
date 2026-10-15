"""Modelo de token de refresco para la autenticación."""

from pydantic import AwareDatetime

from app.models.base import TimestampedDocument
from app.models.types import PyObjectId


class RefreshToken(TimestampedDocument):
    """Token de refresco asociado a un usuario.

    Nunca se guarda el token en claro: solo su *hash* (`token_hash`). Así,
    un filtrado de la base de datos no permite reutilizar los tokens.
    """

    user_id: PyObjectId
    token_hash: str
    expires_at: AwareDatetime
    revoked: bool = False
    user_agent: str | None = None
    ip_address: str | None = None
