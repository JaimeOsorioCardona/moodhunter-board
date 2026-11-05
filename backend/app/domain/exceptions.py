"""Domain exceptions for Mood Hunter business rules.

These exceptions have zero external dependencies (no FastAPI, no SQLAlchemy).
"""

from typing import Any


class DomainError(Exception):
    """Base exception for all domain logic violations."""

    def __init__(self, message: str, code: str = "domain_error", details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class TransitionNotAllowedError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current: str, target: str, allowed: list[str]):
        allowed_repr = ", ".join(f"'{s}'" for s in allowed) if allowed else "ninguno (estado terminal)"
        msg = f"No se permite la transición de '{current}' a '{target}'. Estados permitidos: [{allowed_repr}]."
        super().__init__(
            message=msg,
            code="transition_not_allowed",
            details={
                "current": current,
                "target": target,
                "allowed": allowed,
            },
        )
        self.current = current
        self.target = target
        self.allowed = allowed


class RequestNotFoundError(DomainError):
    """Raised when a request cannot be located by its identifier."""

    def __init__(self, public_id: str):
        super().__init__(
            message=f"No se encontró la solicitud con ID '{public_id}'.",
            code="request_not_found",
            details={"public_id": public_id},
        )
        self.public_id = public_id


class UnknownStatusError(DomainError):
    """Raised when an invalid status code/slug is supplied."""

    def __init__(self, code_val: str):
        super().__init__(
            message=f"El estado '{code_val}' no es válido en el sistema.",
            code="unknown_status",
            details={"provided_status": code_val},
        )
        self.code_val = code_val


class ConcurrencyConflictError(DomainError):
    """Raised when an optimistic lock conflict or state mutation collision occurs."""

    def __init__(self, public_id: str, version: int):
        super().__init__(
            message=f"Conflicto de concurrencia al actualizar la solicitud '{public_id}'. El recurso fue modificado por otra transacción.",
            code="concurrency_conflict",
            details={"public_id": public_id, "version": version},
        )
        self.public_id = public_id
        self.version = version
