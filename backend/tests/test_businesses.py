"""Tests del CRUD de negocios: creación, slug único, permisos y listado."""

import pytest
from fastapi import HTTPException

from app.schemas.business import BusinessCreate, BusinessUpdate
from app.services import business as business_service
from tests.factories import make_admin, make_business, make_owner, make_user


async def test_owner_creates_business_with_generated_slug():
    owner = await make_owner()
    business = await make_business(owner, name="Café Ñandú")

    assert business.name == "Café Ñandú"
    assert business.slug == "cafe-nandu"
    assert business.owner_id == owner.id
    assert business.is_active is True


async def test_customer_cannot_create_business():
    customer = await make_user(role="customer")

    with pytest.raises(HTTPException) as exc:
        await business_service.create_business(customer, BusinessCreate(name="X"))
    assert exc.value.status_code == 403


async def test_duplicate_name_gets_numeric_slug_suffix():
    owner = await make_owner()
    first = await make_business(owner, name="Barbería")
    second = await make_business(owner, name="Barbería")

    assert first.slug == "barberia"
    assert second.slug == "barberia-2"


async def test_explicit_duplicate_slug_is_rejected():
    owner = await make_owner()
    await business_service.create_business(owner, BusinessCreate(name="Uno", slug="mi-slug"))

    with pytest.raises(HTTPException) as exc:
        await business_service.create_business(owner, BusinessCreate(name="Dos", slug="mi-slug"))
    assert exc.value.status_code == 409


async def test_list_businesses_only_returns_own_for_owner():
    owner_a = await make_owner(email="a@turnix.app")
    owner_b = await make_owner(email="b@turnix.app")
    await make_business(owner_a, name="De A")
    await make_business(owner_b, name="De B")

    assert len(await business_service.list_businesses(owner_a)) == 1
    assert len(await business_service.list_businesses(owner_b)) == 1


async def test_admin_sees_all_businesses():
    owner = await make_owner()
    await make_business(owner, name="Uno")
    await make_business(owner, name="Dos")
    admin = await make_admin(email="admin@turnix.app")

    assert len(await business_service.list_businesses(admin)) == 2


async def test_other_owner_cannot_manage_business():
    owner = await make_owner()
    intruder = await make_owner(email="intruso@turnix.app")
    business = await make_business(owner)

    with pytest.raises(HTTPException) as exc:
        await business_service.get_business(str(business.id), intruder)
    assert exc.value.status_code == 403


async def test_get_business_with_invalid_id_returns_404():
    owner = await make_owner()

    with pytest.raises(HTTPException) as exc:
        await business_service.get_business("no-es-un-objectid", owner)
    assert exc.value.status_code == 404


async def test_update_business_partial():
    owner = await make_owner()
    business = await make_business(owner, name="Original")

    updated = await business_service.update_business(
        str(business.id), owner, BusinessUpdate(name="Renombrado", description="Nueva")
    )
    assert updated.name == "Renombrado"
    assert updated.description == "Nueva"
    assert updated.slug == business.slug  # no cambia si no se envía


async def test_update_slug_to_existing_is_conflict():
    owner = await make_owner()
    await business_service.create_business(owner, BusinessCreate(name="Uno", slug="uno-slug"))
    two = await business_service.create_business(owner, BusinessCreate(name="Dos", slug="dos-slug"))

    with pytest.raises(HTTPException) as exc:
        await business_service.update_business(str(two.id), owner, BusinessUpdate(slug="uno-slug"))
    assert exc.value.status_code == 409


async def test_delete_business():
    owner = await make_owner()
    business = await make_business(owner)

    await business_service.delete_business(str(business.id), owner)

    with pytest.raises(HTTPException) as exc:
        await business_service.get_business(str(business.id), owner)
    assert exc.value.status_code == 404
