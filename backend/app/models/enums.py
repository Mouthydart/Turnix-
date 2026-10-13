"""Enumeraciones de dominio compartidas por los modelos de Turnix.

Se usan `StrEnum`: los valores son strings, por lo que se guardan en MongoDB
tal cual y se serializan a JSON sin conversiones adicionales.
"""

from enum import StrEnum


class PlanName(StrEnum):
    """Planes comerciales disponibles para un negocio."""

    FREEMIUM = "freemium"
    PRO = "pro"


class UserRole(StrEnum):
    """Rol de un usuario dentro de la plataforma."""

    OWNER = "owner"
    STAFF = "staff"
    CUSTOMER = "customer"
    ADMIN = "admin"


class BookingStatus(StrEnum):
    """Estados posibles del ciclo de vida de una reserva."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class WaitlistStatus(StrEnum):
    """Estados de una entrada en la lista de espera."""

    WAITING = "waiting"
    OFFERED = "offered"
    BOOKED = "booked"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
