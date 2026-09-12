"""
E-Signer Application Service.
Orchestrates the E-Signer service workflow:
- reachability/health checks
- (future) calling the E-Signer API endpoints via the external adapter

Controllers delegate here; this layer coordinates the external client and
contains no HTTP details of its own. Concrete operations will be added one by
one as endpoints are implemented.
"""

import logging
from typing import Any

from src.api.v1.schemas.esigner_schema import (
    ESignerChangePasswordResponse,
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
from src.infrastructure.external.esigner.esigner_client import (
    ESignerClient,
    ESignerError,
)

logger = logging.getLogger(__name__)


class ESignerService:
    """Application service for the E-Signer integration."""

    def __init__(self, client: ESignerClient) -> None:
        self._client = client

    # ─── Health ───

    async def check_health(self) -> ESignerHealthResponse:
        """Report whether the E-Signer service is reachable and configured."""
        result = await self._client.health_check()
        return ESignerHealthResponse(
            service="E-Signer",
            configured=self._client.is_configured,
            base_url=self._client.base_url,
            status=result.get("status", "unknown"),
            status_code=result.get("status_code"),
            error=result.get("error"),
            url=result.get("url"),
        )

    # ─── ValidateLogin ───

    async def login(self) -> ESignerLoginResponse:
        """
        Authenticate against E-Signer via ``/ValidateLogin`` using the
        credentials configured in the environment (ESIGNER_EMAIL /
        ESIGNER_PASSWORD) and return the parsed response (including the auth
        token when successful).

        Raises:
            ESignerError (and subclasses): propagated from the client for the
                controller to map to an HTTP status. A rejected login is NOT an
                error — it is returned with ``IsSuccess=False``.
        """
        if not self._client.is_configured:
            raise ESignerError(
                "E-Signer is not configured. Set ESIGNER_BASE_URL, "
                "ESIGNER_USERNAME, ESIGNER_PASSWORD, ESIGNER_EMAIL, "
                "ESIGNER_APP_NAME and ESIGNER_SECRET_KEY."
            )

        data = await self._client.login()
        return ESignerLoginResponse.model_validate(data)

    # ─── ChangePassword (rotation) ───

    async def rotate_password(self) -> ESignerRotatePasswordResponse:
        """
        Rotate the E-Signer account password without changing the effective
        credential: change it to the configured temporary password, then change
        it straight back to the original ESIGNER_PASSWORD.

        This satisfies password-expiry policies while leaving the password other
        applications use unchanged.

        The second step is only attempted if the first succeeds. If the first
        succeeds but the second fails, the account is left on the temporary
        password — this is surfaced loudly in the response and logged as an
        error so it can be corrected.

        Raises:
            ESignerError (and subclasses): configuration problems, or transport/
                HTTP failures propagated from the client.
        """
        if not self._client.is_configured:
            raise ESignerError(
                "E-Signer is not configured. Set ESIGNER_BASE_URL, "
                "ESIGNER_USERNAME, ESIGNER_PASSWORD, ESIGNER_EMAIL, "
                "ESIGNER_APP_NAME and ESIGNER_SECRET_KEY."
            )
        if not self._client.has_temp_password:
            raise ESignerError(
                "ESIGNER_TEMP_PASSWORD is not set; cannot rotate the password."
            )

        original = self._client.configured_password
        temp = self._client.temp_password
        if original == temp:
            raise ESignerError(
                "ESIGNER_TEMP_PASSWORD must differ from ESIGNER_PASSWORD."
            )

        # Step 1: original -> temporary
        step1 = ESignerChangePasswordResponse.model_validate(
            await self._client.change_password(original, temp)
        )
        if not step1.IsSuccess:
            detail = " ".join(m for m in step1.Messages if m) or "unknown error"
            logger.warning(
                "E-Signer password rotation aborted at step 1: %s", detail
            )
            return ESignerRotatePasswordResponse(
                IsSuccess=False,
                message=f"Step 1 (change to temporary password) failed: {detail}",
                step1=step1,
                step2=None,
            )

        # Step 2: temporary -> original
        step2 = ESignerChangePasswordResponse.model_validate(
            await self._client.change_password(temp, original)
        )
        if step2.IsSuccess:
            logger.info("E-Signer password rotated and restored successfully")
            return ESignerRotatePasswordResponse(
                IsSuccess=True,
                message="Password rotated successfully and restored to the original.",
                step1=step1,
                step2=step2,
            )

        detail = " ".join(m for m in step2.Messages if m) or "unknown error"
        logger.error(
            "E-Signer password rotation FAILED to restore original password. "
            "The account is currently set to the temporary password. %s",
            detail,
        )
        return ESignerRotatePasswordResponse(
            IsSuccess=False,
            message=(
                "CRITICAL: changed to the temporary password but failed to "
                f"restore the original. The E-Signer account is currently on the "
                f"temporary password — restore it manually. Details: {detail}"
            ),
            step1=step1,
            step2=step2,
        )

    # ─── InitiateEmbeddedSigning ───

    async def initiate_embedded_signing(
        self, payload: dict[str, Any]
    ) -> ESignerInitiateSigningResponse:
        """
        Start an embedded signing session.

        Authorization for this endpoint uses a user access token rather than the
        AppName/SecretKey headers, so this first calls ValidateLogin to obtain a
        fresh ``AuthToken`` and then forwards the caller's JSON payload to
        ``/InitiateEmbeddedSigning`` with that token.

        Raises:
            ESignerError (and subclasses): configuration/login problems, or
                transport/HTTP failures propagated from the client.
        """
        token = await self._login_for_token()
        data = await self._client.initiate_embedded_signing(payload, token)
        return ESignerInitiateSigningResponse.model_validate(data)

    # ─── GetWorkflowInfo ───

    async def get_workflow_info(
        self, workflow_id: int
    ) -> ESignerWorkflowInfoResponse:
        """
        Fetch the status/details of a workflow and its documents.

        Like embedded signing, this endpoint is authorized by a user access
        token, so it logs in first to obtain a fresh ``AuthToken``.

        Raises:
            ESignerError (and subclasses): configuration/login problems, or
                transport/HTTP failures propagated from the client.
        """
        token = await self._login_for_token()
        data = await self._client.get_workflow_info(workflow_id, token)
        return ESignerWorkflowInfoResponse.model_validate(data)

    # ─── DownloadWorkflowDocuments ───

    async def download_workflow_documents(
        self, workflow_id: int
    ) -> ESignerDownloadDocumentsResponse:
        """
        Download a workflow's documents as base64-encoded files.

        Like the other document endpoints, this is authorized by a user access
        token, so it logs in first to obtain a fresh ``AuthToken``.

        Raises:
            ESignerError (and subclasses): configuration/login problems, or
                transport/HTTP failures propagated from the client.
        """
        token = await self._login_for_token()
        data = await self._client.download_workflow_documents(workflow_id, token)
        return ESignerDownloadDocumentsResponse.model_validate(data)

    # ─── GetWorkflowAttachments ───

    async def get_workflow_attachments(
        self, workflow_id: int
    ) -> ESignerWorkflowAttachmentsResponse:
        """
        Fetch a workflow's attachments as base64-encoded files.

        Like the other document endpoints, this is authorized by a user access
        token, so it logs in first to obtain a fresh ``AuthToken``.

        Raises:
            ESignerError (and subclasses): configuration/login problems, or
                transport/HTTP failures propagated from the client.
        """
        token = await self._login_for_token()
        data = await self._client.get_workflow_attachments(workflow_id, token)
        return ESignerWorkflowAttachmentsResponse.model_validate(data)

    # ─── GetDocumentLog ───

    async def get_document_log(
        self, workflow_id: int
    ) -> ESignerDocumentLogResponse:
        """
        Fetch the audit-log history of a workflow's documents.

        Like the other document endpoints, this is authorized by a user access
        token, so it logs in first to obtain a fresh ``AuthToken``.

        Raises:
            ESignerError (and subclasses): configuration/login problems, or
                transport/HTTP failures propagated from the client.
        """
        token = await self._login_for_token()
        data = await self._client.get_document_log(workflow_id, token)
        return ESignerDocumentLogResponse.model_validate(data)

    # ─── GetSigningURL ───

    async def get_signing_url(
        self, workflow_id: int
    ) -> ESignerSigningUrlResponse:
        """
        Fetch the ad-hoc signing URL for a workflow.

        Like the other document endpoints, this is authorized by a user access
        token, so it logs in first to obtain a fresh ``AuthToken``.

        Raises:
            ESignerError (and subclasses): configuration/login problems, or
                transport/HTTP failures propagated from the client.
        """
        token = await self._login_for_token()
        data = await self._client.get_signing_url(workflow_id, token)
        return ESignerSigningUrlResponse.model_validate(data)

    # ─── Shared helpers ───

    async def _login_for_token(self) -> str:
        """
        Authenticate via ValidateLogin and return a non-empty ``AuthToken``.

        Raises:
            ESignerError: if the login fails or returns no token.
        """
        login = await self.login()
        token = login.Response.AuthToken if login.Response else ""
        if not login.IsSuccess or not token:
            detail = (
                " ".join(m for m in login.Messages if m)
                or "login did not return an auth token"
            )
            raise ESignerError(f"E-Signer login failed: {detail}")
        return token
