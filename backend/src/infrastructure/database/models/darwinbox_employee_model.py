"""
SQLAlchemy ORM model for Darwinbox employee master records.
Maps to the 'darwinbox_employees' table. Stores the employee master
(active + inactive) synced from the Darwinbox master API.

Free-form fields use unbounded ``Text`` because Darwinbox values
(addresses, proxy emails, long designations) can exceed conventional
length limits. Only ``employee_id`` and ``employee_status`` stay bounded
since they are controlled short values (natural key / status enum).
"""

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class DarwinboxEmployeeModel(BaseModel):
    """Darwinbox employee master table — stores data synced from Darwinbox."""

    __tablename__ = "darwinbox_employees"

    # Natural key from Darwinbox — used for upsert. Kept bounded + indexed.
    employee_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Darwinbox internal numeric id (surfaced as "employeeid" in the Darwin AD API).
    employeeid_num: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )

    first_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    middle_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_name: Mapped[str] = mapped_column(Text, nullable=False, default="")

    company_email_id: Mapped[str] = mapped_column(Text, nullable=False, default="", index=True)
    employee_status: Mapped[str] = mapped_column(String(50), nullable=False, default="", index=True)

    designation_title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    job_level: Mapped[str] = mapped_column(Text, nullable=False, default="")
    role: Mapped[str] = mapped_column(Text, nullable=False, default="")

    department: Mapped[str] = mapped_column(Text, nullable=False, default="")
    business_unit: Mapped[str] = mapped_column(Text, nullable=False, default="")
    division: Mapped[str] = mapped_column(Text, nullable=False, default="")
    group_company: Mapped[str] = mapped_column(Text, nullable=False, default="")
    catalyst_additional_department: Mapped[str] = mapped_column(Text, nullable=False, default="")
    departments_hierarchy: Mapped[str] = mapped_column(Text, nullable=False, default="")

    cost_center_id: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cost_center: Mapped[str] = mapped_column(Text, nullable=False, default="")

    office_mobile_no: Mapped[str] = mapped_column(Text, nullable=False, default="")
    extension_mobile_no: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personal_mobile_no: Mapped[str] = mapped_column(Text, nullable=False, default="")

    current_address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    current_country: Mapped[str] = mapped_column(Text, nullable=False, default="")
    current_location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    office_location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    custom_location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    office_state: Mapped[str] = mapped_column(Text, nullable=False, default="")
    office_city: Mapped[str] = mapped_column(Text, nullable=False, default="")

    direct_manager_employee_id: Mapped[str] = mapped_column(Text, nullable=False, default="")
    direct_manager_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    direct_manager_email: Mapped[str] = mapped_column(Text, nullable=False, default="")

    territory_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    territory_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    split_territory: Mapped[str] = mapped_column(Text, nullable=False, default="")
    split_department: Mapped[str] = mapped_column(Text, nullable=False, default="")
    split_role: Mapped[str] = mapped_column(Text, nullable=False, default="")

    bank_pan: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date_of_birth: Mapped[str] = mapped_column(Text, nullable=False, default="")
    gender: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date_of_exit: Mapped[str] = mapped_column(Text, nullable=False, default="")
