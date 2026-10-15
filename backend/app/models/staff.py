"""Modelo de empleado (staff) de un negocio."""

from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.schedule import WeeklySchedule
from app.models.types import PyObjectId


class Staff(TimestampedDocument):
    """Empleado o profesional que presta servicios en un negocio.

    El nombre visible (`display_name`) puede diferir del de la cuenta de
    usuario, y la vinculación con un `User` (`user_id`) es opcional: un
    negocio puede registrar empleados sin que tengan acceso a la plataforma.
    """

    business_id: PyObjectId
    user_id: PyObjectId | None = None
    display_name: str
    title: str | None = None
    color: str | None = None
    services: list[PyObjectId] = Field(default_factory=list)
    schedule: WeeklySchedule | None = None
    is_active: bool = True
