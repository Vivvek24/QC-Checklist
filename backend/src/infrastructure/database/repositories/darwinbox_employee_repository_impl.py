"""
Darwinbox employee repository implementation (Adapter).
Implements IDarwinboxEmployeeRepository using SQLAlchemy async.
"""

from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import Select, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.darwinbox_employee import DarwinboxEmployee
from src.domain.repositories.darwinbox_employee_repository import (
    IDarwinboxEmployeeRepository,
)
from src.infrastructure.database.models.darwinbox_employee_model import (
    DarwinboxEmployeeModel,
)

# Preserves the caller's row type through `_apply_filters` — see its docstring.
_TSelect = TypeVar("_TSelect", bound=Select[Any])

# Business fields shared between the ORM model and the domain entity.
# Audit fields (id/created_*/modified_*) are handled explicitly.
_FIELDS: tuple[str, ...] = (
    "employee_id",
    "employeeid_num",
    "first_name",
    "middle_name",
    "last_name",
    "full_name",
    "company_email_id",
    "employee_status",
    "designation_title",
    "job_level",
    "role",
    "department",
    "business_unit",
    "division",
    "group_company",
    "catalyst_additional_department",
    "departments_hierarchy",
    "cost_center_id",
    "cost_center",
    "office_mobile_no",
    "extension_mobile_no",
    "personal_mobile_no",
    "current_address",
    "current_country",
    "current_location",
    "office_location",
    "custom_location",
    "office_state",
    "office_city",
    "direct_manager_employee_id",
    "direct_manager_name",
    "direct_manager_email",
    "territory_code",
    "territory_name",
    "split_territory",
    "split_department",
    "split_role",
    "bank_pan",
    "date_of_birth",
    "gender",
    "date_of_exit",
)


