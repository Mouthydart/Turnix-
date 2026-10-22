"""Límites de los planes comerciales.

Concentra en un único sitio la traducción de `PlanName` a límites concretos
(tomados de la configuración) y los validadores reutilizables. Así, cambiar un
límite solo requiere tocar `Settings`, y añadir un plan nuevo solo esta función.

Se usa el código **402 Payment Required** (no 403) para los límites de plan:
comunica "tu plan no lo permite, actualiza" en lugar de "no tienes permiso".
"""

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.config import settings
from app.models import PlanName


@dataclass(frozen=True)
class PlanLimits:
    """Límites efectivos de un plan."""

    max_employees: int
    max_services: int
    max_bookings_per_month: int
    waitlist_enabled: bool


def limits_for(plan: PlanName) -> PlanLimits:
    """Devuelve los límites configurados para un plan.

    Cualquier plan distinto de `pro` cae en los límites de `freemium`.
    """
    if plan == PlanName.PRO:
        return PlanLimits(
            max_employees=settings.PRO_MAX_EMPLOYEES,
            max_services=settings.PRO_MAX_SERVICES,
            max_bookings_per_month=settings.PRO_MAX_BOOKINGS_PER_MONTH,
            waitlist_enabled=settings.PRO_MAX_WAITLIST_ENABLED,
        )
    return PlanLimits(
        max_employees=settings.FREEMIUM_MAX_EMPLOYEES,
        max_services=settings.FREEMIUM_MAX_SERVICES,
        max_bookings_per_month=settings.FREEMIUM_MAX_BOOKINGS_PER_MONTH,
        waitlist_enabled=settings.FREEMIUM_MAX_WAITLIST_ENABLED,
    )


def assert_within_limit(current: int, limit: int, resource: str, plan: PlanName) -> None:
    """Verifica que añadir un recurso más no supere el límite del plan.

    `current` es la cantidad ya existente (antes de crear el nuevo).

    Raises:
        HTTPException: 402 si ya se alcanzó el límite.
    """
    if current >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"El plan {plan.value} permite un máximo de {limit} {resource}. "
                "Actualiza tu plan para añadir más."
            ),
        )


def assert_feature_enabled(enabled: bool, feature: str, plan: PlanName) -> None:
    """Verifica que la función esté disponible en el plan.

    Raises:
        HTTPException: 402 si la función no está incluida en el plan.
    """
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"La función '{feature}' no está incluida en el plan {plan.value}. "
                "Actualiza tu plan para usarla."
            ),
        )
