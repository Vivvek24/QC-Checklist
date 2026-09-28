"""Template Layout Column — repository port.

Defines WHAT persistence the flat column table needs, not HOW. Lives in the
domain layer and imports no framework code.
"""

from abc import ABC, abstractmethod

from src.domain.entities.masters.template import TemplateLayoutColumn


class ITemplateLayoutColumnRepository(ABC):
    """Persistence contract for TemplateLayoutColumn rows."""

    @abstractmethod
    async def list_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None
    ) -> list[TemplateLayoutColumn]:
        """Columns for a stage (section_id None) or a section, ordered by display_order."""
        ...

    @abstractmethod
    async def list_for_stage(self, format_stage_mapping_id: int) -> list[TemplateLayoutColumn]:
        """All columns (stage-level and every section) under one stage mapping."""
        ...

    @abstractmethod
    async def replace_for_scope(
        self,
        template_id: int,
        format_stage_mapping_id: int,
        section_id: int | None,
        columns: list[TemplateLayoutColumn],
    ) -> list[TemplateLayoutColumn]:
        """Replace all columns for a scope with the given set, in order."""
        ...

    @abstractmethod
    async def delete_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None
    ) -> None:
        """Remove all columns for a stage/section scope, if any."""
        ...
