"""Esquemas de salida para el dashboard de estadísticas de un negocio."""

from decimal import Decimal

from app.models import AppBaseModel
from app.models.types import PyObjectId


class StatsItem(AppBaseModel):
    """Elemento agregado del ranking (servicio o empleado)."""

    id: PyObjectId
    name: str
    count: int


class BusinessStats(AppBaseModel):
    """Estadísticas agregadas de un negocio.

    - `bookings_by_status`: nº de reservas por cada estado.
    - `revenue_completed`: suma de los importes de las reservas completadas.
    - `top_services` / `top_staff`: los más reservados (sin contar canceladas).
    """

    total_bookings: int
    bookings_by_status: dict[str, int]
    revenue_completed: Decimal
    currency: str
    top_services: list[StatsItem]
    top_staff: list[StatsItem]
