"""SAP Integration Suite — service endpoints.

Exposed under the Services menu, gated by the `services.sap` permission:
  - GET /services/sap/health        — SAP reachability + config status
  - GET /services/sap/qc-checklist  — QC checklist lookup by inspection lot
                                      (logs the raw SAP response)
"""

from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.services.sap.sap_service import SapService
from src.infrastructure.external.sap.sap_client import (
    SapAuthError,
    SapError,
    SapUnavailableError,
)
from src.infrastructure.security.permission_manager import require_permission

router = APIRouter(
    prefix="/services/sap",
    tags=["SAP Service"],
    dependencies=[Depends(require_permission("services.sap"))],
)

_service = SapService()


def _raise_for_sap_error(exc: SapError) -> NoReturn:
    """Map SAP client exceptions to HTTP responses."""
    if isinstance(exc, SapAuthError):
        raise HTTPException(status_code=401, detail=exc.detail)
    if isinstance(exc, SapUnavailableError):
        raise HTTPException(status_code=503, detail=exc.detail)
    raise HTTPException(status_code=502, detail=exc.detail)


@router.get("/health", summary="Check SAP Integration Suite reachability")
async def check_health() -> dict[str, Any]:
    """Verify whether the SAP service is reachable and configured."""
    return await _service.health()


@router.get("/qc-checklist", summary="SAP QC checklist lookup by inspection lot")
async def get_qc_checklist(
    insp_lot: str = Query(..., alias="I_INSP", description="Inspection lot number"),
) -> dict[str, Any]:
    """Fetch the SAP QC checklist row for an inspection lot. Returns the parsed
    item + the raw response (also logged server-side)."""
    try:
        return await _service.get_qc_checklist(insp_lot)
    except SapError as exc:
        _raise_for_sap_error(exc)
