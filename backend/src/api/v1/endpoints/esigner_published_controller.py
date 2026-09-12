"""
Published E-Signer service endpoints.

Migration target for the legacy "Catalyst" e-signing integration. These
endpoints reproduce the original paths and XML response contracts so that
consuming applications only need to change the base URL (host), not their code.

Endpoints (matching the legacy contract):
  - POST /rest/embededsign/v1/Login_and_Send_Document
        Authenticate against E-Signer and initiate an embedded signing session
        in a single call, returning the ``<Response_To_Catalyst>`` XML envelope.
  - GET  /rest/embededsign/v1/Get_Status?WorkFlowId=<id>
        Return the workflow/document status as the raw E-Signer GetWorkflowInfo
        JSON envelope.
  - POST /rest/embededsign/v1/Download_Document
        Download a workflow's documents (base64) as the raw E-Signer
        DownloadWorkflowDocuments JSON envelope.
  - GET  /rest/embededsign/v1/GetAttachments?workflowId=<id>
        Return a workflow's attachments (base64) as a bare JSON array.
  - GET  /rest/embededsign/v1/GetDocumentLogs?workflowId=<id>
        Return a workflow's document audit log as a bare (flattened) JSON array.
  - GET  /rest/embededsign/v1/GetSignatureURL?WorkflowID=<id>
        Return the ad-hoc signing URL as the raw E-Signer GetSigningURL JSON
        envelope.

Auth: optional shared secret via the ``X-API-Key`` header, enforced only when
``settings.ESIGNER_PUBLISHED_API_KEY`` is configured.
"""

import logging
import secrets
from typing import Any
from xml.sax.saxutils import escape

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)
from pydantic import BaseModel, Field

