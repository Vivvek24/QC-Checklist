"""Issue Vials — application service.

Ports the Mendix "Issue Vials" save microflow for a recon-sheet test row:

  1. The answer must have a receiver (analyst) selected. If not, the caller
     surfaces the inline "Please Select Analyst Name!" validation — this service
     raises a BusinessRuleViolationError so the API returns 400.
  2. Find the request's Basic Details stage and its StartDate answer (the
     mapping whose custom_answers = 'StartDate'). If that answer's date_time is
     empty, stamp it with the current date/time (analysis start date).
  3. Stamp the clicked answer: issued_by_date = now, is_issued_vails = true,
     issuer_name = the acting user's full name, received_by_date = now.

Commit is NOT done here — get_db_session commits once per request.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums.custom_answer_enum import CustomAnswer
from src.domain.exceptions.domain_exceptions import (
    BusinessRuleViolationError,
    EntityNotFoundError,
)
from src.infrastructure.database.models.masters.format_stage_mapping_model import (
    FormatStageMappingModel,
)
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.models.masters.question_model import QuestionModel
from src.infrastructure.database.models.masters.stage_question_mapping_model import (
    StageQuestionMappingModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import (
    ChecklistStageModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_model import (
    QuestionAnswerModel,
)
from src.infrastructure.database.models.user_details_model import UserDetailsModel
from src.infrastructure.database.models.user_model import UserModel

BASIC_DETAILS = "Basic Details"


class IssueVialsService:
    """Persists the supervisor "Issue Vials" action on a single test-row answer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def issue_vials(
        self, answer_id: int, user_id: int, receiver_user_id: int | None,
    ) -> QuestionAnswerModel:
        now = datetime.now(timezone.utc)

        answer = await self._require_answer(answer_id)

        # Step 1 — a receiving analyst must be selected. Honour an already-saved
        # receiver, else take the one supplied with this action.
        receiver = receiver_user_id or answer.receiver_user_id
        if receiver is None:
            raise BusinessRuleViolationError("Please Select Analyst Name!")

        # Step 2 — stamp the Basic Details StartDate answer (once) with now.
        await self._stamp_start_date_if_empty(answer.checklist_stage_id, user_id, now)

        # Step 3 — stamp the clicked answer's issue attributes.
        answer.receiver_user_id = receiver
        answer.issued_by_date = now
        answer.received_by_date = now
        answer.is_issued_vails = True
        answer.issuer_name = await self._full_name(user_id)
        answer.modified_by = str(user_id)
        answer.modified_date = now

        await self._session.flush()
        return answer

    async def calculate_sample_destroyed(
        self, answer_id: int, user_id: int,
    ) -> QuestionAnswerModel:
        """Compute "Remaining Samples destroyed By" for the recon Test stage
        (ports the Mendix Calculate microflow):

          1. All vials must be issued — any non-declaration Test-stage answer
             with has_vails and NOT is_issued_vails blocks with
             "Calculate once all vails are issued !".
          2. Read the Test stage's Sample Consumed answer (declaration mapping
             custom_answers = Calculate_SampleConsumed) and the Basic Details
             is_calculated answer (its answer_total_vails = total received).
          3. If the consumed value is blank → "Please select product !".
          4. destroyed = received_total - consumed; if < 0 → negative error.
          5. Set this answer's textbox_value = str(destroyed).
        """
        now = datetime.now(timezone.utc)
        answer = await self._require_answer(answer_id)
        stage_id = answer.checklist_stage_id

        # 1 — all vials issued?
        decl_subq = (
            select(StageQuestionMappingModel.id)
            .where(StageQuestionMappingModel.is_declaration_question.is_(True))
        )
        unissued = await self._session.execute(
            select(QuestionAnswerModel.id).where(
                QuestionAnswerModel.checklist_stage_id == stage_id,
                QuestionAnswerModel.has_vails.is_(True),
                QuestionAnswerModel.is_issued_vails.is_(False),
                QuestionAnswerModel.stage_question_mapping_id.notin_(decl_subq)
                | QuestionAnswerModel.stage_question_mapping_id.is_(None),
            ).limit(1)
        )
        if unissued.scalar_one_or_none() is not None:
            raise BusinessRuleViolationError("Calculate once all vails are issued !")

        # 2 — Sample Consumed (Test stage declaration mapping).
        consumed_result = await self._session.execute(
            select(QuestionAnswerModel.textbox_value)
            .join(
                StageQuestionMappingModel,
                StageQuestionMappingModel.id == QuestionAnswerModel.stage_question_mapping_id,
            )
            .where(
                QuestionAnswerModel.checklist_stage_id == stage_id,
                StageQuestionMappingModel.custom_answers
                == CustomAnswer.CALCULATE_SAMPLE_CONSUMED.value,
            )
            .limit(1)
        )
        consumed_value = consumed_result.scalar_one_or_none()

        # 2 — Basic Details is_calculated answer → answer_total_vails (received).
        basic_stage_id = await self._basic_details_stage_id(stage_id)
        received_total = 0
        if basic_stage_id is not None:
            received_result = await self._session.execute(
                select(QuestionAnswerModel.answer_total_vails)
                .join(
                    QuestionModel,
                    QuestionModel.id == QuestionAnswerModel.question_id,
                )
                .where(
                    QuestionAnswerModel.checklist_stage_id == basic_stage_id,
                    QuestionModel.is_calculated.is_(True),
                )
                .limit(1)
            )
            received_total = received_result.scalar_one_or_none() or 0

        # 3 — consumed must be filled (product picked).
        if not consumed_value or not consumed_value.strip():
            raise BusinessRuleViolationError("Please select product !")

        # 4 — destroyed = received_total - consumed; cannot be negative.
        destroyed = received_total - int(consumed_value.strip())
        if destroyed < 0:
            raise BusinessRuleViolationError(
                "Please Check Sample Quantity received total as calculation value "
                "cannot be negative!"
            )

        # 5 — persist the computed destroyed value on this answer.
        answer.textbox_value = str(destroyed)
        answer.modified_by = str(user_id)
        answer.modified_date = now
        await self._session.flush()
        return answer

    # ── helpers ────────────────────────────────────────────────────────────────

    async def _require_answer(self, answer_id: int) -> QuestionAnswerModel:
        result = await self._session.execute(
            select(QuestionAnswerModel).where(QuestionAnswerModel.id == answer_id)
        )
        answer = result.scalar_one_or_none()
        if answer is None:
            raise EntityNotFoundError("QuestionAnswer", answer_id)
        return answer

    async def _basic_details_stage_id(self, any_stage_id: int) -> int | None:
        """Resolve the Basic Details stage id for the request that owns the
        given stage (the clicked answer's stage belongs to the same request)."""
        req_result = await self._session.execute(
            select(ChecklistStageModel.checklist_request_id).where(
                ChecklistStageModel.id == any_stage_id
            )
        )
        request_id = req_result.scalar_one_or_none()
        if request_id is None:
            return None

        result = await self._session.execute(
            select(ChecklistStageModel.id)
            .join(
                FormatStageMappingModel,
                FormatStageMappingModel.id == ChecklistStageModel.format_stage_mapping_id,
            )
            .join(StageModel, StageModel.id == FormatStageMappingModel.stage_id)
            .where(
                ChecklistStageModel.checklist_request_id == request_id,
                StageModel.stage_name == BASIC_DETAILS,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _stamp_start_date_if_empty(
        self, any_stage_id: int, user_id: int, now: datetime,
    ) -> None:
        """Find the Basic Details StartDate answer; if its date_time is empty,
        set it to now (mirrors the Mendix analysis-start-date stamp)."""
        basic_stage_id = await self._basic_details_stage_id(any_stage_id)
        if basic_stage_id is None:
            return

        result = await self._session.execute(
            select(QuestionAnswerModel)
            .join(
                StageQuestionMappingModel,
                StageQuestionMappingModel.id == QuestionAnswerModel.stage_question_mapping_id,
            )
            .where(
                QuestionAnswerModel.checklist_stage_id == basic_stage_id,
                StageQuestionMappingModel.custom_answers == CustomAnswer.START_DATE.value,
            )
            .limit(1)
        )
        start_answer = result.scalar_one_or_none()
        if start_answer is None:
            return
        if start_answer.date_time is None:
            start_answer.date_time = now
            start_answer.modified_by = str(user_id)
            start_answer.modified_date = now

    async def _full_name(self, user_id: int) -> str:
        """The acting user's full name (user_details.employee_name), falling
        back to the username when no details row exists."""
        result = await self._session.execute(
            select(UserDetailsModel.employee_name).where(
                UserDetailsModel.user_id == user_id
            )
        )
        name = result.scalar_one_or_none()
        if name:
            return name
        uname_result = await self._session.execute(
            select(UserModel.username).where(UserModel.id == user_id)
        )
        return uname_result.scalar_one_or_none() or ""
