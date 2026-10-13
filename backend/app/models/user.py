"""Modelo de usuario de la plataforma."""

from pydantic import EmailStr

from app.models.base import TimestampedDocument
from app.models.enums import UserRole
from app.models.types import PyObjectId


class User(TimestampedDocument):
    """Usuario de Turnix.

    Un usuario puede ser dueño de un negocio (`owner`), un empleado
    (`staff`) o un cliente (`customer`) que reserva servicios.

    Campos como `email` y `document_id` son opcionales porque un cliente
    puede reservar sin registrarse, y son únicos a nivel de colección.
    """

    email: EmailStr | None = None
    document_id: str | None = None
    full_name: str
    phone: str | None = None
    hashed_password: str | None = None
    role: UserRole = UserRole.CUSTOMER
    business_id: PyObjectId | None = None
    is_active: bool = True