from src.api.v1.schemas.esigner_schema import (
    ESignerDownloadDocumentsResponse,
    ESignerSigningUrlResponse,
    ESignerWorkflowInfoResponse,
)
from src.application.services.esigner_service import ESignerService
from src.config.settings import settings
from src.infrastructure.external.esigner.esigner_client import (
    ESignerClient,
    ESignerError,
)

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Enforce the shared-secret API key when one is configured.

    No-op (open access) when ``ESIGNER_PUBLISHED_API_KEY`` is empty, preserving
    drop-in compatibility for callers migrated from the legacy service. Uses a
    constant-time comparison to avoid timing leaks.
    """
    expected = settings.ESIGNER_PUBLISHED_API_KEY
    if not expected:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


router = APIRouter(
    prefix="/rest/embededsign/v1",
    tags=["E-Signer (Published)"],
    dependencies=[Depends(verify_api_key)],
)


class DownloadDocumentRequest(BaseModel):
    """Request body for ``/Download_Document`` (matches the Catalyst contract)."""

    WorkFlowId: int = Field(
        ..., ge=1, description="The E-Signer WorkFlowId whose documents to download"
    )


class PublishedAttachment(BaseModel):
    """
    A single attachment in the published ``/GetAttachments`` response.

    The legacy contract returns a bare array of these objects (no envelope),
    exposing only the fields below.
    """

    AttachmentName: str | None = None
    Base64FileData: str | None = None
    UploadedBy: int = 0
    UploaderName: str | None = None


class PublishedDocumentLog(BaseModel):
    """
    A single audit-log entry in the published ``/GetDocumentLogs`` response.

    The legacy contract returns a bare, flat array of these entries (log entries
    across all documents are flattened, not grouped by document).
    """

    DateTime: str | None = None
    UserEmail: str | None = None
    Action: str | None = None
    IPAddress: str | None = None


def _get_esigner_service() -> ESignerService:
    """FastAPI dependency — creates ESignerService with injected dependencies."""
    return ESignerService(client=ESignerClient())


def _build_catalyst_response(
    is_success: bool, status_value: bool, workflow_id: int | None
) -> str:
    """
    Build the legacy ``<Response_To_Catalyst>`` XML envelope.

    Booleans are rendered lowercase (``true``/``false``) and the WorkflowId is
    rendered as an empty element when unavailable, matching the legacy contract.
    """
    workflow_text = "" if workflow_id is None else escape(str(workflow_id))
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<Response_To_Catalyst>\n"
        f"  <IsSuccess>{str(is_success).lower()}</IsSuccess>\n"
        f"  <Status>{str(status_value).lower()}</Status>\n"
        f"  <WorkflowId>{workflow_text}</WorkflowId>\n"
        "</Response_To_Catalyst>"
    )


@router.post(
    "/Login_and_Send_Document",
    summary="Login and initiate an embedded signing session (Catalyst contract)",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "The <Response_To_Catalyst> XML envelope.",
        }
    },
)
async def login_and_send_document(
    payload: dict[str, Any] = Body(
        ..., description="The InitiateEmbeddedSigning request body (forwarded as-is)"
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> Response:
    """
    Authenticate against E-Signer (ValidateLogin) and initiate an embedded
    signing session (InitiateEmbeddedSigning) in a single call.

    Returns the legacy ``<Response_To_Catalyst>`` XML envelope. Transport or
    login failures are reported as ``IsSuccess=false`` within the XML envelope
    rather than as HTTP errors, so the consuming application always receives a
    parseable response.
    """
    try:
        result = await service.initiate_embedded_signing(payload)
        data = result.Response
        xml = _build_catalyst_response(
            is_success=result.IsSuccess,
            status_value=bool(data.Status) if data else False,
            workflow_id=data.WorkflowId if data else None,
        )
    except ESignerError as exc:
        logger.error("Published Login_and_Send_Document failed: %s", exc.detail)
        xml = _build_catalyst_response(
            is_success=False, status_value=False, workflow_id=None
        )

    return Response(content=xml, media_type="application/xml")


@router.get(
    "/Get_Status",
    response_model=ESignerWorkflowInfoResponse,
    summary="Get workflow/document status by WorkFlowId (Catalyst contract)",
)
async def get_status(
    workflow_id: int = Query(
        ...,
        alias="WorkFlowId",
        ge=1,
        description="The E-Signer WorkFlowId to look up",
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerWorkflowInfoResponse:
    """
    Return the status/details of a workflow and its documents as the raw
    E-Signer ``GetWorkflowInfo`` JSON envelope.

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``GetWorkflowInfo``. A "no documents found" result is returned by
    E-Signer as ``IsSuccess=false`` (HTTP 200) and passed through unchanged.
    Login/transport failures are also reported as ``IsSuccess=false`` within the
    JSON envelope rather than as HTTP errors.
    """
    try:
        return await service.get_workflow_info(workflow_id)
    except ESignerError as exc:
        logger.error("Published Get_Status failed: %s", exc.detail)
        return ESignerWorkflowInfoResponse(
            IsSuccess=False,
            Messages=[exc.detail],
            Response=[],
        )


@router.post(
    "/Download_Document",
    response_model=ESignerDownloadDocumentsResponse,
    summary="Download a workflow's documents by WorkFlowId (Catalyst contract)",
)
async def download_document(
    request: DownloadDocumentRequest = Body(...),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerDownloadDocumentsResponse:
    """
    Download a workflow's documents as base64-encoded files, returned as the raw
    E-Signer ``DownloadWorkflowDocuments`` JSON envelope.

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``DownloadWorkflowDocuments``. Login/transport failures are
    reported as ``IsSuccess=false`` within the JSON envelope rather than as HTTP
    errors.
    """
    try:
        return await service.download_workflow_documents(request.WorkFlowId)
    except ESignerError as exc:
        logger.error("Published Download_Document failed: %s", exc.detail)
        return ESignerDownloadDocumentsResponse(
            IsSuccess=False,
            Messages=[exc.detail],
            Response=None,
        )


@router.get(
    "/GetAttachments",
    response_model=list[PublishedAttachment],
    summary="Get a workflow's attachments by workflowId (Catalyst contract)",
)
async def get_attachments(
    workflow_id: int = Query(
        ...,
        alias="workflowId",
        ge=1,
        description="The E-Signer workflowId whose attachments to download",
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> list[PublishedAttachment]:
    """
    Return a workflow's attachments as base64-encoded files, as a bare JSON
    array (the legacy contract has no envelope for this endpoint).

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``GetWorkflowAttachments`` and projects each record down to the
    published field set. Login/transport failures (and a "no attachments"
    result) yield an empty array.
    """
    try:
        result = await service.get_workflow_attachments(workflow_id)
    except ESignerError as exc:
        logger.error("Published GetAttachments failed: %s", exc.detail)
        return []

    attachments = result.Response or []
    return [
        PublishedAttachment(
            AttachmentName=a.AttachmentName,
            Base64FileData=a.Base64FileData,
            UploadedBy=a.UploadedBy,
            UploaderName=a.UploaderName,
        )
        for a in attachments
    ]


@router.get(
    "/GetDocumentLogs",
    response_model=list[PublishedDocumentLog],
    summary="Get a workflow's document audit log by workflowId (Catalyst contract)",
)
async def get_document_logs(
    workflow_id: int = Query(
        ...,
        alias="workflowId",
        ge=1,
        description="The E-Signer workflowId whose document log to fetch",
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> list[PublishedDocumentLog]:
    """
    Return a workflow's document audit log as a bare, flat JSON array (the
    legacy contract has no envelope and does not group entries by document).

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``GetDocumentLog`` and flattens each document's ``DocumentLogs``
    entries into a single array, projected to the published field set.
    Login/transport failures (and a "no logs" result) yield an empty array.
    """
    try:
        result = await service.get_document_log(workflow_id)
    except ESignerError as exc:
        logger.error("Published GetDocumentLogs failed: %s", exc.detail)
        return []

    documents = result.Response or []
    return [
        PublishedDocumentLog(
            DateTime=entry.DateTime,
            UserEmail=entry.UserEmail,
            Action=entry.Action,
            IPAddress=entry.IPAddress,
        )
        for document in documents
        for entry in (document.DocumentLogs or [])
    ]


@router.get(
    "/GetSignatureURL",
    response_model=ESignerSigningUrlResponse,
    summary="Get the ad-hoc signing URL by WorkflowID (Catalyst contract)",
)
async def get_signature_url(
    workflow_id: int = Query(
        ...,
        alias="WorkflowID",
        ge=1,
        description="The E-Signer WorkflowID to get a signing URL for",
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerSigningUrlResponse:
    """
    Return the ad-hoc signing URL for a workflow as the raw E-Signer
    ``GetSigningURL`` JSON envelope (``Response`` is the URL string).

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``GetSigningURL``. Login/transport failures are reported as
    ``IsSuccess=false`` within the JSON envelope rather than as HTTP errors.
    """
    try:
        return await service.get_signing_url(workflow_id)
    except ESignerError as exc:
        logger.error("Published GetSignatureURL failed: %s", exc.detail)
        return ESignerSigningUrlResponse(
            IsSuccess=False,
            Messages=[exc.detail],
            Response=None,
        )
