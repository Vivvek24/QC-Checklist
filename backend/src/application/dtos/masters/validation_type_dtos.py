from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CreateValidationTypeDTO:
    name: str; is_active: bool = True
@dataclass(frozen=True)
class UpdateValidationTypeDTO:
    name: str | None = None; is_active: bool | None = None
@dataclass(frozen=True)
class ValidationTypeDTO:
    id: int; name: str; is_active: bool; created_by: str; created_date: datetime; modified_by: str; modified_date: datetime
@dataclass(frozen=True)
class ValidationTypeListDTO:
    items: list[ValidationTypeDTO]; total: int; skip: int; limit: int
