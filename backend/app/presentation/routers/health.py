"""Healthcheck endpoint."""

from fastapi import APIRouter
from sqlalchemy import text
from app.infrastructure.db.session import engine
from app.presentation.schemas import HealthResponseSchema

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponseSchema, summary="Verificar estado del servicio")
async def health_check() -> HealthResponseSchema:
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc!s}"

    return HealthResponseSchema(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        circuit_breaker="closed",
    )
