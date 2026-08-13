"""Unit Master — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateUnitDTO:
    name: str
    business_unit_id: int
    is_active: bool = True


@dataclass(frozen=True)
class UpdateUnitDTO:
    name: str | None = None
    business_unit_id: int | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class UnitDTO:
    id: int
    name: str
    business_unit_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class UnitListDTO:
    items: list[UnitDTO]
    total: int
    skip: int
    limit: int
