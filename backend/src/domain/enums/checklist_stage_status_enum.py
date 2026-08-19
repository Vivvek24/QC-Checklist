"""ChecklistStage status enum."""

from enum import StrEnum


class ChecklistStageStatus(StrEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DRAFT = "Draft"
    REFER_BACK = "ReferBack"
    INITIAL = "Initial"
    REMOVED = "Removed"
    SAVED = "Saved"
