"""SAP Integration Suite client.

Thin async adapter over the SAP Integration Suite (QAS) HTTP endpoints. Uses
HTTP Basic auth (SAP_USERNAME / SAP_PASSWORD) against SAP_BASE_URL. No business
logic here — only the HTTP interaction, mirroring EmployeeADClient.

Add one method per SAP endpoint the app consumes (e.g. a material/batch lookup
for the AQL template) using the shared _get / _post helpers.
"""

from __future__ import annotations

import logging
from typing import Any, NoReturn

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)


class SapError(Exception):
    """Base class for SAP adapter errors."""

    def __init__(self, detail: str = "SAP service error") -> None:
        super().__init__(detail)
        self.detail = detail


class SapAuthError(SapError):
    """SAP rejected the request with an HTTP 401/403 status."""

    def __init__(self, detail: str = "SAP authentication failed") -> None:
        super().__init__(detail)


class SapUnavailableError(SapError):
    """SAP service could not be reached."""

    def __init__(self, detail: str = "SAP service unavailable") -> None:
        super().__init__(detail)


class SapClient:
    """Client for the SAP Integration Suite HTTP endpoints (Basic auth)."""

    _TIMEOUT = 60

    def __init__(self) -> None:
        self._base_url = settings.SAP_BASE_URL.rstrip("/")
        self._auth = (settings.SAP_USERNAME, settings.SAP_PASSWORD)

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def is_configured(self) -> bool:
        """True when the base URL + credentials are all set."""
        return bool(self._base_url and settings.SAP_USERNAME and settings.SAP_PASSWORD)

    # ─── shared HTTP helpers ──────────────────────────────────────────────
    def _handle_http_error(self, exc: httpx.HTTPStatusError, context: str) -> NoReturn:
        detail = f"{context}: {exc.response.status_code} - {exc.response.text[:200]}"
        logger.error(detail)
        if exc.response.status_code in (401, 403):
            raise SapAuthError(detail) from exc
        raise SapError(detail) from exc

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET {base}/{path} with Basic auth; returns parsed JSON."""
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
                response = await client.get(
                    url, params=params, auth=self._auth,
                    headers={"accept": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, f"SAP GET {path} error")
        except httpx.RequestError as exc:
            logger.error("SAP API connection error: %s", exc)
            raise SapUnavailableError(str(exc)) from exc

    async def _post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        """POST JSON to {base}/{path} with Basic auth; returns parsed JSON."""
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
                response = await client.post(
                    url, json=payload, auth=self._auth,
                    headers={"accept": "application/json", "content-type": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, f"SAP POST {path} error")
        except httpx.RequestError as exc:
            logger.error("SAP API connection error: %s", exc)
            raise SapUnavailableError(str(exc)) from exc

    # ─── QC Checklist lookup ──────────────────────────────────────────────
    async def get_qc_checklist(self, insp_lot: str) -> dict[str, Any]:
        """GET /Get/QC_Checklist?I_INSP=<insp_lot>.

        Returns the raw SAP JSON. On success the material/batch details live
        under T_OUTPUT.item.
        """
        return await self._get("Get/QC_Checklist", params={"I_INSP": insp_lot})

    # ─── health ───────────────────────────────────────────────────────────
    async def health_check(self) -> dict[str, Any]:
        """Report whether the SAP base URL is reachable."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self._base_url, auth=self._auth,
                    headers={"accept": "application/json"},
                )
                return {
                    "status": "reachable",
                    "status_code": response.status_code,
                    "url": self._base_url,
                }
        except httpx.RequestError as exc:
            logger.error("SAP service unreachable: %s", exc)
            return {"status": "unreachable", "error": str(exc), "url": self._base_url}
