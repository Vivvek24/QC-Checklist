"""FormatStageMapping — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class FormatStageMapping(BaseEntity):
    """Maps a Format to a Stage with configuration flags."""

    format_id: int = field(default=0)
    stage_id: int = field(default=0)
    is_active: bool = field(default=True)
    is_approvable: bool = field(default=False)
    is_refer_back: bool = field(default=False)
    has_section: bool = field(default=False)
