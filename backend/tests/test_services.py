"""Tests del CRUD de servicios: creación, propiedades y aislamiento por negocio."""

import pytest
from fastapi import HTTPException

from app.schemas.service import ServiceCreate, ServiceUpdate
from app.services import service as service_service
from tests.factories import make_business, make_owner, make_service, make_user


async def test_create_service_stores_price_and_duration():
    owner = await make_owner()
    business = await make_business(owner)

    service = await make_service(owner, business, name="Masaje", duration_minutes=45, price=50000)

    assert service.name == "Masaje"
    assert service.duration_minutes == 45
    assert str(service.price) == "50000"
    assert service.business_id == business.id


async def test_customer_cannot_create_service():
    owner = await make_owner()
    business = await make_business(owner)
    customer = await make_user(email="c@turnix.app", role="customer")

    with pytest.raises(HTTPException) as exc:
        await service_service.create_service(
            customer, str(business.id), ServiceCreate(name="X", duration_minutes=30)
        )
    assert exc.value.status_code == 403


async def test_other_owner_cannot_create_service():
    owner = await make_owner()
    business = await make_business(owner)
    intruder = await make_owner(email="intruso@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await service_service.create_service(
            intruder, str(business.id), ServiceCreate(name="X", duration_minutes=30)
        )
    assert exc.value.status_code == 403


async def test_list_and_get_service_scoped_to_business():
    owner = await make_owner()
    business_a = await make_business(owner, name="A")
    business_b = await make_business(owner, name="B")
    service_a = await make_service(owner, business_a, name="Sv A")
    await make_service(owner, business_b, name="Sv B")

    assert len(await service_service.list_services(owner, str(business_a.id))) == 1
    assert (await service_service.get_service(owner, str(business_a.id), str(service_a.id))).name == "Sv A"

    # Pedir un servicio de A a través de B da 404.
    with pytest.raises(HTTPException) as exc:
        await service_service.get_service(owner, str(business_b.id), str(service_a.id))
    assert exc.value.status_code == 404


async def test_update_service_partial():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, name="Antiguo")

    updated = await service_service.update_service(
        owner, str(business.id), str(service.id), ServiceUpdate(name="Nuevo", price=99000)
    )
    assert updated.name == "Nuevo"
    assert str(updated.price) == "99000"


async def test_delete_service():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)

    await service_service.delete_service(owner, str(business.id), str(service.id))

    assert await service_service.list_services(owner, str(business.id)) == []
