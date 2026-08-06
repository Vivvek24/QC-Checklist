"""Workflow definition repository port."""

from abc import abstractmethod

from src.domain.entities.workflow import WorkflowDefinition, WorkflowStatus, WorkflowTransition
from src.domain.repositories.base_repository import IRepository


class IWorkflowDefinitionRepository(IRepository[WorkflowDefinition]):

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> list[WorkflowDefinition]: ...

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
    async def get_definitions_by_ids(self, definition_ids: list[int]) -> list[WorkflowDefinition]: ...

    @abstractmethod
    async def list_statuses(self, definition_id: int) -> list[WorkflowStatus]: ...

    @abstractmethod
    async def get_status(self, status_id: int) -> WorkflowStatus | None: ...

    @abstractmethod
    async def get_statuses_by_ids(self, status_ids: list[int]) -> list[WorkflowStatus]: ...

    @abstractmethod
    async def get_initial_status(self, definition_id: int) -> WorkflowStatus | None: ...

    @abstractmethod
    async def exists_status_code(
        self, definition_id: int, code: str, exclude_id: int | None = None
    ) -> bool: ...

    @abstractmethod
    async def create_status(self, status: WorkflowStatus) -> WorkflowStatus: ...

    @abstractmethod
    async def update_status(self, status: WorkflowStatus) -> WorkflowStatus: ...

    @abstractmethod
    async def delete_status(self, status_id: int) -> None: ...

    @abstractmethod
    async def count_transitions_touching_status(self, status_id: int) -> int: ...

    @abstractmethod
    async def count_instances_in_status(self, status_id: int) -> int: ...

    @abstractmethod
    async def list_transitions(self, definition_id: int) -> list[WorkflowTransition]: ...

    @abstractmethod
    async def list_transitions_from(
        self, definition_id: int, from_status_id: int
    ) -> list[WorkflowTransition]: ...

    @abstractmethod
    async def get_transition(self, transition_id: int) -> WorkflowTransition | None: ...

    @abstractmethod
    async def find_transition(
        self, definition_id: int, from_status_id: int, action_code: str
    ) -> WorkflowTransition | None: ...

    @abstractmethod
    async def exists_transition(
        self, definition_id: int, from_status_id: int, action_code: str
    ) -> bool: ...

    @abstractmethod
    async def create_transition(self, transition: WorkflowTransition) -> WorkflowTransition: ...

    @abstractmethod
    async def delete_transition(self, transition_id: int) -> None: ...
