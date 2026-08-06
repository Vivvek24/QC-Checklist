"""Workflow instance repository port."""

from abc import ABC, abstractmethod

from src.domain.entities.workflow import WorkflowHistoryEntry, WorkflowInstance


class IWorkflowInstanceRepository(ABC):

    @abstractmethod
    async def get_by_id(self, instance_id: int) -> WorkflowInstance | None: ...

    @abstractmethod
    async def create(self, instance: WorkflowInstance) -> WorkflowInstance: ...

    @abstractmethod
    async def update(self, instance: WorkflowInstance) -> WorkflowInstance: ...

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        entity_type: str | None = None,
        entity_id: int | None = None,
        definition_id: int | None = None,
        status_id: int | None = None,
        initiated_by: int | None = None,
        is_completed: bool | None = None,
    ) -> list[WorkflowInstance]: ...

    @abstractmethod
    async def count(
        self,
        entity_type: str | None = None,
        entity_id: int | None = None,
        definition_id: int | None = None,
        status_id: int | None = None,
        initiated_by: int | None = None,
        is_completed: bool | None = None,
    ) -> int: ...

    @abstractmethod
    async def get_open_for_entity(
        self, entity_type: str, entity_id: int
    ) -> WorkflowInstance | None: ...

    @abstractmethod
    async def add_history(self, entry: WorkflowHistoryEntry) -> WorkflowHistoryEntry: ...

    @abstractmethod
    async def list_history(self, instance_id: int) -> list[WorkflowHistoryEntry]: ...
