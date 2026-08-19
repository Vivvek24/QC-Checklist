"""ChecklistStageSection — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class ChecklistStageSection(BaseEntity):
    """A section within a checklist stage."""

    checklist_stage_id: int = field(default=0)
    section_id: int = field(default=0)
