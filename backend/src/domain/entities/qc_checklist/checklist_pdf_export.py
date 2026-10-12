"""ChecklistPdfExport — domain entity.

An audit record that a request's PDF was exported. The "who" and "when" come
from BaseEntity's audit fields (created_by / created_date); this entity only
adds which request was exported.
"""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class ChecklistPdfExport(BaseEntity):
    """A single PDF-export event for a checklist request."""

    request_number: str = field(default="")
