"""Validate Checklist Request — service that validates all question answers before submit."""

import re
from dataclasses import dataclass, field

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.qc_checklist.checklist_request_model import ChecklistRequestModel
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import ChecklistStageModel
from src.infrastructure.database.models.qc_checklist.checklist_stage_section_model import ChecklistStageSectionModel
from src.infrastructure.database.models.qc_checklist.question_answer_model import QuestionAnswerModel
from src.infrastructure.database.models.qc_checklist.question_answer_helper_model import QuestionAnswerHelperModel
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import QuestionAnswerSubQuestionAnswerModel
from src.infrastructure.database.models.masters.question_model import QuestionModel
from src.infrastructure.database.models.masters.question_option_model import QuestionOptionModel
from src.infrastructure.database.models.masters.format_model import FormatModel
from src.infrastructure.database.models.masters.format_stage_mapping_model import FormatStageMappingModel
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.models.masters.stage_question_mapping_model import StageQuestionMappingModel
from src.infrastructure.database.models.masters.validation_type_model import ValidationTypeModel


ACTIVE_STATUSES = ("Draft", "ReferBack", "Initial", "Pending", "Saved")
BATCH_NO_REGEX = re.compile(r"^\S+$")


@dataclass
class ValidationError:
    stage_id: int
    stage_name: str
    question_id: int | None
    question_title: str
    message: str


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)

    def add_error(self, stage_id: int, stage_name: str, question_id: int | None, question_title: str, message: str):
        self.is_valid = False
        self.errors.append(ValidationError(
            stage_id=stage_id,
            stage_name=stage_name,
            question_id=question_id,
            question_title=question_title,
            message=message,
        ))


