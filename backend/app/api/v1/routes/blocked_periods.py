"""Rutas del CRUD de bloqueos de agenda (anidadas bajo un negocio)."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.blocked_period import (
    BlockedPeriodCreate,
    BlockedPeriodPublic,
    BlockedPeriodUpdate,
)
from app.services import blocked_period as block_service

router = APIRouter()


@router.post(
    "/{business_id}/blocked-periods",
    response_model=BlockedPeriodPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un bloqueo",
)
async def create_block(
    business_id: str,
    payload: BlockedPeriodCreate,
    user: User = Depends(get_current_active_user),
) -> BlockedPeriodPublic:
    block = await block_service.create_block(user, business_id, payload)
    return BlockedPeriodPublic.model_validate(block)


@router.get(
    "/{business_id}/blocked-periods",
    response_model=list[BlockedPeriodPublic],
    summary="Listar bloqueos de un negocio",
)
async def list_blocks(
    business_id: str,
    user: User = Depends(get_current_active_user),
) -> list[BlockedPeriodPublic]:
    blocks = await block_service.list_blocks(user, business_id)
    return [BlockedPeriodPublic.model_validate(block) for block in blocks]


@router.get(
    "/{business_id}/blocked-periods/{block_id}",
    response_model=BlockedPeriodPublic,
    summary="Obtener un bloqueo",
)
async def get_block(
    business_id: str,
    block_id: str,
    user: User = Depends(get_current_active_user),
) -> BlockedPeriodPublic:
    block = await block_service.get_block(user, business_id, block_id)
    return BlockedPeriodPublic.model_validate(block)


@router.patch(
    "/{business_id}/blocked-periods/{block_id}",
    response_model=BlockedPeriodPublic,
    summary="Actualizar un bloqueo",
)
async def update_block(
    business_id: str,
    block_id: str,
    payload: BlockedPeriodUpdate,
    user: User = Depends(get_current_active_user),
) -> BlockedPeriodPublic:
    block = await block_service.update_block(user, business_id, block_id, payload)
    return BlockedPeriodPublic.model_validate(block)


@router.delete(
    "/{business_id}/blocked-periods/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un bloqueo",
)
async def delete_block(
    business_id: str,
    block_id: str,
    user: User = Depends(get_current_active_user),
) -> None:
    await block_service.delete_block(user, business_id, block_id)
