"""Global exception handlers mapping domain exceptions to HTTP responses."""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    ConcurrencyConflictError,
    DomainError,
    RequestNotFoundError,
    TransitionNotAllowedError,
    UnknownStatusError,
)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Map domain exceptions to RFC-compliant HTTP status codes."""
    if isinstance(exc, RequestNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (TransitionNotAllowedError, ConcurrencyConflictError)):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, UnknownStatusError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format Pydantic schema validation errors uniformly."""
    first_error = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(l) for l in first_error.get("loc", []))
    msg = first_error.get("msg", "Error de validación")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": f"Error en el campo '{loc}': {msg}",
            "details": {"errors": exc.errors()},
        },
    )
