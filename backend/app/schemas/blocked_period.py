"""Esquemas de entrada y salida para los bloqueos de agenda."""

from datetime import datetime

from pydantic import AwareDatetime, Field

from app.models import AppBaseModel
from app.models.types import PyObjectId


class BlockedPeriodCreate(AppBaseModel):
    """Datos para crear un bloqueo.

    Si `staff_id` es `None`, el bloqueo afecta a todo el negocio; si tiene
    valor, solo al empleado indicado (vacaciones, ausencias, almuerzos...).
    """

    staff_id: PyObjectId | None = None
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    reason: str | None = Field(default=None, max_length=200)


class BlockedPeriodUpdate(AppBaseModel):
    """Actualización parcial de un bloqueo (todos los campos opcionales)."""

    staff_id: PyObjectId | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    reason: str | None = Field(default=None, max_length=200)


class BlockedPeriodPublic(AppBaseModel):
    """Datos públicos de un bloqueo."""

    id: PyObjectId
    business_id: PyObjectId
    staff_id: PyObjectId | None = None
    starts_at: datetime
    ends_at: datetime
    reason: str | None = None
    created_at: datetime
    updated_at: datetime
