"""Permission repository interface (Port)."""

from abc import ABC, abstractmethod

from src.domain.entities.role import Permission


class IPermissionRepository(ABC):

    @abstractmethod
    async def get_by_id(self, permission_id: int) -> Permission | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Permission | None: ...

    @abstractmethod
    async def list_active(self, scope: str | None = None) -> list[Permission]: ...

    @abstractmethod
    async def create(self, permission: Permission) -> Permission: ...
