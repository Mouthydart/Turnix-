"""Rutas del CRUD de empleados (anidadas bajo un negocio)."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.staff import StaffCreate, StaffPublic, StaffUpdate
from app.services import staff as staff_service

router = APIRouter()


@router.post(
    "/{business_id}/staff",
    response_model=StaffPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un empleado",
)
async def create_staff(
    business_id: str,
    payload: StaffCreate,
    user: User = Depends(get_current_active_user),
) -> StaffPublic:
    staff = await staff_service.create_staff(user, business_id, payload)
    return StaffPublic.model_validate(staff)


@router.get(
    "/{business_id}/staff",
    response_model=list[StaffPublic],
    summary="Listar empleados de un negocio",
)
async def list_staff(
    business_id: str,
    user: User = Depends(get_current_active_user),
) -> list[StaffPublic]:
    staff_members = await staff_service.list_staff(user, business_id)
    return [StaffPublic.model_validate(member) for member in staff_members]


@router.get(
    "/{business_id}/staff/{staff_id}",
    response_model=StaffPublic,
    summary="Obtener un empleado",
)
async def get_staff(
    business_id: str,
    staff_id: str,
    user: User = Depends(get_current_active_user),
) -> StaffPublic:
    staff = await staff_service.get_staff(user, business_id, staff_id)
    return StaffPublic.model_validate(staff)


@router.patch(
    "/{business_id}/staff/{staff_id}",
    response_model=StaffPublic,
    summary="Actualizar un empleado",
)
async def update_staff(
    business_id: str,
    staff_id: str,
    payload: StaffUpdate,
    user: User = Depends(get_current_active_user),
) -> StaffPublic:
    staff = await staff_service.update_staff(user, business_id, staff_id, payload)
    return StaffPublic.model_validate(staff)


@router.delete(
    "/{business_id}/staff/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un empleado",
)
async def delete_staff(
    business_id: str,
    staff_id: str,
    user: User = Depends(get_current_active_user),
) -> None:
    await staff_service.delete_staff(user, business_id, staff_id)
