"""Approval Label Master — domain entity."""
from dataclasses import dataclass, field
from src.domain.entities.base_entity import BaseEntity

@dataclass
class ApprovalLabel(BaseEntity):
    label: str = field(default="")
    stage_id: int = field(default=0)
    role_ids: list[int] = field(default_factory=list)
    is_active: bool = field(default=True)
