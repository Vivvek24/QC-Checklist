"""
Darwinbox Application Service.
Orchestrates the Darwinbox employee master workflow:
- reachability/health checks
- fetching the master from the Darwinbox API (external adapter)
- syncing (upserting) records into the local database (repository)
- listing stored records

Controllers delegate here; this layer coordinates the external client and
the repository. It contains no HTTP or persistence details of its own.
"""

import logging
import re
from typing import Any
from uuid import uuid4

from src.api.v1.schemas.darwinbox_schema import (
    DarwinboxEmployeeListResponse,
    DarwinboxEmployeeResponse,
    DarwinboxHealthResponse,
    SyncEmployeesResponse,
)
from src.domain.entities.darwinbox_employee import DarwinboxEmployee
from src.domain.entities.user import User
from src.domain.repositories.darwinbox_employee_repository import (
    IDarwinboxEmployeeRepository,
)
from src.infrastructure.external.darwinbox.darwinbox_client import (
    DarwinboxClient,
    DarwinboxDataset,
    DarwinboxError,
)

logger = logging.getLogger(__name__)

# Mirrors the Mendix SplitString java action ("Bracket" mode): split on optional
# whitespace followed by "(", and return the first segment, trimmed. Used to
# derive the split_* fields. No fallback — an empty source yields an empty result.
_BRACKET_SPLIT = re.compile(r"\s*\(")


def _split_before_bracket(value: str) -> str:
    """Return the part of ``value`` before the first '(' (whitespace-trimmed)."""
    if not value:
        return ""
    return _BRACKET_SPLIT.split(value, maxsplit=1)[0].strip()


