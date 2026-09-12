"""
Darwinbox employee domain entity.
Represents an employee master record synced from the Darwinbox master API.
"""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class DarwinboxEmployee(BaseEntity):
    """
    Darwinbox employee aggregate.

    Business Rules:
    - employee_id is the natural key and is unique across the master.
    - employee_status ("Active"/"Inactive") drives active vs inactive filtering.
    """

    employee_id: str = field(default="")
    # Darwinbox internal numeric id (distinct from the string employee_id).
    # Surfaced verbatim as "employeeid" in the published Darwin AD response.
    employeeid_num: int = field(default=0)
    first_name: str = field(default="")
    middle_name: str = field(default="")
    last_name: str = field(default="")
    full_name: str = field(default="")
    company_email_id: str = field(default="")
    employee_status: str = field(default="")
    designation_title: str = field(default="")
    job_level: str = field(default="")
    role: str = field(default="")
    department: str = field(default="")
    business_unit: str = field(default="")
    division: str = field(default="")
    group_company: str = field(default="")
    catalyst_additional_department: str = field(default="")
    # Full department path as reported by Darwinbox (e.g. "Regulatory Affairs").
    departments_hierarchy: str = field(default="")
    cost_center_id: str = field(default="")
    cost_center: str = field(default="")
    office_mobile_no: str = field(default="")
    extension_mobile_no: str = field(default="")
    personal_mobile_no: str = field(default="")
    current_address: str = field(default="")
    current_country: str = field(default="")
    current_location: str = field(default="")
    office_location: str = field(default="")
    custom_location: str = field(default="")
    office_state: str = field(default="")
    office_city: str = field(default="")
    direct_manager_employee_id: str = field(default="")
    direct_manager_name: str = field(default="")
    direct_manager_email: str = field(default="")
    territory_code: str = field(default="")
    territory_name: str = field(default="")
    split_territory: str = field(default="")
    split_department: str = field(default="")
    split_role: str = field(default="")
    bank_pan: str = field(default="")
    date_of_birth: str = field(default="")
    gender: str = field(default="")
    date_of_exit: str = field(default="")

    @property
    def is_active(self) -> bool:
        """True when the employee is marked active in Darwinbox."""
        return self.employee_status.strip().lower() == "active"
