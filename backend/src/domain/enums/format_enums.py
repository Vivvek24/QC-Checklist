"""Format Master enums."""

from enum import StrEnum


class FormatType(StrEnum):
    CHROMATOGRAPHIC = "Chromatographic"
    AQL = "AQL"
    RECEIPT_CHECKLIST_STANDARD = "RECEIPT_CHECKLIST_STANDARD"
    RECONCILATION_SHEET = "ReconcilationSheet"
