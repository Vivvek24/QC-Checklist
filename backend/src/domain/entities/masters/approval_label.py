"""Approval Label Master — domain entity."""
from dataclasses import dataclass, field
from src.domain.entities.base_entity import BaseEntity

@dataclass
class ApprovalLabel(BaseEntity):
    label: str = field(default="")
    # A label belongs to either a stage or a question (one set, the other None).
    stage_id: int | None = field(default=None)
    question_id: int | None = field(default=None)
    role_ids: list[int] = field(default_factory=list)
    is_active: bool = field(default=True)
