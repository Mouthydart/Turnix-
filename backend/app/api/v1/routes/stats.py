"""Ruta del dashboard de estadísticas de un negocio (solo gestores)."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.stats import BusinessStats
from app.services import stats as stats_service

router = APIRouter()


@router.get(
    "/{business_id}/stats",
    response_model=BusinessStats,
    summary="Estadísticas del negocio",
)
async def get_business_stats(
    business_id: str,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user: User = Depends(get_current_active_user),
) -> BusinessStats:
    return await stats_service.get_business_stats(user, business_id, date_from, date_to)
