"""Approval matrix repository port."""

from abc import abstractmethod

from src.domain.entities.approval_matrix import ApprovalMatrix, ApprovalTask
from src.domain.repositories.base_repository import IRepository


class IApprovalMatrixRepository(IRepository[ApprovalMatrix]):

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> list[ApprovalMatrix]: ...

    @abstractmethod
    async def count(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> int: ...

    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...

    @abstractmethod
    async def list_active_for_entity_type(self, entity_type: str) -> list[ApprovalMatrix]: ...

    @abstractmethod
    async def create_task(self, task: ApprovalTask) -> ApprovalTask: ...

    @abstractmethod
    async def get_task(self, task_id: int) -> ApprovalTask | None: ...

    @abstractmethod
    async def update_task(self, task: ApprovalTask) -> ApprovalTask: ...

    @abstractmethod
    async def list_tasks_for_instance(self, instance_id: int) -> list[ApprovalTask]: ...

    @abstractmethod
    async def list_pending_tasks_for_user(self, user_id: int) -> list[ApprovalTask]: ...

    @abstractmethod
    async def cancel_open_tasks_for_instance(self, instance_id: int) -> int: ...

    @abstractmethod
    async def list_tasks_for_user(self, user_id: int) -> list[ApprovalTask]: ...
