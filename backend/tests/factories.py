"""Fábricas de datos para los tests.

Funciones `async` que crean entidades reales a través de los servicios, de modo
que los tests ejercitan la misma lógica que la API. Cada test parte de una base
de datos limpia, así que los emails/slugs no colisionan entre tests.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.security import hash_password
from app.db.repositories import user_repository
from app.models import Booking, Business, Service, Staff, User, Waitlist
from app.schemas import RegisterRequest
from app.schemas.booking import BookingCreate
from app.schemas.business import BusinessCreate
from app.schemas.service import ServiceCreate
from app.schemas.staff import StaffCreate
from app.schemas.waitlist import WaitlistCreate
from app.services import (
    auth as auth_service,
)
from app.services import (
    booking as booking_service,
)
from app.services import (
    business as business_service,
)
from app.services import (
    service as service_service,
)
from app.services import (
    staff as staff_service,
)
from app.services import (
    waitlist as waitlist_service,
)

DEFAULT_PASSWORD = "secreto123"
TIMEZONE = ZoneInfo(settings.DEFAULT_TIMEZONE)


async def make_user(
    email: str = "user@turnix.app",
    *,
    role: str = "customer",
    full_name: str = "Usuario Test",
    phone: str | None = None,
    password: str = DEFAULT_PASSWORD,
) -> User:
    """Registra un usuario."""
    return await auth_service.register_user(
        RegisterRequest(
            full_name=full_name,
            email=email,
            password=password,
            phone=phone,
            role=role,
        )
    )


async def make_owner(email: str = "owner@turnix.app", **kwargs) -> User:
    """Registra un usuario con rol `owner`."""
    kwargs.setdefault("full_name", "Propietario")
    return await make_user(email, role="owner", **kwargs)


async def make_admin(email: str = "admin@turnix.app", **kwargs) -> User:
    """Crea un usuario `admin`.

    No se puede vía registro público (solo admite `customer`/`owner`), así que
    se inserta directamente en el repositorio, como haría un seed interno.
    """
    user = User(
        full_name=kwargs.get("full_name", "Administrador"),
        email=email,
        phone=kwargs.get("phone"),
        role="admin",
        hashed_password=hash_password(kwargs.get("password", DEFAULT_PASSWORD)),
    )
    return await user_repository.insert(user)


async def make_business(owner: User, name: str = "Barbería Turnix", **kwargs) -> Business:
    """Crea un negocio propiedad de `owner`."""
    return await business_service.create_business(owner, BusinessCreate(name=name, **kwargs))


async def make_service(
    owner: User,
    business: Business,
    *,
    name: str = "Corte",
    duration_minutes: int = 60,
    buffer_minutes: int = 0,
    price: Decimal | None = Decimal("35000"),
    **kwargs,
) -> Service:
    """Crea un servicio en el negocio."""
    return await service_service.create_service(
        owner,
        str(business.id),
        ServiceCreate(
            name=name,
            duration_minutes=duration_minutes,
            buffer_minutes=buffer_minutes,
            price=price,
            **kwargs,
        ),
    )


async def make_staff(
    owner: User,
    business: Business,
    *,
    display_name: str = "Empleado",
    services: list[str] | None = None,
    **kwargs,
) -> Staff:
    """Crea un empleado en el negocio."""
    return await staff_service.create_staff(
        owner,
        str(business.id),
        StaffCreate(display_name=display_name, services=services or [], **kwargs),
    )


async def make_booking(
    customer: User,
    business: Business,
    service: Service,
    staff: Staff,
    start_at: datetime,
) -> Booking:
    """Crea una reserva del cliente para ese servicio/empleado/hora."""
    return await booking_service.create_booking(
        customer,
        str(business.id),
        BookingCreate(service_id=service.id, staff_id=staff.id, start_at=start_at),
    )


async def make_waitlist_entry(
    business: Business,
    *,
    customer: User | None = None,
    customer_name: str = "Invitado",
    **kwargs,
) -> Waitlist:
    """Anota a un cliente (o invitado) en la lista de espera."""
    return await waitlist_service.join_waitlist(
        str(business.id),
        WaitlistCreate(customer_name=customer_name, **kwargs),
        customer,
    )


def next_open_day(weekday: int = 0, *, days_ahead: int = 1) -> date:
    """Devuelve la próxima fecha (a partir de mañana) que caiga en `weekday`.

    `weekday` sigue la convención de `date.weekday()` (0 = lunes).
    """
    today = datetime.now(TIMEZONE).date()
    target = today + timedelta(days=days_ahead)
    while target.weekday() != weekday:
        target += timedelta(days=1)
    return target


def at(date_, hour: int, minute: int = 0) -> datetime:
    """Combina una fecha con una hora local en la zona del negocio por defecto."""
    return datetime.combine(date_, time(hour, minute), tzinfo=TIMEZONE)
