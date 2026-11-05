"""SQLAlchemy implementation of the Unit of Work pattern."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import IUnitOfWork
from app.infrastructure.db.repositories import SQLAlchemyRequestRepository
from app.infrastructure.db.session import AsyncSessionLocal


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session_factory=AsyncSessionLocal):
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self.requests: SQLAlchemyRequestRepository = None  # type: ignore

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.requests = SQLAlchemyRequestRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            if self.session:
                await self.session.close()

    async def commit(self) -> None:
        if self.session:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()
