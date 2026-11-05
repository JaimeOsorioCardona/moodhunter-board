"""Pydantic schemas for presentation layer (API request & response models)."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class RequestCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, description="Título conciso de la solicitud.")
    description: Optional[str] = Field(None, max_length=5000, description="Descripción detallada de la solicitud.")


class RequestUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150, description="Nuevo título de la solicitud.")
    description: Optional[str] = Field(None, max_length=5000, description="Nueva descripción de la solicitud.")


class RequestTransitionSchema(BaseModel):
    target_status: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Slug del estado destino (ej. 'in_review', 'in_progress', 'paused', 'done').",
        examples=["in_review"],
    )


class HistoryItemSchema(BaseModel):
    id: Optional[int] = None
    from_status: Optional[str] = None
    to_status: str
    changed_at: datetime


class RequestResponseSchema(BaseModel):
    public_id: str
    title: str
    description: Optional[str] = None
    status: str
    allowed_transitions: list[str]
    version: int
    created_at: datetime
    updated_at: datetime
    history: Optional[list[HistoryItemSchema]] = None


class AllowedTransitionsResponseSchema(BaseModel):
    public_id: str
    current_status: str
    allowed: list[str]


class ErrorResponseSchema(BaseModel):
    error: str = Field(..., description="Código de error estandarizado.")
    message: str = Field(..., description="Mensaje legible para humanos en español.")
    details: Optional[dict[str, Any]] = Field(default=None, description="Detalles adicionales contextuales del error.")


class SummaryResponseSchema(BaseModel):
    source: str = Field(..., description="'llm' si fue generado por IA o 'fallback' si fue generado localmente.")
    headline: str = Field(..., description="Titular resumen ejecutivo (máx 140 chars).")
    highlights: list[str] = Field(default_factory=list, description="Puntos destacados clave.")
    risks: list[str] = Field(default_factory=list, description="Riesgos identificados o solicitudes estancadas.")
    next_actions: list[str] = Field(default_factory=list, description="Acciones prioritarias sugeridas.")
    generated_at: str = Field(..., description="Timestamp ISO del momento de generación.")
    cached: bool = Field(default=False, description="Indica si la respuesta provino de caché en memoria.")


class HealthResponseSchema(BaseModel):
    status: str
    database: str
    circuit_breaker: str
