"""Lógica de negocio de la lista de espera.

Un cliente se anota cuando no encuentra hueco (o de forma preventiva). El
negocio gestiona las entradas cambiando su estado. Además, al cancelarse una
reserva, las entradas compatibles pasan a `offered` para avisar de que hay
disponibilidad.
"""

from fastapi import HTTPException, status
from pymongo import ASCENDING

from app.db.repositories import (
    business_repository,
    service_repository,
    staff_repository,
    waitlist_repository,
)
from app.models import (
    Booking,
    Business,
    Service,
    Staff,
    User,
    Waitlist,
    WaitlistStatus,
)
from app.models.types import validate_object_id
from app.schemas.waitlist import WaitlistCreate, WaitlistStatusUpdate
from app.services.business import get_managed_business


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


async def _get_active_business(business_id: str) -> Business:
    """Carga un negocio activo (los clientes se anotan sin ser propietarios)."""
    try:
        object_id = validate_object_id(business_id)
    except ValueError as exc:
        raise _not_found("Negocio no encontrado") from exc

    business = await business_repository.get_by_id(object_id)
    if business is None or not business.is_active:
        raise _not_found("Negocio no encontrado")
    return business


async def _validate_service(business_id: object, service_id: object) -> Service:
    """Comprueba que el servicio pertenece al negocio."""
    try:
        service = await service_repository.find_one(
            {"_id": validate_object_id(service_id), "business_id": business_id}
        )
    except ValueError as exc:
        raise _unprocessable("El servicio indicado no es válido") from exc
    if service is None:
        raise _unprocessable("El servicio indicado no pertenece a este negocio")
    return service


async def _validate_staff(business_id: object, staff_id: object) -> Staff:
    """Comprueba que el empleado pertenece al negocio."""
    try:
        staff = await staff_repository.find_one(
            {"_id": validate_object_id(staff_id), "business_id": business_id}
        )
    except ValueError as exc:
        raise _unprocessable("El empleado indicado no es válido") from exc
    if staff is None:
        raise _unprocessable("El empleado indicado no pertenece a este negocio")
    return staff


def _assert_desired_range(desired_from, desired_to) -> None:
    """Verifica que la ventana deseada sea coherente."""
    if desired_from and desired_to and desired_to <= desired_from:
        raise _unprocessable("`desired_to` debe ser posterior a `desired_from`")


async def join_waitlist(
    business_id: str, payload: WaitlistCreate, user: User | None = None
) -> Waitlist:
    """Anota a un cliente en la lista de espera de un negocio.

    Funciona para usuarios registrados (se enlaza `customer_id` y se heredan
    nombre/teléfono) y para invitados (deben aportar `customer_name`).
    """
    business = await _get_active_business(business_id)

    if payload.service_id is not None:
        await _validate_service(business.id, payload.service_id)
    if payload.staff_id is not None:
        await _validate_staff(business.id, payload.staff_id)

    _assert_desired_range(payload.desired_from, payload.desired_to)

    customer_name = payload.customer_name or (user.full_name if user else None)
    if not customer_name:
        raise _unprocessable("Se requiere `customer_name`")

    customer_phone = payload.customer_phone or (user.phone if user else None)

    entry = Waitlist(
        business_id=business.id,
        service_id=payload.service_id,
        staff_id=payload.staff_id,
        customer_id=user.id if user else None,
        customer_name=customer_name,
        customer_phone=customer_phone,
        desired_from=payload.desired_from,
        desired_to=payload.desired_to,
        status=WaitlistStatus.WAITING,
        notes=payload.notes,
    )
    return await waitlist_repository.insert(entry)


async def list_business_waitlist(
    user: User, business_id: str, entry_status: WaitlistStatus | None = None
) -> list[Waitlist]:
    """Lista las entradas de la lista de espera de un negocio gestionable."""
    business = await get_managed_business(business_id, user)
    query: dict[str, object] = {"business_id": business.id}
    if entry_status is not None:
        query["status"] = entry_status
    return await waitlist_repository.find_many(query, sort=[("created_at", ASCENDING)])


