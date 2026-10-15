"""Modelo de entrada en la lista de espera."""

from pydantic import AwareDatetime, model_validator

from app.models.base import TimestampedDocument
from app.models.enums import WaitlistStatus
from app.models.types import PyObjectId


class Waitlist(TimestampedDocument):
    """Solicitud de un cliente cuando no hay hueco disponible.

    Recoge datos de contacto directos (`customer_name`, `customer_phone`)
    porque la persona puede no estar registrada. Cuando se libera un hueco,
    se ofrece la plaza cambiando `status` a `offered`.
    """

    business_id: PyObjectId
    service_id: PyObjectId | None = None
    staff_id: PyObjectId | None = None
    customer_id: PyObjectId | None = None
    customer_name: str
    customer_phone: str | None = None
    desired_from: AwareDatetime | None = None
    desired_to: AwareDatetime | None = None
    status: WaitlistStatus = WaitlistStatus.WAITING
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_range(self) -> "Waitlist":
        """Si se define una ventana deseada, valida que sea coherente."""
        if self.desired_from and self.desired_to and self.desired_to <= self.desired_from:
            raise ValueError("`desired_to` debe ser posterior a `desired_from`")
        return self
