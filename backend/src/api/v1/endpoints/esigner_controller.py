"""
E-Signer Service API endpoints.
Thin controller — delegates all business logic to ESignerService.

Endpoints:
  - GET  /health                    — Check E-Signer service reachability
  - POST /login                     — Authenticate against E-Signer (ValidateLogin)
  - POST /change-password           — Rotate the account password (change and restore)
  - POST /initiate-embedded-signing — Start an embedded signing session
  - GET  /workflow-info             — Get workflow/document status by WorkflowId
  - GET  /workflow-documents        — Download a workflow's documents (base64)
  - GET  /workflow-attachments      — Download a workflow's attachments (base64)
  - GET  /document-log              — Get a workflow's document audit log
  - GET  /signing-url               — Get the ad-hoc signing URL for a workflow

Additional endpoints will be added one by one as they are implemented.

Protected: requires the 'services.esigner' permission.
"""

from typing import Any, NoReturn

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from src.api.v1.schemas.esigner_schema import (
    ESignerDocumentLogResponse,
    ESignerDownloadDocumentsResponse,
    ESignerHealthResponse,
    ESignerInitiateSigningResponse,
    ESignerLoginResponse,
    ESignerRotatePasswordResponse,
    ESignerSigningUrlResponse,
    ESignerWorkflowAttachmentsResponse,
    ESignerWorkflowInfoResponse,
)
from src.application.services.esigner_service import ESignerService
from src.infrastructure.external.esigner.esigner_client import (
    ESignerAuthError,
    ESignerClient,
    ESignerError,
    ESignerUnavailableError,
)
from src.infrastructure.security.permission_manager import require_permission

router = APIRouter(
    prefix="/services/esigner",
    tags=["E-Signer Service"],
    dependencies=[Depends(require_permission("services.esigner"))],
)


def _get_esigner_service() -> ESignerService:
    """FastAPI dependency — creates ESignerService with injected dependencies."""
    return ESignerService(client=ESignerClient())


def _raise_for_esigner_error(exc: ESignerError) -> NoReturn:
    """
    Map E-Signer client/service exceptions to HTTP responses.

    Declared `NoReturn`, not `None`: every branch raises. With `None`, mypy treats
    a caller's `except ESignerError: _raise_for_esigner_error(exc)` as falling off
    the end of the function and reports a missing return on all nine endpoints —
    which hides the fact that a genuine fall-through would look identical.
    """
    if isinstance(exc, ESignerAuthError):
        raise HTTPException(status_code=401, detail=exc.detail) from exc
    if isinstance(exc, ESignerUnavailableError):
        raise HTTPException(status_code=503, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=exc.detail) from exc


