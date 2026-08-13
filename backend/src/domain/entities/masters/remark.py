"""Remark Master — domain entity."""
from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class Remark(BaseEntity):
    remark: str = field(default="")
    role_ids: list[int] = field(default_factory=list)
    is_active: bool = field(default=True)
