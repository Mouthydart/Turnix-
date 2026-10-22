"""Esquemas de entrada y salida para las reseñas."""

from datetime import datetime

from pydantic import Field

from app.models import AppBaseModel
from app.models.types import PyObjectId


class ReviewCreate(AppBaseModel):
    """Datos que aporta el cliente al reseñar una cita."""

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewPublic(AppBaseModel):
    """Datos públicos de una reseña."""

    id: PyObjectId
    booking_id: PyObjectId
    business_id: PyObjectId
    staff_id: PyObjectId
    service_id: PyObjectId
    customer_id: PyObjectId
    rating: int
    comment: str | None = None
    created_at: datetime
    updated_at: datetime
