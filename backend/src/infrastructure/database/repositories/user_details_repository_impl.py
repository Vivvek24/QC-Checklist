"""User details repository implementation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user_details import UserDetails
from src.domain.repositories.user_details_repository import IUserDetailsRepository
from src.infrastructure.database.models.user_details_model import UserDetailsModel


class UserDetailsRepositoryImpl(IUserDetailsRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> UserDetails | None:
        stmt = select(UserDetailsModel).where(UserDetailsModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_many_by_user_ids(self, user_ids: list[int]) -> dict[int, UserDetails]:
        if not user_ids:
            return {}
        stmt = select(UserDetailsModel).where(UserDetailsModel.user_id.in_(user_ids))
        result = await self._session.execute(stmt)
        return {m.user_id: self._to_entity(m) for m in result.scalars().all()}

    @staticmethod
    def _to_entity(model: UserDetailsModel) -> UserDetails:
        return UserDetails(
            id=model.id,
            user_id=model.user_id,
            employee_id=model.employee_id,
            employee_name=model.employee_name,
            first_name=model.first_name,
            middle_name=model.middle_name,
            last_name=model.last_name,
            email=model.email,
            designation_title=model.designation_title,
            department=model.department,
            business_unit=model.business_unit,
            group_company=model.group_company,
            location=model.location,
            region=model.region,
            zone=model.zone,
            grade=model.grade,
            office_mobile_no=model.office_mobile_no,
            personal_mobile_no=model.personal_mobile_no,
            date_of_joining=model.date_of_joining,
            reporting_manager=model.reporting_manager,
            direct_manager_employee_id=model.direct_manager_employee_id,
            direct_manager_name=model.direct_manager_name,
            direct_manager_email=model.direct_manager_email,
            sap_user_id=model.sap_user_id,
            division_id=model.division_id,
            territory_id=model.territory_id,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
