"""Rutas de reservas y disponibilidad.

- Reservas anidadas bajo el negocio: crear, listar, obtener, cambiar estado y
  eliminar.
- `GET /bookings/mine`: reservas del usuario autenticado como cliente.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.booking import (
    AvailabilityResponse,
    BookingCreate,
    BookingPublic,
    BookingStatusUpdate,
)
from app.services import booking as booking_service

router = APIRouter()
me_router = APIRouter()


@router.get(
    "/{business_id}/availability",
    response_model=AvailabilityResponse,
    summary="Consultar disponibilidad",
)
async def get_availability(
    business_id: str,
    service_id: str = Query(...),
    staff_id: str = Query(...),
    target_date: date = Query(..., alias="date"),
) -> AvailabilityResponse:
    return await booking_service.get_availability(business_id, service_id, staff_id, target_date)


@router.post(
    "/{business_id}/bookings",
    response_model=BookingPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una reserva",
)
async def create_booking(
    business_id: str,
    payload: BookingCreate,
    user: User = Depends(get_current_active_user),
) -> BookingPublic:
    booking = await booking_service.create_booking(user, business_id, payload)
    return BookingPublic.model_validate(booking)


@router.get(
    "/{business_id}/bookings",
    response_model=list[BookingPublic],
    summary="Listar reservas de un negocio",
)
async def list_business_bookings(
    business_id: str,
    user: User = Depends(get_current_active_user),
) -> list[BookingPublic]:
    bookings = await booking_service.list_business_bookings(user, business_id)
    return [BookingPublic.model_validate(booking) for booking in bookings]


@router.get(
    "/{business_id}/bookings/{booking_id}",
    response_model=BookingPublic,
    summary="Obtener una reserva",
)
async def get_booking(
    business_id: str,
    booking_id: str,
    user: User = Depends(get_current_active_user),
) -> BookingPublic:
    booking = await booking_service.get_booking(user, business_id, booking_id)
    return BookingPublic.model_validate(booking)


@router.patch(
    "/{business_id}/bookings/{booking_id}/status",
    response_model=BookingPublic,
    summary="Cambiar el estado de una reserva",
)
async def update_booking_status(
    business_id: str,
    booking_id: str,
    payload: BookingStatusUpdate,
    user: User = Depends(get_current_active_user),
) -> BookingPublic:
    booking = await booking_service.update_booking_status(user, business_id, booking_id, payload)
    return BookingPublic.model_validate(booking)


@router.delete(
    "/{business_id}/bookings/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una reserva",
)
async def delete_booking(
    business_id: str,
    booking_id: str,
    user: User = Depends(get_current_active_user),
) -> None:
    await booking_service.delete_booking(user, business_id, booking_id)


@me_router.get("/mine", response_model=list[BookingPublic], summary="Mis reservas")
async def list_my_bookings(
    user: User = Depends(get_current_active_user),
) -> list[BookingPublic]:
    bookings = await booking_service.list_my_bookings(user)
    return [BookingPublic.model_validate(booking) for booking in bookings]
