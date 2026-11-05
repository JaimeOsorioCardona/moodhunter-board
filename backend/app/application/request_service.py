"""Application service orchestrating request workflows and state transitions."""

import uuid
from typing import Optional
from app.application.ports import IUnitOfWork
from app.domain.entities import RequestEntity, StatusHistoryEntity
from app.domain.exceptions import RequestNotFoundError
from app.domain.fsm import Status, allowed_from, assert_transition, validate_status
from app.infrastructure.db.models import RequestModel, RequestStatusHistoryModel, utcnow


class RequestService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def create_request(self, title: str, description: Optional[str] = None) -> RequestEntity:
        """Create a new request starting strictly in the 'created' status."""
        title_clean = title.strip()
        desc_clean = description.strip() if description else None

        async with self.uow:
            created_status_model = await self.uow.requests.get_status_by_code(Status.CREATED.value)
            if not created_status_model:
                raise RuntimeError("Estado inicial 'created' no encontrado en el catálogo de base de datos.")

            public_id = str(uuid.uuid4())
            now = utcnow()

            request_model = RequestModel(
                public_id=public_id,
                title=title_clean,
                description=desc_clean,
                status_id=created_status_model.id,
                version=1,
                created_at=now,
                updated_at=now,
            )
            await self.uow.requests.create(request_model)

            # Record initial history entry (from_status=None -> to_status='created')
            history_model = RequestStatusHistoryModel(
                request_id=request_model.id,
                from_status_id=None,
                to_status_id=created_status_model.id,
                changed_at=now,
            )
            await self.uow.requests.add_history(history_model)
            await self.uow.commit()

            # Retrieve with relationships
            refreshed = await self.uow.requests.get_by_public_id(public_id)
            return self._to_entity(refreshed or request_model)

    async def list_requests(self, status_code: Optional[str] = None) -> list[RequestEntity]:
        """List requests, optionally filtered by status code."""
        if status_code:
            # Validate status slug to fail fast on invalid filters
            validate_status(status_code)

        async with self.uow:
            models = await self.uow.requests.list(status_code=status_code)
            return [self._to_entity(m) for m in models]

    async def get_request(self, public_id: str) -> RequestEntity:
        """Get request details by public UUID."""
        async with self.uow:
            model = await self.uow.requests.get_by_public_id(public_id)
            if not model:
                raise RequestNotFoundError(public_id)
            return self._to_entity(model)

    async def update_request(
        self, public_id: str, title: Optional[str] = None, description: Optional[str] = None
    ) -> RequestEntity:
        """Update request title and/or description without altering status."""
        async with self.uow:
            model = await self.uow.requests.get_by_public_id(public_id, for_update=True)
            if not model:
                raise RequestNotFoundError(public_id)

            if title is not None:
                model.title = title.strip()
            if description is not None:
                model.description = description.strip() if description else None

            model.version += 1
            model.updated_at = utcnow()

            await self.uow.commit()

            refreshed = await self.uow.requests.get_by_public_id(public_id)
            return self._to_entity(refreshed or model)

    async def get_allowed_transitions(self, public_id: str) -> dict[str, list[str] | str]:
        """Query allowed target transitions from the current request state."""
        async with self.uow:
            model = await self.uow.requests.get_by_public_id(public_id)
            if not model:
                raise RequestNotFoundError(public_id)

            current_status = Status(model.status.code)
            valid_targets = allowed_from(current_status)
            return {
                "public_id": public_id,
                "current_status": current_status.value,
                "allowed": sorted([s.value for s in valid_targets]),
            }

    async def execute_transition(self, public_id: str, target_slug: str) -> RequestEntity:
        """Execute a state transition under row lock and atomic Unit of Work."""
        target_status = validate_status(target_slug)

        async with self.uow:
            # Row lock prevents concurrent transition race conditions
            model = await self.uow.requests.get_by_public_id(public_id, for_update=True)
            if not model:
                raise RequestNotFoundError(public_id)

            current_status = Status(model.status.code)

            # Validate against declarative FSM (raises TransitionNotAllowedError on violation)
            assert_transition(current_status, target_status)

            # Resolve target status ID
            target_status_model = await self.uow.requests.get_status_by_code(target_status.value)
            if not target_status_model:
                raise RuntimeError(f"Estado objetivo '{target_status.value}' no encontrado en BD.")

            from_status_id = model.status_id
            model.status_id = target_status_model.id
            model.status = target_status_model
            model.version += 1
            now = utcnow()
            model.updated_at = now

            # Record transition history entry
            history = RequestStatusHistoryModel(
                request_id=model.id,
                from_status_id=from_status_id,
                to_status_id=target_status_model.id,
                changed_at=now,
            )
            await self.uow.requests.add_history(history)
            await self.uow.commit()

            refreshed = await self.uow.requests.get_by_public_id(public_id)
            return self._to_entity(refreshed or model)

    def _to_entity(self, model: RequestModel) -> RequestEntity:
        """Map SQLAlchemy model to clean domain entity."""
        from sqlalchemy import inspect
        from sqlalchemy.orm.base import NO_VALUE

        history_entities = []
        insp = inspect(model)
        if "history" in insp.attrs and insp.attrs.history.loaded_value is not NO_VALUE:
            for h in model.history:
                history_entities.append(
                    StatusHistoryEntity(
                        id=h.id,
                        from_status=Status(h.from_status.code) if h.from_status else None,
                        to_status=Status(h.to_status.code) if h.to_status else Status.CREATED,
                        changed_at=h.changed_at,
                    )
                )

        status_code = model.status.code if model.status else Status.CREATED.value
        return RequestEntity(
            public_id=model.public_id,
            title=model.title,
            description=model.description,
            status=Status(status_code),
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
            history=history_entities,
        )
