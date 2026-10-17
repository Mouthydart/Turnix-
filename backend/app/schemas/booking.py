"""Esquemas de entrada y salida para las reservas y la disponibilidad."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import AwareDatetime, Field

from app.models import AppBaseModel, BookingStatus
from app.models.types import PyObjectId


class BookingCreate(AppBaseModel):
    """Datos para crear una reserva.

    El cliente es el usuario autenticado; el `business_id` viaja en la ruta.
    """

    service_id: PyObjectId
    staff_id: PyObjectId
    start_at: AwareDatetime
    notes: str | None = Field(default=None, max_length=1000)


class BookingStatusUpdate(AppBaseModel):
    """Cambio de estado de una reserva."""

    status: BookingStatus
    cancellation_reason: str | None = Field(default=None, max_length=500)


class BookingPublic(AppBaseModel):
    """Datos públicos de una reserva."""

    id: PyObjectId
    business_id: PyObjectId
    staff_id: PyObjectId
    service_id: PyObjectId
    customer_id: PyObjectId
    start_at: datetime
    end_at: datetime
    status: BookingStatus
    price: Decimal
    currency: str
    customer_name: str | None = None
    customer_phone: str | None = None
    notes: str | None = None
    cancellation_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class AvailabilitySlot(AppBaseModel):
    """Un hueco disponible (inicio y fin)."""

    start_at: datetime
    end_at: datetime


class AvailabilityResponse(AppBaseModel):
    """Disponibilidad de un empleado para un servicio en una fecha."""

    date: date
    timezone: str
    service_id: PyObjectId
    staff_id: PyObjectId
    slots: list[AvailabilitySlot]
