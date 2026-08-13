"""SAP Field Master — domain entity."""
from dataclasses import dataclass, field
from src.domain.entities.base_entity import BaseEntity

@dataclass
class SapField(BaseEntity):
    field_name: str = field(default="")
    is_active: bool = field(default=True)
