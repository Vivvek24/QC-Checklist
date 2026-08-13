"""Stage Master — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class Stage(BaseEntity):
    """Stage aggregate root."""

    stage_name: str = field(default="")
    is_active: bool = field(default=True)

    def activate(self, modified_by: str) -> None:
        self.is_active = True
        self.mark_modified(modified_by)

    def deactivate(self, modified_by: str) -> None:
        self.is_active = False
        self.mark_modified(modified_by)
