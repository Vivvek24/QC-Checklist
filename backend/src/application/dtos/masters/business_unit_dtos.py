"""
Business Unit Master — application DTOs.
Service-layer contracts; no HTTP concerns.
"""

from dataclasses import dataclass, field
from datetime import datetime


# ─── Command DTOs (inputs) ───

@dataclass(frozen=True)
class CreateBusinessUnitDTO:
    """Command: create a new business unit."""
    name: str
    is_active: bool = True


@dataclass(frozen=True)
class UpdateBusinessUnitDTO:
    """Command: update a business unit. Only supplied fields are changed."""
    name: str | None = None
    is_active: bool | None = None


# ─── Result DTOs (outputs) ───

@dataclass(frozen=True)
class BusinessUnitDTO:
    """Read projection of a single business unit."""
    id: int
    name: str
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class BusinessUnitListDTO:
    """Paginated list of business units."""
    items: list[BusinessUnitDTO]
    total: int
    skip: int
    limit: int
