# Punto de entrada FAST API

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.indexes import create_indexes
from app.db.mongo import close_database, get_client, ping_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # Obtiene la conexión a la base de datos y crea los índices al iniciar la aplicación
    client = get_client()
    app.state.db = client[settings.MONGO_DB_NAME]
    try:
        await create_indexes(client, settings.MONGO_DB_NAME)
    except PyMongoError as exc:
        logger.warning("No se pudieron crear los indices al iniciar: %s", exc)
    yield
    await close_database()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
async def health() -> dict[str, object]:
    mongo_ok = await ping_database()
    return {
        "status": "ok" if mongo_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "up" if mongo_ok else "down",
        "timestamp": datetime.now(UTC).isoformat(),
    }
