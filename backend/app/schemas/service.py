"""Esquemas de entrada y salida para los servicios."""

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models import AppBaseModel
from app.models.types import BsonDecimal, PyObjectId


class ServiceCreate(AppBaseModel):
    """Datos para crear un servicio dentro de un negocio."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int = Field(gt=0)
    buffer_minutes: int = Field(default=0, ge=0)
    price: BsonDecimal = Field(default=Decimal(0), ge=0)
    is_active: bool = True


class ServiceUpdate(AppBaseModel):
    """Actualización parcial de un servicio (todos los campos opcionales)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int | None = Field(default=None, gt=0)
    buffer_minutes: int | None = Field(default=None, ge=0)
    price: BsonDecimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ServicePublic(AppBaseModel):
    """Datos públicos de un servicio."""

    id: PyObjectId
    business_id: PyObjectId
    name: str
    description: str | None = None
    duration_minutes: int
    buffer_minutes: int
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
