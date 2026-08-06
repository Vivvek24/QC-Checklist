"""User application DTOs. ids are int (BigInt)."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CreateUserDTO:
    username: str
    password: str
    is_validate_ad: bool = True
    role_id: int | None = None


@dataclass(frozen=True)
class UpdateUserDTO:
    is_active: bool | None = None
    is_blocked: bool | None = None
    is_validate_ad: bool | None = None
    role_id: int | None = None


@dataclass(frozen=True)
class UserDTO:
    id: int
    username: str
    is_active: bool
    is_blocked: bool
    is_validate_ad: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime
    employee_id: str | None = None
    employee_name: str | None = None
    email: str | None = None
    last_login: datetime | None = None


@dataclass(frozen=True)
class UserDetailDTO:
    id: int
    username: str
    is_active: bool
    is_blocked: bool
    is_validate_ad: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime
    employee_id: str | None = None
    employee_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    designation_title: str | None = None
    department: str | None = None
    business_unit: str | None = None
    group_company: str | None = None
    location: str | None = None
    region: str | None = None
    zone: str | None = None
    grade: str | None = None
    office_mobile_no: str | None = None
    personal_mobile_no: str | None = None
    date_of_joining: str | None = None
    reporting_manager: str | None = None
    direct_manager_employee_id: str | None = None
    direct_manager_name: str | None = None
    direct_manager_email: str | None = None
    sap_user_id: str | None = None
    division_id: str | None = None
    territory_id: str | None = None


@dataclass(frozen=True)
class UserListDTO:
    users: list[UserDTO]
    total: int
    skip: int
    limit: int
