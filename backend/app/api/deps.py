"""Dependencias reutilizables de la API (autenticación, usuario actual)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_token
from app.db.repositories import user_repository
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    """Obtiene el usuario autenticado a partir del `Bearer` token de acceso.

    Decodifica el JWT, extrae el `sub` (id del usuario) y lo carga desde la
    base de datos. Lanza 401 ante cualquier problema.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except JWTError as exc:
        raise unauthorized from exc

    user = await user_repository.get_by_id(payload.get("sub", ""))
    if user is None:
        raise unauthorized
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Como `get_current_user`, pero exige que la cuenta esté activa."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo",
        )
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User | None:
    """Devuelve el usuario autenticado o `None` si no hay token válido.

    Útil en endpoints públicos que se enriquecen cuando hay sesión (por
    ejemplo, anotarse a la lista de espera: registrado o invitado).
    """
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except JWTError:
        return None
    return await user_repository.get_by_id(payload.get("sub", ""))
