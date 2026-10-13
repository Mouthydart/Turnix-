"""Modelos base y utilidades comunes a todos los documentos de Turnix."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.types import PyObjectId


def utcnow() -> datetime:
    """Devuelve la fecha y hora actuales en UTC (con zona horaria)."""
    return datetime.now(UTC)


class AppBaseModel(BaseModel):
    """Configuración base común a todos los modelos de la aplicación."""

    model_config = ConfigDict(
        # Permite construir el modelo usando el alias (`_id`) o el nombre (`id`).
        populate_by_name=True,
        # Recorta espacios en todos los campos de texto.
        str_strip_whitespace=True,
        # Permite construir el modelo desde objetos (p. ej. documentos de Mongo).
        from_attributes=True,
        # Necesario para usar `bson.ObjectId` como tipo de campo.
        arbitrary_types_allowed=True,
    )


class MongoDocument(AppBaseModel):
    """Documento persistido en MongoDB.

    Expone el `_id` de Mongo como `id` en la API. El alias `_id` permite tanto
    leer documentos existentes como nombrar correctamente el campo al guardar.
    """

    id: PyObjectId | None = Field(default=None, alias="_id")


class TimestampedDocument(MongoDocument):
    """Documento de Mongo con marcas de auditoría de creación y actualización."""

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
