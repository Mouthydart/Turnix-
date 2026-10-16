"""Esquemas de entrada y salida para los negocios."""

from datetime import datetime

from pydantic import Field

from app.core.config import settings
from app.models import AppBaseModel, PlanName
from app.models.schedule import WeeklySchedule
from app.models.types import PyObjectId


class BusinessCreate(AppBaseModel):
    """Datos para crear un negocio.

    Si no se envía `slug`, se genera automáticamente a partir del `name`.
    Si no se envía `schedule`, se aplica el horario por defecto.
    """

    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=60)
    timezone: str = settings.DEFAULT_TIMEZONE
    currency: str = settings.DEFAULT_CURRENCY
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    schedule: WeeklySchedule | None = None


class BusinessUpdate(AppBaseModel):
    """Actualización parcial de un negocio (todos los campos opcionales)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=60)
    timezone: str | None = None
    currency: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    schedule: WeeklySchedule | None = None
    is_active: bool | None = None


class BusinessPublic(AppBaseModel):
    """Datos públicos de un negocio."""

    id: PyObjectId
    name: str
    slug: str
    owner_id: PyObjectId
    plan: PlanName
    timezone: str
    currency: str
    phone: str | None = None
    address: str | None = None
    description: str | None = None
    is_active: bool
    schedule: WeeklySchedule
    created_at: datetime
    updated_at: datetime
