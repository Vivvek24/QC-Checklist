"""QuestionAnswer — application service."""

from src.application.dtos.qc_checklist.question_answer_dtos import (
    CreateQuestionAnswerDTO,
    QuestionAnswerDTO,
    QuestionAnswerListDTO,
    UpdateQuestionAnswerDTO,
)
from src.domain.entities.qc_checklist.question_answer import QuestionAnswer
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.qc_checklist.question_answer_repository import IQuestionAnswerRepository

ENTITY = "QuestionAnswer"


class QuestionAnswerService:
    def __init__(self, repo: IQuestionAnswerRepository) -> None:
        self._repo = repo

    async def list_answers(self, skip: int = 0, limit: int = 100) -> QuestionAnswerListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit)
        total = await self._repo.count()
        return QuestionAnswerListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[QuestionAnswerDTO]:
        items = await self._repo.list_by_checklist_stage(checklist_stage_id)
        return [self._to_dto(i) for i in items]

    async def list_by_stage_question_mapping(self, stage_question_mapping_id: int) -> list[QuestionAnswerDTO]:
        items = await self._repo.list_by_stage_question_mapping(stage_question_mapping_id)
        return [self._to_dto(i) for i in items]

    async def get_answer(self, answer_id: int) -> QuestionAnswerDTO:
        return self._to_dto(await self._require(answer_id))

    async def create_answer(self, dto: CreateQuestionAnswerDTO, actor: User) -> QuestionAnswerDTO:
        created = await self._repo.create(QuestionAnswer(
            checklist_stage_id=dto.checklist_stage_id,
            checklist_stage_section_id=dto.checklist_stage_section_id,
            product_id=dto.product_id,
            question_id=dto.question_id,
            question_option_id=dto.question_option_id,
            receiver_user_id=dto.receiver_user_id,
            response_question_option_id=dto.response_question_option_id,
            stage_question_mapping_id=dto.stage_question_mapping_id,
            textbox_value=dto.textbox_value,
            response_answer=dto.response_answer,
            comma_separated_name=dto.comma_separated_name,
            has_helper=dto.has_helper,
            serial_number=dto.serial_number,
            sub_answer_serial_no=dto.sub_answer_serial_no,
            date_time=dto.date_time,
            test_title=dto.test_title,
            sample_vails=dto.sample_vails,
            answer_total_vails=dto.answer_total_vails,
            issued_by_date=dto.issued_by_date,
            received_by_date=dto.received_by_date,
            issuer_name=dto.issuer_name,
            is_issued_vails=dto.is_issued_vails,
            has_vails=dto.has_vails,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_answer(self, answer_id: int, dto: UpdateQuestionAnswerDTO, actor: User) -> QuestionAnswerDTO:
        entity = await self._require(answer_id)
        if dto.checklist_stage_section_id is not None:
            entity.checklist_stage_section_id = dto.checklist_stage_section_id
        if dto.product_id is not None:
            entity.product_id = dto.product_id
        if dto.question_id is not None:
            entity.question_id = dto.question_id
        if dto.question_option_id is not None:
            entity.question_option_id = dto.question_option_id
        if dto.receiver_user_id is not None:
            entity.receiver_user_id = dto.receiver_user_id
        if dto.response_question_option_id is not None:
            entity.response_question_option_id = dto.response_question_option_id
        if dto.stage_question_mapping_id is not None:
            entity.stage_question_mapping_id = dto.stage_question_mapping_id
        if dto.textbox_value is not None:
            entity.textbox_value = dto.textbox_value
        if dto.response_answer is not None:
            entity.response_answer = dto.response_answer
        if dto.comma_separated_name is not None:
            entity.comma_separated_name = dto.comma_separated_name
        if dto.has_helper is not None:
            entity.has_helper = dto.has_helper
        if dto.serial_number is not None:
            entity.serial_number = dto.serial_number
        if dto.sub_answer_serial_no is not None:
            entity.sub_answer_serial_no = dto.sub_answer_serial_no
        if dto.date_time is not None:
            entity.date_time = dto.date_time
        if dto.test_title is not None:
            entity.test_title = dto.test_title
        if dto.sample_vails is not None:
            entity.sample_vails = dto.sample_vails
        if dto.answer_total_vails is not None:
            entity.answer_total_vails = dto.answer_total_vails
        if dto.issued_by_date is not None:
            entity.issued_by_date = dto.issued_by_date
        if dto.received_by_date is not None:
            entity.received_by_date = dto.received_by_date
        if dto.issuer_name is not None:
            entity.issuer_name = dto.issuer_name
        if dto.is_issued_vails is not None:
            entity.is_issued_vails = dto.is_issued_vails
        if dto.has_vails is not None:
            entity.has_vails = dto.has_vails
        entity.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(entity))

    async def delete_answer(self, answer_id: int) -> None:
        await self._require(answer_id)
        await self._repo.delete(answer_id)

    async def _require(self, answer_id: int) -> QuestionAnswer:
        entity = await self._repo.get_by_id(answer_id)
        if entity is None:
            raise EntityNotFoundError(ENTITY, answer_id)
        return entity

    @staticmethod
    def _to_dto(e: QuestionAnswer) -> QuestionAnswerDTO:
        return QuestionAnswerDTO(
            id=e.id,
            checklist_stage_id=e.checklist_stage_id,
            checklist_stage_section_id=e.checklist_stage_section_id,
            product_id=e.product_id,
            question_id=e.question_id,
            question_option_id=e.question_option_id,
            receiver_user_id=e.receiver_user_id,
            response_question_option_id=e.response_question_option_id,
            stage_question_mapping_id=e.stage_question_mapping_id,
            textbox_value=e.textbox_value,
            response_answer=e.response_answer,
            comma_separated_name=e.comma_separated_name,
            has_helper=e.has_helper,
            serial_number=e.serial_number,
            sub_answer_serial_no=e.sub_answer_serial_no,
            date_time=e.date_time,
            test_title=e.test_title,
            sample_vails=e.sample_vails,
            answer_total_vails=e.answer_total_vails,
            issued_by_date=e.issued_by_date,
            received_by_date=e.received_by_date,
            issuer_name=e.issuer_name,
            is_issued_vails=e.is_issued_vails,
            has_vails=e.has_vails,
            created_by=e.created_by,
            created_date=e.created_date,
            modified_by=e.modified_by,
            modified_date=e.modified_date,
        )
