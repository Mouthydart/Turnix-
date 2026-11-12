"""Ruta de reportes avanzados de un negocio (solo gestores)."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.reports import BusinessReports
from app.services import reports as reports_service

router = APIRouter()


@router.get(
    "/{business_id}/reports",
    response_model=BusinessReports,
    summary="Reportes avanzados del negocio",
)
async def get_business_reports(
    business_id: str,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user: User = Depends(get_current_active_user),
) -> BusinessReports:
    return await reports_service.get_business_reports(
        user, business_id, date_from, date_to
    )
