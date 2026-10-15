"""Repositorio CRUD genérico sobre MongoDB.

Concentra la lógica de acceso a datos para que las rutas y los servicios no
tengan que escribir consultas de PyMongo. Cada colección define una subclase
con su nombre de colección y su modelo Pydantic.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from pymongo import ReturnDocument

from app.db.mongo import get_db
from app.models.base import MongoDocument, utcnow
from app.models.types import validate_object_id


class BaseRepository[ModelT: MongoDocument]:
    """Operaciones CRUD básicas contra una colección de MongoDB."""

    collection_name: str
    model: type[ModelT]

    @property
    def collection(self):
        """Devuelve la colección de MongoDB asociada al repositorio."""
        return get_db()[self.collection_name]

    def _to_model(self, document: Mapping[str, Any] | None) -> ModelT | None:
        """Convierte un documento de Mongo en su modelo Pydantic."""
        if document is None:
            return None
        return self.model.model_validate(document)

    async def insert(self, document: ModelT) -> ModelT:
        """Inserta un documento y devuelve el modelo con su `id` asignado."""
        data = document.model_dump(by_alias=True)
        if data.get("_id") is None:
            # Sin `_id` dejamos que MongoDB genere el ObjectId.
            data.pop("_id", None)
        result = await self.collection.insert_one(data)
        return self.model.model_validate({**data, "_id": result.inserted_id})

    async def get_by_id(self, id_: Any) -> ModelT | None:
        """Busca un documento por su `_id`."""
        document = await self.collection.find_one({"_id": validate_object_id(id_)})
        return self._to_model(document)

    async def find_one(self, filters: Mapping[str, Any]) -> ModelT | None:
        """Busca el primer documento que cumpla los filtros."""
        document = await self.collection.find_one(dict(filters))
        return self._to_model(document)

    async def find_many(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        skip: int = 0,
        limit: int = 0,
        sort: Sequence[tuple[str, int]] | None = None,
    ) -> list[ModelT]:
        """Devuelve los documentos que cumplan los filtros y la paginación."""
        cursor = self.collection.find(dict(filters) if filters else {})
        if sort:
            cursor = cursor.sort(list(sort))
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return [self.model.model_validate(document) async for document in cursor]

    async def update(self, id_: Any, updates: Mapping[str, Any]) -> ModelT | None:
        """Actualiza los campos indicados y renueva `updated_at`."""
        fields = {**updates, "updated_at": utcnow()}
        document = await self.collection.find_one_and_update(
            {"_id": validate_object_id(id_)},
            {"$set": fields},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_model(document)

    async def delete(self, id_: Any) -> bool:
        """Elimina un documento por su `_id`. Devuelve `True` si existía."""
        result = await self.collection.delete_one({"_id": validate_object_id(id_)})
        return result.deleted_count == 1

    async def count(self, filters: Mapping[str, Any] | None = None) -> int:
        """Cuenta los documentos que cumplan los filtros."""
        return await self.collection.count_documents(dict(filters) if filters else {})

    async def exists(self, filters: Mapping[str, Any]) -> bool:
        """Indica si existe al menos un documento que cumpla los filtros."""
        document = await self.collection.find_one(dict(filters), projection={"_id": 1})
        return document is not None

    async def touch(self, id_: Any, *, at: datetime | None = None) -> ModelT | None:
        """Actualiza únicamente `updated_at` (sin cambiar otros campos)."""
        document = await self.collection.find_one_and_update(
            {"_id": validate_object_id(id_)},
            {"$set": {"updated_at": at or utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_model(document)
