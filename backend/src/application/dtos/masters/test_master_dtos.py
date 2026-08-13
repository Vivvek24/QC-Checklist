"""TestMaster — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateTestMasterDTO:
    test_name: str
    no_of_samples_issued: int
    sample_qty: int
    product_id: int
    is_active: bool = True


@dataclass(frozen=True)
class UpdateTestMasterDTO:
    test_name: str | None = None
    no_of_samples_issued: int | None = None
    sample_qty: int | None = None
    product_id: int | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class TestMasterDTO:
    id: int
    test_name: str
    no_of_samples_issued: int
    sample_qty: int
    product_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class TestMasterListDTO:
    items: list[TestMasterDTO]
    total: int
    skip: int
    limit: int
