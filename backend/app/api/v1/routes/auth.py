"""Rutas de autenticación: registro, login, refresco y sesión actual."""

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.services import auth as auth_service

router = APIRouter()


def _client_metadata(request: Request) -> dict[str, str | None]:
    """Extrae metadatos del cliente para auditar los tokens de refresco."""
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None,
    }


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario",
)
async def register(payload: RegisterRequest) -> UserPublic:
    user = await auth_service.register_user(payload)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    user = await auth_service.authenticate(payload.email, payload.password)
    return await auth_service.issue_tokens(user, **_client_metadata(request))


@router.post("/refresh", response_model=TokenResponse, summary="Refrescar tokens")
async def refresh(payload: RefreshRequest, request: Request) -> TokenResponse:
    tokens = await auth_service.refresh_tokens(payload.refresh_token)
    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
async def logout(payload: RefreshRequest) -> None:
    await auth_service.logout(payload.refresh_token)


@router.get("/me", response_model=UserPublic, summary="Usuario autenticado")
async def me(user: User = Depends(get_current_active_user)) -> UserPublic:
    return UserPublic.model_validate(user)
