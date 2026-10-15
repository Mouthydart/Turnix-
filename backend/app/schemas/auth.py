"""Esquemas de entrada y salida para la autenticación."""

from typing import Literal

from pydantic import EmailStr, Field

from app.models import AppBaseModel, UserRole


class RegisterRequest(AppBaseModel):
    """Datos para registrar un nuevo usuario.

    El `role` se limita a `customer` u `owner` para impedir que alguien se
    autoasigne roles privilegiados (`admin`/`staff`) desde la API pública.
    """

    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=30)
    role: Literal[UserRole.CUSTOMER, UserRole.OWNER] = UserRole.CUSTOMER


class LoginRequest(AppBaseModel):
    """Credenciales para iniciar sesión."""

    email: EmailStr
    password: str


class RefreshRequest(AppBaseModel):
    """Token de refresco para obtener un nuevo par de tokens."""

    refresh_token: str


class TokenResponse(AppBaseModel):
    """Par de tokens devuelto tras autenticarse o refrescar."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
