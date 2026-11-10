"""Tipos personalizados de Pydantic compartidos por los modelos de Turnix."""

from datetime import time
from decimal import Decimal
from typing import Annotated, Any

from bson import ObjectId
from bson.decimal128 import Decimal128
from pydantic import BeforeValidator, PlainSerializer


def validate_object_id(value: Any) -> ObjectId:
    """Normaliza un valor a `bson.ObjectId`.

    Acepta tanto un `ObjectId` ya construido (por ejemplo, al leer de MongoDB)
    como su representación en string (por ejemplo, al recibir JSON de la API).

    Args:
        value: Valor recibido, en principio `ObjectId` o `str`.

    Returns:
        El `ObjectId` correspondiente.

    Raises:
        ValueError: Si el valor no es un `ObjectId` ni un string válido.
    """
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError("ObjectId inválido")


def parse_time(value: Any) -> time:
    """Convierte un valor a `datetime.time`.

    Acepta un `time` ya construido o un string en formato ISO ("09:00").
    """
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        return time.fromisoformat(value)
    raise ValueError("Hora inválida")


# Tipo reutilizable para referencias a documentos de MongoDB.
# - `BeforeValidator`: convierte el valor entrante (str u ObjectId) a ObjectId.
# - `PlainSerializer`: al serializar a JSON lo expone como string legible.
PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id),
    PlainSerializer(str, return_type=str, when_used="json"),
]

# Tipo para horas de un horario. BSON no puede guardar `datetime.time`, así que
# se serializan como string "HH:MM" (tanto para MongoDB como para JSON) y se
# vuelven a convertir a `time` al leer.
BsonTime = Annotated[
    time,
    BeforeValidator(parse_time),
    PlainSerializer(lambda value: value.strftime("%H:%M"), return_type=str),
]


def parse_decimal(value: Any) -> Decimal:
    """Convierte un valor a `decimal.Decimal`.

    Acepta `Decimal`, `Decimal128` de BSON, o números/texto representables.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, Decimal128):
        return value.to_decimal()
    if isinstance(value, int | float | str):
        return Decimal(str(value))
    raise ValueError("Número decimal inválido")


def _serialize_decimal(value: Decimal, info: Any) -> Any:
    """Serializa un `Decimal` como `Decimal128` (Mongo) o string (JSON)."""
    if getattr(info, "mode", "python") == "json":
        return str(value)
    return Decimal128(value)


# Tipo para importes monetarios. En Python es `Decimal` (sin errores de float),
# en MongoDB se guarda como `Decimal128` y en JSON se expone como string.
BsonDecimal = Annotated[
    Decimal,
    BeforeValidator(parse_decimal),
    PlainSerializer(_serialize_decimal),
]

