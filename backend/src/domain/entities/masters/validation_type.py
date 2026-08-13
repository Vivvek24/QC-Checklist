"""Validation Type Master — domain entity."""
from dataclasses import dataclass, field
from src.domain.entities.base_entity import BaseEntity

@dataclass
class ValidationType(BaseEntity):
    name: str = field(default="")
    is_active: bool = field(default=True)