async def list_my_waitlist(user: User) -> list[Waitlist]:
    """Lista las entradas del usuario como cliente."""
    return await waitlist_repository.find_many(
        {"customer_id": user.id}, sort=[("created_at", ASCENDING)]
    )


async def _get_entry_in_business(entry_id: object, business_id: object) -> Waitlist:
    """Carga una entrada asegurando que pertenece al negocio indicado."""
    try:
        object_id = validate_object_id(entry_id)
    except ValueError as exc:
        raise _not_found("Entrada no encontrada") from exc

    entry = await waitlist_repository.find_one({"_id": object_id, "business_id": business_id})
    if entry is None:
        raise _not_found("Entrada no encontrada")
    return entry


async def get_waitlist_entry(user: User, business_id: str, entry_id: str) -> Waitlist:
    """Devuelve una entrada de un negocio gestionable por el usuario."""
    business = await get_managed_business(business_id, user)
    return await _get_entry_in_business(entry_id, business.id)


async def update_waitlist_status(
    user: User, business_id: str, entry_id: str, payload: WaitlistStatusUpdate
) -> Waitlist:
    """Cambia el estado de una entrada (solo gestores del negocio)."""
    business = await get_managed_business(business_id, user)
    entry = await _get_entry_in_business(entry_id, business.id)

    updated = await waitlist_repository.update(entry.id, {"status": payload.status})
    if updated is None:  # pragma: no cover - la entrada existe, no debería ocurrir
        raise _not_found("Entrada no encontrada")
    return updated


async def cancel_my_waitlist(user: User, entry_id: str) -> Waitlist:
    """Cancela una entrada propia del usuario."""
    try:
        object_id = validate_object_id(entry_id)
    except ValueError as exc:
        raise _not_found("Entrada no encontrada") from exc

    entry = await waitlist_repository.find_one({"_id": object_id, "customer_id": user.id})
    if entry is None:
        raise _not_found("Entrada no encontrada")

    updated = await waitlist_repository.update(entry.id, {"status": WaitlistStatus.CANCELLED})
    if updated is None:  # pragma: no cover - la entrada existe, no debería ocurrir
        raise _not_found("Entrada no encontrada")
    return updated


async def delete_waitlist_entry(user: User, business_id: str, entry_id: str) -> None:
    """Elimina una entrada de la lista de espera (solo gestores)."""
    business = await get_managed_business(business_id, user)
    entry = await _get_entry_in_business(entry_id, business.id)
    await waitlist_repository.delete(entry.id)


def _matches_freed_slot(entry: Waitlist, booking: Booking) -> bool:
    """Indica si una entrada compatible cubre el hueco que acaba de liberarse."""
    if entry.service_id is not None and entry.service_id != booking.service_id:
        return False
    if entry.staff_id is not None and entry.staff_id != booking.staff_id:
        return False
    if entry.desired_from is not None and booking.start_at < entry.desired_from:
        return False
    return not (entry.desired_to is not None and booking.end_at > entry.desired_to)


async def offer_freed_slot(business_id: object, booking: Booking) -> int:
    """Marca como `offered` las entradas en espera que encajan con un hueco libre.

    Se invoca cuando una reserva se cancela. Devuelve cuántas entradas se
    ofrecieron.
    """
    entries = await waitlist_repository.find_many(
        {"business_id": business_id, "status": WaitlistStatus.WAITING},
        sort=[("created_at", ASCENDING)],
    )
    offered = 0
    for entry in entries:
        if not _matches_freed_slot(entry, booking):
            continue
        updated = await waitlist_repository.update(entry.id, {"status": WaitlistStatus.OFFERED})
        if updated is not None:
            offered += 1
    return offered
