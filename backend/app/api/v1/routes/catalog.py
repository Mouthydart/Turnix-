"""Rutas públicas del catálogo de negocios.

Permiten explorar negocios activos, sus servicios y sus empleados sin iniciar
sesión. La creación de la reserva sí requiere autenticación.
"""

from fastapi import APIRouter, Query

from app.schemas.catalog import CatalogBusiness, CatalogBusinessDetail
from app.schemas.service import ServicePublic
from app.schemas.staff import StaffPublic
from app.services import catalog as catalog_service

router = APIRouter()


@router.get(
    "",
    response_model=list[CatalogBusiness],
    summary="Explorar negocios",
)
async def list_catalog_businesses(
    q: str | None = Query(default=None, max_length=120),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[CatalogBusiness]:
    businesses = await catalog_service.list_catalog_businesses(
        query=q,
        skip=skip,
        limit=limit,
    )
    return [CatalogBusiness.model_validate(business) for business in businesses]


@router.get(
    "/{business_id}",
    response_model=CatalogBusinessDetail,
    summary="Ver un negocio y sus servicios",
)
async def get_catalog_business(business_id: str) -> CatalogBusinessDetail:
    business, services, staff = await catalog_service.get_catalog_business(business_id)
    return CatalogBusinessDetail(
        **CatalogBusiness.model_validate(business).model_dump(),
        services=[ServicePublic.model_validate(service) for service in services],
        staff=[StaffPublic.model_validate(member) for member in staff],
    )
