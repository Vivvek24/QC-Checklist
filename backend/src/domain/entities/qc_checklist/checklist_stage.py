"""ChecklistStage — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.checklist_stage_status_enum import ChecklistStageStatus


@dataclass
class ChecklistStage(BaseEntity):
    """A stage within a QC Checklist request."""

    checklist_request_id: int = field(default=0)
    user_id: int | None = field(default=None)
    format_stage_mapping_id: int | None = field(default=None)
    status: str = field(default=ChecklistStageStatus.PENDING)
    performed_remark: str = field(default="")
    approved_remark: str = field(default="")
    is_self_verified: bool = field(default=False)
    self_verification_details: str = field(default="")
    is_approvable: bool = field(default=False)
    is_last_stage: bool = field(default=False)
    submit_remarks: str = field(default="")
    self_approved_remark: str = field(default="")
