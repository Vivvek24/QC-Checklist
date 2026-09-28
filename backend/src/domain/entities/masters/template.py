"""Template — domain entities.

A Template is the anchor for a format's checklist design: one row per format
(for now), identifying "the template" that format's layout columns belong to.

TemplateLayoutColumn is a single column of a checklist table for a given
scope (a stage, or a section within a stage). Its scope
(format_stage_mapping_id, section_id) is carried directly on the column row —
not on an intermediate parent — so a column alone is fully self-describing
about which template/stage/section it belongs to. This is a self-contained
design artifact: it references existing masters (formats, format_stage_mappings,
sections) by id but does not own or modify them.
"""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.template_enums import ColumnType


@dataclass
class Template(BaseEntity):
    """The template anchor for a format's checklist design."""

    format_id: int = field(default=0)
    is_active: bool = field(default=True)


@dataclass
class TemplateLayoutColumn(BaseEntity):
    """A single column of a checklist table, scoped to a stage/section."""

    template_id: int = field(default=0)
    format_stage_mapping_id: int = field(default=0)
    # None => stage-level column; a value => section-level column.
    section_id: int | None = field(default=None)
    header: str = field(default="")
    column_type: ColumnType = field(default=ColumnType.ANSWER)
    display_order: int = field(default=0)
    width: str | None = field(default=None)
    is_required: bool = field(default=False)
