"""
Configuración global de pytest para IntellectClone.
Fixtures de base de datos y cliente HTTP para tests de integración.

Patrón de event loop (SQLAlchemy 2 async + pytest-asyncio 1.x + asyncpg):
  - asyncio_default_fixture_loop_scope = "function" en pyproject.toml hace que
    los fixtures async usen el mismo loop que el test que los usa (function-scoped).
    Esto elimina el error "Future attached to a different loop" de asyncpg.
  - create_test_schema: fixture síncrono session-scoped que crea/destruye el
    esquema con asyncio.run() — completamente aislado de los loops de los tests.
  - test_session: fixture async function-scoped. Crea un engine NullPool propio
    (ligado al loop del test actual). Usa join_transaction_mode="create_savepoint"
    para que el commit() de get_db no llegue a la DB real; conn.rollback()
    revierte todo al finalizar sin necesidad de TRUNCATE.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from intellectclone.db.base import Base
from intellectclone.db.session import get_db
from intellectclone.main import app as main_app

TEST_DATABASE_URL = (
    "postgresql+asyncpg://intellectclone:intellectclone_dev@localhost:5432/intellectclone_test"
)


@pytest.fixture(scope="session", autouse=True)
def create_test_schema() -> Generator[None, None, None]:
    """
    Crea el esquema una vez para toda la sesión (fixture síncrono).
    asyncio.run() crea su propio loop independiente — no interfiere con los
    loops function-scoped de los tests.
    """

    async def _setup() -> None:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_setup())
    yield

    async def _teardown() -> None:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_teardown())


@pytest_asyncio.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Sesión de base de datos para cada test.

    Crea un engine NullPool propio en el loop del test (sin pool compartido).
    Abre una transacción externa y usa join_transaction_mode="create_savepoint"
    para que el commit() de get_db solo libere un savepoint — todos los cambios
    se revierten con conn.rollback() al finalizar el test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    conn = await engine.connect()
    await conn.begin()

    session_factory = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await conn.rollback()
        await conn.close()


@pytest_asyncio.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP asíncrono para tests de integración.
    Inyecta la sesión de test via dependency_overrides para que todos
    los endpoints usen la misma transacción revertible.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    main_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=main_app),
        base_url="http://testserver",
    ) as c:
        yield c

    main_app.dependency_overrides.clear()
