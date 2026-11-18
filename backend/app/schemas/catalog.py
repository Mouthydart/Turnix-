"""Esquemas de salida para el catálogo público de negocios."""

from app.models import AppBaseModel
from app.models.schedule import WeeklySchedule
from app.models.types import PyObjectId
from app.schemas.service import ServicePublic
from app.schemas.staff import StaffPublic


class CatalogBusiness(AppBaseModel):
    """Datos visibles de un negocio en el catálogo público."""

    id: PyObjectId
    name: str
    slug: str
    timezone: str
    currency: str
    phone: str | None = None
    address: str | None = None
    description: str | None = None
    schedule: WeeklySchedule
    rating_avg: float = 0.0
    rating_count: int = 0


class CatalogBusinessDetail(CatalogBusiness):
    """Negocio del catálogo con sus servicios y empleados reservables."""

    services: list[ServicePublic]
    staff: list[StaffPublic]
