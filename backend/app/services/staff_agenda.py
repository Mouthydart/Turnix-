"""Lógica de negocio de la agenda del empleado ("mi agenda").

Un usuario con rol `staff` se vincula a un negocio mediante su registro `Staff`
(campo `user_id`). Aquí se resuelve ese registro y se ofrecen sus consultas:
perfil, sus reservas (como profesional asignado) y los bloqueos que le afectan.

Todo es de **solo lectura** y estrictamente acotado al propio empleado: no se
expone ninguna reserva ajena.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from pymongo import ASCENDING

from app.db.repositories import (
    blocked_period_repository,
    booking_repository,
    business_repository,
    staff_repository,
)
from app.models import BlockedPeriod, Booking, BookingStatus, Business, Staff, User
from app.models.types import validate_object_id

# Días por defecto que abarca la agenda si no se indica rango.
DEFAULT_AGENDA_DAYS = 30


async def resolve_staff_for_user(user: User) -> Staff:
    """Devuelve el registro `Staff` vinculado al usuario autenticado.

    La vinculación se hace por `Staff.user_id`. Si el usuario no está vinculado
    a ningún empleado, no puede usar la agenda (403).
    """
    staff = await staff_repository.find_one({"user_id": user.id})
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta no está vinculada a ningún empleado",
        )
    return staff


async def _get_business_or_404(business_id: object) -> Business:
    business = await business_repository.get_by_id(business_id)
    if business is None:  # pragma: no cover - la FK debería existir
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado"
        )
    return business


def _day_bounds(date_from: date | None, date_to: date | None, tz: ZoneInfo) -> tuple:
    """Convierte un rango de fechas locales en límites UTC semiabiertos.

    Por defecto abarca desde hoy hasta `DEFAULT_AGENDA_DAYS` días después.
    """
    today = datetime.now(tz).date()
    start_date = date_from or today
    end_date = date_to or (start_date + timedelta(days=DEFAULT_AGENDA_DAYS))

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="`date_to` no puede ser anterior a `date_from`",
        )

    start = datetime.combine(start_date, time(0, 0), tzinfo=tz).astimezone(UTC)
    end = datetime.combine(end_date + timedelta(days=1), time(0, 0), tzinfo=tz).astimezone(UTC)
    return start, end


async def get_my_profile(user: User) -> tuple[Staff, Business]:
    """Devuelve el empleado del usuario y su negocio."""
    staff = await resolve_staff_for_user(user)
    business = await _get_business_or_404(staff.business_id)
    return staff, business


async def list_my_agenda(
    user: User, date_from: date | None = None, date_to: date | None = None
) -> list[Booking]:
    """Lista las reservas asignadas al empleado dentro del rango indicado.

    Se excluyen las reservas canceladas y se ordenan por hora de inicio.
    """
    staff = await resolve_staff_for_user(user)
    business = await _get_business_or_404(staff.business_id)
    start, end = _day_bounds(date_from, date_to, ZoneInfo(business.timezone))

    return await booking_repository.find_many(
        {
            "staff_id": staff.id,
            "status": {"$ne": BookingStatus.CANCELLED},
            "start_at": {"$gte": start, "$lt": end},
        },
        sort=[("start_at", ASCENDING)],
    )


async def get_my_booking(user: User, booking_id: str) -> Booking:
    """Devuelve una reserva del empleado. 404 si no es suya."""
    staff = await resolve_staff_for_user(user)
    try:
        object_id = validate_object_id(booking_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada"
        ) from exc

    booking = await booking_repository.find_one({"_id": object_id, "staff_id": staff.id})
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada"
        )
    return booking


async def list_my_blocked_periods(
    user: User, date_from: date | None = None, date_to: date | None = None
) -> list[BlockedPeriod]:
    """Lista los bloqueos que afectan al empleado (propios y de todo el negocio).

    Un bloqueo afecta al empleado si tiene su `staff_id` o si su `staff_id` es
    `None` (bloqueo de negocio). Se filtra por solapamiento con el rango.
    """
    staff = await resolve_staff_for_user(user)
    business = await _get_business_or_404(staff.business_id)
    start, end = _day_bounds(date_from, date_to, ZoneInfo(business.timezone))

    return await blocked_period_repository.find_many(
        {
            "business_id": business.id,
            "$or": [{"staff_id": staff.id}, {"staff_id": None}],
            "starts_at": {"$lt": end},
            "ends_at": {"$gt": start},
        },
        sort=[("starts_at", ASCENDING)],
    )
