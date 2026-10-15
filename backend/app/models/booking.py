"""Modelo de reserva (booking)."""

from decimal import Decimal

from pydantic import AwareDatetime, Field, model_validator

from app.core.config import settings
from app.models.base import TimestampedDocument
from app.models.enums import BookingStatus
from app.models.types import PyObjectId


class Booking(TimestampedDocument):
    """Reserva de un servicio con un empleado en un rango de tiempo.

    `start_at` y `end_at` son `AwareDatetime`: exigen zona horaria, lo que
    evita errores al mezclar horarios locales de distintos negocios.

    `price` y `currency` son una *instantánea* del precio del servicio en el
    momento de reservar: si el servicio cambia de precio, la reserva histórica
    conserva el valor cobrado.
    """

    business_id: PyObjectId
    staff_id: PyObjectId
    service_id: PyObjectId
    customer_id: PyObjectId
    start_at: AwareDatetime
    end_at: AwareDatetime
    status: BookingStatus = BookingStatus.PENDING
    price: Decimal = Field(default=Decimal(0), ge=0)
    currency: str = settings.DEFAULT_CURRENCY
    customer_name: str | None = None
    customer_phone: str | None = None
    notes: str | None = None
    cancellation_reason: str | None = None

    @model_validator(mode="after")
    def _validate_range(self) -> "Booking":
        """Verifica que el fin de la reserva sea posterior a su inicio."""
        if self.end_at <= self.start_at:
            raise ValueError("`end_at` debe ser posterior a `start_at`")
        return self
