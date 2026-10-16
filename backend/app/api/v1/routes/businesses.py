"""Rutas del CRUD de negocios."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.business import BusinessCreate, BusinessPublic, BusinessUpdate
from app.services import business as business_service

router = APIRouter()


@router.post(
    "",
    response_model=BusinessPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un negocio",
)
async def create_business(
    payload: BusinessCreate,
    user: User = Depends(get_current_active_user),
) -> BusinessPublic:
    business = await business_service.create_business(user, payload)
    return BusinessPublic.model_validate(business)


@router.get("", response_model=list[BusinessPublic], summary="Listar mis negocios")
async def list_businesses(
    user: User = Depends(get_current_active_user),
) -> list[BusinessPublic]:
    businesses = await business_service.list_businesses(user)
    return [BusinessPublic.model_validate(business) for business in businesses]


@router.get("/{business_id}", response_model=BusinessPublic, summary="Obtener un negocio")
async def get_business(
    business_id: str,
    user: User = Depends(get_current_active_user),
) -> BusinessPublic:
    business = await business_service.get_business(business_id, user)
    return BusinessPublic.model_validate(business)


@router.patch(
    "/{business_id}",
    response_model=BusinessPublic,
    summary="Actualizar un negocio",
)
async def update_business(
    business_id: str,
    payload: BusinessUpdate,
    user: User = Depends(get_current_active_user),
) -> BusinessPublic:
    business = await business_service.update_business(business_id, user, payload)
    return BusinessPublic.model_validate(business)


@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un negocio",
)
async def delete_business(
    business_id: str,
    user: User = Depends(get_current_active_user),
) -> None:
    await business_service.delete_business(business_id, user)
