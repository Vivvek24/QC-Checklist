"""
Darwinbox master API integration client.

Fetches the full employee master (active + inactive) from the Darwinbox
master API at:
  https://emcure.darwinbox.in/masterapi/employee

The endpoint expects HTTP Basic auth and a JSON body:
  {"api_key": "<...>", "datasetKey": "<...>"}

and returns:
  {
    "status": 1,
    "message": "Successfully loaded all employees data",
    "employee_data": [ { ...employee fields... } ]
  }

Uses httpx for async HTTP calls. No business logic — only Darwinbox API
interaction. Mirrors the EmployeeADClient pattern.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Selects which credential/key set (and therefore which population) to fetch.
DarwinboxDataset = Literal["active", "inactive"]


class DarwinboxError(Exception):
    """Base class for Darwinbox adapter errors."""

    def __init__(self, detail: str = "Darwinbox service error") -> None:
        super().__init__(detail)
        self.detail = detail


class DarwinboxAuthError(DarwinboxError):
    """Darwinbox rejected the request with an HTTP 401/403 status."""

    def __init__(self, detail: str = "Darwinbox authentication failed") -> None:
        super().__init__(detail)


class DarwinboxUnavailableError(DarwinboxError):
    """Darwinbox service could not be reached."""

    def __init__(self, detail: str = "Darwinbox service unavailable") -> None:
        super().__init__(detail)


@dataclass(frozen=True)
class _DatasetCredentials:
    """Basic-auth credentials and API keys for a single Darwinbox dataset."""

    username: str
    password: str
    api_key: str
    dataset_key: str

    @property
    def is_configured(self) -> bool:
        return all([self.username, self.password, self.api_key, self.dataset_key])


@dataclass(frozen=True)
class EmployeeFetchResult:
    """Parsed result of a Darwinbox employee master call."""

    status: int
    message: str
    employees: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.status == 1


class DarwinboxClient:
    """Client for the Darwinbox master employee API (active + inactive datasets)."""

    def __init__(self) -> None:
        # Ensure no trailing slash for clean URL joining
        self._base_url = settings.DARWINBOX_BASE_URL.rstrip("/")
        self._credentials: dict[DarwinboxDataset, _DatasetCredentials] = {
            "active": _DatasetCredentials(
                username=settings.DARWINBOX_USERNAME,
                password=settings.DARWINBOX_PASSWORD,
                api_key=settings.DARWINBOX_API_KEY,
                dataset_key=settings.DARWINBOX_DATASET_KEY,
            ),
            "inactive": _DatasetCredentials(
                username=settings.DARWINBOX_INACTIVE_USERNAME,
                password=settings.DARWINBOX_INACTIVE_PASSWORD,
                api_key=settings.DARWINBOX_INACTIVE_API_KEY,
                dataset_key=settings.DARWINBOX_INACTIVE_DATASET_KEY,
            ),
        }

    @property
    def base_url(self) -> str:
        return self._base_url

    def is_configured(self, dataset: DarwinboxDataset = "active") -> bool:
        """True when the base URL and the given dataset's credentials are all set."""
        return bool(self._base_url) and self._credentials[dataset].is_configured

    def _handle_http_error(self, exc: httpx.HTTPStatusError, context: str) -> None:
        """Raise appropriate exception based on HTTP status code."""
        detail = f"{context}: {exc.response.status_code} - {exc.response.text[:200]}"
        logger.error(detail)
        if exc.response.status_code in (401, 403):
            raise DarwinboxAuthError(detail) from exc
        raise DarwinboxError(detail) from exc

    async def health_check(self) -> dict[str, Any]:
        """
        Check if the Darwinbox service is reachable by hitting the base URL.

        Returns:
            Dict with status and response details.
        """
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
            logger.error("Darwinbox service unreachable: %s", exc)
            return {
                "status": "unreachable",
                "error": str(exc),
                "url": self._base_url,
            }

    async def fetch_employees(
        self, dataset: DarwinboxDataset = "active"
    ) -> EmployeeFetchResult:
        """
        POST to the master API to fetch the employee master for the given dataset.

        Args:
            dataset: "active" or "inactive" — selects the credential/key set and
                therefore the population returned by Darwinbox.

        Returns:
            EmployeeFetchResult with status, message and the employee list.

        Raises:
            DarwinboxAuthError: Darwinbox responded with 401/403.
            DarwinboxError: Darwinbox responded with another HTTP error or an
                unexpected payload.
            DarwinboxUnavailableError: Darwinbox was unreachable.
        """
        creds = self._credentials[dataset]
        logger.info("Calling Darwinbox master employee API (dataset=%s)", dataset)

        try:
            async with httpx.AsyncClient(verify=False, timeout=120) as client:
                response = await client.post(
                    self._base_url,
                    json={
                        "api_key": creds.api_key,
                        "datasetKey": creds.dataset_key,
                    },
                    auth=(creds.username, creds.password),
                    headers={
                        "accept": "application/json",
                        "content-type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, f"Darwinbox master employee error ({dataset})")
            raise  # unreachable but satisfies type checker
        except httpx.RequestError as exc:
            logger.error("Darwinbox API connection error: %s", exc)
            raise DarwinboxUnavailableError(str(exc)) from exc

        if not isinstance(data, dict):
            raise DarwinboxError(
                f"Unexpected Darwinbox response type: {type(data).__name__}"
            )

        status = int(data.get("status", 0))
        message = str(data.get("message", ""))
        employees = data.get("employee_data", []) or []
        if not isinstance(employees, list):
            raise DarwinboxError("Darwinbox 'employee_data' is not a list")

        logger.info(
            "Darwinbox master response (dataset=%s): status=%s, count=%s",
            dataset,
            status,
            len(employees),
        )
        return EmployeeFetchResult(
            status=status, message=message, employees=employees
        )
