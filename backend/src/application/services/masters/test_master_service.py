"""TestMaster — application service."""

from src.application.dtos.masters.test_master_dtos import (
    CreateTestMasterDTO,
    TestMasterDTO,
    TestMasterListDTO,
    UpdateTestMasterDTO,
)
from src.domain.entities.masters.test_master import TestMaster
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.test_master_repository import ITestMasterRepository

ENTITY = "TestMaster"


class TestMasterService:
    def __init__(self, repo: ITestMasterRepository) -> None:
        self._repo = repo

    async def list_tests(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> TestMasterListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return TestMasterListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_product(self, product_id: int) -> list[TestMasterDTO]:
        items = await self._repo.list_by_product(product_id)
        return [self._to_dto(i) for i in items]

    async def get_test(self, test_id: int) -> TestMasterDTO:
        return self._to_dto(await self._require(test_id))

    async def create_test(self, dto: CreateTestMasterDTO, actor: User) -> TestMasterDTO:
        if await self._repo.exists_by_name(dto.test_name):
            raise DuplicateEntityError(ENTITY, "test_name", dto.test_name)
        created = await self._repo.create(TestMaster(
            test_name=dto.test_name.strip(),
            no_of_samples_issued=dto.no_of_samples_issued,
            sample_qty=dto.sample_qty,
            product_id=dto.product_id,
            is_active=dto.is_active,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_test(self, test_id: int, dto: UpdateTestMasterDTO, actor: User) -> TestMasterDTO:
        test = await self._require(test_id)
        if dto.test_name is not None and dto.test_name.strip() != test.test_name:
            if await self._repo.exists_by_name(dto.test_name, exclude_id=test_id):
                raise DuplicateEntityError(ENTITY, "test_name", dto.test_name)
            test.test_name = dto.test_name.strip()
        if dto.no_of_samples_issued is not None:
            test.no_of_samples_issued = dto.no_of_samples_issued
        if dto.sample_qty is not None:
            test.sample_qty = dto.sample_qty
        if dto.product_id is not None:
            test.product_id = dto.product_id
        if dto.is_active is not None:
            test.is_active = dto.is_active
        test.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(test))

    async def delete_test(self, test_id: int) -> None:
        await self._require(test_id)
        await self._repo.delete(test_id)

    async def _require(self, test_id: int) -> TestMaster:
        t = await self._repo.get_by_id(test_id)
        if t is None:
            raise EntityNotFoundError(ENTITY, test_id)
        return t

    @staticmethod
    def _to_dto(t: TestMaster) -> TestMasterDTO:
        return TestMasterDTO(
            id=t.id,
            test_name=t.test_name,
            no_of_samples_issued=t.no_of_samples_issued,
            sample_qty=t.sample_qty,
            product_id=t.product_id,
            is_active=t.is_active,
            created_by=t.created_by,
            created_date=t.created_date,
            modified_by=t.modified_by,
            modified_date=t.modified_date,
        )
