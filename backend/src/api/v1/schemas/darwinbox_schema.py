"""
Darwinbox service schemas (Pydantic v2).
Request/response DTOs for the Darwinbox employee sync endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DarwinboxHealthResponse(BaseModel):
    """Reachability/health of the Darwinbox master API."""

    service: str
    active_configured: bool = Field(
        ..., description="Active dataset credentials/keys are all set"
    )
    inactive_configured: bool = Field(
        ..., description="Inactive dataset credentials/keys are all set"
    )
    base_url: str
    status: str
    status_code: int | None = None
    error: str | None = None
    url: str | None = None


class DarwinboxEmployeeResponse(BaseModel):
    """A single Darwinbox employee master record stored locally."""

    id: UUID
    employee_id: str
    employeeid_num: int
    full_name: str
    first_name: str
    middle_name: str
    last_name: str
    company_email_id: str
    employee_status: str
    designation_title: str
    job_level: str
    role: str
    department: str
    business_unit: str
    division: str
    group_company: str
    catalyst_additional_department: str
    departments_hierarchy: str
    cost_center_id: str
    cost_center: str
    office_mobile_no: str
    extension_mobile_no: str
    personal_mobile_no: str
    current_address: str
    current_country: str
    current_location: str
    office_location: str
    custom_location: str
    office_state: str
    office_city: str
    direct_manager_employee_id: str
    direct_manager_name: str
    direct_manager_email: str
    territory_code: str
    territory_name: str
    split_territory: str
    split_department: str
    split_role: str
    bank_pan: str
    date_of_birth: str
    gender: str
    date_of_exit: str
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class DarwinboxEmployeeListResponse(BaseModel):
    """Paginated list of stored Darwinbox employees."""

    employees: list[DarwinboxEmployeeResponse]
    total: int
    skip: int
    limit: int


class SyncEmployeesResponse(BaseModel):
    """Result of a Darwinbox sync operation (aggregated across datasets)."""

    datasets: list[str] = Field(
        default_factory=list, description="Datasets included in this sync"
    )
    total: int = Field(..., description="Employees returned by Darwinbox")
    created: int
    updated: int
    failed: int
    message: str = ""
