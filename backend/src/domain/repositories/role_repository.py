"""Role repository interface (Port)."""

from abc import ABC, abstractmethod

from src.domain.entities.role import Role


class IRoleRepository(ABC):

    @abstractmethod
    async def get_by_id(self, role_id: int, *, with_permissions: bool = False) -> Role | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Role | None: ...

    @abstractmethod
    async def list_active(self, tenant_id: int | None = None) -> list[Role]: ...

    @abstractmethod
    async def list_by_ids(self, role_ids: list[int]) -> list[Role]: ...

    @abstractmethod
    async def create(self, role: Role) -> Role: ...

    @abstractmethod
    async def update(self, role: Role) -> Role: ...

    @abstractmethod
    async def is_permission_granted(self, role_id: int, permission_id: int) -> bool: ...

    @abstractmethod
    async def grant_permission(self, role_id: int, permission_id: int, granted_by: str) -> None: ...

    @abstractmethod
    async def revoke_permission(self, role_id: int, permission_id: int) -> bool: ...
