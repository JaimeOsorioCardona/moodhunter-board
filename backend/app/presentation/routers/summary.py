"""Router for generating and retrieving the executive AI summary."""

from fastapi import APIRouter, Depends, Query, status
from app.application.summary_service import SummaryService
from app.core.config import get_settings
from app.infrastructure.db.uow import SQLAlchemyUnitOfWork
from app.infrastructure.llm.circuit_breaker import CircuitBreaker
from app.infrastructure.llm.gemini_gateway import GeminiGateway
from app.presentation.schemas import SummaryResponseSchema

router = APIRouter(prefix="/requests", tags=["AI Summary"])

settings = get_settings()
_global_breaker = CircuitBreaker(
    failure_threshold=settings.LLM_CIRCUIT_BREAKER_FAIL_THRESHOLD,
    reset_timeout=settings.LLM_CIRCUIT_BREAKER_RESET_SECONDS,
)


def get_summary_service() -> SummaryService:
    uow = SQLAlchemyUnitOfWork()
    gateway = GeminiGateway(
        api_key=settings.GEMINI_API_KEY,
        model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        circuit_breaker=_global_breaker,
    )
    return SummaryService(uow=uow, gateway=gateway)


@router.post(
    "/ai-summary",
    response_model=SummaryResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Generar o consultar el resumen ejecutivo potenciado por LLM",
    description=(
        "Construye un snapshot minimizado de métricas y tareas críticas. "
        "Si la IA falla o la cuota se agota, responde 200 de forma transparente con un resumen determinista local."
    ),
)
async def generate_summary(
    refresh: bool = Query(False, description="Forzar la regeneración omitiendo la caché"),
    service: SummaryService = Depends(get_summary_service),
) -> SummaryResponseSchema:
    result = await service.get_or_generate_summary(force_refresh=refresh)
    return SummaryResponseSchema(**result)
