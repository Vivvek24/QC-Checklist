"""Audit log repository interface (Port). Append-only."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.audit_log import AuditLog


class IAuditLogRepository(ABC):

    @abstractmethod
    async def add(self, entry: AuditLog) -> None: ...

    @abstractmethod
    async def query(
        self,
        *,
        action: str | None = None,
        actor_id: int | None = None,
        actor_username: str | None = None,
        resource_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def count(
        self,
        *,
        action: str | None = None,
        actor_id: int | None = None,
        actor_username: str | None = None,
        resource_type: str | None = None,
    ) -> int: ...

    @abstractmethod
    async def latest_timestamp_by_actor(
        self, action: str, actor_ids: list[int]
    ) -> dict[int, datetime]: ...
