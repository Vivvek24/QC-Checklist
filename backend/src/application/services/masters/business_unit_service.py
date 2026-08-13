"""
Business Unit Master — application service.
All business logic lives here. No HTTP concepts.
"""

from src.application.dtos.masters.business_unit_dtos import (
    BusinessUnitDTO,
    BusinessUnitListDTO,
    CreateBusinessUnitDTO,
    UpdateBusinessUnitDTO,
)
from src.domain.entities.masters.business_unit import BusinessUnit
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.business_unit_repository import IBusinessUnitRepository

ENTITY = "BusinessUnit"


class BusinessUnitService:
    """Application service for Business Unit master CRUD."""

    def __init__(self, repo: IBusinessUnitRepository) -> None:
        self._repo = repo

    # ─── List ───

    async def list_business_units(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> BusinessUnitListDTO:
        """Return a paginated list of business units."""
        items = await self._repo.list_all(
            skip=skip, limit=limit, search=search, is_active=is_active
        )
        total = await self._repo.count(search=search, is_active=is_active)
        return BusinessUnitListDTO(
            items=[self._to_dto(i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    # ─── Get ───

    async def get_business_unit(self, business_unit_id: int) -> BusinessUnitDTO:
        """Return a single business unit by id."""
        return self._to_dto(await self._require(business_unit_id))

    # ─── Create ───

    async def create_business_unit(
        self, dto: CreateBusinessUnitDTO, actor: User
    ) -> BusinessUnitDTO:
        """Create a new business unit after checking name uniqueness."""
        if await self._repo.exists_by_name(dto.name):
            raise DuplicateEntityError(ENTITY, "name", dto.name)

        created = await self._repo.create(
            BusinessUnit(
                name=dto.name.strip(),
                is_active=dto.is_active,
                created_by=actor.username,
                modified_by=actor.username,
            )
        )
        return self._to_dto(created)

    # ─── Update ───

    async def update_business_unit(
        self, business_unit_id: int, dto: UpdateBusinessUnitDTO, actor: User
    ) -> BusinessUnitDTO:
        """Apply a partial update to a business unit."""
        bu = await self._require(business_unit_id)

        if dto.name is not None and dto.name.strip() != bu.name:
            if await self._repo.exists_by_name(dto.name, exclude_id=business_unit_id):
                raise DuplicateEntityError(ENTITY, "name", dto.name)
            bu.name = dto.name.strip()

        if dto.is_active is not None:
            bu.is_active = dto.is_active

        bu.mark_modified(actor.username)
        updated = await self._repo.update(bu)
        return self._to_dto(updated)

    # ─── Delete ───

    async def delete_business_unit(self, business_unit_id: int) -> None:
        """Delete a business unit by id."""
        await self._require(business_unit_id)
        await self._repo.delete(business_unit_id)

    # ─── Internals ───

    async def _require(self, business_unit_id: int) -> BusinessUnit:
        bu = await self._repo.get_by_id(business_unit_id)
        if bu is None:
            raise EntityNotFoundError(ENTITY, business_unit_id)
        return bu

    @staticmethod
    def _to_dto(bu: BusinessUnit) -> BusinessUnitDTO:
        return BusinessUnitDTO(
            id=bu.id,
            name=bu.name,
            is_active=bu.is_active,
            created_by=bu.created_by,
            created_date=bu.created_date,
            modified_by=bu.modified_by,
            modified_date=bu.modified_date,
        )