@router.get(
    "/health",
    response_model=ESignerHealthResponse,
    summary="Check E-Signer service reachability",
)
async def check_health(
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerHealthResponse:
    """Verify whether the E-Signer service is reachable."""
    return await service.check_health()


@router.post(
    "/login",
    response_model=ESignerLoginResponse,
    summary="Authenticate against E-Signer (ValidateLogin)",
)
async def login(
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerLoginResponse:
    """
    Authenticate against the E-Signer ``/ValidateLogin`` endpoint using the
    credentials configured in the environment.

    A rejected login returns HTTP 200 with ``IsSuccess=false``; only
    transport/HTTP failures raise an error.
    """
    try:
        return await service.login()
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.post(
    "/change-password",
    response_model=ESignerRotatePasswordResponse,
    summary="Rotate the E-Signer account password (change and restore)",
)
async def change_password(
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerRotatePasswordResponse:
    """
    Rotate the configured E-Signer account password to satisfy password-expiry
    policies WITHOUT changing the effective credential.

    It changes the password to the configured temporary password
    (ESIGNER_TEMP_PASSWORD), then immediately changes it back to the original
    (ESIGNER_PASSWORD), so other applications using the same account are
    unaffected. ``IsSuccess`` is true only when both steps succeed.
    """
    try:
        return await service.rotate_password()
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.post(
    "/initiate-embedded-signing",
    response_model=ESignerInitiateSigningResponse,
    summary="Start an embedded signing session",
)
async def initiate_embedded_signing(
    payload: dict[str, Any] = Body(
        ..., description="The InitiateEmbeddedSigning request body (forwarded as-is)"
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerInitiateSigningResponse:
    """
    Start an embedded signing session.

    This endpoint authenticates first (ValidateLogin) to obtain an access token,
    then forwards the supplied JSON body to E-Signer's ``/InitiateEmbeddedSigning``
    using that token in the ``Authorization`` header. On success the response
    includes the embedded signing ``URL``.
    """
    try:
        return await service.initiate_embedded_signing(payload)
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.get(
    "/workflow-info",
    response_model=ESignerWorkflowInfoResponse,
    summary="Get workflow/document status by WorkflowId",
)
async def get_workflow_info(
    workflow_id: int = Query(
        ..., description="The E-Signer WorkflowId to look up", ge=1
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerWorkflowInfoResponse:
    """
    Fetch the status/details of a workflow and its documents.

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``/GetWorkflowInfo`` with that token in the ``Authorization``
    header.
    """
    try:
        return await service.get_workflow_info(workflow_id)
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.get(
    "/workflow-documents",
    response_model=ESignerDownloadDocumentsResponse,
    summary="Download a workflow's documents (base64) by WorkflowId",
)
async def download_workflow_documents(
    workflow_id: int = Query(
        ..., description="The E-Signer WorkflowId whose documents to download", ge=1
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerDownloadDocumentsResponse:
    """
    Download a workflow's documents as base64-encoded files.

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``/DownloadWorkflowDocuments`` with that token in the
    ``Authorization`` header.
    """
    try:
        return await service.download_workflow_documents(workflow_id)
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.get(
    "/workflow-attachments",
    response_model=ESignerWorkflowAttachmentsResponse,
    summary="Download a workflow's attachments (base64) by workflowId",
)
async def get_workflow_attachments(
    workflow_id: int = Query(
        ..., description="The E-Signer workflowId whose attachments to download", ge=1
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerWorkflowAttachmentsResponse:
    """
    Download a workflow's attachments as base64-encoded files.

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``/GetWorkflowAttachments`` with that token in the
    ``Authorization`` header.
    """
    try:
        return await service.get_workflow_attachments(workflow_id)
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.get(
    "/document-log",
    response_model=ESignerDocumentLogResponse,
    summary="Get a workflow's document audit log by workflowId",
)
async def get_document_log(
    workflow_id: int = Query(
        ..., description="The E-Signer workflowId whose document log to fetch", ge=1
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerDocumentLogResponse:
    """
    Fetch the audit-log history of a workflow's documents (uploads, workflow
    initiation, signatures, and other actions).

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``/GetDocumentLog`` with that token in the ``Authorization``
    header.
    """
    try:
        return await service.get_document_log(workflow_id)
    except ESignerError as exc:
        _raise_for_esigner_error(exc)


@router.get(
    "/signing-url",
    response_model=ESignerSigningUrlResponse,
    summary="Get the ad-hoc signing URL for a workflow by workflowId",
)
async def get_signing_url(
    workflow_id: int = Query(
        ..., description="The E-Signer WorkFlowId to get a signing URL for", ge=1
    ),
    service: ESignerService = Depends(_get_esigner_service),
) -> ESignerSigningUrlResponse:
    """
    Fetch the ad-hoc signing URL for a workflow.

    Authenticates first (ValidateLogin) to obtain an access token, then calls
    E-Signer's ``/GetSigningURL`` (POST body ``{"WorkFlowId": <id>}``) with that
    token in the ``Authorization`` header. On success the response ``Response``
    field holds the signing URL.
    """
    try:
        return await service.get_signing_url(workflow_id)
    except ESignerError as exc:
        _raise_for_esigner_error(exc)