class DarwinboxService:
    """Application service for the Darwinbox employee master integration."""

    def __init__(
        self,
        client: DarwinboxClient,
        repository: IDarwinboxEmployeeRepository,
    ) -> None:
        self._client = client
        self._repository = repository

    # ─── Health ───

    async def check_health(self) -> DarwinboxHealthResponse:
        """Report whether the Darwinbox master API is reachable and configured."""
        result = await self._client.health_check()
        return DarwinboxHealthResponse(
            service="Darwinbox (Employee Master)",
            active_configured=self._client.is_configured("active"),
            inactive_configured=self._client.is_configured("inactive"),
            base_url=self._client.base_url,
            status=result.get("status", "unknown"),
            status_code=result.get("status_code"),
            error=result.get("error"),
            url=result.get("url"),
        )

    # ─── Fetch (no persistence) ───

    async def fetch_remote_employees(
        self, dataset: DarwinboxDataset = "active"
    ) -> dict[str, Any]:
        """
        Fetch the raw employee master for a dataset from Darwinbox without persisting.

        Raises:
            DarwinboxError: propagated from the client for the controller to map.
        """
        result = await self._client.fetch_employees(dataset)
        return {
            "dataset": dataset,
            "status": result.status,
            "message": result.message,
            "count": len(result.employees),
            "employee_data": result.employees,
        }

    # ─── Sync (fetch + upsert) ───

    async def sync_employees(
        self, actor: User, datasets: list[DarwinboxDataset]
    ) -> SyncEmployeesResponse:
        """
        Fetch one or more Darwinbox datasets (active/inactive) and upsert each
        record (keyed on employee_id) into the local database.

        Raises:
            DarwinboxError: if Darwinbox is unreachable or returns a failure.
        """
        total = 0
        created = 0
        updated = 0
        failed = 0
        messages: list[str] = []

        for dataset in datasets:
            result = await self._client.fetch_employees(dataset)
            if not result.is_success:
                raise DarwinboxError(
                    f"Darwinbox ({dataset}) returned status={result.status}: "
                    f"{result.message}"
                )

            counts = await self._upsert_employees(result.employees, actor.username)
            total += len(result.employees)
            created += counts["created"]
            updated += counts["updated"]
            failed += counts["failed"]
            messages.append(f"{dataset}: {result.message}")

        return SyncEmployeesResponse(
            datasets=list(datasets),
            total=total,
            created=created,
            updated=updated,
            failed=failed,
            message=" | ".join(messages),
        )

    async def _upsert_employees(
        self, employees: list[dict[str, Any]], actor_username: str
    ) -> dict[str, Any]:
        """
        Bulk-upsert a batch of Darwinbox payloads, returning created/updated/failed
        counts.

        Payloads are mapped to entities and de-duplicated by employee_id (last one
        wins). Existing ids are looked up in a single query so we can report accurate
        created vs updated counts, then everything is written in a single bulk upsert.
        """
        failed = 0
        entities_by_id: dict[str, DarwinboxEmployee] = {}

        for payload in employees:
            employee_id = str(payload.get("employee_id", "")).strip()
            if not employee_id:
                failed += 1
                continue
            entities_by_id[employee_id] = self._map_payload_to_entity(
                payload, actor_username
            )

        if not entities_by_id:
            return {"created": 0, "updated": 0, "failed": failed}

        ids = list(entities_by_id.keys())
        existing_ids = await self._repository.get_existing_employee_ids(ids)
        updated = len(existing_ids)
        created = len(ids) - updated

        await self._repository.bulk_upsert(list(entities_by_id.values()))

        return {"created": created, "updated": updated, "failed": failed}

    # ─── List stored records ───

    async def list_employees(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        search: str | None = None,
    ) -> DarwinboxEmployeeListResponse:
        """List employees already stored in the local database."""
        employees = await self._repository.list_all(
            skip=skip, limit=limit, status=status, search=search
        )
        total = await self._repository.count(status=status, search=search)
        return DarwinboxEmployeeListResponse(
            employees=[self._to_response(e) for e in employees],
            total=total,
            skip=skip,
            limit=limit,
        )

    # ─── Private helpers ───

    @staticmethod
    def _map_payload_to_entity(payload: dict[str, Any], actor_username: str) -> DarwinboxEmployee:
        """Map a raw Darwinbox employee payload into a domain entity."""

        def get(key: str) -> str:
            val = payload.get(key, "")
            return str(val).strip() if val is not None else ""

        def get_int(key: str) -> int:
            val = payload.get(key)
            try:
                return int(str(val).strip()) if val not in (None, "") else 0
            except (TypeError, ValueError):
                return 0

        first = get("first_name")
        middle = get("middle_name")
        last = get("last_name")
        full_name = " ".join(part for part in [first, middle, last] if part)

        return DarwinboxEmployee(
            id=uuid4(),
            created_by=actor_username,
            modified_by=actor_username,
            employee_id=get("employee_id"),
            employeeid_num=get_int("employeeid"),
            first_name=first,
            middle_name=middle,
            last_name=last,
            full_name=full_name,
            company_email_id=get("company_email_id"),
            employee_status=get("employee_status"),
            designation_title=get("designation_title"),
            job_level=get("job_level"),
            role=get("role"),
            department=get("department"),
            business_unit=get("business_unit"),
            division=get("division"),
            group_company=get("group_company"),
            catalyst_additional_department=get("catalyst_additional_department"),
            departments_hierarchy=get("departments_hierarchy"),
            cost_center_id=get("cost_center_id"),
            cost_center=get("cost_center"),
            office_mobile_no=get("office_mobile_no"),
            extension_mobile_no=get("extension_mobile_no"),
            personal_mobile_no=get("personal_mobile_no"),
            current_address=get("current_address"),
            current_country=get("current_country"),
            current_location=get("current_location"),
            office_location=get("office_location"),
            custom_location=get("custom_location"),
            office_state=get("office_state"),
            office_city=get("office_city"),
            direct_manager_employee_id=get("direct_manager_employee_id"),
            direct_manager_name=get("direct_manager_name"),
            direct_manager_email=get("direct_manager_email"),
            territory_code=get("territory_code_(sales_hq_code)"),
            territory_name=get("territory_name"),
            split_territory=_split_before_bracket(get("territory_name")),
            split_department=_split_before_bracket(get("department")),
            split_role=_split_before_bracket(get("role")),
            bank_pan=get("bank_pan"),
            date_of_birth=get("date_of_birth"),
            gender=get("gender"),
            date_of_exit=get("date_of_exit"),
        )

    @staticmethod
    def _to_response(entity: DarwinboxEmployee) -> DarwinboxEmployeeResponse:
        """Map a domain entity into the response DTO."""
        return DarwinboxEmployeeResponse(
            id=entity.id,
            employee_id=entity.employee_id,
            employeeid_num=entity.employeeid_num,
            full_name=entity.full_name,
            first_name=entity.first_name,
            middle_name=entity.middle_name,
            last_name=entity.last_name,
            company_email_id=entity.company_email_id,
            employee_status=entity.employee_status,
            designation_title=entity.designation_title,
            job_level=entity.job_level,
            role=entity.role,
            department=entity.department,
            business_unit=entity.business_unit,
            division=entity.division,
            group_company=entity.group_company,
            catalyst_additional_department=entity.catalyst_additional_department,
            departments_hierarchy=entity.departments_hierarchy,
            cost_center_id=entity.cost_center_id,
            cost_center=entity.cost_center,
            office_mobile_no=entity.office_mobile_no,
            extension_mobile_no=entity.extension_mobile_no,
            personal_mobile_no=entity.personal_mobile_no,
            current_address=entity.current_address,
            current_country=entity.current_country,
            current_location=entity.current_location,
            office_location=entity.office_location,
            custom_location=entity.custom_location,
            office_state=entity.office_state,
            office_city=entity.office_city,
            direct_manager_employee_id=entity.direct_manager_employee_id,
            direct_manager_name=entity.direct_manager_name,
            direct_manager_email=entity.direct_manager_email,
            territory_code=entity.territory_code,
            territory_name=entity.territory_name,
            split_territory=entity.split_territory,
            split_department=entity.split_department,
            split_role=entity.split_role,
            bank_pan=entity.bank_pan,
            date_of_birth=entity.date_of_birth,
            gender=entity.gender,
            date_of_exit=entity.date_of_exit,
            created_by=entity.created_by,
            created_date=entity.created_date,
            modified_by=entity.modified_by,
            modified_date=entity.modified_date,
        )
