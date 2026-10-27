"""Dashboard — Pydantic schemas for the QC Checklist dashboard grid."""

from pydantic import BaseModel


class DashboardRowSchema(BaseModel):
    request_number: str
    format_name: str
    status_format: str
    created_date: str | None = None
    stage_status: str
    requested_by: str
    request_status: str
    is_last_stage: bool
    batch_no: str
    product_name: str
    test_name: str
    action_flag: bool = False


class DashboardResponse(BaseModel):
    pending: list[DashboardRowSchema]
    approved: list[DashboardRowSchema]
    total: int = 0
