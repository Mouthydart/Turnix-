"""Esquemas de salida relacionados con el usuario."""

from datetime import datetime

from pydantic import EmailStr

from app.models import AppBaseModel, UserRole
from app.models.types import PyObjectId


class UserPublic(AppBaseModel):
    """Datos de usuario seguros para exponer en la API.

    Deliberadamente **no** incluye `hashed_password` ni campos internos.
    """

    id: PyObjectId
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    role: UserRole
    business_id: PyObjectId | None = None
    is_active: bool
    created_at: datetime
