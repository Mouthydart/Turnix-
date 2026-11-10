"""Tests de la lista de espera: alta pública/registrada, gestión y enganche.

La lista de espera es una función del plan **pro**, así que estos tests crean
negocios en ese plan (en freemium está deshabilitada; ver `test_plan_limits`).
"""

import pytest
from fastapi import HTTPException

from app.models import BookingStatus, WaitlistStatus
from app.schemas.booking import BookingStatusUpdate
from app.schemas.waitlist import WaitlistCreate, WaitlistStatusUpdate
from app.services import booking as booking_service
from app.services import waitlist as waitlist_service
from tests.factories import (
    at,
    make_booking,
    make_business,
    make_owner,
    make_service,
    make_staff,
    make_user,
    make_waitlist_entry,
    next_open_day,
)


async def test_guest_can_join_with_name():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")

    entry = await waitlist_service.join_waitlist(
        str(business.id), WaitlistCreate(customer_name="Invitado", customer_phone="300")
    )

    assert entry.customer_name == "Invitado"
    assert entry.customer_id is None
    assert entry.status == WaitlistStatus.WAITING


async def test_guest_without_name_is_rejected():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.join_waitlist(str(business.id), WaitlistCreate())
    assert exc.value.status_code == 422


async def test_registered_user_inherits_name_and_links_id():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    customer = await make_user(email="cli@turnix.app", full_name="Cliente")

    entry = await waitlist_service.join_waitlist(str(business.id), WaitlistCreate(), customer)

    assert entry.customer_id == customer.id
    assert entry.customer_name == "Cliente"


async def test_join_with_foreign_service_is_rejected():
    owner = await make_owner()
    business_a = await make_business(owner, plan="pro", name="A")
    business_b = await make_business(owner, plan="pro", name="B")
    foreign_service = await make_service(owner, business_b)

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.join_waitlist(
            str(business_a.id),
            WaitlistCreate(customer_name="X", service_id=foreign_service.id),
        )
    assert exc.value.status_code == 422


async def test_join_with_invalid_desired_window_is_rejected():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.join_waitlist(
            str(business.id),
            WaitlistCreate(
                customer_name="X", desired_from=at(day, 12), desired_to=at(day, 11)
            ),
        )
    assert exc.value.status_code == 422


async def test_business_owner_lists_and_filters_entries():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    await make_waitlist_entry(business, customer_name="Uno")
    two = await make_waitlist_entry(business, customer_name="Dos")
    await waitlist_service.update_waitlist_status(
        owner, str(business.id), str(two.id), WaitlistStatusUpdate(status=WaitlistStatus.OFFERED)
    )

    assert len(await waitlist_service.list_business_waitlist(owner, str(business.id))) == 2
    waiting = await waitlist_service.list_business_waitlist(
        owner, str(business.id), WaitlistStatus.WAITING
    )
    assert [e.customer_name for e in waiting] == ["Uno"]


async def test_other_owner_cannot_list_entries():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    intruder = await make_owner(email="intruso@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.list_business_waitlist(intruder, str(business.id))
    assert exc.value.status_code == 403


async def test_client_cancels_own_entry():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    customer = await make_user(email="cli@turnix.app")
    entry = await make_waitlist_entry(business, customer=customer, customer_name="Cli")

    cancelled = await waitlist_service.cancel_my_waitlist(customer, str(entry.id))
    assert cancelled.status == WaitlistStatus.CANCELLED


async def test_client_cannot_cancel_someone_elses_entry():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    alice = await make_user(email="alice@turnix.app")
    bob = await make_user(email="bob@turnix.app")
    entry = await make_waitlist_entry(business, customer=alice, customer_name="Alice")

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.cancel_my_waitlist(bob, str(entry.id))
    assert exc.value.status_code == 404


async def test_list_my_waitlist():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    customer = await make_user(email="cli@turnix.app")
    await make_waitlist_entry(business, customer=customer, customer_name="Cli")
    await make_waitlist_entry(business, customer_name="Otro")

    assert len(await waitlist_service.list_my_waitlist(customer)) == 1


async def test_delete_entry():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business)

    await waitlist_service.delete_waitlist_entry(owner, str(business.id), str(entry.id))

    assert await waitlist_service.list_business_waitlist(owner, str(business.id)) == []


