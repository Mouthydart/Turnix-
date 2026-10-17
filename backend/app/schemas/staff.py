"""Esquemas de entrada y salida para los empleados (staff)."""

from datetime import datetime

from pydantic import Field

from app.models import AppBaseModel
from app.models.schedule import WeeklySchedule
from app.models.types import PyObjectId


class StaffCreate(AppBaseModel):
    """Datos para crear un empleado dentro de un negocio.

    `services` es la lista de servicios que puede prestar el empleado; deben
    pertenecer al mismo negocio. `schedule` es opcional: si no se indica, el
    empleado hereda el horario del negocio.
    """

    display_name: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=20)
    user_id: PyObjectId | None = None
    services: list[PyObjectId] = Field(default_factory=list)
    schedule: WeeklySchedule | None = None
    is_active: bool = True


class StaffUpdate(AppBaseModel):
    """Actualización parcial de un empleado (todos los campos opcionales)."""

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=20)
    user_id: PyObjectId | None = None
    services: list[PyObjectId] | None = None
    schedule: WeeklySchedule | None = None
    is_active: bool | None = None


class StaffPublic(AppBaseModel):
    """Datos públicos de un empleado."""

    id: PyObjectId
    business_id: PyObjectId
    user_id: PyObjectId | None = None
    display_name: str
    title: str | None = None
    color: str | None = None
    services: list[PyObjectId] = Field(default_factory=list)
    schedule: WeeklySchedule | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