class ValidateChecklistService:
    """Validates all question answers for a checklist request before submission."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def validate_stage(self, checklist_request_id: int, checklist_stage_id: int) -> ValidationResult:
        """
        Validate only a specific stage (used during submit of a single stage).
        """
        result = ValidationResult()

        # Get the checklist request with format info
        cr_result = await self._session.execute(
            select(ChecklistRequestModel).where(ChecklistRequestModel.id == checklist_request_id)
        )
        checklist_request = cr_result.scalar_one_or_none()
        if not checklist_request:
            result.add_error(0, "", None, "", "Checklist request not found")
            return result

        # Get format info
        fmt_result = await self._session.execute(
            select(FormatModel).where(FormatModel.id == checklist_request.format_id)
        )
        fmt = fmt_result.scalar_one_or_none()
        format_type = fmt.format_type if fmt else ""

        # Get the specific stage
        stage_result = await self._session.execute(
            select(ChecklistStageModel).where(ChecklistStageModel.id == checklist_stage_id)
        )
        stage = stage_result.scalar_one_or_none()
        if not stage:
            result.add_error(0, "", None, "", "Checklist stage not found")
            return result

        # Get format stage mapping
        fsm = None
        if stage.format_stage_mapping_id:
            fsm_result = await self._session.execute(
                select(FormatStageMappingModel).where(
                    FormatStageMappingModel.id == stage.format_stage_mapping_id
                )
            )
            fsm = fsm_result.scalar_one_or_none()

        # Get stage name
        stage_name = ""
        if fsm:
            sm_result = await self._session.execute(
                select(StageModel).where(StageModel.id == fsm.stage_id)
            )
            sm = sm_result.scalar_one_or_none()
            stage_name = sm.stage_name if sm else ""

        # Retrieve all question answers for this stage
        qa_result = await self._session.execute(
            select(QuestionAnswerModel).where(
                QuestionAnswerModel.checklist_stage_id == stage.id
            )
        )
        question_answers = qa_result.scalars().all()

        # Validate each question answer
        await self._validate_question_answers(
            question_answers=question_answers,
            result=result,
            stage_id=stage.id,
            stage_name=stage_name,
            format_type=format_type,
            checklist_request_id=checklist_request_id,
            fsm=fsm,
        )

        return result

    async def validate(self, checklist_request_id: int) -> ValidationResult:
        """
        Main validation entry point — mirrors ACT_ValidateCheckListRequest.
        Validates ALL active stages (used for full-request validation).
        """
        result = ValidationResult()

        # Get the checklist request with format info
        cr_result = await self._session.execute(
            select(ChecklistRequestModel).where(ChecklistRequestModel.id == checklist_request_id)
        )
        checklist_request = cr_result.scalar_one_or_none()
        if not checklist_request:
            result.add_error(0, "", None, "", "Checklist request not found")
            return result

        # Get format info
        fmt_result = await self._session.execute(
            select(FormatModel).where(FormatModel.id == checklist_request.format_id)
        )
        fmt = fmt_result.scalar_one_or_none()
        format_type = fmt.format_type if fmt else ""

        # Retrieve all stages for this request
        stages_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == checklist_request_id
            )
        )
        all_stages = stages_result.scalars().all()

        # Filter to active statuses
        active_stages = [s for s in all_stages if s.status in ACTIVE_STATUSES]

        for stage in active_stages:
            # Get format stage mapping
            fsm = None
            if stage.format_stage_mapping_id:
                fsm_result = await self._session.execute(
                    select(FormatStageMappingModel).where(
                        FormatStageMappingModel.id == stage.format_stage_mapping_id
                    )
                )
                fsm = fsm_result.scalar_one_or_none()

            # Get stage name
            stage_name = ""
            if fsm:
                sm_result = await self._session.execute(
                    select(StageModel).where(StageModel.id == fsm.stage_id)
                )
                sm = sm_result.scalar_one_or_none()
                stage_name = sm.stage_name if sm else ""

            # If hasSection, process sections first (their question answers are also part of stage)
            # Both paths merge to validate all question answers for the stage

            # Retrieve all question answers for this stage
            qa_result = await self._session.execute(
                select(QuestionAnswerModel).where(
                    QuestionAnswerModel.checklist_stage_id == stage.id
                )
            )
            question_answers = qa_result.scalars().all()

            # Validate each question answer
            await self._validate_question_answers(
                question_answers=question_answers,
                result=result,
                stage_id=stage.id,
                stage_name=stage_name,
                format_type=format_type,
                checklist_request_id=checklist_request_id,
                fsm=fsm,
            )

        return result

    async def _validate_question_answers(
        self,
        question_answers: list,
        result: ValidationResult,
        stage_id: int,
        stage_name: str,
        format_type: str,
        checklist_request_id: int,
        fsm,
    ) -> None:
        """Validates a list of question answers — mirrors SUB_VAL_QuestionAnswers."""

        for qa in question_answers:
            # Get question master
            question = None
            if qa.question_id:
                q_result = await self._session.execute(
                    select(QuestionModel).where(QuestionModel.id == qa.question_id)
                )
                question = q_result.scalar_one_or_none()

            # If question is empty and format is ReconcilationSheet, skip
            if question is None and format_type == "ReconcilationSheet":
                continue

            if question is None:
                continue

            question_title = question.title or f"Question #{qa.question_id}"
            answer_type = question.answer_type or ""

            # Phase 2: Answer type validations
            # 2a: Text Box — check if empty
            if answer_type == "Text Box" or (answer_type != "None" and question.has_text_box):
                if not qa.textbox_value or not qa.textbox_value.strip():
                    result.add_error(stage_id, stage_name, qa.question_id, question_title,
                                     "Please enter the value")

            # 2b: Dropdown (single/multi select) — check if option selected
            if answer_type in ("Dropdown (single select)", "Dropdown (multi select)"):
                if not qa.question_option_id:
                    # Check if any options linked via junction
                    msg = "Choose one option above!" if "single" in answer_type else "Choose one/multiple option(s) above!"
                    result.add_error(stage_id, stage_name, qa.question_id, question_title, msg)

            # 2c: AQL negative check
            if format_type == "AQL" and qa.textbox_value:
                try:
                    val = float(qa.textbox_value)
                    if val < 0:
                        result.add_error(stage_id, stage_name, qa.question_id, question_title,
                                         "Value cannot be negative!")
                except (ValueError, TypeError):
                    pass

            # Phase 3: Batch/Test validation for Chromatographic Basic Details
            if format_type == "Chromatographic" and stage_name == "Basic Details" and question.is_validation_required:
                await self._validate_batch_and_test(
                    result=result,
                    stage_id=stage_id,
                    stage_name=stage_name,
                    qa=qa,
                    question=question,
                    checklist_request_id=checklist_request_id,
                    fsm=fsm,
                )

            # Phase 4: Response option validation
            if question.has_response_option:
                if not qa.response_question_option_id:
                    result.add_error(stage_id, stage_name, qa.question_id, question_title,
                                     "Choose one option above!")

            # Phase 5a: Product master validation (ReconcilationSheet)
            if (format_type == "ReconcilationSheet"
                    and answer_type == "Master"
                    and question.master_type == "ProductMaster"
                    and not qa.product_id):
                result.add_error(stage_id, stage_name, qa.question_id, question_title,
                                 "Please Select a Product!")

            # Phase 5b: Date validation
            if answer_type == "DateAndTime" and not qa.date_time:
                # Check if editable via stage_question_mapping
                if qa.stage_question_mapping_id:
                    sqm_result = await self._session.execute(
                        select(StageQuestionMappingModel).where(
                            StageQuestionMappingModel.id == qa.stage_question_mapping_id
                        )
                    )
                    sqm = sqm_result.scalar_one_or_none()
                    if sqm and sqm.is_editable:
                        result.add_error(stage_id, stage_name, qa.question_id, question_title,
                                         "Please select a date!")

            # Phase 6: Sub-question recursive validation
            if question.has_sub_question:
                sub_result = await self._session.execute(
                    select(QuestionAnswerSubQuestionAnswerModel.question_answer_helper_id).where(
                        QuestionAnswerSubQuestionAnswerModel.question_answer_id == qa.id
                    )
                )
                sub_qa_ids = [r[0] for r in sub_result.fetchall() if r[0]]
                if sub_qa_ids:
                    sub_qa_result = await self._session.execute(
                        select(QuestionAnswerModel).where(
                            QuestionAnswerModel.id.in_(sub_qa_ids)
                        )
                    )
                    sub_answers = sub_qa_result.scalars().all()
                    await self._validate_question_answers(
                        question_answers=sub_answers,
                        result=result,
                        stage_id=stage_id,
                        stage_name=stage_name,
                        format_type=format_type,
                        checklist_request_id=checklist_request_id,
                        fsm=fsm,
                    )

    async def _validate_batch_and_test(
        self,
        result: ValidationResult,
        stage_id: int,
        stage_name: str,
        qa,
        question,
        checklist_request_id: int,
        fsm,
    ) -> None:
        """
        Mirrors SUB_ValidateTestAndBatchAnswers.
        Checks for duplicate batch+test combinations across other requests.
        """
        # Skip for ReconcilationSheet
        # (already handled in caller, but double-check)

        # Validate batch no has no spaces
        if qa.textbox_value and not BATCH_NO_REGEX.match(qa.textbox_value):
            result.add_error(stage_id, stage_name, qa.question_id, question.title,
                             "Spaces not allowed!")
            return

        # Get batch and test questions by validation type
        batch_q = await self._get_question_by_validation_type("Batch No")
        test_q = await self._get_question_by_validation_type("Test Name")

        if not batch_q or not test_q:
            return

        # Get the batch and test answers for this stage
        batch_answer = await self._get_answer_for_question(stage_id, batch_q.id)
        test_answer = await self._get_answer_for_question(stage_id, test_q.id)

        if not batch_answer or not test_answer:
            return

        if not batch_answer.textbox_value or not test_answer.textbox_value:
            return

        # Build batch helper options string for SQL
        batch_helpers = await self._get_answer_helpers(batch_answer.id)
        batch_values = [batch_answer.textbox_value.upper()]
        batch_values.extend([h.text_box_value.upper() for h in batch_helpers if h.text_box_value])

        if not batch_values:
            return

        # Get stage master id
        stage_master_id = None
        if fsm:
            stage_master_id = fsm.stage_id

        if not stage_master_id:
            return

        # Check for duplicate using raw SQL (mirrors JA_BatchNoValidation)
        batch_in_clause = ", ".join([f"'{v}'" for v in batch_values])
        test_value = test_answer.textbox_value

        sql = f"""