async def test_cancelling_booking_offers_matching_waitlist_entry():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    service = await make_service(owner, business, duration_minutes=60)
    staff = await make_staff(owner, business, services=[str(service.id)])
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, business, service, staff, at(day, 10, 0))

    entry = await make_waitlist_entry(
        business,
        customer=customer,
        customer_name="Cli",
        service_id=service.id,
        staff_id=staff.id,
    )
    assert entry.status == WaitlistStatus.WAITING

    # Cancelar la reserva dispara el ofrecimiento del hueco.
    await booking_service.update_booking_status(
        owner, str(business.id), str(reservation.id),
        BookingStatusUpdate(status=BookingStatus.CANCELLED),
    )

    refreshed = await waitlist_service.get_waitlist_entry(owner, str(business.id), str(entry.id))
    assert refreshed.status == WaitlistStatus.OFFERED


async def test_waitlist_entry_for_other_service_is_not_offered():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    service = await make_service(owner, business, duration_minutes=60)
    other_service = await make_service(owner, business, name="Otro", duration_minutes=60)
    staff = await make_staff(owner, business, services=[str(service.id), str(other_service.id)])
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, business, service, staff, at(day, 10, 0))

    entry = await make_waitlist_entry(
        business, customer=customer, customer_name="Cli", service_id=other_service.id
    )

    await booking_service.update_booking_status(
        owner, str(business.id), str(reservation.id),
        BookingStatusUpdate(status=BookingStatus.CANCELLED),
    )

    refreshed = await waitlist_service.get_waitlist_entry(owner, str(business.id), str(entry.id))
    assert refreshed.status == WaitlistStatus.WAITING


async def test_manager_can_offer_entry_manually():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business, customer_name="Cli")

    offered = await waitlist_service.offer_waitlist_entry(owner, str(business.id), str(entry.id))
    assert offered.status == WaitlistStatus.OFFERED


async def test_manager_can_cancel_entry():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business, customer_name="Cli")

    cancelled = await waitlist_service.cancel_waitlist_entry(owner, str(business.id), str(entry.id))
    assert cancelled.status == WaitlistStatus.CANCELLED


async def test_cancelling_entry_twice_is_idempotent():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business, customer_name="Cli")

    first = await waitlist_service.cancel_waitlist_entry(owner, str(business.id), str(entry.id))
    second = await waitlist_service.cancel_waitlist_entry(owner, str(business.id), str(entry.id))
    assert first.status == WaitlistStatus.CANCELLED
    assert second.status == WaitlistStatus.CANCELLED


async def test_offer_terminal_entry_rejected():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business, customer_name="Cli")
    await waitlist_service.cancel_waitlist_entry(owner, str(business.id), str(entry.id))

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.offer_waitlist_entry(owner, str(business.id), str(entry.id))
    assert exc.value.status_code == 409


async def test_offer_already_offered_is_idempotent():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business, customer_name="Cli")

    first = await waitlist_service.offer_waitlist_entry(owner, str(business.id), str(entry.id))
    second = await waitlist_service.offer_waitlist_entry(owner, str(business.id), str(entry.id))
    assert first.status == WaitlistStatus.OFFERED
    assert second.status == WaitlistStatus.OFFERED


async def test_waitlist_offer_and_cancel_endpoints_http(client):
    owner = await make_owner()
    business = await make_business(owner, plan="pro")
    entry = await make_waitlist_entry(business, customer_name="Cli")

    # Sin token -> 401
    assert (
        await client.post(f"/api/v1/businesses/{business.id}/waitlist/{entry.id}/offer")
    ).status_code == 401

    # Login del dueño (creado por la factory con password por defecto)
    login = await client.post(
        "/api/v1/auth/login", json={"email": owner.email, "password": "secreto123"}
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    offered = await client.post(
        f"/api/v1/businesses/{business.id}/waitlist/{entry.id}/offer", headers=headers
    )
    assert offered.status_code == 200
    assert offered.json()["status"] == WaitlistStatus.OFFERED

    cancelled = await client.post(
        f"/api/v1/businesses/{business.id}/waitlist/{entry.id}/cancel", headers=headers
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == WaitlistStatus.CANCELLED

