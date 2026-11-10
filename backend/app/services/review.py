"""Lógica de negocio de las reseñas.

Un cliente solo puede reseñar **su propia** reserva y únicamente cuando la cita
ya está **completada**. Además, cada reserva admite una sola reseña.

Al crear una reseña se recalculan los agregados (`rating_avg`, `rating_count`)
del empleado y del negocio afectados, para exponerlos sin coste en las lecturas.
"""

from fastapi import HTTPException, status
from pymongo import DESCENDING

from app.db.repositories import (
    booking_repository,
    business_repository,
    review_repository,
    staff_repository,
)
from app.models import BookingStatus, Business, Review, User
from app.models.types import validate_object_id
from app.schemas.review import ReviewCreate


async def _rating_stats(filters: dict) -> tuple[float, int]:
    """Devuelve (promedio redondeado, cantidad) de las reseñas que cumplen el filtro."""
    pipeline = [
        {"$match": filters},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    result = await review_repository.aggregate(pipeline)
    if not result:
        return 0.0, 0
    return round(result[0]["avg"], 2), result[0]["count"]


async def _refresh_rating_aggregates(business_id: object, staff_id: object) -> None:
    """Recalcula y persiste los agregados del empleado y del negocio."""
    staff_avg, staff_count = await _rating_stats({"staff_id": staff_id})
    await staff_repository.update(
        staff_id, {"rating_avg": staff_avg, "rating_count": staff_count}
    )

    business_avg, business_count = await _rating_stats({"business_id": business_id})
    await business_repository.update(
        business_id,
        {"rating_avg": business_avg, "rating_count": business_count},
    )


async def create_review(user: User, booking_id: str, payload: ReviewCreate) -> Review:
    """Crea la reseña de una reserva completada del cliente autenticado."""
    try:
        object_id = validate_object_id(booking_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada"
        ) from exc

    booking = await booking_repository.find_one({"_id": object_id})
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada"
        )

    if booking.customer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes reseñar una reserva que no es tuya",
        )

    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo puedes reseñar una cita completada",
        )

    already_reviewed = await review_repository.exists({"booking_id": booking.id})
    if already_reviewed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya has reseñado esta cita",
        )

    review = Review(
        booking_id=booking.id,
        business_id=booking.business_id,
        staff_id=booking.staff_id,
        service_id=booking.service_id,
        customer_id=user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    created = await review_repository.insert(review)

    await _refresh_rating_aggregates(booking.business_id, booking.staff_id)
    return created


async def _get_active_business(business_id: str) -> Business:
    """Carga un negocio activo o responde 404."""
    try:
        object_id = validate_object_id(business_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado"
        ) from exc

    business = await business_repository.get_by_id(object_id)
    if business is None or not business.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado"
        )
    return business


async def list_business_reviews(business_id: str) -> list[Review]:
    """Lista públicamente las reseñas de un negocio activo (más recientes primero)."""
    business = await _get_active_business(business_id)
    return await review_repository.find_many(
        {"business_id": business.id}, sort=[("created_at", DESCENDING)]
    )
