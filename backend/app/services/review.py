"""Lógica de negocio de las reseñas.

Un cliente solo puede reseñar **su propia** reserva y únicamente cuando la cita
ya está **completada**. Además, cada reserva admite una sola reseña.
"""

from fastapi import HTTPException, status

from app.db.repositories import booking_repository, review_repository
from app.models import BookingStatus, Review, User
from app.models.types import validate_object_id
from app.schemas.review import ReviewCreate


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
    return await review_repository.insert(review)
