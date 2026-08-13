"""QuestionOption Master — application service."""

from src.application.dtos.masters.question_option_dtos import (
    CreateQuestionOptionDTO,
    QuestionOptionDTO,
    QuestionOptionListDTO,
    UpdateQuestionOptionDTO,
)
from src.domain.entities.masters.question_option import QuestionOption
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.question_option_repository import IQuestionOptionRepository

ENTITY = "QuestionOption"


class QuestionOptionService:
    def __init__(self, repo: IQuestionOptionRepository) -> None:
        self._repo = repo

    async def list_question_options(
        self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None
    ) -> QuestionOptionListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return QuestionOptionListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_question(self, question_id: int) -> list[QuestionOptionDTO]:
        items = await self._repo.list_by_question(question_id)
        return [self._to_dto(i) for i in items]

    async def get_question_option(self, option_id: int) -> QuestionOptionDTO:
        return self._to_dto(await self._require(option_id))

    async def create_question_option(self, dto: CreateQuestionOptionDTO, actor: User) -> QuestionOptionDTO:
        if await self._repo.exists_by_title_for_question(dto.option_title, dto.question_id):
            raise DuplicateEntityError(ENTITY, "option_title", dto.option_title)
        created = await self._repo.create(QuestionOption(
            option_title=dto.option_title.strip(),
            is_response_option=dto.is_response_option,
            question_id=dto.question_id,
            is_active=dto.is_active,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_question_option(self, option_id: int, dto: UpdateQuestionOptionDTO, actor: User) -> QuestionOptionDTO:
        opt = await self._require(option_id)
        question_id = dto.question_id if dto.question_id is not None else opt.question_id
        if dto.option_title is not None and dto.option_title.strip() != opt.option_title:
            if await self._repo.exists_by_title_for_question(dto.option_title, question_id, exclude_id=option_id):
                raise DuplicateEntityError(ENTITY, "option_title", dto.option_title)
            opt.option_title = dto.option_title.strip()
        if dto.is_response_option is not None:
            opt.is_response_option = dto.is_response_option
        if dto.question_id is not None:
            opt.question_id = dto.question_id
        if dto.is_active is not None:
            opt.is_active = dto.is_active
        opt.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(opt))

    async def delete_question_option(self, option_id: int) -> None:
        await self._require(option_id)
        await self._repo.delete(option_id)

    async def _require(self, option_id: int) -> QuestionOption:
        opt = await self._repo.get_by_id(option_id)
        if opt is None:
            raise EntityNotFoundError(ENTITY, option_id)
        return opt

    @staticmethod
    def _to_dto(o: QuestionOption) -> QuestionOptionDTO:
        return QuestionOptionDTO(
            id=o.id,
            option_title=o.option_title,
            is_response_option=o.is_response_option,
            question_id=o.question_id,
            is_active=o.is_active,
            created_by=o.created_by,
            created_date=o.created_date,
            modified_by=o.modified_by,
            modified_date=o.modified_date,
        )
