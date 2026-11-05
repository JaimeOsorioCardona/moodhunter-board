"""API routes for managing requests and executing state transitions."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.application.request_service import RequestService
from app.infrastructure.db.uow import SQLAlchemyUnitOfWork
from app.presentation.schemas import (
    AllowedTransitionsResponseSchema,
    ErrorResponseSchema,
    HistoryItemSchema,
    RequestCreateSchema,
    RequestResponseSchema,
    RequestTransitionSchema,
    RequestUpdateSchema,
)

router = APIRouter(prefix="/requests", tags=["Requests"])


def get_request_service() -> RequestService:
    uow = SQLAlchemyUnitOfWork()
    return RequestService(uow)


@router.post(
    "",
    response_model=RequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva solicitud",
    responses={422: {"model": ErrorResponseSchema}},
)
async def create_request(
    payload: RequestCreateSchema,
    service: RequestService = Depends(get_request_service),
) -> RequestResponseSchema:
    entity = await service.create_request(title=payload.title, description=payload.description)
    return RequestResponseSchema(
        public_id=entity.public_id,
        title=entity.title,
        description=entity.description,
        status=entity.status.value,
        allowed_transitions=entity.allowed_transitions,
        version=entity.version,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get(
    "",
    response_model=list[RequestResponseSchema],
    summary="Listar solicitudes (con filtro opcional de estado)",
    responses={422: {"model": ErrorResponseSchema}},
)
async def list_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrar por slug de estado (ej: created, in_review)"),
    service: RequestService = Depends(get_request_service),
) -> list[RequestResponseSchema]:
    entities = await service.list_requests(status_code=status_filter)
    return [
        RequestResponseSchema(
            public_id=e.public_id,
            title=e.title,
            description=e.description,
            status=e.status.value,
            allowed_transitions=e.allowed_transitions,
            version=e.version,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in entities
    ]


@router.get(
    "/{public_id}",
    response_model=RequestResponseSchema,
    summary="Consultar una solicitud por su ID público",
    responses={404: {"model": ErrorResponseSchema}},
)
async def get_request(
    public_id: str,
    service: RequestService = Depends(get_request_service),
) -> RequestResponseSchema:
    entity = await service.get_request(public_id)
    history = [
        HistoryItemSchema(
            id=h.id,
            from_status=h.from_status.value if h.from_status else None,
            to_status=h.to_status.value,
            changed_at=h.changed_at,
        )
        for h in entity.history
    ]
    return RequestResponseSchema(
        public_id=entity.public_id,
        title=entity.title,
        description=entity.description,
        status=entity.status.value,
        allowed_transitions=entity.allowed_transitions,
        version=entity.version,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        history=history,
    )


@router.patch(
    "/{public_id}",
    response_model=RequestResponseSchema,
    summary="Editar título y descripción de una solicitud",
    responses={
        404: {"model": ErrorResponseSchema},
        422: {"model": ErrorResponseSchema},
    },
)
async def update_request(
    public_id: str,
    payload: RequestUpdateSchema,
    service: RequestService = Depends(get_request_service),
) -> RequestResponseSchema:
    entity = await service.update_request(
        public_id=public_id,
        title=payload.title,
        description=payload.description,
    )
    return RequestResponseSchema(
        public_id=entity.public_id,
        title=entity.title,
        description=entity.description,
        status=entity.status.value,
        allowed_transitions=entity.allowed_transitions,
        version=entity.version,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get(
    "/{public_id}/allowed-transitions",
    response_model=AllowedTransitionsResponseSchema,
    summary="Consultar transiciones permitidas desde el estado actual",
    responses={404: {"model": ErrorResponseSchema}},
)
async def get_allowed_transitions(
    public_id: str,
    service: RequestService = Depends(get_request_service),
) -> AllowedTransitionsResponseSchema:
    result = await service.get_allowed_transitions(public_id)
    return AllowedTransitionsResponseSchema(
        public_id=str(result["public_id"]),
        current_status=str(result["current_status"]),
        allowed=list(result["allowed"]),
    )


@router.post(
    "/{public_id}/transitions",
    response_model=RequestResponseSchema,
    summary="Ejecutar una transición de estado respetando las reglas de negocio",
    responses={
        404: {"model": ErrorResponseSchema, "description": "Solicitud no encontrada"},
        409: {"model": ErrorResponseSchema, "description": "Transición no permitida por las reglas de negocio"},
        422: {"model": ErrorResponseSchema, "description": "Slug de estado destino inválido"},
    },
)
async def execute_transition(
    public_id: str,
    payload: RequestTransitionSchema,
    service: RequestService = Depends(get_request_service),
) -> RequestResponseSchema:
    entity = await service.execute_transition(
        public_id=public_id,
        target_slug=payload.target_status,
    )
    history = [
        HistoryItemSchema(
            id=h.id,
            from_status=h.from_status.value if h.from_status else None,
            to_status=h.to_status.value,
            changed_at=h.changed_at,
        )
        for h in entity.history
    ]
    return RequestResponseSchema(
        public_id=entity.public_id,
        title=entity.title,
        description=entity.description,
        status=entity.status.value,
        allowed_transitions=entity.allowed_transitions,
        version=entity.version,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        history=history,
    )
