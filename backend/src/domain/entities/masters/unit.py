"""Unit Master — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class Unit(BaseEntity):
    """
    Unit aggregate root.

    Attributes:
        name:            Display name of the unit (unique within a business unit).
        business_unit_id: FK to the parent BusinessUnit.
        is_active:       Whether the unit is currently active.
    """

    name: str = field(default="")
    business_unit_id: int = field(default=0)
    is_active: bool = field(default=True)

    def activate(self, modified_by: str) -> None:
        self.is_active = True
        self.mark_modified(modified_by)

    def deactivate(self, modified_by: str) -> None:
        self.is_active = False
        self.mark_modified(modified_by)
