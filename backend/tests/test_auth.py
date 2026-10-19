"""Tests de autenticación: registro, login, refresco con rotación y logout."""

import pytest
from fastapi import HTTPException

from app.schemas import LoginRequest, RegisterRequest
from app.services import auth as auth
from tests.factories import DEFAULT_PASSWORD, make_user


async def test_register_creates_user_with_hashed_password():
    user = await make_user(email="ana@turnix.app", full_name="Ana")

    assert user.full_name == "Ana"
    assert user.hashed_password != DEFAULT_PASSWORD
    assert user.hashed_password.startswith("$2")  # bcrypt


async def test_register_rejects_duplicate_email():
    await make_user(email="dup@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await make_user(email="dup@turnix.app")

    assert exc.value.status_code == 409


async def test_authenticate_success_and_failure():
    await make_user(email="login@turnix.app", password="correcta123")

    user = await auth.authenticate("login@turnix.app", "correcta123")
    assert user.email == "login@turnix.app"

    with pytest.raises(HTTPException) as exc:
        await auth.authenticate("login@turnix.app", "incorrecta")
    assert exc.value.status_code == 401


async def test_authenticate_rejects_unknown_email():
    with pytest.raises(HTTPException) as exc:
        await auth.authenticate("nadie@turnix.app", "x")
    assert exc.value.status_code == 401


async def test_issue_tokens_persists_hashed_refresh_token():
    from app.db.repositories import refresh_token_repository

    user = await make_user(email="tokens@turnix.app")
    tokens = await auth.issue_tokens(user)

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"

    record = await refresh_token_repository.find_one({"user_id": user.id})
    assert record is not None
    # El token en claro nunca se guarda; solo su hash.
    assert record.token_hash != tokens.refresh_token


async def test_refresh_rotates_and_invalidates_old_token():
    user = await make_user(email="rotate@turnix.app")
    first = await auth.issue_tokens(user)

    second = await auth.refresh_tokens(first.refresh_token)
    assert second.refresh_token != first.refresh_token

    # El token anterior quedó revocado: reutilizarlo falla.
    with pytest.raises(HTTPException) as exc:
        await auth.refresh_tokens(first.refresh_token)
    assert exc.value.status_code == 401


async def test_refresh_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await auth.refresh_tokens("esto-no-es-un-jwt")
    assert exc.value.status_code == 401


async def test_logout_revokes_refresh_token():
    user = await make_user(email="logout@turnix.app")
    tokens = await auth.issue_tokens(user)

    await auth.logout(tokens.refresh_token)

    with pytest.raises(HTTPException) as exc:
        await auth.refresh_tokens(tokens.refresh_token)
    assert exc.value.status_code == 401


async def test_login_and_refresh_schemas_roundtrip():
    """Los esquemas de entrada aceptan datos válidos."""
    payload = RegisterRequest(full_name="X", email="x@turnix.app", password="12345678")
    assert payload.role == "customer"
    assert LoginRequest(email="x@turnix.app", password="12345678").email == "x@turnix.app"
