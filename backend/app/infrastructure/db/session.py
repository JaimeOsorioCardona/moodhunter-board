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
    """Create tables if needed and ensure standard statuses and sample requests exist."""
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

        # Seed sample requests if table is empty
        from app.infrastructure.db.models import RequestModel, RequestStatusHistoryModel, utcnow
        from datetime import timedelta
        req_result = await session.execute(select(RequestModel.id).limit(1))
        if req_result.scalar_one_or_none() is None:
            now = utcnow()
            samples = [
                RequestModel(id=1, public_id="9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d", title="Configurar webhook de pagos Stripe", description="Implementar validación de firma y manejo de eventos checkout.session.completed", status_id=1, version=1, created_at=now - timedelta(days=2), updated_at=now - timedelta(days=2)),
                RequestModel(id=2, public_id="a5c7f8e1-4d2b-4e9a-8c11-9f2d5e7a8b3c", title="Refactorizar módulo de autenticación con JWT", description="Migrar almacenamiento de tokens a cookies HttpOnly y rotación de refresh tokens", status_id=2, version=2, created_at=now - timedelta(days=4), updated_at=now - timedelta(days=1)),
                RequestModel(id=3, public_id="b8e2d4c6-7a1f-4b9e-9d33-1c5e7a9f2b4d", title="Optimizar consultas lentas del dashboard", description="Crear índices compuestos y cachear agregaciones pesadas en Redis", status_id=3, version=3, created_at=now - timedelta(days=6), updated_at=now - timedelta(hours=3)),
                RequestModel(id=4, public_id="c1f4e7a9-2b5d-4c8e-8a22-3d6f8b1a4c5e", title="Integrar proveedor alternativo de SMS para 2FA", description="En espera de aprobación presupuestal del proveedor Twilio / MessageBird", status_id=4, version=3, created_at=now - timedelta(days=10), updated_at=now - timedelta(days=8)),
                RequestModel(id=5, public_id="d3a6c9f2-5e8b-4a1d-9f44-5b7c9e2a1d3f", title="Actualizar dependencias críticas de seguridad", description="Mitigación de vulnerabilidades CVE en bibliotecas de hashing y serialización", status_id=5, version=4, created_at=now - timedelta(days=12), updated_at=now - timedelta(days=5)),
            ]
            session.add_all(samples)
            await session.flush()

            histories = [
                RequestStatusHistoryModel(request_id=1, from_status_id=None, to_status_id=1, changed_at=now - timedelta(days=2)),
                RequestStatusHistoryModel(request_id=2, from_status_id=None, to_status_id=1, changed_at=now - timedelta(days=4)),
                RequestStatusHistoryModel(request_id=2, from_status_id=1, to_status_id=2, changed_at=now - timedelta(days=1)),
                RequestStatusHistoryModel(request_id=3, from_status_id=None, to_status_id=1, changed_at=now - timedelta(days=6)),
                RequestStatusHistoryModel(request_id=3, from_status_id=1, to_status_id=2, changed_at=now - timedelta(days=4)),
                RequestStatusHistoryModel(request_id=3, from_status_id=2, to_status_id=3, changed_at=now - timedelta(hours=3)),
                RequestStatusHistoryModel(request_id=4, from_status_id=None, to_status_id=1, changed_at=now - timedelta(days=10)),
                RequestStatusHistoryModel(request_id=4, from_status_id=1, to_status_id=2, changed_at=now - timedelta(days=9)),
                RequestStatusHistoryModel(request_id=4, from_status_id=2, to_status_id=4, changed_at=now - timedelta(days=8)),
                RequestStatusHistoryModel(request_id=5, from_status_id=None, to_status_id=1, changed_at=now - timedelta(days=12)),
                RequestStatusHistoryModel(request_id=5, from_status_id=1, to_status_id=2, changed_at=now - timedelta(days=10)),
                RequestStatusHistoryModel(request_id=5, from_status_id=2, to_status_id=3, changed_at=now - timedelta(days=7)),
                RequestStatusHistoryModel(request_id=5, from_status_id=3, to_status_id=5, changed_at=now - timedelta(days=5)),
            ]
            session.add_all(histories)
            await session.commit()
