"""Tests del catálogo público de negocios."""

import pytest
from fastapi import HTTPException

from app.schemas.business import BusinessUpdate
from app.services import business as business_service
from app.services import catalog as catalog_service
from tests.factories import (
    make_business,
    make_owner,
    make_service,
    make_staff,
    next_open_day,
)


async def test_catalog_lists_only_active_businesses():
    owner = await make_owner()
    active = await make_business(owner, name="Barbería Activa")
    inactive = await make_business(owner, name="Barbería Cerrada")
    await business_service.update_business(
        str(inactive.id), owner, BusinessUpdate(is_active=False)
    )

    result = await catalog_service.list_catalog_businesses()

    assert [business.id for business in result] == [active.id]


async def test_catalog_searches_by_name_description_and_address():
    owner = await make_owner()
    await make_business(owner, name="Peluquería Sol", description="Cortes y color")
    await make_business(owner, name="Barbería Luna", address="Calle 10")

    by_name = await catalog_service.list_catalog_businesses(query="luna")
    by_description = await catalog_service.list_catalog_businesses(query="color")
    by_address = await catalog_service.list_catalog_businesses(query="calle 10")

    assert [business.name for business in by_name] == ["Barbería Luna"]
    assert [business.name for business in by_description] == ["Peluquería Sol"]
    assert [business.name for business in by_address] == ["Barbería Luna"]


async def test_catalog_detail_only_includes_bookable_services_and_staff():
    owner = await make_owner()
    business = await make_business(owner, name="Estudio Turnix", plan="pro")
    active_service = await make_service(owner, business, name="Corte")
    inactive_service = await make_service(
        owner, business, name="Tinte", is_active=False
    )
    offered = [str(active_service.id), str(inactive_service.id)]
    active_staff = await make_staff(
        owner, business, display_name="Ana", services=offered
    )
    await make_staff(
        owner, business, display_name="Beto", services=offered, is_active=False
    )
    await make_staff(owner, business, display_name="Carla", services=[])
    await make_staff(
        owner,
        business,
        display_name="Diego",
        services=[str(inactive_service.id)],
    )

    found, services, staff = await catalog_service.get_catalog_business(
        str(business.id)
    )

    assert found.id == business.id
    assert [service.id for service in services] == [active_service.id]
    assert [member.id for member in staff] == [active_staff.id]


async def test_catalog_detail_rejects_unknown_or_inactive_business():
    owner = await make_owner()
    business = await make_business(owner)
    await business_service.update_business(
        str(business.id), owner, BusinessUpdate(is_active=False)
    )

    with pytest.raises(HTTPException) as invalid:
        await catalog_service.get_catalog_business("no-es-un-objectid")
    assert invalid.value.status_code == 404

    with pytest.raises(HTTPException) as inactive:
        await catalog_service.get_catalog_business(str(business.id))
    assert inactive.value.status_code == 404


async def test_catalog_endpoints_are_public(client):
    owner = await make_owner()
    business = await make_business(owner, name="Café Central")
    service = await make_service(owner, business, name="Desayuno")
    await make_staff(owner, business, display_name="Ana", services=[str(service.id)])

    listing = await client.get("/api/v1/catalog/businesses", params={"q": "café"})
    assert listing.status_code == 200
    assert [item["name"] for item in listing.json()] == ["Café Central"]

    detail = await client.get(f"/api/v1/catalog/businesses/{business.id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["id"] == str(business.id)
    assert [item["name"] for item in payload["services"]] == ["Desayuno"]
    assert [item["display_name"] for item in payload["staff"]] == ["Ana"]


async def test_customer_books_from_public_catalog(client):
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)
    staff = await make_staff(owner, business, services=[str(service.id)])

    catalog = await client.get(f"/api/v1/catalog/businesses/{business.id}")
    assert catalog.status_code == 200
    catalog_payload = catalog.json()
    assert catalog_payload["services"][0]["id"] == str(service.id)
    assert catalog_payload["staff"][0]["id"] == str(staff.id)

    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Cliente",
            "email": "cliente-catalogo@turnix.app",
            "password": "secreto123",
            "role": "customer",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "cliente-catalogo@turnix.app", "password": "secreto123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    day = next_open_day(0)
    availability = await client.get(
        f"/api/v1/businesses/{business.id}/availability",
        params={
            "service_id": str(service.id),
            "staff_id": str(staff.id),
            "date": day.isoformat(),
        },
    )
    assert availability.status_code == 200
    slot = availability.json()["slots"][0]["start_at"]

    booking = await client.post(
        f"/api/v1/businesses/{business.id}/bookings",
        headers=headers,
        json={
            "service_id": str(service.id),
            "staff_id": str(staff.id),
            "start_at": slot,
        },
    )
    assert booking.status_code == 201

    mine = await client.get("/api/v1/bookings/mine", headers=headers)
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()] == [booking.json()["id"]]
