"""Domain entities for requests and history."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.domain.fsm import Status, allowed_from


@dataclass
class StatusEntity:
    code: Status
    name: str
    description: Optional[str] = None
    sort_order: int = 0


@dataclass
class StatusHistoryEntity:
    id: Optional[int]
    from_status: Optional[Status]
    to_status: Status
    changed_at: datetime


@dataclass
class RequestEntity:
    public_id: str
    title: str
    description: Optional[str]
    status: Status
    version: int
    created_at: datetime
    updated_at: datetime
    history: list[StatusHistoryEntity] = field(default_factory=list)

    @property
    def allowed_transitions(self) -> list[str]:
        return sorted([s.value for s in allowed_from(self.status)])
