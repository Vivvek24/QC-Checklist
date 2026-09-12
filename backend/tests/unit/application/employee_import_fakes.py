"""
Hand-written fakes for the employee (Darwin AD) import service.

`EmployeeImportService` takes two ports — `IEmployeeImportWriter` and
`IPasswordHasher` — so its unit test needs neither a database nor bcrypt. These
follow the established convention: small classes implementing the same interface,
a `dict`/`list` for storage, no mock library.
"""

from typing import Any

from src.application.ports.employee_import_writer import (
    EmployeeImportOutcome,
    IEmployeeImportWriter,
)
from src.domain.services.password_hasher import IPasswordHasher

__all__ = ["FakeEmployeeImportWriter", "FakePasswordHasher", "WriterCall"]


class WriterCall:
    """One recorded `upsert_employee` invocation, for assertions."""

    def __init__(
        self,
        employee_id: str,
        details_fields: dict[str, Any],
        new_user_password_hash: str,
        actor: str,
    ) -> None:
        self.employee_id = employee_id
        self.details_fields = details_fields
        self.new_user_password_hash = new_user_password_hash
        self.actor = actor


class FakeEmployeeImportWriter(IEmployeeImportWriter):
    """
    Records every call and returns a scripted outcome.

    By default every employee id reports `"created"`. A test that cares about the
    updated/failed tallies scripts them via `outcomes` (keyed by employee id) or
    changes `default_status`.
    """

    def __init__(self) -> None:
        self.calls: list[WriterCall] = []
        self.outcomes: dict[str, EmployeeImportOutcome] = {}
        self.default_status: str = "created"

    async def upsert_employee(
        self,
        *,
        employee_id: str,
        details_fields: dict[str, Any],
        new_user_password_hash: str,
        actor: str,
    ) -> EmployeeImportOutcome:
        self.calls.append(
            WriterCall(
                employee_id=employee_id,
                details_fields=dict(details_fields),
                new_user_password_hash=new_user_password_hash,
                actor=actor,
            )
        )
        scripted = self.outcomes.get(employee_id)
        if scripted is not None:
            return scripted
        return EmployeeImportOutcome(
            employee_id=employee_id,
            status=self.default_status,  # type: ignore[arg-type]
        )


class FakePasswordHasher(IPasswordHasher):
    """Deterministic, reversible stand-in for bcrypt — fast and assertable."""

    PREFIX = "hashed:"

    def __init__(self) -> None:
        self.hashed: list[str] = []

    def hash(self, plain_password: str) -> str:
        self.hashed.append(plain_password)
        return f"{self.PREFIX}{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"{self.PREFIX}{plain_password}"
