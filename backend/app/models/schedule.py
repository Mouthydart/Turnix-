"""Modelos de horario reutilizables por negocios y empleados."""

from datetime import time

from pydantic import Field, model_validator

from app.models.base import AppBaseModel
from app.models.enums import Weekday


class TimeRange(AppBaseModel):
    """Franja horaria dentro de un día (por ejemplo, 09:00 a 13:00)."""

    open: time
    close: time

    @model_validator(mode="after")
    def _validate_order(self) -> "TimeRange":
        """Verifica que la hora de cierre sea posterior a la de apertura."""
        if self.close <= self.open:
            raise ValueError("La hora de cierre debe ser posterior a la de apertura")
        return self


class DaySchedule(AppBaseModel):
    """Horario de un día concreto de la semana.

    Un día puede estar cerrado (`is_closed=True`) o abierto con una o varias
    franjas (`intervals`), lo que permite representar pausas como el almuerzo.
    """

    weekday: Weekday
    is_closed: bool = True
    intervals: list[TimeRange] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_consistency(self) -> "DaySchedule":
        """Coherencia entre el estado de cierre y las franjas horarias."""
        if self.is_closed and self.intervals:
            raise ValueError("Un día cerrado no puede tener franjas horarias")
        if not self.is_closed and not self.intervals:
            raise ValueError("Un día abierto debe tener al menos una franja horaria")
        return self


class WeeklySchedule(AppBaseModel):
    """Horario semanal compuesto por los siete días."""

    days: list[DaySchedule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_unique_weekdays(self) -> "WeeklySchedule":
        """Evita días repetidos en el horario."""
        weekdays = [day.weekday for day in self.days]
        if len(set(weekdays)) != len(weekdays):
            raise ValueError("No puede haber días duplicados en el horario")
        return self

    @classmethod
    def default(cls) -> "WeeklySchedule":
        """Horario por defecto: lunes a viernes de 09:00 a 18:00, fin de semana cerrado."""
        days: list[DaySchedule] = []
        for weekday in Weekday:
            if weekday in (Weekday.SATURDAY, Weekday.SUNDAY):
                days.append(DaySchedule(weekday=weekday, is_closed=True))
            else:
                days.append(
                    DaySchedule(
                        weekday=weekday,
                        is_closed=False,
                        intervals=[TimeRange(open=time(9, 0), close=time(18, 0))],
                    )
                )
        return cls(days=days)
