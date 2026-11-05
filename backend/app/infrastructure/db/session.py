"""Database session and engine management with Async SQLAlchemy 2.0."""

from collections.abc import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.infrastructure.db.models import Base, StatusModel

settings = get_settings()

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=connect_args,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining an AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(engine_instance: AsyncEngine = engine) -> None:
    """Create tables if needed and ensure standard statuses exist."""
    async with engine_instance.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Verify seed statuses
    async with AsyncSession(engine_instance) as session:
        result = await session.execute(select(StatusModel.id).limit(1))
        if result.scalar_one_or_none() is None:
            initial_statuses = [
                StatusModel(id=1, code="created", name="Creada", description="Solicitud recién registrada", sort_order=1),
                StatusModel(id=2, code="in_review", name="En revisión", description="Siendo evaluada", sort_order=2),
                StatusModel(id=3, code="in_progress", name="En progreso", description="Trabajo en curso", sort_order=3),
                StatusModel(id=4, code="paused", name="Pausada", description="Detenida temporalmente", sort_order=4),
                StatusModel(id=5, code="done", name="Finalizada", description="Completada", sort_order=5),
            ]
            session.add_all(initial_statuses)
            await session.commit()
