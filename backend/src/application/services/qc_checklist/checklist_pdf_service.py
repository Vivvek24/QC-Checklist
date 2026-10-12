"""Checklist PDF Service — renders a request's PdfDocument to a PDF file.

Thin orchestration: ask the repository for the assembled PdfDocument entity,
render it to bytes, and wrap the result for delivery. All the SQL + document
assembly lives in the repository; all the drawing lives in the renderer.
"""

from dataclasses import dataclass

from src.domain.repositories.qc_checklist.pdf_export_repository import IPdfExportRepository

from .checklist_pdf_renderer import ChecklistPdfRenderer


class RequestNotFoundError(Exception):
    """Raised when the request number does not resolve to a request."""


@dataclass
class PdfExportResult:
    """The rendered PDF plus how to deliver it (the controller just streams
    these bytes with the given filename/content type)."""

    content: bytes
    filename: str
    media_type: str = "application/pdf"


class ChecklistPdfService:
    """Builds and renders the PDF for a checklist request."""

    def __init__(self, repo: IPdfExportRepository) -> None:
        self._repo = repo

    async def export_pdf(self, request_number: str, actor: str) -> PdfExportResult:
        """Render the request's document to bytes, record the export (who/when),
        and name the file.

        Raises RequestNotFoundError if the request number does not resolve.
        """
        document = await self._repo.get_document(request_number)
        if document is None:
            raise RequestNotFoundError(request_number)

        content = ChecklistPdfRenderer().render(document)
        await self._repo.record_export(request_number, actor)
        return PdfExportResult(content=content, filename=f"{request_number}.pdf")
