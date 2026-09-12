"""
Darwinbox employee repository interface (Port).
Defines the contract for Darwinbox employee persistence operations.
The domain layer owns this interface; infrastructure implements it.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.darwinbox_employee import DarwinboxEmployee


class IDarwinboxEmployeeRepository(ABC):
    """Abstract repository for DarwinboxEmployee persistence."""

    @abstractmethod
    async def get_by_employee_id(self, employee_id: str) -> DarwinboxEmployee | None:
        """Retrieve an employee by their Darwinbox employee_id."""
        ...

    @abstractmethod
    async def create(self, employee: DarwinboxEmployee) -> DarwinboxEmployee:
        """Persist a new employee record."""
        ...

    @abstractmethod
    async def update(self, employee: DarwinboxEmployee) -> DarwinboxEmployee:
        """Update an existing employee record."""
        ...

    @abstractmethod
    async def get_existing_employee_ids(self, employee_ids: list[str]) -> set[str]:
        """Return the subset of the given employee_ids that already exist."""
        ...

    @abstractmethod
    async def bulk_upsert(self, employees: list[DarwinboxEmployee]) -> None:
        """Insert or update many employees in bulk (keyed on employee_id)."""
        ...

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        search: str | None = None,
    ) -> list[DarwinboxEmployee]:
        """List employees with pagination and optional status/search filters."""
        ...

    @abstractmethod
    async def get_all(self, status: str | None = None) -> list[DarwinboxEmployee]:
        """Return every stored employee (optionally filtered by status), unpaginated."""
        ...

    @abstractmethod
    async def find_by_identifiers(
        self, identifiers: list[str]
    ) -> list[DarwinboxEmployee]:
        """
        Return employees matching any of the given identifiers.
        An identifier may be an ``employee_id`` or a ``company_email_id``
        (email match is case-insensitive).
        """
        ...

    @abstractmethod
    async def fetch_hierarchy(self, active_only: bool = False) -> list[dict[str, Any]]:
        """
        Return the distinct role/designation hierarchy built by walking the
        ``direct_manager_employee_id`` chain (recursive CTE). Each row carries
        ``split_role``, ``role``, ``designation_title``, ``department``,
        ``split_department``, ``job_level`` and the max ``level`` (depth).

        When ``active_only`` is True, only 'Active' employees are considered.
        """
        ...

    @abstractmethod
    async def count(self, status: str | None = None, search: str | None = None) -> int:
        """Count employees, optionally filtered by status/search."""
        ...
