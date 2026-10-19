"""Esquemas de entrada y salida para la lista de espera."""

from datetime import datetime

from pydantic import AwareDatetime, Field

from app.models import AppBaseModel, WaitlistStatus
from app.models.types import PyObjectId


class WaitlistCreate(AppBaseModel):
    """Datos para anotarse a la lista de espera.

    `customer_name`/`customer_phone` son opcionales si el solicitante está
    autenticado (se toman de su perfil); obligatorios para invitados.
    """

    service_id: PyObjectId | None = None
    staff_id: PyObjectId | None = None
    customer_name: str | None = Field(default=None, max_length=120)
    customer_phone: str | None = Field(default=None, max_length=30)
    desired_from: AwareDatetime | None = None
    desired_to: AwareDatetime | None = None
    notes: str | None = Field(default=None, max_length=500)


class WaitlistStatusUpdate(AppBaseModel):
    """Cambio de estado de una entrada (gestión del negocio)."""

    status: WaitlistStatus


class WaitlistPublic(AppBaseModel):
    """Datos públicos de una entrada en la lista de espera."""

    id: PyObjectId
    business_id: PyObjectId
    service_id: PyObjectId | None = None
    staff_id: PyObjectId | None = None
    customer_id: PyObjectId | None = None
    customer_name: str
    customer_phone: str | None = None
    desired_from: datetime | None = None
    desired_to: datetime | None = None
    status: WaitlistStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
