"""Esquemas Pydantic de entrada y salida de la API."""

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.blocked_period import (
    BlockedPeriodCreate,
    BlockedPeriodPublic,
    BlockedPeriodUpdate,
)
from app.schemas.booking import (
    AvailabilityResponse,
    AvailabilitySlot,
    BookingCreate,
    BookingPublic,
    BookingStatusUpdate,
    StaffBookingStatusUpdate,
)
from app.schemas.business import BusinessCreate, BusinessPublic, BusinessUpdate
from app.schemas.review import ReviewCreate, ReviewPublic
from app.schemas.service import ServiceCreate, ServicePublic, ServiceUpdate
from app.schemas.staff import StaffCreate, StaffPublic, StaffUpdate
from app.schemas.stats import BusinessStats, StatsItem
from app.schemas.user import UserPublic
from app.schemas.waitlist import WaitlistCreate, WaitlistPublic, WaitlistStatusUpdate

__all__ = [
    "AvailabilityResponse",
    "AvailabilitySlot",
    "BlockedPeriodCreate",
    "BlockedPeriodPublic",
    "BlockedPeriodUpdate",
    "BookingCreate",
    "BookingPublic",
    "BookingStatusUpdate",
    "BusinessCreate",
    "BusinessPublic",
    "BusinessStats",
    "BusinessUpdate",
    "LoginRequest",
    "RefreshRequest",
    "RegisterRequest",
    "ReviewCreate",
    "ReviewPublic",
    "ServiceCreate",
    "ServicePublic",
    "ServiceUpdate",
    "StaffBookingStatusUpdate",
    "StaffCreate",
    "StaffPublic",
    "StaffUpdate",
    "StatsItem",
    "TokenResponse",
    "UserPublic",
    "WaitlistCreate",
    "WaitlistPublic",
    "WaitlistStatusUpdate",
]
