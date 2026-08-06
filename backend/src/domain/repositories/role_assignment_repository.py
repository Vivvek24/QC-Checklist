"""Role assignment repository interface (Port)."""

from abc import ABC, abstractmethod

from src.domain.entities.role import RoleAssignment


class IRoleAssignmentRepository(ABC):

    @abstractmethod
    async def get_active(self, user_id: int, role_id: int) -> RoleAssignment | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: int) -> list[RoleAssignment]: ...

    @abstractmethod
    async def list_active_for_user(self, user_id: int) -> list[RoleAssignment]: ...

    @abstractmethod
    async def list_active_user_ids_for_role(self, role_id: int) -> list[int]: ...

    @abstractmethod
    async def deactivate_all_for_user(self, user_id: int, modified_by: str) -> int: ...

    @abstractmethod
    async def create(self, assignment: RoleAssignment) -> RoleAssignment: ...

    @abstractmethod
    async def deactivate(self, assignment_id: int, modified_by: str) -> None: ...
