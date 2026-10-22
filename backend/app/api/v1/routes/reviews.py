"""Rutas públicas de reseñas de un negocio."""

from fastapi import APIRouter

from app.schemas.review import ReviewPublic
from app.services import review as review_service

router = APIRouter()


@router.get(
    "/{business_id}/reviews",
    response_model=list[ReviewPublic],
    summary="Listar las reseñas de un negocio",
)
async def list_business_reviews(business_id: str) -> list[ReviewPublic]:
    reviews = await review_service.list_business_reviews(business_id)
    return [ReviewPublic.model_validate(review) for review in reviews]
