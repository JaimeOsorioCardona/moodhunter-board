"""Application ports (interfaces) for repositories, unit of work, and LLM gateway."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from app.infrastructure.db.models import RequestModel, RequestStatusHistoryModel, StatusModel


class IRequestRepository(ABC):
    @abstractmethod
    async def create(self, request: RequestModel) -> RequestModel:
        pass

    @abstractmethod
    async def get_by_public_id(self, public_id: str, for_update: bool = False) -> Optional[RequestModel]:
        pass

    @abstractmethod
    async def list(self, status_code: Optional[str] = None) -> list[RequestModel]:
        pass

    @abstractmethod
    async def get_status_by_code(self, code: str) -> Optional[StatusModel]:
        pass

    @abstractmethod
    async def get_all_statuses(self) -> list[StatusModel]:
        pass

    @abstractmethod
    async def add_history(self, history: RequestStatusHistoryModel) -> RequestStatusHistoryModel:
        pass

    @abstractmethod
    async def count_by_status(self) -> dict[str, int]:
        pass


class IUnitOfWork(ABC):
    requests: IRequestRepository

    async def __aenter__(self) -> "IUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass


class ILLMGateway(ABC):
    @abstractmethod
    async def generate_summary(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Generate executive summary from a board snapshot.

        Must return a dict conforming to the summary schema.
        """
        pass
