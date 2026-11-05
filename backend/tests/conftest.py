"""Test configuration and fixtures for integration tests."""

import os
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.application.request_service import RequestService
from app.application.summary_service import SummaryService
from app.core.config import get_settings
from app.infrastructure.db.models import Base
from app.infrastructure.db.session import init_db
from app.infrastructure.db.uow import SQLAlchemyUnitOfWork
from app.infrastructure.llm.gemini_gateway import GeminiGateway
from app.main import app
from app.presentation.routers.requests import get_request_service
from app.presentation.routers.summary import get_summary_service

settings = get_settings()
settings.ENVIRONMENT = "test"
settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await init_db(engine)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session_factory(test_engine):
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def test_uow(test_session_factory):
    return SQLAlchemyUnitOfWork(session_factory=test_session_factory)


@pytest.fixture
async def client(test_uow) -> AsyncGenerator[AsyncClient, None]:
    def override_request_service():
        return RequestService(test_uow)

    def override_summary_service():
        gateway = GeminiGateway(api_key=None)
        return SummaryService(uow=test_uow, gateway=gateway)

    app.dependency_overrides[get_request_service] = override_request_service
    app.dependency_overrides[get_summary_service] = override_summary_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
