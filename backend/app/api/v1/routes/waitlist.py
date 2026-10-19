"""Rutas de la lista de espera.

- Lado negocio (anidadas bajo el negocio): listar, ver y gestionar entradas.
- Lado cliente (`/waitlist`): mis entradas y cancelar una propia.
"""

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_active_user, get_optional_user
from app.models import User, WaitlistStatus
from app.schemas.waitlist import (
    WaitlistCreate,
    WaitlistPublic,
    WaitlistStatusUpdate,
)
from app.services import waitlist as waitlist_service

router = APIRouter()
me_router = APIRouter()


@router.post(
    "/{business_id}/waitlist",
    response_model=WaitlistPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Anotarse a la lista de espera",
)
async def join_waitlist(
    business_id: str,
    payload: WaitlistCreate,
    user: User | None = Depends(get_optional_user),
) -> WaitlistPublic:
    entry = await waitlist_service.join_waitlist(business_id, payload, user)
    return WaitlistPublic.model_validate(entry)


@router.get(
    "/{business_id}/waitlist",
    response_model=list[WaitlistPublic],
    summary="Listar la lista de espera de un negocio",
)
async def list_waitlist(
    business_id: str,
    entry_status: WaitlistStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_active_user),
) -> list[WaitlistPublic]:
    entries = await waitlist_service.list_business_waitlist(user, business_id, entry_status)
    return [WaitlistPublic.model_validate(entry) for entry in entries]


@router.get(
    "/{business_id}/waitlist/{entry_id}",
    response_model=WaitlistPublic,
    summary="Obtener una entrada de la lista de espera",
)
async def get_waitlist_entry(
    business_id: str,
    entry_id: str,
    user: User = Depends(get_current_active_user),
) -> WaitlistPublic:
    entry = await waitlist_service.get_waitlist_entry(user, business_id, entry_id)
    return WaitlistPublic.model_validate(entry)


@router.patch(
    "/{business_id}/waitlist/{entry_id}/status",
    response_model=WaitlistPublic,
    summary="Cambiar el estado de una entrada",
)
async def update_waitlist_status(
    business_id: str,
    entry_id: str,
    payload: WaitlistStatusUpdate,
    user: User = Depends(get_current_active_user),
) -> WaitlistPublic:
    entry = await waitlist_service.update_waitlist_status(user, business_id, entry_id, payload)
    return WaitlistPublic.model_validate(entry)


@router.delete(
    "/{business_id}/waitlist/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una entrada de la lista de espera",
)
async def delete_waitlist_entry(
    business_id: str,
    entry_id: str,
    user: User = Depends(get_current_active_user),
) -> None:
    await waitlist_service.delete_waitlist_entry(user, business_id, entry_id)


@me_router.get("/mine", response_model=list[WaitlistPublic], summary="Mis entradas en espera")
async def list_my_waitlist(
    user: User = Depends(get_current_active_user),
) -> list[WaitlistPublic]:
    entries = await waitlist_service.list_my_waitlist(user)
    return [WaitlistPublic.model_validate(entry) for entry in entries]


@me_router.post(
    "/mine/{entry_id}/cancel",
    response_model=WaitlistPublic,
    summary="Cancelar una entrada propia",
)
async def cancel_my_waitlist(
    entry_id: str,
    user: User = Depends(get_current_active_user),
) -> WaitlistPublic:
    entry = await waitlist_service.cancel_my_waitlist(user, entry_id)
    return WaitlistPublic.model_validate(entry)
