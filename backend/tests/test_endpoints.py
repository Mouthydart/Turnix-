"""Tests de extremo a extremo (HTTP) sobre los endpoints principales.

Verifican routing, dependencias de autenticación, códigos de estado y
serialización JSON. La BD sigue siendo la fixture `db` (mongomock).
"""


async def _register_and_login(client, email="owner@turnix.app", role="owner"):
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Owner", "email": email, "password": "secreto123", "role": role},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "secreto123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_register_and_me_endpoint(client):
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ana", "email": "ana@turnix.app", "password": "secreto123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "ana@turnix.app", "password": "secreto123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "ana@turnix.app"
    assert "hashed_password" not in me.json()


async def test_me_without_token_is_401(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_login_with_bad_credentials_is_401(client):
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ana", "email": "ana@turnix.app", "password": "secreto123"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": "ana@turnix.app", "password": "mala-clave"}
    )
    assert response.status_code == 401


async def test_full_booking_flow_over_http(client):
    headers = await _register_and_login(client)

    business = await client.post(
        "/api/v1/businesses", headers=headers, json={"name": "Barbería HTTP"}
    )
    assert business.status_code == 201
    business_id = business.json()["id"]

    service = await client.post(
        f"/api/v1/businesses/{business_id}/services",
        headers=headers,
        json={"name": "Corte", "duration_minutes": 60, "price": "35000"},
    )
    assert service.status_code == 201
    service_id = service.json()["id"]

    staff = await client.post(
        f"/api/v1/businesses/{business_id}/staff",
        headers=headers,
        json={"display_name": "Luis", "services": [service_id]},
    )
    assert staff.status_code == 201
    staff_id = staff.json()["id"]

    # La disponibilidad no exige autenticación.
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Bogota")
    day = datetime.now(tz).date() + timedelta(days=1)
    while day.weekday() != 0:
        day += timedelta(days=1)

    availability = await client.get(
        f"/api/v1/businesses/{business_id}/availability",
        params={"service_id": service_id, "staff_id": staff_id, "date": day.isoformat()},
    )
    assert availability.status_code == 200
    slots = availability.json()["slots"]
    assert len(slots) == 33

    # Reserva en el primer hueco del cliente (mismo usuario = owner, permitido).
    booking = await client.post(
        f"/api/v1/businesses/{business_id}/bookings",
        headers=headers,
        json={"service_id": service_id, "staff_id": staff_id, "start_at": slots[0]["start_at"]},
    )
    assert booking.status_code == 201
    assert booking.json()["status"] == "pending"

    # El hueco ya no está disponible: reservar 09:00-10:00 quita 4 huecos
    # (los que empiezan en 09:00, 09:15, 09:30 y 09:45).
    availability2 = await client.get(
        f"/api/v1/businesses/{business_id}/availability",
        params={"service_id": service_id, "staff_id": staff_id, "date": day.isoformat()},
    )
    assert len(availability2.json()["slots"]) == 29


async def test_protected_endpoint_requires_token(client):
    response = await client.get("/api/v1/businesses")
    assert response.status_code == 401


async def test_validation_error_returns_422(client):
    headers = await _register_and_login(client, email="val@turnix.app")

    response = await client.post(
        "/api/v1/businesses", headers=headers, json={"name": ""}
    )
    assert response.status_code == 422


async def test_health_endpoint(client):
    response = await client.get("/health")
    # Sin MongoDB real `ping_database` falla, pero el endpoint responde igualmente.
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}
