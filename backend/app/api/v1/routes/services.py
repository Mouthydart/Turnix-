"""Rutas del CRUD de servicios (anidadas bajo un negocio)."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.service import ServiceCreate, ServicePublic, ServiceUpdate
from app.services import service as service_service

router = APIRouter()


@router.post(
    "/{business_id}/services",
    response_model=ServicePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un servicio",
)
async def create_service(
    business_id: str,
    payload: ServiceCreate,
    user: User = Depends(get_current_active_user),
) -> ServicePublic:
    service = await service_service.create_service(user, business_id, payload)
    return ServicePublic.model_validate(service)


@router.get(
    "/{business_id}/services",
    response_model=list[ServicePublic],
    summary="Listar servicios de un negocio",
)
async def list_services(
    business_id: str,
    user: User = Depends(get_current_active_user),
) -> list[ServicePublic]:
    services = await service_service.list_services(user, business_id)
    return [ServicePublic.model_validate(service) for service in services]


@router.get(
    "/{business_id}/services/{service_id}",
    response_model=ServicePublic,
    summary="Obtener un servicio",
)
async def get_service(
    business_id: str,
    service_id: str,
    user: User = Depends(get_current_active_user),
) -> ServicePublic:
    service = await service_service.get_service(user, business_id, service_id)
    return ServicePublic.model_validate(service)


@router.patch(
    "/{business_id}/services/{service_id}",
    response_model=ServicePublic,
    summary="Actualizar un servicio",
)
async def update_service(
    business_id: str,
    service_id: str,
    payload: ServiceUpdate,
    user: User = Depends(get_current_active_user),
) -> ServicePublic:
    service = await service_service.update_service(user, business_id, service_id, payload)
    return ServicePublic.model_validate(service)


@router.delete(
    "/{business_id}/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un servicio",
)
async def delete_service(
    business_id: str,
    service_id: str,
    user: User = Depends(get_current_active_user),
) -> None:
    await service_service.delete_service(user, business_id, service_id)
