"""Esquemas de salida del módulo de reportes del negocio."""

from datetime import date, datetime
from decimal import Decimal

from app.models import AppBaseModel
from app.models.types import PyObjectId


class RevenueDay(AppBaseModel):
    """Ingresos completados de un día local del negocio."""

    date: date
    revenue: Decimal
    completed_bookings: int


class RevenueBreakdown(AppBaseModel):
    """Ingresos agrupados por servicio o empleado."""

    id: PyObjectId
    name: str
    revenue: Decimal
    completed_bookings: int
    average_ticket: Decimal


class RevenueReport(AppBaseModel):
    """Reporte 1: ingresos y ticket promedio."""

    total_revenue: Decimal
    completed_bookings: int
    average_ticket: Decimal
    previous_total_revenue: Decimal
    previous_average_ticket: Decimal
    revenue_change_percent: float | None = None
    average_ticket_change_percent: float | None = None
    daily: list[RevenueDay]
    by_service: list[RevenueBreakdown]
    by_staff: list[RevenueBreakdown]


class OccupancyStaff(AppBaseModel):
    """Ocupación de un empleado en el periodo."""

    id: PyObjectId
    name: str
    available_minutes: int
    booked_minutes: int
    no_show_minutes: int
    occupancy_rate: float


class OccupancyDay(AppBaseModel):
    """Ocupación agregada de un día local."""

    date: date
    available_minutes: int
    booked_minutes: int
    no_show_minutes: int
    occupancy_rate: float


class OccupancyReport(AppBaseModel):
    """Reporte 2: ocupación real de la agenda."""

    available_minutes: int
    booked_minutes: int
    idle_minutes: int
    no_show_minutes: int
    occupancy_rate: float
    by_staff: list[OccupancyStaff]
    daily: list[OccupancyDay]


class ServiceProfitability(AppBaseModel):
    """Rentabilidad por hora de agenda de un servicio."""

    id: PyObjectId
    name: str
    duration_minutes: int
    buffer_minutes: int
    completed_bookings: int
    revenue: Decimal
    slot_minutes: int
    revenue_per_hour: Decimal


class ProfitabilityReport(AppBaseModel):
    """Reporte 3: rentabilidad por hora de agenda."""

    revenue: Decimal
    slot_minutes: int
    revenue_per_hour: Decimal
    by_service: list[ServiceProfitability]


class WaitlistBreakdown(AppBaseModel):
    """Entradas de lista de espera agrupadas por servicio o empleado."""

    id: PyObjectId | None = None
    name: str
    total: int
    waiting: int
    offered: int
    booked: int
    expired: int
    cancelled: int
    conversion_rate: float
    estimated_value: Decimal


class WaitlistReport(AppBaseModel):
    """Reporte 6: lista de espera y demanda no atendida."""

    total_entries: int
    by_status: dict[str, int]
    conversion_rate: float
    lost_rate: float
    estimated_value: Decimal
    estimated_converted_value: Decimal
    by_service: list[WaitlistBreakdown]
    by_staff: list[WaitlistBreakdown]


class CustomerSummary(AppBaseModel):
    """Resumen de un cliente para los rankings del reporte."""

    id: PyObjectId
    name: str
    visits: int
    completed_revenue: Decimal
    last_visit: datetime | None = None


class CustomerReport(AppBaseModel):
    """Reporte 9: clientes nuevos, recurrentes y retención."""

    active_customers: int
    new_customers: int
    returning_customers: int
    repeat_customers: int
    inactive_customers_count: int
    new_customer_rate: float
    repeat_rate: float
    retention_rate: float | None = None
    average_visits_per_customer: float
    average_days_between_visits: float | None = None
    top_customers: list[CustomerSummary]
    inactive_customers: list[CustomerSummary]


class BusinessReports(AppBaseModel):
    """Respuesta completa del módulo de reportes."""

    date_from: date
    date_to: date
    timezone: str
    currency: str
    revenue: RevenueReport
    occupancy: OccupancyReport
    profitability: ProfitabilityReport
    waitlist: WaitlistReport
    customers: CustomerReport
