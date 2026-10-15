"""Modelo de servicio ofrecido por un negocio."""

from decimal import Decimal

from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.types import PyObjectId


class Service(TimestampedDocument):
    """Servicio reservable de un negocio.

    La duración (`duration_minutes`) y el margen posterior
    (`buffer_minutes`) los usa el motor de reservas para calcular la
    disponibilidad y evitar solapamientos entre citas.
    """

    business_id: PyObjectId
    name: str
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    buffer_minutes: int = Field(default=0, ge=0)
    price: Decimal = Field(default=Decimal(0), ge=0)
    is_active: bool = True
