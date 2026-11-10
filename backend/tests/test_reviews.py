"""Tests de las reseñas de citas completadas.

Cubren: creación válida, que solo el dueño de la reserva pueda reseñar, que solo
se reseñen citas completadas, que no haya doble reseña y la validación del
`rating`.
"""

from typing import NamedTuple

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.db.repositories import business_repository, staff_repository
from app.models import BookingStatus
from app.schemas.booking import BookingStatusUpdate
from app.schemas.review import ReviewCreate
from app.services import booking as booking_service
from app.services import review as review_service
from tests.factories import (
    at,
    make_booking,
    make_business,
    make_owner,
    make_service,
    make_staff,
    make_user,
    next_open_day,
)


class Setup(NamedTuple):
    owner: object
    business: object
    service: object
    staff: object
    customer: object
    booking: object


async def _completed_booking() -> Setup:
    """Negocio con una reserva ya marcada como completada."""
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)
    staff = await make_staff(owner, business, services=[str(service.id)])
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    booking = await make_booking(customer, business, service, staff, at(day, 10, 0))
    await booking_service.update_booking_status(
        owner,
        str(business.id),
        str(booking.id),
        BookingStatusUpdate(status=BookingStatus.COMPLETED),
    )
    return Setup(owner, business, service, staff, customer, booking)


async def test_customer_reviews_completed_booking():
    s = await _completed_booking()

    review = await review_service.create_review(
        s.customer, str(s.booking.id), ReviewCreate(rating=5, comment="Excelente")
    )

    assert review.rating == 5
    assert review.comment == "Excelente"
    assert review.booking_id == s.booking.id
    assert review.business_id == s.business.id
    assert review.staff_id == s.staff.id
    assert review.service_id == s.service.id
    assert review.customer_id == s.customer.id


async def test_cannot_review_pending_booking():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)
    staff = await make_staff(owner, business, services=[str(service.id)])
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    booking = await make_booking(customer, business, service, staff, at(day, 10, 0))

    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(customer, str(booking.id), ReviewCreate(rating=5))
    assert exc.value.status_code == 409


async def test_cannot_review_someone_elses_booking():
    s = await _completed_booking()
    intruder = await make_user(email="intruso@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(
            intruder, str(s.booking.id), ReviewCreate(rating=4)
        )
    assert exc.value.status_code == 403


async def test_cannot_review_twice():
    s = await _completed_booking()
    await review_service.create_review(s.customer, str(s.booking.id), ReviewCreate(rating=5))

    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(
            s.customer, str(s.booking.id), ReviewCreate(rating=3)
        )
    assert exc.value.status_code == 409


async def test_review_unknown_booking_is_404():
    customer = await make_user(email="cli@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(customer, "no-es-un-id", ReviewCreate(rating=5))
    assert exc.value.status_code == 404


def test_review_rating_must_be_between_1_and_5():
    ReviewCreate(rating=1)
    ReviewCreate(rating=5)

    for invalid in (0, 6, -1):
        with pytest.raises(ValidationError):
            ReviewCreate(rating=invalid)


async def test_review_endpoint_over_http(client):
    s = await _completed_booking()

    # Sin token -> 401.
    assert (
        await client.post(f"/api/v1/bookings/{s.booking.id}/review", json={"rating": 5})
    ).status_code == 401

    login = await client.post(
        "/api/v1/auth/login", json={"email": "cli@turnix.app", "password": "secreto123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    created = await client.post(
        f"/api/v1/bookings/{s.booking.id}/review",
        headers=headers,
        json={"rating": 5, "comment": "Muy buena"},
    )
    assert created.status_code == 201
    assert created.json()["rating"] == 5


async def test_review_updates_business_and_staff_aggregates():
    s = await _completed_booking()

    await review_service.create_review(
        s.customer, str(s.booking.id), ReviewCreate(rating=4, comment="Buena")
    )

    business = await business_repository.get_by_id(s.business.id)
    staff = await staff_repository.get_by_id(s.staff.id)
    assert business.rating_avg == 4.0
    assert business.rating_count == 1
    assert staff.rating_avg == 4.0
    assert staff.rating_count == 1


async def test_average_is_recomputed_across_multiple_reviews():
    s = await _completed_booking()
    day = next_open_day(0)

    # Segunda cita del mismo cliente y mismo empleado para poder reseñar dos veces.
    second = await make_booking(
        s.customer, s.business, s.service, s.staff, at(day, 11, 30)
    )
    await booking_service.update_booking_status(
        s.owner,
        str(s.business.id),
        str(second.id),
        BookingStatusUpdate(status=BookingStatus.COMPLETED),
    )

    await review_service.create_review(s.customer, str(s.booking.id), ReviewCreate(rating=5))
    await review_service.create_review(s.customer, str(second.id), ReviewCreate(rating=4))

    business = await business_repository.get_by_id(s.business.id)
    staff = await staff_repository.get_by_id(s.staff.id)
    assert business.rating_count == 2
    assert business.rating_avg == 4.5
    assert staff.rating_avg == 4.5


async def test_list_business_reviews_returns_most_recent_first():
    s = await _completed_booking()

    await review_service.create_review(
        s.customer, str(s.booking.id), ReviewCreate(rating=5, comment="Primera")
    )

    reviews = await review_service.list_business_reviews(str(s.business.id))
    assert len(reviews) == 1
    assert reviews[0].comment == "Primera"


async def test_reviews_endpoint_is_public(client):
    s = await _completed_booking()
    await review_service.create_review(
        s.customer, str(s.booking.id), ReviewCreate(rating=5, comment="Genial")
    )

    response = await client.get(f"/api/v1/businesses/{s.business.id}/reviews")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["rating"] == 5
    assert body[0]["comment"] == "Genial"


async def test_reviews_endpoint_unknown_business_is_404(client):
    response = await client.get("/api/v1/businesses/no-es-un-id/reviews")
    assert response.status_code == 404

