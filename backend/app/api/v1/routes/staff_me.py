"""Rutas de la agenda del empleado autenticado ("/staff/me").

Solo lectura y acotadas al propio empleado: perfil, sus reservas y los bloqueos
que le afectan.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.blocked_period import BlockedPeriodPublic
from app.schemas.booking import BookingPublic
from app.schemas.staff import StaffPublic
from app.services import staff_agenda as agenda_service

router = APIRouter()


@router.get("/me", response_model=StaffPublic, summary="Mi perfil de empleado")
async def get_my_profile(
    user: User = Depends(get_current_active_user),
) -> StaffPublic:
    staff, _ = await agenda_service.get_my_profile(user)
    return StaffPublic.model_validate(staff)


@router.get("/me/agenda", response_model=list[BookingPublic], summary="Mi agenda")
async def list_my_agenda(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user: User = Depends(get_current_active_user),
) -> list[BookingPublic]:
    bookings = await agenda_service.list_my_agenda(user, date_from, date_to)
    return [BookingPublic.model_validate(booking) for booking in bookings]


@router.get(
    "/me/agenda/{booking_id}",
    response_model=BookingPublic,
    summary="Una cita de mi agenda",
)
async def get_my_booking(
    booking_id: str,
    user: User = Depends(get_current_active_user),
) -> BookingPublic:
    booking = await agenda_service.get_my_booking(user, booking_id)
    return BookingPublic.model_validate(booking)


@router.get(
    "/me/blocked-periods",
    response_model=list[BlockedPeriodPublic],
    summary="Bloqueos que me afectan",
)
async def list_my_blocked_periods(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user: User = Depends(get_current_active_user),
) -> list[BlockedPeriodPublic]:
    blocks = await agenda_service.list_my_blocked_periods(user, date_from, date_to)
    return [BlockedPeriodPublic.model_validate(block) for block in blocks]
