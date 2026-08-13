"""Section Master — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class Section(BaseEntity):
    """Section aggregate root."""

    section_name: str = field(default="")
    format_stage_mapping_id: int | None = field(default=None)
    is_active: bool = field(default=True)
