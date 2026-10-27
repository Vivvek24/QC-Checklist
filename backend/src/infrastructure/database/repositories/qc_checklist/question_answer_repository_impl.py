"""QuestionAnswer — repository implementation."""

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import aliased

from src.domain.entities.qc_checklist.question_answer import QuestionAnswer
from src.domain.repositories.qc_checklist.question_answer_repository import (
    IQuestionAnswerRepository,
)
from src.infrastructure.database.models.qc_checklist.question_answer_helper_model import (
    QuestionAnswerHelperModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_model import (
    QuestionAnswerModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import (  # noqa: E501
    QuestionAnswerSubQuestionAnswerModel,
)
from src.infrastructure.database.models.user_details_model import UserDetailsModel
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class QuestionAnswerRepositoryImpl(
    SqlAlchemyRepository[QuestionAnswer, QuestionAnswerModel], IQuestionAnswerRepository
):
    _model = QuestionAnswerModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return QuestionAnswerModel.id == -1

    async def list_all(
        self, skip: int = 0, limit: int = 100,
        search: str | None = None, is_active: bool | None = None,
    ) -> list[QuestionAnswer]:
        stmt = (
            select(QuestionAnswerModel)
            .order_by(QuestionAnswerModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = select(func.count()).select_from(QuestionAnswerModel)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[QuestionAnswer]:
        stmt = select(QuestionAnswerModel).where(
            QuestionAnswerModel.checklist_stage_id == checklist_stage_id
        ).order_by(QuestionAnswerModel.serial_number)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_stage_question_mapping(
        self, stage_question_mapping_id: int
    ) -> list[QuestionAnswer]:
        stmt = select(QuestionAnswerModel).where(
            QuestionAnswerModel.stage_question_mapping_id == stage_question_mapping_id
        ).order_by(QuestionAnswerModel.serial_number)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete_sub_answers_by_parent(self, parent_question_answer_id: int) -> None:
        link_result = await self._session.execute(
            select(QuestionAnswerSubQuestionAnswerModel).where(
                QuestionAnswerSubQuestionAnswerModel.question_answer_parent_id
                == parent_question_answer_id
            )
        )
        links = link_result.scalars().all()
        child_ids = [link.question_answer_id for link in links]
        for link in links:
            await self._session.delete(link)
        if child_ids:
            old_children = await self._session.execute(
                select(QuestionAnswerModel).where(QuestionAnswerModel.id.in_(child_ids))
            )
            for child in old_children.scalars().all():
                await self._session.delete(child)
        await self._session.flush()

    async def link_sub_answer(
        self, parent_question_answer_id: int, child_question_answer_id: int, actor: str
    ) -> None:
        self._session.add(QuestionAnswerSubQuestionAnswerModel(
            question_answer_id=child_question_answer_id,
            question_answer_parent_id=parent_question_answer_id,
            created_by=actor,
            modified_by=actor,
        ))
        await self._session.flush()

    async def create(self, entity: QuestionAnswer) -> QuestionAnswer:
        model = QuestionAnswerModel(
            checklist_stage_id=entity.checklist_stage_id,
            checklist_stage_section_id=entity.checklist_stage_section_id,
            product_id=entity.product_id,
            question_id=entity.question_id,
            question_option_id=entity.question_option_id,
            receiver_user_id=entity.receiver_user_id,
            response_question_option_id=entity.response_question_option_id,
            stage_question_mapping_id=entity.stage_question_mapping_id,
            textbox_value=entity.textbox_value,
            response_answer=entity.response_answer,
            comma_separated_name=entity.comma_separated_name,
            has_helper=entity.has_helper,
            serial_number=entity.serial_number,
            sub_answer_serial_no=entity.sub_answer_serial_no,
            date_time=entity.date_time,
            test_title=entity.test_title,
            sample_vails=entity.sample_vails,
            answer_total_vails=entity.answer_total_vails,
            issued_by_date=entity.issued_by_date,
            received_by_date=entity.received_by_date,
            issuer_name=entity.issuer_name,
            is_issued_vails=entity.is_issued_vails,
            has_vails=entity.has_vails,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: QuestionAnswer) -> QuestionAnswer:
        model = await self._require_model(entity.id)
        model.checklist_stage_id = entity.checklist_stage_id
        model.checklist_stage_section_id = entity.checklist_stage_section_id
        model.product_id = entity.product_id
        model.question_id = entity.question_id
        model.question_option_id = entity.question_option_id
        model.receiver_user_id = entity.receiver_user_id
        model.response_question_option_id = entity.response_question_option_id
        model.stage_question_mapping_id = entity.stage_question_mapping_id
        model.textbox_value = entity.textbox_value
        model.response_answer = entity.response_answer
        model.comma_separated_name = entity.comma_separated_name
        model.has_helper = entity.has_helper
        model.serial_number = entity.serial_number
        model.sub_answer_serial_no = entity.sub_answer_serial_no
        model.date_time = entity.date_time
        model.test_title = entity.test_title
        model.sample_vails = entity.sample_vails
        model.answer_total_vails = entity.answer_total_vails
        model.issued_by_date = entity.issued_by_date
        model.received_by_date = entity.received_by_date
        model.issuer_name = entity.issuer_name
        model.is_issued_vails = entity.is_issued_vails
        model.has_vails = entity.has_vails
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    async def list_sub_answers_grouped(
        self, checklist_stage_id: int
    ) -> dict[int, list[tuple[int, int | None, int | None, str, str]]]:
        parent = aliased(QuestionAnswerModel)
        child = aliased(QuestionAnswerModel)
        stmt = (
            select(
                parent.question_id,
                child.question_id,
                child.question_option_id,
                child.response_question_option_id,
                child.textbox_value,
                child.response_answer,
            )
            .select_from(QuestionAnswerSubQuestionAnswerModel)
            .join(
                parent,
                parent.id == QuestionAnswerSubQuestionAnswerModel.question_answer_parent_id,
            )
            .join(child, child.id == QuestionAnswerSubQuestionAnswerModel.question_answer_id)
            .where(parent.checklist_stage_id == checklist_stage_id)
            .order_by(parent.question_id, child.id)
        )
        rows = (await self._session.execute(stmt)).all()
        grouped: dict[int, list[tuple[int, int | None, int | None, str, str]]] = {}
        for parent_qid, qid, opt_id, resp_opt_id, textbox, resp_answer in rows:
            grouped.setdefault(parent_qid, []).append(
                (qid, opt_id, resp_opt_id, textbox or "", resp_answer or "")
            )
        return grouped

    async def resolve_user_names(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = (await self._session.execute(
            select(UserModel.id, UserModel.username, UserDetailsModel.employee_name)
            .outerjoin(UserDetailsModel, UserDetailsModel.user_id == UserModel.id)
            .where(UserModel.id.in_(user_ids))
        )).all()
        return {r.id: (r.employee_name or r.username or "") for r in rows}

    async def list_helpers_by_answer_ids(
        self, answer_ids: list[int]
    ) -> dict[int, list[str]]:
        if not answer_ids:
            return {}
        rows = (await self._session.execute(
            select(
                QuestionAnswerHelperModel.question_answer_id,
                QuestionAnswerHelperModel.text_box_value,
            )
            .where(QuestionAnswerHelperModel.question_answer_id.in_(answer_ids))
            .order_by(QuestionAnswerHelperModel.id)
        )).all()
        out: dict[int, list[str]] = {}
        for answer_id, value in rows:
            out.setdefault(answer_id, []).append(value or "")
        return out

    @staticmethod
    def _to_entity(model: QuestionAnswerModel) -> QuestionAnswer:
        return QuestionAnswer(
            id=model.id,
            checklist_stage_id=model.checklist_stage_id,
            checklist_stage_section_id=model.checklist_stage_section_id,
            product_id=model.product_id,
            question_id=model.question_id,
            question_option_id=model.question_option_id,
            receiver_user_id=model.receiver_user_id,
            response_question_option_id=model.response_question_option_id,
            stage_question_mapping_id=model.stage_question_mapping_id,
            textbox_value=model.textbox_value,
            response_answer=model.response_answer,
            comma_separated_name=model.comma_separated_name,
            has_helper=model.has_helper,
            serial_number=model.serial_number,
            sub_answer_serial_no=model.sub_answer_serial_no,
            date_time=model.date_time,
            test_title=model.test_title,
            sample_vails=model.sample_vails,
            answer_total_vails=model.answer_total_vails,
            issued_by_date=model.issued_by_date,
            received_by_date=model.received_by_date,
            issuer_name=model.issuer_name,
            is_issued_vails=model.is_issued_vails,
            has_vails=model.has_vails,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