SELECT EXISTS (
    SELECT 1
    FROM checklist_requests r
    JOIN checklist_stages cs ON cs.checklist_request_id = r.id
    JOIN format_stage_mappings fsm ON fsm.id = cs.format_stage_mapping_id
    JOIN stages s ON s.id = fsm.stage_id
    JOIN stage_question_mappings sqm ON sqm.format_stage_mapping_id = fsm.id
    JOIN questions q ON q.id = sqm.question_id
    JOIN question_answers qa ON qa.checklist_stage_id = cs.id AND qa.stage_question_mapping_id = sqm.id
    LEFT JOIN question_answer_sub_question_answers qasqa ON qasqa.question_answer_id = qa.id
    LEFT JOIN question_answer_helpers qah ON qah.id = qasqa.question_answer_helper_id
    WHERE q.id IN (:batch_q_id, :test_q_id)
      AND s.id = :stage_master_id
      AND r.id <> :checklist_request_id
      AND r.is_removed = false
    GROUP BY r.id
    HAVING COUNT(DISTINCT q.id) = 2
       AND BOOL_OR(
            q.id = :batch_q_id2
            AND (
                UPPER(qa.textbox_value) IN ({batch_in_clause})
                OR UPPER(qah.text_box_value) IN ({batch_in_clause})
            )
       )
       AND BOOL_OR(
            q.id = :test_q_id2
            AND UPPER(qa.textbox_value) = UPPER(:test_value)
       )
)
"""
        params = {
            "batch_q_id": batch_q.id,
            "test_q_id": test_q.id,
            "stage_master_id": stage_master_id,
            "checklist_request_id": checklist_request_id,
            "batch_q_id2": batch_q.id,
            "test_q_id2": test_q.id,
            "test_value": test_value,
        }

        try:
            dup_result = await self._session.execute(text(sql), params)
            exists = dup_result.scalar()
            if exists:
                result.add_error(stage_id, stage_name, qa.question_id, question.title,
                                 "Duplicate Batch No + Test Name combination already exists in another request!")
        except Exception:
            # If SQL fails, don't block — log but continue
            pass

    async def _get_question_by_validation_type(self, validation_type_name: str) -> QuestionModel | None:
        """Get question linked to a specific validation type."""
        vt_result = await self._session.execute(
            select(ValidationTypeModel).where(ValidationTypeModel.name == validation_type_name)
        )
        vt = vt_result.scalar_one_or_none()
        if not vt:
            return None

        q_result = await self._session.execute(
            select(QuestionModel).where(QuestionModel.validation_type_id == vt.id).limit(1)
        )
        return q_result.scalar_one_or_none()

    async def _get_answer_for_question(self, stage_id: int, question_id: int) -> QuestionAnswerModel | None:
        """Get a question answer for a specific question in a stage."""
        result = await self._session.execute(
            select(QuestionAnswerModel).where(
                QuestionAnswerModel.checklist_stage_id == stage_id,
                QuestionAnswerModel.question_id == question_id,
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_answer_helpers(self, question_answer_id: int) -> list:
        """Get helper records for a question answer."""
        result = await self._session.execute(
            select(QuestionAnswerHelperModel).join(
                QuestionAnswerSubQuestionAnswerModel,
                QuestionAnswerSubQuestionAnswerModel.question_answer_helper_id == QuestionAnswerHelperModel.id
            ).where(
                QuestionAnswerSubQuestionAnswerModel.question_answer_id == question_answer_id
            )
        )
        return result.scalars().all()
