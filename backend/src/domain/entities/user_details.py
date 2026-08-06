"""UserDetails domain entity. One-to-one with User."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class UserDetails(BaseEntity):
    user_id: int | None = field(default=None)
    employee_id: str = field(default="")
    employee_name: str = field(default="")
    first_name: str = field(default="")
    middle_name: str = field(default="")
    last_name: str = field(default="")
    email: str = field(default="")
    designation_title: str = field(default="")
    department: str = field(default="")
    business_unit: str = field(default="")
    group_company: str = field(default="")
    location: str = field(default="")
    region: str = field(default="")
    zone: str = field(default="")
    grade: str = field(default="")
    office_mobile_no: str = field(default="")
    personal_mobile_no: str = field(default="")
    date_of_joining: str = field(default="")
    reporting_manager: str = field(default="")
    direct_manager_employee_id: str = field(default="")
    direct_manager_name: str = field(default="")
    direct_manager_email: str = field(default="")
    sap_user_id: str = field(default="")
    division_id: str = field(default="")
    territory_id: str = field(default="")
