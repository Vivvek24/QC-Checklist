"""QuestionAnswerHelper — application service."""

from src.application.dtos.qc_checklist.question_answer_helper_dtos import (
    CreateQuestionAnswerHelperDTO,
    QuestionAnswerHelperDTO,
    QuestionAnswerHelperListDTO,
    UpdateQuestionAnswerHelperDTO,
)
from src.domain.entities.qc_checklist.question_answer_helper import QuestionAnswerHelper
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.qc_checklist.question_answer_helper_repository import IQuestionAnswerHelperRepository

ENTITY = "QuestionAnswerHelper"


class QuestionAnswerHelperService:
    def __init__(self, repo: IQuestionAnswerHelperRepository) -> None:
        self._repo = repo

    async def list_helpers(self, skip: int = 0, limit: int = 100) -> QuestionAnswerHelperListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit)
        total = await self._repo.count()
        return QuestionAnswerHelperListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_question_answer(self, question_answer_id: int) -> list[QuestionAnswerHelperDTO]:
        items = await self._repo.list_by_question_answer(question_answer_id)
        return [self._to_dto(i) for i in items]

    async def get_helper(self, helper_id: int) -> QuestionAnswerHelperDTO:
        return self._to_dto(await self._require(helper_id))

    async def create_helper(self, dto: CreateQuestionAnswerHelperDTO, actor: User) -> QuestionAnswerHelperDTO:
        created = await self._repo.create(QuestionAnswerHelper(
            text_box_value=dto.text_box_value,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_helper(self, helper_id: int, dto: UpdateQuestionAnswerHelperDTO, actor: User) -> QuestionAnswerHelperDTO:
        entity = await self._require(helper_id)
        if dto.text_box_value is not None:
            entity.text_box_value = dto.text_box_value
        entity.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(entity))

    async def delete_helper(self, helper_id: int) -> None:
        await self._require(helper_id)
        await self._repo.delete(helper_id)

    async def _require(self, helper_id: int) -> QuestionAnswerHelper:
        entity = await self._repo.get_by_id(helper_id)
        if entity is None:
            raise EntityNotFoundError(ENTITY, helper_id)
        return entity

    @staticmethod
    def _to_dto(e: QuestionAnswerHelper) -> QuestionAnswerHelperDTO:
        return QuestionAnswerHelperDTO(
            id=e.id,
            text_box_value=e.text_box_value,
            created_by=e.created_by,
            created_date=e.created_date,
            modified_by=e.modified_by,
            modified_date=e.modified_date,
        )
