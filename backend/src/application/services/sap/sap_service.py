"""SAP application service.

Wraps SapClient for the Services menu: a reachability health check and the
QC_Checklist lookup. Logs the raw SAP response so integration issues are
traceable, and surfaces the parsed T_OUTPUT.item alongside the raw payload.
"""

import logging
from typing import Any

from src.infrastructure.external.sap.sap_client import SapClient

logger = logging.getLogger(__name__)


class SapService:
    """Thin orchestration over SapClient for the SAP service page."""

    def __init__(self, client: SapClient | None = None) -> None:
        self._client = client or SapClient()

    @property
    def client(self) -> SapClient:
        return self._client

    async def health(self) -> dict[str, Any]:
        """Service reachability + whether credentials/base URL are configured."""
        result = await self._client.health_check()
        return {
            "service": "SAP Integration Suite",
            "configured": self._client.is_configured,
            "base_url": self._client.base_url,
            **result,
        }

    async def get_qc_checklist(self, insp_lot: str) -> dict[str, Any]:
        """Fetch the QC checklist row for an inspection lot. Logs the raw
        response and returns both the raw payload and the parsed item."""
        raw = await self._client.get_qc_checklist(insp_lot)
        logger.info("SAP QC_Checklist raw response for I_INSP=%s: %s", insp_lot, raw)

        item: dict[str, Any] = {}
        if isinstance(raw, dict):
            output = raw.get("T_OUTPUT")
            if isinstance(output, dict) and isinstance(output.get("item"), dict):
                item = output["item"]

        return {"insp_lot": insp_lot, "item": item, "raw_response": raw}
