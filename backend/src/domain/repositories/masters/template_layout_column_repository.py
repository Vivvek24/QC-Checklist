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
        self, format_stage_mapping_id: int, section_id: int | None,
        is_declaration: bool = False,
    ) -> list[TemplateLayoutColumn]:
        """Columns for a scope (stage/section × normal/declaration), ordered by display_order."""
        ...

    @abstractmethod
    async def list_for_stage(self, format_stage_mapping_id: int) -> list[TemplateLayoutColumn]:
        """All columns (stage-level and every section, both normal and
        declaration) under one stage mapping."""
        ...

    @abstractmethod
    async def replace_for_scope(
        self,
        template_id: int,
        format_stage_mapping_id: int,
        section_id: int | None,
        columns: list[TemplateLayoutColumn],
        is_declaration: bool = False,
    ) -> list[TemplateLayoutColumn]:
        """Replace all columns for a scope with the given set, in order."""
        ...

    @abstractmethod
    async def delete_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None,
        is_declaration: bool = False,
    ) -> None:
        """Remove all columns for a stage/section/declaration scope, if any."""
        ...
