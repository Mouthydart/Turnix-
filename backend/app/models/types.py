"""Tipos personalizados de Pydantic compartidos por los modelos de Turnix."""

from typing import Annotated, Any

from bson import ObjectId
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


# Tipo reutilizable para referencias a documentos de MongoDB.
# - `BeforeValidator`: convierte el valor entrante (str u ObjectId) a ObjectId.
# - `PlainSerializer`: al serializar a JSON lo expone como string legible.
PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id),
    PlainSerializer(str, return_type=str, when_used="json"),
]
