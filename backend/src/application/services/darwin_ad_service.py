"""
Darwin AD Published Service (application layer).

Serves the endpoints migrated from the legacy Mendix "Darwin AD integrator"
service. Employee data is served from the locally-synced ``darwinbox_employees``
table (populated by DarwinboxService), so these read endpoints have no live
LDAP/AD dependency. Credential validation is intentionally NOT handled here —
it requires a live LDAP bind and is implemented separately.

Controllers delegate here; this layer owns the read orchestration and the
entity -> Darwin AD wire-format mapping.
"""

import logging

from src.api.v1.schemas.darwin_ad_schema import (
    DarwinEmployeeRecord,
    EmployeeDataResponse,
    HierarchyItem,
    HierarchyResponse,
)
from src.domain.repositories.darwinbox_employee_repository import (
    IDarwinboxEmployeeRepository,
)

logger = logging.getLogger(__name__)


class DarwinAdService:
    """Read service backing the published Darwin AD endpoints."""

    def __init__(self, repository: IDarwinboxEmployeeRepository) -> None:
        self._repository = repository

    async def get_all_employees(
        self, status: str | None = None
    ) -> EmployeeDataResponse:
        """Return every stored employee in the Darwin AD envelope."""
        employees = await self._repository.get_all(status=status)
        logger.info("Darwin AD getemployees returned %d records", len(employees))
        return EmployeeDataResponse(
            employeeData=[DarwinEmployeeRecord.from_entity(e) for e in employees]
        )

    async def get_employees_by_identifiers(
        self, identifiers: list[str]
    ) -> EmployeeDataResponse:
        """
        Return employees matching the given identifiers. Each identifier may be
        an ``employee_id`` or a ``company_email_id`` (case-insensitive).
        """
        employees = await self._repository.find_by_identifiers(identifiers)
        logger.info(
            "Darwin AD lookup for %d identifier(s) matched %d record(s)",
            len(identifiers),
            len(employees),
        )
        return EmployeeDataResponse(
            employeeData=[DarwinEmployeeRecord.from_entity(e) for e in employees]
        )

    async def get_hierarchy(self, active_only: bool = False) -> HierarchyResponse:
        """
        Build the role/designation hierarchy by walking the manager chain.
        Mirrors the Mendix JA_GetHierarchyData recursive CTE.
        """
        rows = await self._repository.fetch_hierarchy(active_only=active_only)
        logger.info(
            "Darwin AD getHierarchyData returned %d nodes (active_only=%s)",
            len(rows),
            active_only,
        )
        return HierarchyResponse(
            hierarchy=[HierarchyItem(**row) for row in rows]
        )

    @staticmethod
    def parse_identifiers(raw: str) -> list[str]:
        """Split a comma-separated identifier string into a clean list."""
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]
