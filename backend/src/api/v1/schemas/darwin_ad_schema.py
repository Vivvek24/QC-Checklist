"""
Published Darwin AD service schemas (Pydantic v2).

These DTOs reproduce, field-for-field, the responses of the legacy Mendix
"Darwin AD integrator" service so consuming applications can repoint their
base URL without any request/response changes.

Field names intentionally mirror the Mendix payload exactly, including the
parenthesised ``territory_code_(sales_hq_code)`` key (declared via alias).
FastAPI serialises response models by alias by default, so the wire format
matches the original service.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.darwinbox_employee import DarwinboxEmployee


class DarwinEmployeeRecord(BaseModel):
    """A single employee record in the Darwin AD ``employeeData`` array."""

    model_config = ConfigDict(populate_by_name=True)

    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    employee_id: str = ""
    current_address: str = ""
    division: str = ""
    designation_title: str = ""
    office_mobile_no: str = ""
    extension_mobile_no: str = ""
    cost_center_id: str = ""
    cost_center: str = ""
    current_country: str = ""
    business_unit: str = ""
    department: str = ""
    group_company: str = ""
    personal_mobile_no: str = ""
    employee_status: str = ""
    job_level: str = ""
    direct_manager_employee_id: str = ""
    direct_manager_name: str = ""
    direct_manager_email: str = ""
    company_email_id: str = ""
    employeeid: int = 0
    current_location: str = ""
    office_location: str = ""
    custom_location: str = ""
    bank_pan: str = ""
    date_of_birth: str = ""
    role: str = ""
    territory_code: str = Field(default="", alias="territory_code_(sales_hq_code)")
    territory_name: str = ""
    split_territory: str = ""
    split_department: str = ""
    split_role: str = ""
    office_state: str = ""
    office_city: str = ""
    gender: str = ""
    catalyst_additional_department: str = ""
    date_of_exit: str = ""
    # Additive extension beyond the original Mendix contract: Darwinbox now
    # reports a department hierarchy path. Appended last so the pre-existing
    # keys keep their original order for consumers that care about it.
    departments_hierarchy: str = ""

    @classmethod
    def from_entity(cls, e: DarwinboxEmployee) -> "DarwinEmployeeRecord":
        """Map a stored Darwinbox employee entity to the Darwin AD wire format."""
        return cls(
            first_name=e.first_name,
            middle_name=e.middle_name,
            last_name=e.last_name,
            employee_id=e.employee_id,
            current_address=e.current_address,
            division=e.division,
            designation_title=e.designation_title,
            office_mobile_no=e.office_mobile_no,
            extension_mobile_no=e.extension_mobile_no,
            cost_center_id=e.cost_center_id,
            cost_center=e.cost_center,
            current_country=e.current_country,
            business_unit=e.business_unit,
            department=e.department,
            group_company=e.group_company,
            personal_mobile_no=e.personal_mobile_no,
            employee_status=e.employee_status,
            job_level=e.job_level,
            direct_manager_employee_id=e.direct_manager_employee_id,
            direct_manager_name=e.direct_manager_name,
            direct_manager_email=e.direct_manager_email,
            company_email_id=e.company_email_id,
            employeeid=e.employeeid_num,
            current_location=e.current_location,
            office_location=e.office_location,
            custom_location=e.custom_location,
            bank_pan=e.bank_pan,
            date_of_birth=e.date_of_birth,
            role=e.role,
            territory_code=e.territory_code,
            territory_name=e.territory_name,
            split_territory=e.split_territory,
            split_department=e.split_department,
            split_role=e.split_role,
            office_state=e.office_state,
            office_city=e.office_city,
            gender=e.gender,
            catalyst_additional_department=e.catalyst_additional_department,
            date_of_exit=e.date_of_exit,
            departments_hierarchy=e.departments_hierarchy,
        )


class EmployeeDataResponse(BaseModel):
    """Wrapper matching the Mendix ``{"employeeData": [...]}`` envelope."""

    employeeData: list[DarwinEmployeeRecord] = Field(default_factory=list)


class ValidateCredentialResponse(BaseModel):
    """Matches the Mendix validate-credential response shape."""

    IsSuccess: bool = False
    Message: str = ""
    IsValidUser: bool = False


class HierarchyItem(BaseModel):
    """A single distinct role/designation node in the hierarchy output."""

    split_role: str = ""
    role: str = ""
    designation_title: str = ""
    department: str = ""
    split_department: str = ""
    job_level: str = ""
    level: int = 0


class HierarchyResponse(BaseModel):
    """Wrapper matching the Mendix ``{"hierarchy": [...]}`` envelope."""

    hierarchy: list[HierarchyItem] = Field(default_factory=list)
