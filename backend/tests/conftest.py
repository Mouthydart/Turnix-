"""Fixtures compartidas de la suite de tests.

Cada test recibe una base de datos **limpia**: se crea un cliente `mongomock`
(con `tz_aware=True`, igual que producción) y se parchea `get_db` en el módulo
`app.db.repository`, que es de donde lo toman todos los repositorios.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

import app.db.repository as repository


@pytest.fixture(autouse=True)
def db(monkeypatch):
    """Base de datos aislada por test, expuesta por si el test la necesita."""
    client = AsyncMongoMockClient(tz_aware=True)
    database = client["turnix_test"]
    monkeypatch.setattr(repository, "get_db", lambda: database)
    return database


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP contra la app FastAPI, sin levantar el lifespan real.

    `ASGITransport` no ejecuta el `startup`/`shutdown`, por lo que no se
    intenta conectar a un MongoDB real; la BD se resuelve por la fixture `db`.
    """
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
