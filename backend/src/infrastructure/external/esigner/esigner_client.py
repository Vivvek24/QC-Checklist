"""
E-Signer service integration client.

Talks to the E-Signer service configured via environment variables:
  - ESIGNER_BASE_URL — base URL of the E-Signer API
  - ESIGNER_USERNAME — account username
  - ESIGNER_PASSWORD — account password
  - ESIGNER_EMAIL    — account email

Uses httpx for async HTTP calls. No business logic — only E-Signer API
interaction. Mirrors the exception hierarchy used by the other external
clients (EmployeeADClient / DarwinboxClient).

Concrete endpoints will be added one by one as they are implemented.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)


class ESignerError(Exception):
    """Base class for E-Signer adapter errors."""

    def __init__(self, detail: str = "E-Signer service error") -> None:
        super().__init__(detail)
        self.detail = detail


class ESignerAuthError(ESignerError):
    """E-Signer rejected the request with an HTTP 401/403 status."""

    def __init__(self, detail: str = "E-Signer authentication failed") -> None:
        super().__init__(detail)


class ESignerUnavailableError(ESignerError):
    """E-Signer service could not be reached."""

    def __init__(self, detail: str = "E-Signer service unavailable") -> None:
        super().__init__(detail)


class ESignerClient:
    """Client for the E-Signer service."""

    def __init__(self) -> None:
        # Ensure no trailing slash for clean URL joining
        self._base_url = settings.ESIGNER_BASE_URL.rstrip("/")
        self._username = settings.ESIGNER_USERNAME
        self._password = settings.ESIGNER_PASSWORD
        self._email = settings.ESIGNER_EMAIL
        self._app_name = settings.ESIGNER_APP_NAME
        self._secret_key = settings.ESIGNER_SECRET_KEY
        self._temp_password = settings.ESIGNER_TEMP_PASSWORD

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def is_configured(self) -> bool:
        """True when the base URL, credentials and API headers are all set."""
        return all(
            [
                self._base_url,
                self._username,
                self._password,
                self._email,
                self._app_name,
                self._secret_key,
            ]
        )

    @property
    def configured_password(self) -> str:
        """The configured E-Signer account password (ESIGNER_PASSWORD)."""
        return self._password

    @property
    def temp_password(self) -> str:
        """The configured temporary password used for rotation."""
        return self._temp_password

    @property
    def has_temp_password(self) -> bool:
        """True when a temporary password is configured for rotation."""
        return bool(self._temp_password)

    def _auth_headers(self) -> dict[str, Any]:
        """
        Build the common request headers required by every emSigner API call:
        ``AppName`` and ``SecretKey`` identify the calling application. Without
        these the gateway rejects the request with HTTP 401.
        """
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "AppName": self._app_name,
            "SecretKey": self._secret_key,
        }

    def _token_headers(self, access_token: str) -> dict[str, Any]:
        """
        Build headers for endpoints authorized by a user access token (obtained
        from ValidateLogin). These endpoints do NOT use AppName/SecretKey; the
        token is sent in the ``Authorization`` header as ``basic <token>``.
        """
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"basic {access_token}",
        }

    def _handle_http_error(self, exc: httpx.HTTPStatusError, context: str) -> None:
        """Raise appropriate exception based on HTTP status code."""
        detail = f"{context}: {exc.response.status_code} - {exc.response.text[:200]}"
        logger.error(detail)
        if exc.response.status_code in (401, 403):
            raise ESignerAuthError(detail) from exc
        raise ESignerError(detail) from exc

    async def health_check(self) -> dict[str, Any]:
        """
        Check if the E-Signer service is reachable by hitting the base URL.

        Returns:
            Dict with status and response details. Never raises.
        """
        if not self._base_url:
            return {
                "status": "not_configured",
                "url": self._base_url,
                "error": "E-Signer base URL is not configured",
            }
        try:
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                response = await client.get(
                    self._base_url,
                    headers={"accept": "application/json"},
                )
                return {
                    "status": "reachable",
                    "status_code": response.status_code,
                    "url": self._base_url,
                }
        except httpx.RequestError as exc:
            logger.error("E-Signer service unreachable: %s", exc)
            return {
                "status": "unreachable",
                "error": str(exc),
                "url": self._base_url,
            }

    # ─── Endpoints ───

    async def login(self) -> dict[str, Any]:
        """
        POST /ValidateLogin — authenticate against E-Signer and obtain an auth
        token, using the credentials configured via environment variables.

        Request body: ``{"UserName": <ESIGNER_EMAIL>, "Password": <ESIGNER_PASSWORD>}``

        Returns:
            The raw JSON response dict from E-Signer. Note that E-Signer signals
            invalid credentials with an HTTP 200 and ``IsSuccess: false`` in the
            body, so a failed login is NOT raised here — it is returned as-is for
            the caller to interpret.

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        username = self._email
        url = f"{self._base_url}/ValidateLogin"
        logger.info("Calling E-Signer ValidateLogin for configured user: %s", username)

        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.post(
                    url,
                    json={"UserName": username, "Password": self._password},
                    headers=self._auth_headers(),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer ValidateLogin error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer ValidateLogin response for %s: IsSuccess=%s",
            username,
            data.get("IsSuccess"),
        )
        return data

    async def change_password(
        self, current_password: str, new_password: str
    ) -> dict[str, Any]:
        """
        POST /ChangePassword — change the configured account's password.

        The ``EmailId`` is always the configured account email; only the
        passwords vary. Used by the service to rotate the password (change to a
        temporary value and back).

        Request body:
            ``{"CurrentPassword": ..., "NewPassword": ..., "EmailId": <ESIGNER_EMAIL>}``

        Returns:
            The raw JSON response dict from E-Signer. A rejected change is
            returned with ``IsSuccess: false`` (HTTP 200), not raised.

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/ChangePassword"
        logger.info("Calling E-Signer ChangePassword for user: %s", self._email)

        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.post(
                    url,
                    json={
                        "CurrentPassword": current_password,
                        "NewPassword": new_password,
                        "EmailId": self._email,
                    },
                    headers=self._auth_headers(),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer ChangePassword error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer ChangePassword response for %s: IsSuccess=%s",
            self._email,
            data.get("IsSuccess"),
        )
        return data

    async def initiate_embedded_signing(
        self, payload: dict[str, Any], access_token: str
    ) -> dict[str, Any]:
        """
        POST /InitiateEmbeddedSigning — start an embedded signing session.

        This endpoint is authorized by a user access token (from ValidateLogin)
        passed in the ``Authorization`` header; it does NOT use AppName/SecretKey.
        The request body is the caller-supplied JSON, forwarded as-is.

        Returns:
            The raw JSON response dict from E-Signer.

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/InitiateEmbeddedSigning"
        logger.info("Calling E-Signer InitiateEmbeddedSigning")

        try:
            async with httpx.AsyncClient(verify=False, timeout=60) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._token_headers(access_token),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer InitiateEmbeddedSigning error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer InitiateEmbeddedSigning response: IsSuccess=%s",
            data.get("IsSuccess"),
        )
        return data

    async def get_workflow_info(
        self, workflow_id: int, access_token: str
    ) -> dict[str, Any]:
        """
        GET /GetWorkflowInfo?WorkflowId=<id> — fetch the status/details of a
        workflow and its documents.

        Authorized by a user access token (from ValidateLogin) in the
        ``Authorization`` header; does NOT use AppName/SecretKey.

        Returns:
            The raw JSON response dict from E-Signer.

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/GetWorkflowInfo"
        logger.info("Calling E-Signer GetWorkflowInfo for WorkflowId=%s", workflow_id)

        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.get(
                    url,
                    params={"WorkflowId": workflow_id},
                    headers=self._token_headers(access_token),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer GetWorkflowInfo error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer GetWorkflowInfo response for WorkflowId=%s: IsSuccess=%s",
            workflow_id,
            data.get("IsSuccess"),
        )
        return data

    async def download_workflow_documents(
        self, workflow_id: int, access_token: str
    ) -> dict[str, Any]:
        """
        POST /DownloadWorkflowDocuments — download a workflow's documents as
        base64-encoded files.

        Note: the request body key is ``WorkFlowId`` (capital F), which differs
        from GetWorkflowInfo's ``WorkflowId`` query parameter.

        Authorized by a user access token (from ValidateLogin) in the
        ``Authorization`` header; does NOT use AppName/SecretKey.

        Returns:
            The raw JSON response dict from E-Signer (includes base64 file data).

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/DownloadWorkflowDocuments"
        logger.info(
            "Calling E-Signer DownloadWorkflowDocuments for WorkFlowId=%s",
            workflow_id,
        )

        try:
            async with httpx.AsyncClient(verify=False, timeout=120) as client:
                response = await client.post(
                    url,
                    json={"WorkFlowId": workflow_id},
                    headers=self._token_headers(access_token),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer DownloadWorkflowDocuments error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer DownloadWorkflowDocuments response for WorkFlowId=%s: "
            "IsSuccess=%s",
            workflow_id,
            data.get("IsSuccess"),
        )
        return data

    async def get_workflow_attachments(
        self, workflow_id: int, access_token: str
    ) -> dict[str, Any]:
        """
        GET /GetWorkflowAttachments?workflowId=<id> — fetch a workflow's
        attachments as base64-encoded files.

        Authorized by a user access token (from ValidateLogin) in the
        ``Authorization`` header; does NOT use AppName/SecretKey.

        Returns:
            The raw JSON response dict from E-Signer (includes base64 file data).

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/GetWorkflowAttachments"
        logger.info(
            "Calling E-Signer GetWorkflowAttachments for workflowId=%s",
            workflow_id,
        )

        try:
            async with httpx.AsyncClient(verify=False, timeout=120) as client:
                response = await client.get(
                    url,
                    params={"workflowId": workflow_id},
                    headers=self._token_headers(access_token),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer GetWorkflowAttachments error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer GetWorkflowAttachments response for workflowId=%s: "
            "IsSuccess=%s",
            workflow_id,
            data.get("IsSuccess"),
        )
        return data

    async def get_document_log(
        self, workflow_id: int, access_token: str
    ) -> dict[str, Any]:
        """
        GET /GetDocumentLog?workflowId=<id> — fetch the audit-log history of a
        workflow's documents (uploads, signatures, actions, etc.).

        Authorized by a user access token (from ValidateLogin) in the
        ``Authorization`` header; does NOT use AppName/SecretKey.

        Returns:
            The raw JSON response dict from E-Signer.

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/GetDocumentLog"
        logger.info(
            "Calling E-Signer GetDocumentLog for workflowId=%s",
            workflow_id,
        )

        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.get(
                    url,
                    params={"workflowId": workflow_id},
                    headers=self._token_headers(access_token),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer GetDocumentLog error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer GetDocumentLog response for workflowId=%s: IsSuccess=%s",
            workflow_id,
            data.get("IsSuccess"),
        )
        return data

    async def get_signing_url(
        self, workflow_id: int, access_token: str
    ) -> dict[str, Any]:
        """
        POST /GetSigningURL — fetch the ad-hoc signing URL for a workflow.

        Note: the request body key is ``WorkFlowId`` (capital F), matching
        DownloadWorkflowDocuments rather than GetWorkflowInfo's ``WorkflowId``.

        Authorized by a user access token (from ValidateLogin) in the
        ``Authorization`` header; does NOT use AppName/SecretKey.

        Returns:
            The raw JSON response dict from E-Signer (``Response`` is the URL).

        Raises:
            ESignerAuthError: E-Signer responded with an HTTP 401/403.
            ESignerError: E-Signer responded with another HTTP error or an
                unexpected (non-object) payload.
            ESignerUnavailableError: E-Signer was unreachable.
        """
        url = f"{self._base_url}/GetSigningURL"
        logger.info(
            "Calling E-Signer GetSigningURL for WorkFlowId=%s",
            workflow_id,
        )

        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.post(
                    url,
                    json={"WorkFlowId": workflow_id},
                    headers=self._token_headers(access_token),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "E-Signer GetSigningURL error")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("E-Signer API connection error: %s", exc)
            raise ESignerUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise ESignerError(
                f"Unexpected E-Signer response type: {type(data).__name__}"
            )

        logger.info(
            "E-Signer GetSigningURL response for WorkFlowId=%s: IsSuccess=%s",
            workflow_id,
            data.get("IsSuccess"),
        )
        return data
