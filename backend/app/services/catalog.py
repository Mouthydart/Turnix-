"""Catálogo público de negocios, servicios y empleados.

No requiere autenticación: expone únicamente negocios activos y sus recursos
reservables (servicios y empleados activos). La reserva final sigue siendo
autenticada y se realiza a través del módulo de reservas.
"""

import re

from fastapi import HTTPException, status
from pymongo import ASCENDING, DESCENDING

from app.db.repositories import (
    business_repository,
    service_repository,
    staff_repository,
)
from app.models import Business, Service, Staff
from app.models.types import validate_object_id


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


async def _get_active_business(business_id: str) -> Business:
    """Carga un negocio activo o lanza 404."""
    try:
        object_id = validate_object_id(business_id)
    except ValueError as exc:
        raise _not_found("Negocio no encontrado") from exc

    business = await business_repository.get_by_id(object_id)
    if business is None or not business.is_active:
        raise _not_found("Negocio no encontrado")
    return business


async def list_catalog_businesses(
    *,
    query: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Business]:
    """Lista negocios activos, opcionalmente filtrados por texto."""
    filters: dict = {"is_active": True}
    term = (query or "").strip()
    if term:
        pattern = re.escape(term)
        filters["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
            {"address": {"$regex": pattern, "$options": "i"}},
        ]

    return await business_repository.find_many(
        filters,
        skip=skip,
        limit=limit,
        sort=[("rating_avg", DESCENDING), ("name", ASCENDING)],
    )


async def get_catalog_business(
    business_id: str,
) -> tuple[Business, list[Service], list[Staff]]:
    """Devuelve el negocio activo con sus servicios y empleados reservables.

    Solo se incluyen empleados activos que ofrecen al menos un servicio activo
    del negocio. Así el cliente no ve profesionales sin disponibilidad real.
    """
    business = await _get_active_business(business_id)

    services = await service_repository.find_many(
        {"business_id": business.id, "is_active": True},
        sort=[("name", ASCENDING)],
    )
    active_service_ids = {service.id for service in services}

    staff = await staff_repository.find_many(
        {"business_id": business.id, "is_active": True},
        sort=[("display_name", ASCENDING)],
    )
    bookable_staff = [
        member
        for member in staff
        if any(service_id in active_service_ids for service_id in member.services)
    ]
    return business, services, bookable_staff
