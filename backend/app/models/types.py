# Tipos personalizados para Pydantic y MongoDB

from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


def validate_object_id(value: object) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError("Invalid ObjectId")


def serialize_object_id(value: object, _handler: GetCoreSchemaHandler | None = None) -> str:
    return str(value)


PydanticObjectId = core_schema.no_info_plain_validator_function(
    validate_object_id,
    serialization=core_schema.plain_serializer_function_ser_schema(
        serialize_object_id, return_schema=core_schema.str_schema(), when_used="json"
    ),
)
