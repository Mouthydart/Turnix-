## Índices de la base de datos (Collection Indexes)

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

COLLECTIONS: dict[str, list[tuple[tuple[str, int], dict[str, int]]]] = {
    "users": [
        ([("email", ASCENDING)], {"unique": True, "sparse": True, "name": "uniq_email"}),
        (
            [("document_id", ASCENDING)],
            {"unique": True, "sparse": True, "name": "uniq_document_id"},
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
}


async def create_indexes(client: AsyncMongoClient, db_name: str) -> None:
    db = client[db_name]
    for collection_name, indexes in COLLECTIONS.items():
        for keys, options in indexes:
            await db[collection_name].create_index(keys, **options)
