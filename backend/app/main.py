"""Main FastAPI application entrypoint for Mood Hunter."""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.domain.exceptions import DomainError
from app.infrastructure.db.session import init_db
from app.presentation.handlers import domain_error_handler, validation_error_handler
from app.presentation.routers.health import router as health_router
from app.presentation.routers.requests import router as requests_router
from app.presentation.routers.summary import router as summary_router

settings = get_settings()

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
)
logger = logging.getLogger("moodhunter")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize database tables and seed data if needed."""
    logger.info("Iniciando aplicación Mood Hunter...")
    if settings.ENVIRONMENT != "test":
        try:
            await init_db()
            logger.info("Base de datos conectada y verificada exitosamente.")
        except Exception as exc:
            logger.warning("No se pudo conectar a la BD durante el arranque inicial: %s", exc)
    yield
    logger.info("Deteniendo aplicación Mood Hunter...")


app = FastAPI(
    title="Tablero de Solicitudes con Flujo de Estados | MOOD HUNTER",
    description=(
        "API REST para la gestión de solicitudes con máquina de estados finitos (FSM), "
        "control de concurrencia, resiliencia y asistente de resumen ejecutivo potenciado por LLM."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and structured timing middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)

    logger.info(
        'request_id="%s" method="%s" path="%s" status=%d duration_ms=%.2f',
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        process_time_ms,
    )
    return response


# Register global exception handlers
app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore

# Include Routers
app.include_router(health_router)
app.include_router(requests_router, prefix="/api/v1")
app.include_router(summary_router, prefix="/api/v1")
