"""Template — repository port.

Defines WHAT persistence the template anchor needs, not HOW. Lives in the
domain layer and imports no framework code.
"""

from abc import ABC, abstractmethod

from src.domain.entities.masters.template import Template


class ITemplateRepository(ABC):
    """Persistence contract for the Template aggregate."""

    @abstractmethod
    async def get_by_id(self, template_id: int) -> Template | None:
        """Load a template by id, or None."""
        ...

    @abstractmethod
    async def get_by_format_id(self, format_id: int) -> Template | None:
        """Load the template for a format, or None if it has none yet."""
        ...

    @abstractmethod
    async def create(self, template: Template) -> Template:
        """Create a new template for a format."""
        ...
