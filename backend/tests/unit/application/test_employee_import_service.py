"""
Unit tests for `EmployeeImportService`.

The service owns three decisions and nothing else: which records Darwin's response
actually contains, which employee id each record carries, and how a Darwin payload
maps onto `user_details` columns. Persistence and per-record failure isolation belong
to `IEmployeeImportWriter`, so both ports here are fakes — no session, no bcrypt.

The mapping test matters more than it looks: the writer splats
`_extract_details_fields()` straight into `UserDetails(**fields)`, so a key that is
not a field on that entity is a `TypeError` at request time, not at import time.
"""

from dataclasses import fields as dataclass_fields
from typing import Any

import pytest
from employee_import_fakes import FakeEmployeeImportWriter, FakePasswordHasher

from src.application.ports.employee_import_writer import EmployeeImportOutcome
from src.application.services.employee_import_service import (
    EmployeeImportResult,
    EmployeeImportService,
)
from src.domain.entities.base_entity import BaseEntity
from src.domain.entities.user_details import UserDetails

ACTOR = "admin"


@pytest.fixture
def writer() -> FakeEmployeeImportWriter:
    return FakeEmployeeImportWriter()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def service(
    writer: FakeEmployeeImportWriter, hasher: FakePasswordHasher
) -> EmployeeImportService:
    return EmployeeImportService(writer=writer, password_hasher=hasher)


def _employee(**overrides: Any) -> dict[str, Any]:
    """A minimal Darwin employee record, overridable per test."""
    base: dict[str, Any] = {
        "employee_id": "E1001",
        "first_name": "Asha",
        "last_name": "Rao",
        "company_email_id": "asha.rao@emcure.com",
    }
    base.update(overrides)
    return base


