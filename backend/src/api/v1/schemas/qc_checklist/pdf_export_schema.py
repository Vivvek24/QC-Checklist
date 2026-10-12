"""PDF Export — API schema.

The PDF endpoint returns binary, not JSON, so the "schema" here owns the
translation from the service's PdfExportResult DTO into a FastAPI Response
(bytes + content type + download disposition). This keeps the controller a pure
HTTP layer with no response-building logic of its own, matching the other
qc_checklist controllers.
"""

from fastapi.responses import Response

from src.application.services.qc_checklist.checklist_pdf_service import PdfExportResult


class PdfExportResponseSchema:
    """Wraps a PdfExportResult and renders it as a downloadable PDF Response."""

    @staticmethod
    def to_response(result: PdfExportResult) -> Response:
        return Response(
            content=result.content,
            media_type=result.media_type,
            headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
        )
