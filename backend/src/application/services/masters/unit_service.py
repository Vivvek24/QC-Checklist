"""Unit Master — application service."""

from src.application.dtos.masters.unit_dtos import (
    CreateUnitDTO,
    UnitDTO,
    UnitListDTO,
    UpdateUnitDTO,
)
from src.domain.entities.masters.unit import Unit
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.unit_repository import IUnitRepository

ENTITY = "Unit"


class UnitService:
    """Application service for Unit master CRUD."""

    def __init__(self, repo: IUnitRepository) -> None:
        self._repo = repo

    async def list_units(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> UnitListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return UnitListDTO(
            items=[self._to_dto(i) for i in items],
            total=total, skip=skip, limit=limit,
        )

    async def get_unit(self, unit_id: int) -> UnitDTO:
        return self._to_dto(await self._require(unit_id))

    async def create_unit(self, dto: CreateUnitDTO, actor: User) -> UnitDTO:
        if await self._repo.exists_by_name_in_business_unit(dto.name, dto.business_unit_id):
            raise DuplicateEntityError(ENTITY, "name", dto.name)
        created = await self._repo.create(
            Unit(
                name=dto.name.strip(),
                business_unit_id=dto.business_unit_id,
                is_active=dto.is_active,
                created_by=actor.username,
                modified_by=actor.username,
            )
        )
        return self._to_dto(created)

    async def update_unit(self, unit_id: int, dto: UpdateUnitDTO, actor: User) -> UnitDTO:
        unit = await self._require(unit_id)

        new_name = dto.name.strip() if dto.name is not None else unit.name
        new_bu_id = dto.business_unit_id if dto.business_unit_id is not None else unit.business_unit_id

        if new_name != unit.name or new_bu_id != unit.business_unit_id:
            if await self._repo.exists_by_name_in_business_unit(new_name, new_bu_id, exclude_id=unit_id):
                raise DuplicateEntityError(ENTITY, "name", new_name)

        unit.name = new_name
        unit.business_unit_id = new_bu_id
        if dto.is_active is not None:
            unit.is_active = dto.is_active

        unit.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(unit))

    async def delete_unit(self, unit_id: int) -> None:
        await self._require(unit_id)
        await self._repo.delete(unit_id)

    async def _require(self, unit_id: int) -> Unit:
        unit = await self._repo.get_by_id(unit_id)
        if unit is None:
            raise EntityNotFoundError(ENTITY, unit_id)
        return unit

    @staticmethod
    def _to_dto(unit: Unit) -> UnitDTO:
        return UnitDTO(
            id=unit.id,
            name=unit.name,
            business_unit_id=unit.business_unit_id,
            is_active=unit.is_active,
            created_by=unit.created_by,
            created_date=unit.created_date,
            modified_by=unit.modified_by,
            modified_date=unit.modified_date,
        )
