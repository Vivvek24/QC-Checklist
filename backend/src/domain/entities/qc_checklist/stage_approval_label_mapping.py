"""StageApprovalLabelMapping — domain entity."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.base_entity import BaseEntity


@dataclass
class StageApprovalLabelMapping(BaseEntity):
    """Maps an approval label action to a checklist stage."""

    checklist_stage_id: int = field(default=0)
    approval_label_id: int = field(default=0)
    remark_id: int | None = field(default=None)
    user_id: int | None = field(default=None)
    role_id: int | None = field(default=None)
    date_of_action: datetime | None = field(default=None)
    remark: str = field(default="")
    is_show: bool = field(default=False)
    is_refer_back: bool = field(default=False)
