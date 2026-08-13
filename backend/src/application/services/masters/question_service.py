"""Question Master — application service."""
from src.application.dtos.masters.question_dtos import CreateQuestionDTO, QuestionDTO, QuestionListDTO, UpdateQuestionDTO
from src.domain.entities.masters.question import Question
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.question_repository import IQuestionRepository

ENTITY = "Question"


class QuestionService:
    def __init__(self, repo: IQuestionRepository) -> None:
        self._repo = repo

    async def list_questions(self, skip=0, limit=100, search=None, is_active=None) -> QuestionListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return QuestionListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def get_question(self, question_id: int) -> QuestionDTO:
        return self._to_dto(await self._require(question_id))

    async def create_question(self, dto: CreateQuestionDTO, actor: User) -> QuestionDTO:
        if await self._repo.exists_by_title(dto.title):
            raise DuplicateEntityError(ENTITY, "title", dto.title)
        created = await self._repo.create(Question(
            title=dto.title.strip(), answer_type=dto.answer_type,
            has_text_box=dto.has_text_box, has_multiple_text_box=dto.has_multiple_text_box,
            has_sub_question=dto.has_sub_question, is_validation_required=dto.is_validation_required,
            has_response_option=dto.has_response_option, allow_multiple_input=dto.allow_multiple_input,
            has_associated_master=dto.has_associated_master, is_calculated=dto.is_calculated,
            is_active=dto.is_active, validation_type_id=dto.validation_type_id,
            parent_question_id=dto.parent_question_id, master_type=dto.master_type,
            sub_question_ids=dto.sub_question_ids,
            created_by=actor.username, modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_question(self, question_id: int, dto: UpdateQuestionDTO, actor: User) -> QuestionDTO:
        q = await self._require(question_id)
        if dto.title is not None and dto.title.strip() != q.title:
            if await self._repo.exists_by_title(dto.title, exclude_id=question_id):
                raise DuplicateEntityError(ENTITY, "title", dto.title)
            q.title = dto.title.strip()
        if dto.answer_type is not None: q.answer_type = dto.answer_type
        if dto.has_text_box is not None: q.has_text_box = dto.has_text_box
        if dto.has_multiple_text_box is not None: q.has_multiple_text_box = dto.has_multiple_text_box
        if dto.has_sub_question is not None: q.has_sub_question = dto.has_sub_question
        if dto.is_validation_required is not None: q.is_validation_required = dto.is_validation_required
        if dto.has_response_option is not None: q.has_response_option = dto.has_response_option
        if dto.allow_multiple_input is not None: q.allow_multiple_input = dto.allow_multiple_input
        if dto.has_associated_master is not None: q.has_associated_master = dto.has_associated_master
        if dto.is_calculated is not None: q.is_calculated = dto.is_calculated
        if dto.is_active is not None: q.is_active = dto.is_active
        if dto.validation_type_id is not None: q.validation_type_id = dto.validation_type_id
        if dto.parent_question_id is not None: q.parent_question_id = dto.parent_question_id
        if dto.master_type is not None: q.master_type = dto.master_type
        if dto.sub_question_ids is not None: q.sub_question_ids = dto.sub_question_ids
        q.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(q))

    async def delete_question(self, question_id: int) -> None:
        await self._require(question_id); await self._repo.delete(question_id)

    async def _require(self, question_id: int) -> Question:
        q = await self._repo.get_by_id(question_id)
        if q is None: raise EntityNotFoundError(ENTITY, question_id)
        return q

    @staticmethod
    def _to_dto(q: Question) -> QuestionDTO:
        return QuestionDTO(
            id=q.id, title=q.title, answer_type=q.answer_type,
            has_text_box=q.has_text_box, has_multiple_text_box=q.has_multiple_text_box,
            has_sub_question=q.has_sub_question, is_validation_required=q.is_validation_required,
            has_response_option=q.has_response_option, allow_multiple_input=q.allow_multiple_input,
            has_associated_master=q.has_associated_master, is_calculated=q.is_calculated,
            is_active=q.is_active, validation_type_id=q.validation_type_id,
            parent_question_id=q.parent_question_id, master_type=q.master_type,
            sub_question_ids=q.sub_question_ids,
            created_by=q.created_by, created_date=q.created_date,
            modified_by=q.modified_by, modified_date=q.modified_date,
        )
