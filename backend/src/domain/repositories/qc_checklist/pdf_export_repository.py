"""PDF export — repository port.

Read-only contract that returns the assembled PdfDocument entity for a request
(or None if the request does not exist). The infrastructure layer runs the
queries and maps the results into the domain entity; the application service
just renders it.

This is a dedicated port (not IRepository) because PDF export is a pure read
projection across many tables, not CRUD over a single aggregate.
"""

from abc import ABC, abstractmethod

from src.domain.entities.qc_checklist.checklist_pdf_document import PdfDocument


class IPdfExportRepository(ABC):
    """Persistence contract backing the checklist PDF export."""

    @abstractmethod
    async def get_document(self, request_number: str) -> PdfDocument | None:
        """Build the full PdfDocument for a request, or None if not found."""
        ...

    @abstractmethod
    async def record_export(self, request_number: str, actor: str) -> None:
        """Record that `actor` exported the PDF for `request_number` (audit)."""
        ...
