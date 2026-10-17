"""Lógica de negocio del CRUD de empleados (staff).

Además de la verificación habitual (dueño del negocio + pertenencia del
recurso), valida que los servicios asignados al empleado pertenezcan al mismo
negocio. Si se vincula una cuenta de usuario (`user_id`), comprueba que exista.
"""

from fastapi import HTTPException, status

from app.db.repositories import service_repository, staff_repository, user_repository
from app.models import Staff, User
from app.models.types import validate_object_id
from app.schemas.staff import StaffCreate, StaffUpdate
from app.services.business import get_managed_business


async def _get_staff_in_business(staff_id: object, business_id: object) -> Staff:
    """Carga un empleado asegurando que pertenece al negocio indicado."""
    try:
        object_id = validate_object_id(staff_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado",
        ) from exc

    staff = await staff_repository.find_one({"_id": object_id, "business_id": business_id})
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado",
        )
    return staff


async def _validated_services(business_id: object, service_ids: list) -> list:
    """Valida que todos los servicios pertenezcan al negocio.

    Deduplica conservando el orden y comprueba en una sola consulta (`$in`)
    que la cantidad de servicios encontrados coincida con la solicitada.

    Raises:
        HTTPException: 422 si alguno de los servicios no pertenece al negocio.
    """
    unique_ids = list(dict.fromkeys(service_ids))
    if not unique_ids:
        return []

    found = await service_repository.find_many(
        {"_id": {"$in": unique_ids}, "business_id": business_id}
    )
    if len(found) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uno o más servicios no pertenecen a este negocio",
        )
    return unique_ids


async def _validated_user(user_id: object) -> None:
    """Comprueba que la cuenta de usuario vinculada exista."""
    if await user_repository.get_by_id(user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario indicado no existe",
        )


async def create_staff(user: User, business_id: str, payload: StaffCreate) -> Staff:
    """Crea un empleado en un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    services = await _validated_services(business.id, payload.services)
    if payload.user_id is not None:
        await _validated_user(payload.user_id)

    staff = Staff(
        business_id=business.id,
        user_id=payload.user_id,
        display_name=payload.display_name,
        title=payload.title,
        color=payload.color,
        services=services,
        schedule=payload.schedule,
        is_active=payload.is_active,
    )
    return await staff_repository.insert(staff)


async def list_staff(user: User, business_id: str) -> list[Staff]:
    """Lista los empleados de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await staff_repository.find_many({"business_id": business.id})


async def get_staff(user: User, business_id: str, staff_id: str) -> Staff:
    """Devuelve un empleado de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await _get_staff_in_business(staff_id, business.id)


async def update_staff(
    user: User, business_id: str, staff_id: str, payload: StaffUpdate
) -> Staff:
    """Actualiza parcialmente un empleado de un negocio gestionable."""
    business = await get_managed_business(business_id, user)
    staff = await _get_staff_in_business(staff_id, business.id)

    changes = payload.model_dump(exclude_unset=True)
    if "services" in changes:
        changes["services"] = await _validated_services(business.id, payload.services or [])
    if changes.get("user_id") is not None:
        await _validated_user(payload.user_id)

    if not changes:
        return staff

    updated = await staff_repository.update(staff.id, changes)
    if updated is None:  # pragma: no cover - el empleado existe, no debería ocurrir
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado",
        )
    return updated


async def delete_staff(user: User, business_id: str, staff_id: str) -> None:
    """Elimina un empleado de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    staff = await _get_staff_in_business(staff_id, business.id)
    await staff_repository.delete(staff.id)
