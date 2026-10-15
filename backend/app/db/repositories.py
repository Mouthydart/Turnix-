"""Repositorios concretos, uno por colección de Turnix.

Cada repositorio fija el `collection_name` (coincidente con `db/indexes.py`)
y el modelo Pydantic asociado. A continuación se exponen instancias listas
para usar mediante inyección de dependencias en las rutas.
"""

from app.db.repository import BaseRepository
from app.models import (
    BlockedPeriod,
    Booking,
    Business,
    RefreshToken,
    Service,
    Staff,
    User,
    Waitlist,
)


class UserRepository(BaseRepository[User]):
    collection_name = "users"
    model = User


class BusinessRepository(BaseRepository[Business]):
    collection_name = "businesses"
    model = Business


class StaffRepository(BaseRepository[Staff]):
    collection_name = "staff"
    model = Staff


class ServiceRepository(BaseRepository[Service]):
    collection_name = "services"
    model = Service


class BookingRepository(BaseRepository[Booking]):
    collection_name = "bookings"
    model = Booking


class BlockedPeriodRepository(BaseRepository[BlockedPeriod]):
    collection_name = "blocked_periods"
    model = BlockedPeriod


class WaitlistRepository(BaseRepository[Waitlist]):
    collection_name = "waitlist"
    model = Waitlist


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    collection_name = "refresh_tokens"
    model = RefreshToken


user_repository = UserRepository()
business_repository = BusinessRepository()
staff_repository = StaffRepository()
service_repository = ServiceRepository()
booking_repository = BookingRepository()
blocked_period_repository = BlockedPeriodRepository()
waitlist_repository = WaitlistRepository()
refresh_token_repository = RefreshTokenRepository()
