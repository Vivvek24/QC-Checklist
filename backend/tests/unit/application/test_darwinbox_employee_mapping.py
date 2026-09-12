"""
Unit tests for the Darwinbox employee field-mapping chain.

Covers the three pure mapping functions that carry a Darwinbox payload key all
the way to a wire response, with no repository or database involved:

    Darwinbox JSON  --_map_payload_to_entity-->  DarwinboxEmployee
    DarwinboxEmployee --_to_response-->          DarwinboxEmployeeResponse  (internal)
    DarwinboxEmployee --from_entity-->           DarwinEmployeeRecord       (published)

Focus is ``departments_hierarchy``, the field Darwinbox added to its employee
payload, plus a regression guard on the published Mendix-compatible contract.
"""

from typing import Any
from uuid import uuid4

from src.api.v1.schemas.darwin_ad_schema import DarwinEmployeeRecord
from src.application.services.darwinbox_service import DarwinboxService
from src.domain.entities.darwinbox_employee import DarwinboxEmployee


def _payload(**overrides: Any) -> dict[str, Any]:
    """A minimal Darwinbox employee payload, overridable per test."""
    base: dict[str, Any] = {
        "employee_id": "E1001",
        "employeeid": "4242",
        "first_name": "Asha",
        "last_name": "Rao",
        "company_email_id": "asha.rao@emcure.com",
        "employee_status": "Active",
        "department": "Regulatory Affairs (India)",
        "departments_hierarchy": "Regulatory Affairs",
    }
    base.update(overrides)
    return base


def _entity(**overrides: Any) -> DarwinboxEmployee:
    """A stored employee entity, overridable per test."""
    defaults: dict[str, Any] = {
        "id": uuid4(),
        "created_by": "system",
        "modified_by": "system",
        "employee_id": "E1001",
        "departments_hierarchy": "Regulatory Affairs",
    }
    defaults.update(overrides)
    return DarwinboxEmployee(**defaults)


class TestMapPayloadToEntity:
    """Darwinbox payload -> domain entity."""

    def test_departments_hierarchy_is_read_from_the_payload(self) -> None:
        entity = DarwinboxService._map_payload_to_entity(_payload(), "sync-bot")

        assert entity.departments_hierarchy == "Regulatory Affairs"

    def test_departments_hierarchy_is_whitespace_stripped(self) -> None:
        entity = DarwinboxService._map_payload_to_entity(
            _payload(departments_hierarchy="  Regulatory Affairs  "), "sync-bot"
        )

        assert entity.departments_hierarchy == "Regulatory Affairs"

    def test_missing_departments_hierarchy_maps_to_empty_string(self) -> None:
        payload = _payload()
        del payload["departments_hierarchy"]

        entity = DarwinboxService._map_payload_to_entity(payload, "sync-bot")

        # NOT NULL column with server_default="" — never None.
        assert entity.departments_hierarchy == ""

    def test_null_departments_hierarchy_maps_to_empty_string(self) -> None:
        entity = DarwinboxService._map_payload_to_entity(
            _payload(departments_hierarchy=None), "sync-bot"
        )

        assert entity.departments_hierarchy == ""

    def test_departments_hierarchy_is_kept_verbatim_not_bracket_split(self) -> None:
        """Unlike department/role/territory_name, the hierarchy path is not split."""
        entity = DarwinboxService._map_payload_to_entity(
            _payload(departments_hierarchy="Quality (QA) / Regulatory Affairs"),
            "sync-bot",
        )

        assert entity.departments_hierarchy == "Quality (QA) / Regulatory Affairs"
        # The sibling department field still splits on "(" as before.
        assert entity.split_department == "Regulatory Affairs"


class TestToResponse:
    """Domain entity -> internal stored-employee response."""

    def test_departments_hierarchy_is_exposed(self) -> None:
        response = DarwinboxService._to_response(_entity())

        assert response.departments_hierarchy == "Regulatory Affairs"


class TestPublishedDarwinAdRecord:
    """Domain entity -> published Darwin AD wire format."""

    def test_departments_hierarchy_is_exposed(self) -> None:
        record = DarwinEmployeeRecord.from_entity(_entity())

        assert record.departments_hierarchy == "Regulatory Affairs"

    def test_departments_hierarchy_is_serialised_under_its_own_key(self) -> None:
        record = DarwinEmployeeRecord.from_entity(_entity())

        dumped = record.model_dump(by_alias=True)

        assert dumped["departments_hierarchy"] == "Regulatory Affairs"

    def test_existing_mendix_contract_is_unchanged(self) -> None:
        """Regression guard: the parenthesised territory alias must survive."""
        record = DarwinEmployeeRecord.from_entity(
            _entity(territory_code="HQ-01", department="Regulatory Affairs (India)")
        )

        dumped = record.model_dump(by_alias=True)

        assert dumped["territory_code_(sales_hq_code)"] == "HQ-01"
        assert "territory_code" not in dumped
        assert dumped["department"] == "Regulatory Affairs (India)"


class TestFieldRegistryCoversTheNewColumn:
    """The repository maps model<->entity off a single field registry."""

    def test_departments_hierarchy_is_registered(self) -> None:
        # Imported here to keep the infrastructure import out of the module scope
        # of these otherwise pure application/domain tests.
        from src.infrastructure.database.repositories.darwinbox_employee_repository_impl import (  # noqa: E501
            _FIELDS,
        )

        # Membership drives create/update/bulk_upsert/_to_entity in one place.
        assert "departments_hierarchy" in _FIELDS
        # Must not be the conflict key, which bulk_upsert excludes from updates.
        assert _FIELDS[0] == "employee_id"
