"""
Business Unit Master — domain entity.
"""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class BusinessUnit(BaseEntity):
    """
    Business Unit aggregate root.

    Attributes:
        name:      Display name of the business unit (unique).
        is_active: Whether the business unit is currently active.
    """

    name: str = field(default="")
    is_active: bool = field(default=True)

    def activate(self, modified_by: str) -> None:
        """Activate this business unit."""
        self.is_active = True
        self.mark_modified(modified_by)

    def deactivate(self, modified_by: str) -> None:
        """Deactivate this business unit."""
        self.is_active = False
        self.mark_modified(modified_by)
