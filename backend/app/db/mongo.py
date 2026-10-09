# Conexión a la base de datos

from pymongo import AsyncMongoClient

from app.core.config import settings

_client: AsyncMongoClient | None = None


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _client


def get_db():
    return get_client()[settings.MONGO_DB_NAME]


async def close_database() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def ping_database() -> bool:
    try:
        await get_client().admin.command("ping")
        return True
    except Exception:
        return False
