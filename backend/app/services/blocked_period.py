"""Lógica de negocio del CRUD de bloqueos de agenda.

Un bloqueo cuelga de un negocio y, opcionalmente, de un empleado. Se verifica
la propiedad del negocio, que el empleado (si se indica) pertenezca a él y que
el rango sea coherente (`ends_at > starts_at`).
"""

from fastapi import HTTPException, status
from pymongo import ASCENDING

from app.db.repositories import blocked_period_repository, staff_repository
from app.models import BlockedPeriod, User
from app.models.types import validate_object_id
from app.schemas.blocked_period import BlockedPeriodCreate, BlockedPeriodUpdate
from app.services.business import get_managed_business


def _assert_range(starts_at, ends_at) -> None:
    """Verifica que el fin del bloqueo sea posterior a su inicio."""
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`ends_at` debe ser posterior a `starts_at`",
        )


async def _validate_staff(business_id: object, staff_id: object) -> None:
    """Comprueba que el empleado pertenece al negocio."""
    try:
        staff = await staff_repository.find_one(
            {"_id": validate_object_id(staff_id), "business_id": business_id}
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado indicado no es válido",
        ) from exc
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado indicado no pertenece a este negocio",
        )


async def _get_block_in_business(block_id: object, business_id: object) -> BlockedPeriod:
    """Carga un bloqueo asegurando que pertenece al negocio indicado."""
    try:
        object_id = validate_object_id(block_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bloqueo no encontrado",
        ) from exc

    block = await blocked_period_repository.find_one(
        {"_id": object_id, "business_id": business_id}
    )
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bloqueo no encontrado",
        )
    return block


async def create_block(user: User, business_id: str, payload: BlockedPeriodCreate) -> BlockedPeriod:
    """Crea un bloqueo en un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    _assert_range(payload.starts_at, payload.ends_at)
    if payload.staff_id is not None:
        await _validate_staff(business.id, payload.staff_id)

    block = BlockedPeriod(
        business_id=business.id,
        staff_id=payload.staff_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        reason=payload.reason,
    )
    return await blocked_period_repository.insert(block)


async def list_blocks(user: User, business_id: str) -> list[BlockedPeriod]:
    """Lista los bloqueos de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await blocked_period_repository.find_many(
        {"business_id": business.id}, sort=[("starts_at", ASCENDING)]
    )


async def get_block(user: User, business_id: str, block_id: str) -> BlockedPeriod:
    """Devuelve un bloqueo de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await _get_block_in_business(block_id, business.id)


async def update_block(
    user: User, business_id: str, block_id: str, payload: BlockedPeriodUpdate
) -> BlockedPeriod:
    """Actualiza parcialmente un bloqueo de un negocio gestionable."""
    business = await get_managed_business(business_id, user)
    block = await _get_block_in_business(block_id, business.id)

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("staff_id") is not None:
        await _validate_staff(business.id, payload.staff_id)

    starts_at = changes.get("starts_at", block.starts_at)
    ends_at = changes.get("ends_at", block.ends_at)
    _assert_range(starts_at, ends_at)

    if not changes:
        return block

    updated = await blocked_period_repository.update(block.id, changes)
    if updated is None:  # pragma: no cover - el bloqueo existe, no debería ocurrir
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bloqueo no encontrado",
        )
    return updated


async def delete_block(user: User, business_id: str, block_id: str) -> None:
    """Elimina un bloqueo de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    block = await _get_block_in_business(block_id, business.id)
    await blocked_period_repository.delete(block.id)