class DarwinboxEmployeeRepositoryImpl(IDarwinboxEmployeeRepository):
    """Concrete implementation of Darwinbox employee persistence using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_employee_id(self, employee_id: str) -> DarwinboxEmployee | None:
        stmt = select(DarwinboxEmployeeModel).where(
            DarwinboxEmployeeModel.employee_id == employee_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, employee: DarwinboxEmployee) -> DarwinboxEmployee:
        model = DarwinboxEmployeeModel(
            id=employee.id,
            created_by=employee.created_by,
            modified_by=employee.modified_by,
            **{name: getattr(employee, name) for name in _FIELDS},
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, employee: DarwinboxEmployee) -> DarwinboxEmployee:
        stmt = select(DarwinboxEmployeeModel).where(
            DarwinboxEmployeeModel.employee_id == employee.employee_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(
                f"Darwinbox employee '{employee.employee_id}' not found"
            )

        for name in _FIELDS:
            setattr(model, name, getattr(employee, name))
        model.modified_by = employee.modified_by

        await self._session.flush()
        return self._to_entity(model)

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        search: str | None = None,
    ) -> list[DarwinboxEmployee]:
        stmt = select(DarwinboxEmployeeModel)
        stmt = self._apply_filters(stmt, status, search)
        stmt = stmt.order_by(DarwinboxEmployeeModel.full_name).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_all(self, status: str | None = None) -> list[DarwinboxEmployee]:
        stmt = select(DarwinboxEmployeeModel)
        stmt = self._apply_filters(stmt, status, search=None)
        stmt = stmt.order_by(DarwinboxEmployeeModel.full_name)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_identifiers(
        self, identifiers: list[str]
    ) -> list[DarwinboxEmployee]:
        cleaned = [i.strip() for i in identifiers if i and i.strip()]
        if not cleaned:
            return []
        lowered = [i.lower() for i in cleaned]
        stmt = select(DarwinboxEmployeeModel).where(
            or_(
                DarwinboxEmployeeModel.employee_id.in_(cleaned),
                func.lower(DarwinboxEmployeeModel.company_email_id).in_(lowered),
            )
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def fetch_hierarchy(self, active_only: bool = False) -> list[dict[str, Any]]:
        # active_only is a controlled boolean (from settings), not user input,
        # so interpolating the filter fragment is safe from injection.
        active_filter = (
            "      AND emp.employee_status = 'Active'\n" if active_only else ""
        )
        active_filter_sub = (
            "      AND sub.employee_status = 'Active'\n" if active_only else ""
        )
        query = text(
            "WITH RECURSIVE hierarchy AS (\n"
            "    SELECT\n"
            "        emp.employee_id,\n"
            "        emp.direct_manager_employee_id,\n"
            "        TRIM(emp.designation_title)             AS designation_title,\n"
            "        TRIM(emp.role)                          AS role,\n"
            "        TRIM(emp.department)                    AS department,\n"
            "        TRIM(SPLIT_PART(emp.role, '(', 1))      AS split_role,\n"
            "        TRIM(SPLIT_PART(emp.department, '(', 1)) AS split_department,\n"
            "        TRIM(emp.job_level)                     AS job_level,\n"
            "        0 AS level\n"
            "    FROM darwinbox_employees emp\n"
            "    WHERE (emp.direct_manager_employee_id IS NULL\n"
            "        OR TRIM(emp.direct_manager_employee_id) = '')\n"
            "      AND emp.designation_title IS NOT NULL\n"
            "      AND TRIM(emp.designation_title) <> ''\n"
            f"{active_filter}"
            "\n"
            "    UNION ALL\n"
            "\n"
            "    SELECT\n"
            "        sub.employee_id,\n"
            "        sub.direct_manager_employee_id,\n"
            "        TRIM(sub.designation_title),\n"
            "        TRIM(sub.role),\n"
            "        TRIM(sub.department),\n"
            "        TRIM(SPLIT_PART(sub.role, '(', 1)),\n"
            "        TRIM(SPLIT_PART(sub.department, '(', 1)),\n"
            "        TRIM(sub.job_level),\n"
            "        h.level + 1\n"
            "    FROM darwinbox_employees sub\n"
            "    INNER JOIN hierarchy h\n"
            "        ON sub.direct_manager_employee_id = h.employee_id\n"
            "    WHERE sub.designation_title IS NOT NULL\n"
            "      AND TRIM(sub.designation_title) <> ''\n"
            f"{active_filter_sub}"
            ")\n"
            "SELECT\n"
            "    split_role, role, designation_title,\n"
            "    department, split_department, job_level,\n"
            "    MAX(level) AS level\n"
            "FROM hierarchy\n"
            "WHERE role IS NOT NULL\n"
            "  AND TRIM(role) <> ''\n"
            "GROUP BY split_role, role, designation_title, department, "
            "split_department, job_level\n"
            "ORDER BY level, role, department, job_level ASC"
        )
        result = await self._session.execute(query)
        return [dict(row._mapping) for row in result.all()]

    @staticmethod
    def _apply_filters(
        stmt: _TSelect, status: str | None, search: str | None
    ) -> _TSelect:
        """
        Apply optional status and search filters to a select statement.

        Generic over the statement type rather than typed `Select[Any]`: this is
        called both with `select(DarwinboxEmployeeModel)` and with
        `select(func.count())`, and a TypeVar hands each caller back the same row
        type it passed in instead of widening both to `Any`.
        """
        if status:
            stmt = stmt.where(DarwinboxEmployeeModel.employee_status == status)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    DarwinboxEmployeeModel.employee_id.ilike(term),
                    DarwinboxEmployeeModel.full_name.ilike(term),
                    DarwinboxEmployeeModel.company_email_id.ilike(term),
                    DarwinboxEmployeeModel.department.ilike(term),
                )
            )
        return stmt

    async def get_existing_employee_ids(self, employee_ids: list[str]) -> set[str]:
        existing: set[str] = set()
        if not employee_ids:
            return existing
        # Chunk the IN clause to keep parameter counts reasonable.
        chunk = 5000
        for start in range(0, len(employee_ids), chunk):
            batch = employee_ids[start : start + chunk]
            stmt = select(DarwinboxEmployeeModel.employee_id).where(
                DarwinboxEmployeeModel.employee_id.in_(batch)
            )
            result = await self._session.execute(stmt)
            existing.update(result.scalars().all())
        return existing

    async def bulk_upsert(self, employees: list[DarwinboxEmployee]) -> None:
        if not employees:
            return

        now = datetime.now(UTC)
        # Columns to refresh when a row already exists (never touch identity/creation).
        update_cols = (*_FIELDS[1:], "modified_by")  # skip employee_id (conflict key)

        # asyncpg caps bind parameters at 32767. Each row binds len(_FIELDS)
        # business columns + 5 audit columns (id, created_by, created_date,
        # modified_by, modified_date). Keep chunks safely under the cap.
        params_per_row = len(_FIELDS) + 5
        chunk = max(1, 30000 // params_per_row)
        for start in range(0, len(employees), chunk):
            batch = employees[start : start + chunk]
            rows = [
                {
                    "id": e.id,
                    "created_by": e.created_by,
                    "created_date": e.created_date,
                    "modified_by": e.modified_by,
                    "modified_date": now,
                    **{name: getattr(e, name) for name in _FIELDS},
                }
                for e in batch
            ]
            stmt = pg_insert(DarwinboxEmployeeModel).values(rows)
            set_ = {col: getattr(stmt.excluded, col) for col in update_cols}
            set_["modified_date"] = now
            stmt = stmt.on_conflict_do_update(
                index_elements=[DarwinboxEmployeeModel.employee_id],
                set_=set_,
            )
            await self._session.execute(stmt)

    async def count(self, status: str | None = None, search: str | None = None) -> int:
        stmt = select(func.count()).select_from(DarwinboxEmployeeModel)
        stmt = self._apply_filters(stmt, status, search)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    def _to_entity(model: DarwinboxEmployeeModel) -> DarwinboxEmployee:
        """Map ORM model to domain entity."""
        return DarwinboxEmployee(
            id=model.id,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
            **{name: getattr(model, name) for name in _FIELDS},
        )
