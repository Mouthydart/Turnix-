"""Modelo de reseña (review) de una reserva completada."""

from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.types import PyObjectId


class Review(TimestampedDocument):
    """Opinión que un cliente deja sobre una cita ya completada.

    Se guardan las referencias (`business_id`, `staff_id`, `service_id`)
    *desnormalizadas* para poder agregar valoraciones por negocio, empleado o
    servicio sin tener que resolver la reserva original.
    """

    booking_id: PyObjectId
    business_id: PyObjectId
    staff_id: PyObjectId
    service_id: PyObjectId
    customer_id: PyObjectId
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
