"""Lógica de negocio de autenticación.

Las rutas se mantienen "finas": validan la entrada y delegan aquí. Este módulo
coordina seguridad (hash/JWT), repositorios y reglas de negocio.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from jose import JWTError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.repositories import refresh_token_repository, user_repository
from app.models import RefreshToken, User
from app.schemas import RegisterRequest, TokenResponse


async def register_user(payload: RegisterRequest) -> User:
    """Registra un usuario nuevo tras comprobar que el email no existe."""
    if await user_repository.exists({"email": payload.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    return await user_repository.insert(user)


async def authenticate(email: str, password: str) -> User:
    """Valida las credenciales y devuelve el usuario autenticado."""
    user = await user_repository.find_one({"email": email})
    if (
        user is None
        or not user.hashed_password
        or not verify_password(password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo",
        )
    return user


async def issue_tokens(
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> TokenResponse:
    """Emite un par de tokens (acceso + refresco) y persiste el refresco.

    El token de refresco se guarda hasheado, con su caducidad y metadatos
    del cliente, lo que permite revocarlo y auditar su uso.
    """
    subject = str(user.id)
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    refresh_claims = decode_token(refresh_token, expected_type="refresh")
    expires_at = datetime.fromtimestamp(refresh_claims["exp"], tz=UTC)

    record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    await refresh_token_repository.insert(record)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    """Rota un token de refresco válido por un par de tokens nuevos.

    Implementa **rotación**: el token usado se revoca y se emite uno nuevo.
    Así, un token robado solo es útil una vez (y queda registrado como revocado).
    """
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido o expirado",
        ) from exc

    record = await refresh_token_repository.find_one(
        {"token_hash": hash_token(refresh_token), "revoked": False}
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco revocado o inexistente",
        )

    user = await user_repository.get_by_id(claims["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido",
        )

    await refresh_token_repository.update(record.id, {"revoked": True})
    return await issue_tokens(user)


async def logout(refresh_token: str) -> None:
    """Revoca un token de refresco (cierre de sesión)."""
    record = await refresh_token_repository.find_one(
        {"token_hash": hash_token(refresh_token), "revoked": False}
    )
    if record is not None:
        await refresh_token_repository.update(record.id, {"revoked": True})
