## Índices de la base de datos (Collection Indexes)

import logging
from typing import Any

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

logger = logging.getLogger(__name__)

COLLECTIONS: dict[str, list[tuple[list[tuple[str, int]], dict[str, Any]]]] = {
    "users": [
        (
            [("email", ASCENDING)],
            {
                "unique": True,
                "name": "uniq_email",
                "partialFilterExpression": {"email": {"$type": "string"}},
            },
        ),
        (
            [("document_id", ASCENDING)],
            {
                "unique": True,
                "name": "uniq_document_id",
                "partialFilterExpression": {"document_id": {"$type": "string"}},
            },
        ),
    ],
    "businesses": [
        ([("slug", ASCENDING)], {"unique": True, "name": "uniq_slug"}),
        ([("owner_id", ASCENDING)], {"name": "idx_owner"}),
    ],
    "staff": [
        ([("business_id", ASCENDING)], {"name": "idx_business"}),
    ],
    "services": [
        ([("business_id", ASCENDING)], {"name": "idx_business"}),
    ],
    "bookings": [
        ([("business_id", ASCENDING), ("start_at", ASCENDING)], {"name": "idx_business_start"}),
        ([("staff_id", ASCENDING), ("start_at", ASCENDING)], {"name": "idx_staff_start"}),
        ([("customer_id", ASCENDING), ("start_at", DESCENDING)], {"name": "idx_customer_start"}),
        ([("business_id", ASCENDING), ("status", ASCENDING)], {"name": "idx_business_status"}),
    ],
    "blocked_periods": [
        ([("business_id", ASCENDING), ("starts_at", ASCENDING)], {"name": "idx_business_starts"}),
    ],
    "waitlist": [
        ([("business_id", ASCENDING), ("status", ASCENDING)], {"name": "idx_business_status"}),
    ],
    "refresh_tokens": [
        ([("user_id", ASCENDING)], {"name": "idx_user"}),
    ],
    "reviews": [
        ([("booking_id", ASCENDING)], {"unique": True, "name": "uniq_booking"}),
        ([("business_id", ASCENDING), ("created_at", DESCENDING)], {"name": "idx_business_created"}),
    ],
}


def _index_matches(
    current: dict[str, Any],
    keys: list[tuple[str, int]],
    options: dict[str, Any],
) -> bool:
    """Indica si un índice existente ya cumple la definición deseada."""
    if [tuple(key) for key in current.get("key", [])] != [tuple(key) for key in keys]:
        return False
    for option in ("unique", "sparse"):
        if bool(current.get(option, False)) != bool(options.get(option, False)):
            return False
    return current.get("partialFilterExpression") == options.get("partialFilterExpression")


async def create_indexes(client: AsyncMongoClient, db_name: str) -> None:
    db = client[db_name]
    for collection_name, indexes in COLLECTIONS.items():
        collection = db[collection_name]
        existing = await collection.index_information()
        for keys, options in indexes:
            name = options.get("name")
            if name and name in existing and not _index_matches(existing[name], keys, options):
                # Migra índices antiguos (p. ej. sparse) a su definición actual.
                logger.info("Recreando índice %s.%s", collection_name, name)
                await collection.drop_index(name)
                existing.pop(name, None)
            await collection.create_index(keys, **options)
