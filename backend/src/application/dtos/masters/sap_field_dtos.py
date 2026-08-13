from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CreateSapFieldDTO:
    field_name: str; is_active: bool = True
@dataclass(frozen=True)
class UpdateSapFieldDTO:
    field_name: str | None = None; is_active: bool | None = None
@dataclass(frozen=True)
class SapFieldDTO:
    id: int; field_name: str; is_active: bool; created_by: str; created_date: datetime; modified_by: str; modified_date: datetime
@dataclass(frozen=True)
class SapFieldListDTO:
    items: list[SapFieldDTO]; total: int; skip: int; limit: int
