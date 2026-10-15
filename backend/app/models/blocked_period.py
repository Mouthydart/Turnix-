"""Modelo de periodo bloqueado en la agenda."""

from pydantic import AwareDatetime, model_validator

from app.models.base import TimestampedDocument
from app.models.types import PyObjectId


class BlockedPeriod(TimestampedDocument):
    """Rango de tiempo en el que no se pueden agendar reservas.

    Si `staff_id` es `None` el bloqueo afecta a todo el negocio; si tiene
    valor, solo al empleado indicado (vacaciones, ausencia, etc.).
    """

    business_id: PyObjectId
    staff_id: PyObjectId | None = None
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_range(self) -> "BlockedPeriod":
        """Verifica que el fin del bloqueo sea posterior a su inicio."""
        if self.ends_at <= self.starts_at:
            raise ValueError("`ends_at` debe ser posterior a `starts_at`")
        return self
