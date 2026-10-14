"""Modelo de negocio (tenant) de Turnix."""

from pydantic import Field

from app.core.config import settings
from app.models.base import TimestampedDocument
from app.models.enums import PlanName
from app.models.schedule import WeeklySchedule
from app.models.types import PyObjectId


class Business(TimestampedDocument):
    """Negocio que ofrece servicios y recibe reservas.

    Es el "tenant" de la plataforma: la mayoría de las colecciones
    (staff, services, bookings, etc.) se relacionan con un negocio.
    """

    name: str
    slug: str
    owner_id: PyObjectId
    plan: PlanName = PlanName.FREEMIUM
    timezone: str = settings.DEFAULT_TIMEZONE
    currency: str = settings.DEFAULT_CURRENCY
    phone: str | None = None
    address: str | None = None
    description: str | None = None
    is_active: bool = True
    schedule: WeeklySchedule = Field(default_factory=WeeklySchedule.default)
