"""Format Master — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.format_enums import FormatType


@dataclass
class Format(BaseEntity):
    """
    Format aggregate root.

    Attributes:
        format_no:    Unique format number (string identifier).
        format_title: Display title of the format.
        format_name:  Full name of the format.
        unit_id:      FK to Unit master.
        format_type:  Enum — Chromatographic | AQL | RECEIPT_CHECKLIST_STANDARD | ReconcilationSheet.
        has_declaration_question: Whether this format includes a declaration question.
        is_active:    Active/Inactive flag.
    """

    format_no: str = field(default="")
    format_title: str = field(default="")
    format_name: str = field(default="")
    unit_id: int = field(default=0)
    format_type: FormatType = field(default=FormatType.AQL)
    has_declaration_question: bool = field(default=False)
    is_active: bool = field(default=True)

    def activate(self, modified_by: str) -> None:
        self.is_active = True
        self.mark_modified(modified_by)

    def deactivate(self, modified_by: str) -> None:
        self.is_active = False
        self.mark_modified(modified_by)