class TestResponseShape:
    """Darwin's envelope has been observed in three shapes; all must be read."""

    async def test_employee_data_key_is_the_normal_case(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        await service.import_employees({"employeeData": [_employee()]}, actor=ACTOR)

        assert [c.employee_id for c in writer.calls] == ["E1001"]

    async def test_bare_list_response_is_accepted(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        await service.import_employees([_employee(employee_id="E2002")], actor=ACTOR)

        assert [c.employee_id for c in writer.calls] == ["E2002"]

    async def test_unknown_key_falls_back_to_first_list_valued_entry(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        response = {"status": "ok", "data": [_employee(employee_id="E3003")]}

        await service.import_employees(response, actor=ACTOR)

        assert [c.employee_id for c in writer.calls] == ["E3003"]

    async def test_empty_employee_data_still_falls_back(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        """`employeeData: []` is not an answer — keep looking for a populated list."""
        response = {"employeeData": [], "records": [_employee(employee_id="E4004")]}

        await service.import_employees(response, actor=ACTOR)

        assert [c.employee_id for c in writer.calls] == ["E4004"]

    async def test_no_list_anywhere_writes_nothing(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        result = await service.import_employees({"status": "ok"}, actor=ACTOR)

        assert writer.calls == []
        assert result == EmployeeImportResult(total=0, created=0, updated=0, failed=0)

    async def test_empty_list_response_writes_nothing(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        result = await service.import_employees([], actor=ACTOR)

        assert writer.calls == []
        assert result.total == 0


class TestEmployeeIdExtraction:
    """Darwin has spelled the id key three ways; all three are honoured."""

    @pytest.mark.parametrize("key", ["employee_id", "EmployeeId", "employeeId"])
    async def test_each_accepted_key_spelling(
        self,
        service: EmployeeImportService,
        writer: FakeEmployeeImportWriter,
        key: str,
    ) -> None:
        await service.import_employees({"employeeData": [{key: "E5005"}]}, actor=ACTOR)

        assert [c.employee_id for c in writer.calls] == ["E5005"]

    async def test_surrounding_whitespace_is_stripped(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        await service.import_employees(
            {"employeeData": [_employee(employee_id="  E6006  ")]}, actor=ACTOR
        )

        assert [c.employee_id for c in writer.calls] == ["E6006"]

    async def test_numeric_id_is_coerced_to_string(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        await service.import_employees(
            {"employeeData": [_employee(employee_id=7007)]}, actor=ACTOR
        )

        assert [c.employee_id for c in writer.calls] == ["7007"]

    async def test_missing_id_is_reported_as_failed_without_touching_the_writer(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        result = await service.import_employees(
            {"employeeData": [{"first_name": "Nameless"}]}, actor=ACTOR
        )

        assert writer.calls == []
        assert result.failed == 1
        assert result.results == [
            {
                "employee_id": "unknown",
                "status": "failed",
                "message": "No EmployeeId in Darwin response",
            }
        ]

    async def test_whitespace_only_id_is_treated_as_missing(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        result = await service.import_employees(
            {"employeeData": [_employee(employee_id="   ")]}, actor=ACTOR
        )

        assert writer.calls == []
        assert result.failed == 1


class TestTallies:
    """The response counts must match the per-record breakdown exactly."""

    async def test_created_updated_and_failed_are_counted_separately(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        writer.outcomes = {
            "E1": EmployeeImportOutcome(employee_id="E1", status="created"),
            "E2": EmployeeImportOutcome(employee_id="E2", status="updated"),
            "E3": EmployeeImportOutcome(
                employee_id="E3", status="failed", message="value too long"
            ),
        }
        response = {
            "employeeData": [
                _employee(employee_id="E1"),
                _employee(employee_id="E2"),
                _employee(employee_id="E3"),
            ]
        }

        result = await service.import_employees(response, actor=ACTOR)

        assert (result.total, result.created, result.updated, result.failed) == (3, 1, 1, 1)

    async def test_total_includes_records_rejected_before_the_writer(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        """An id-less record never reaches the writer but is still one of the total."""
        response = {"employeeData": [_employee(employee_id="E1"), {"first_name": "X"}]}

        result = await service.import_employees(response, actor=ACTOR)

        assert result.total == 2
        assert result.created == 1
        assert result.failed == 1
        assert len(writer.calls) == 1

    async def test_writer_message_is_carried_into_the_breakdown(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        writer.outcomes = {
            "E1": EmployeeImportOutcome(
                employee_id="E1", status="failed", message="username too long"
            )
        }

        result = await service.import_employees(
            {"employeeData": [_employee(employee_id="E1")]}, actor=ACTOR
        )

        assert result.results == [
            {"employee_id": "E1", "status": "failed", "message": "username too long"}
        ]

    async def test_one_failure_does_not_stop_later_records(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        writer.outcomes = {
            "E1": EmployeeImportOutcome(employee_id="E1", status="failed", message="boom")
        }
        response = {
            "employeeData": [_employee(employee_id="E1"), _employee(employee_id="E2")]
        }

        result = await service.import_employees(response, actor=ACTOR)

        assert [c.employee_id for c in writer.calls] == ["E1", "E2"]
        assert result.created == 1
        assert result.failed == 1


class TestWriterArguments:
    """What the service hands the writer, beyond the mapped fields."""

    async def test_new_user_password_is_the_hash_of_the_employee_id(
        self,
        service: EmployeeImportService,
        writer: FakeEmployeeImportWriter,
        hasher: FakePasswordHasher,
    ) -> None:
        await service.import_employees(
            {"employeeData": [_employee(employee_id="E1001")]}, actor=ACTOR
        )

        assert hasher.hashed == ["E1001"]
        assert writer.calls[0].new_user_password_hash == "hashed:E1001"

    async def test_actor_is_forwarded_verbatim(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        await service.import_employees(
            {"employeeData": [_employee()]}, actor="importer.bot"
        )

        assert writer.calls[0].actor == "importer.bot"


class TestDetailsMapping:
    """Darwin payload keys -> user_details columns."""

    async def _fields(
        self,
        service: EmployeeImportService,
        writer: FakeEmployeeImportWriter,
        emp_data: dict[str, Any],
    ) -> dict[str, Any]:
        await service.import_employees({"employeeData": [emp_data]}, actor=ACTOR)
        return writer.calls[0].details_fields

    async def test_darwin_keys_land_on_the_right_columns(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        emp_data = _employee(
            designation_title="Manager",
            department="Regulatory Affairs (India)",
            business_unit="Pharma",
            group_company="Emcure",
            office_location="Pune",
            office_state="Maharashtra",
            office_city="Pune",
            job_level="L4",
            office_mobile_no="9000000000",
            personal_mobile_no="9111111111",
            direct_manager_name="Ravi Kumar",
            direct_manager_employee_id="E0001",
            direct_manager_email="ravi.kumar@emcure.com",
            cost_center_id="CC-77",
            division="DIV-3",
        )
        emp_data["territory_code_(sales_hq_code)"] = "HQ-12"

        fields = await self._fields(service, writer, emp_data)

        assert fields["email"] == "asha.rao@emcure.com"
        assert fields["location"] == "Pune"
        assert fields["region"] == "Maharashtra"
        assert fields["zone"] == "Pune"
        assert fields["grade"] == "L4"
        assert fields["sap_user_id"] == "CC-77"
        assert fields["division_id"] == "DIV-3"
        assert fields["territory_id"] == "HQ-12"
        assert fields["reporting_manager"] == "Ravi Kumar"
        assert fields["direct_manager_employee_id"] == "E0001"

    async def test_employee_name_joins_present_name_parts_only(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        """A blank middle name must not leave a double space in the joined name."""
        fields = await self._fields(
            service,
            writer,
            _employee(first_name="Asha", middle_name="", last_name="Rao"),
        )

        assert fields["employee_name"] == "Asha Rao"

    async def test_employee_name_includes_middle_name_when_present(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        fields = await self._fields(
            service,
            writer,
            _employee(first_name="Asha", middle_name="B", last_name="Rao"),
        )

        assert fields["employee_name"] == "Asha B Rao"

    async def test_null_value_becomes_empty_string_not_the_string_none(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        fields = await self._fields(service, writer, _employee(department=None))

        assert fields["department"] == ""

    async def test_missing_key_becomes_empty_string(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        fields = await self._fields(service, writer, {"employee_id": "E1001"})

        assert fields["department"] == ""
        assert fields["employee_name"] == ""

    async def test_values_are_whitespace_stripped(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        fields = await self._fields(
            service, writer, _employee(department="  Regulatory Affairs  ")
        )

        assert fields["department"] == "Regulatory Affairs"

    async def test_date_of_joining_falls_back_to_date_of_birth(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        """
        Pre-existing behaviour, preserved deliberately: Darwin omits
        `date_of_joining` for some records and the column is non-nullable.
        """
        fields = await self._fields(
            service, writer, _employee(date_of_birth="1990-04-01")
        )

        assert fields["date_of_joining"] == "1990-04-01"

    async def test_date_of_joining_wins_when_both_are_present(
        self, service: EmployeeImportService, writer: FakeEmployeeImportWriter
    ) -> None:
        fields = await self._fields(
            service,
            writer,
            _employee(date_of_joining="2020-01-15", date_of_birth="1990-04-01"),
        )

        assert fields["date_of_joining"] == "2020-01-15"


class TestMappedKeysMatchTheEntity:
    """
    Guard on the writer's `UserDetails(**details_fields)` splat.

    A key the entity does not declare raises `TypeError` inside the request; a key
    the writer supplies itself would be a duplicate-keyword `TypeError`. Both are
    caught here instead of in production.
    """

    WRITER_OWNED = {"id", "user_id", "created_by", "modified_by"}

    def test_every_mapped_key_is_a_user_details_field(self) -> None:
        entity_fields = {f.name for f in dataclass_fields(UserDetails)}

        mapped = set(EmployeeImportService._extract_details_fields({}))

        assert mapped <= entity_fields, (
            "mapped keys are splatted into UserDetails(**fields); these are not "
            f"fields on it: {sorted(mapped - entity_fields)}"
        )

    def test_mapper_does_not_supply_writer_owned_keys(self) -> None:
        mapped = set(EmployeeImportService._extract_details_fields({}))

        assert not mapped & self.WRITER_OWNED, (
            "the writer decides identity and audit columns; the mapper must not "
            f"also send: {sorted(mapped & self.WRITER_OWNED)}"
        )

    def test_mapper_covers_every_non_audit_column(self) -> None:
        """A column added to UserDetails without a Darwin mapping stays empty forever."""
        audit_fields = {f.name for f in dataclass_fields(BaseEntity)}
        expected = {f.name for f in dataclass_fields(UserDetails)} - audit_fields - {"user_id"}

        mapped = set(EmployeeImportService._extract_details_fields({}))

        assert expected <= mapped, (
            "these user_details columns have no Darwin mapping and would never be "
            f"populated by an import: {sorted(expected - mapped)}"
        )
