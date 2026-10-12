"""PDF Export — API controller (thin).

GET /qc-checklist/{request_number}/pdf returns the checklist request rendered
as a downloadable PDF. The service assembles + renders the document and returns
a PdfExportResult DTO; the schema turns that into the binary Response. No
business logic or response-building here. Works for any format.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.pdf_export_schema import PdfExportResponseSchema
from src.application.services.qc_checklist.checklist_pdf_service import (
    ChecklistPdfService,
    RequestNotFoundError,
)
from src.domain.entities.user import User
from src.infrastructure.database.repositories.qc_checklist.pdf_export_repository_impl import (
    PdfExportRepository,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - PDF Export"])


@router.get(
    "/{request_number}/pdf",
    summary="Download a checklist request as a PDF",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
    dependencies=[Depends(require_api_permission("checklist_requests", "EXPORT"))],
)
async def download_request_pdf(
    request_number: str = Path(..., description="The checklist request number"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """Render the request to a PDF and return it as a file download."""
    service = ChecklistPdfService(PdfExportRepository(session))
    try:
        result = await service.export_pdf(request_number, actor=current_user.username)
    except RequestNotFoundError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Request not found: {request_number}",
        ) from e

    return PdfExportResponseSchema.to_response(result)
