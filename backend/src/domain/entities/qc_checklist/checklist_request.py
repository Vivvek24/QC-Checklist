"""ChecklistRequest — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class ChecklistRequest(BaseEntity):
    """A QC Checklist request tracking inspection stages."""

    status: str = field(default="Draft")
    request_number: str = field(default="")
    status_format: str = field(default="")
    is_last_stage: bool = field(default=False)
    is_removed: bool = field(default=False)
    sequence_number: int = field(default=0)
    approver_user_id: int | None = field(default=None)
    format_id: int | None = field(default=None)
