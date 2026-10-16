"""Lógica de negocio del CRUD de servicios.

Un servicio pertenece a un negocio. Para operar sobre él se verifica primero
que el usuario pueda gestionar el negocio (propietario o admin) y después que
el servicio pertenezca a ese negocio.
"""

from fastapi import HTTPException, status

from app.db.repositories import service_repository
from app.models import Service, User
from app.models.types import validate_object_id
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.services.business import get_managed_business


async def _get_service_in_business(service_id: object, business_id: object) -> Service:
    """Carga un servicio asegurando que pertenece al negocio indicado."""
    try:
        object_id = validate_object_id(service_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado",
        ) from exc

    # Filtrar también por `business_id` evita acceder a servicios de otro negocio.
    service = await service_repository.find_one({"_id": object_id, "business_id": business_id})
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado",
        )
    return service


async def create_service(user: User, business_id: str, payload: ServiceCreate) -> Service:
    """Crea un servicio en un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    service = Service(
        business_id=business.id,
        name=payload.name,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        buffer_minutes=payload.buffer_minutes,
        price=payload.price,
        is_active=payload.is_active,
    )
    return await service_repository.insert(service)


async def list_services(user: User, business_id: str) -> list[Service]:
    """Lista los servicios de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await service_repository.find_many({"business_id": business.id})


async def get_service(user: User, business_id: str, service_id: str) -> Service:
    """Devuelve un servicio de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await _get_service_in_business(service_id, business.id)


async def update_service(
    user: User, business_id: str, service_id: str, payload: ServiceUpdate
) -> Service:
    """Actualiza parcialmente un servicio de un negocio gestionable."""
    business = await get_managed_business(business_id, user)
    service = await _get_service_in_business(service_id, business.id)

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return service

    updated = await service_repository.update(service.id, changes)
    if updated is None:  # pragma: no cover - el servicio existe, no debería ocurrir
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado",
        )
    return updated


async def delete_service(user: User, business_id: str, service_id: str) -> None:
    """Elimina un servicio de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    service = await _get_service_in_business(service_id, business.id)
    await service_repository.delete(service.id)
