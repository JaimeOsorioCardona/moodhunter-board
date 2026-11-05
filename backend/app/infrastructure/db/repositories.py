"""SQLAlchemy implementation of the Request repository."""

from __future__ import annotations

from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.application.ports import IRequestRepository
from app.infrastructure.db.models import RequestModel, RequestStatusHistoryModel, StatusModel


class SQLAlchemyRequestRepository(IRequestRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self._status_cache: dict[str, StatusModel] = {}

    async def create(self, request: RequestModel) -> RequestModel:
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_by_public_id(self, public_id: str, for_update: bool = False) -> Optional[RequestModel]:
        stmt = (
            select(RequestModel)
            .options(
                joinedload(RequestModel.status),
                selectinload(RequestModel.history).joinedload(RequestStatusHistoryModel.from_status),
                selectinload(RequestModel.history).joinedload(RequestStatusHistoryModel.to_status),
            )
            .where(RequestModel.public_id == public_id)
        )

        if for_update:
            # Row-level locking (SELECT ... FOR UPDATE) for concurrency protection
            # SQLite does not support FOR UPDATE, so we only apply it on MySQL/PostgreSQL
            bind = self.session.bind
            dialect_name = bind.dialect.name if bind is not None else ""
            if dialect_name != "sqlite":
                stmt = stmt.with_for_update()

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, status_code: Optional[str] = None) -> list[RequestModel]:
        stmt = (
            select(RequestModel)
            .options(
                joinedload(RequestModel.status),
                selectinload(RequestModel.history).joinedload(RequestStatusHistoryModel.from_status),
                selectinload(RequestModel.history).joinedload(RequestStatusHistoryModel.to_status),
            )
            .order_by(RequestModel.updated_at.desc())
        )

        if status_code:
            stmt = stmt.join(StatusModel, RequestModel.status_id == StatusModel.id).where(
                StatusModel.code == status_code
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_status_by_code(self, code: str) -> Optional[StatusModel]:
        if code in self._status_cache:
            return self._status_cache[code]

        stmt = select(StatusModel).where(StatusModel.code == code)
        result = await self.session.execute(stmt)
        status = result.scalar_one_or_none()
        if status:
            self._status_cache[code] = status
        return status

    async def get_all_statuses(self) -> list[StatusModel]:
        stmt = select(StatusModel).order_by(StatusModel.sort_order.asc())
        result = await self.session.execute(stmt)
        statuses = list(result.scalars().all())
        for s in statuses:
            self._status_cache[s.code] = s
        return statuses

    async def add_history(self, history: RequestStatusHistoryModel) -> RequestStatusHistoryModel:
        self.session.add(history)
        await self.session.flush()
        return history

    async def count_by_status(self) -> dict[str, int]:
        stmt = (
            select(StatusModel.code, func.count(RequestModel.id))
            .select_from(StatusModel)
            .outerjoin(RequestModel, StatusModel.id == RequestModel.status_id)
            .group_by(StatusModel.code)
        )
        result = await self.session.execute(stmt)
        return {code: count for code, count in result.all()}
