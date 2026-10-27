"""Stage action — shared DTOs and base helpers for the checklist stage lifecycle.

The checklist stage lifecycle (submit / save-draft / approve / refer-back /
submit-and-approve) was originally one fat SubmitStageService. It is now split
into one focused service per action, each a thin subclass of StageActionBase
which owns everything the actions share:

  - request/stage resolution + first-time request creation
  - role authorization against the stage's approval labels
  - answer persistence
  - approval-label mapping bookkeeping (record / reset / update)
  - status_format computation, next-stage opening, number generation

Commit is NOT done here — get_db_session commits once per request (or rolls
back on error), so services only flush within the shared transaction.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.qc_checklist.stage_action_dtos import (
    QuestionAnswerPayload,
    QuestionApprovalPayload,
    SubAnswerPayload,
    SubmitStageRequest,
    SubmitStageResult,
)
from src.application.services.qc_checklist.request_creation_service import RequestCreationService
from src.application.services.qc_checklist.validate_checklist_service import (
    ValidateChecklistService,
    ValidationResult,
)
from src.domain.entities.qc_checklist.question_answer import QuestionAnswer
from src.domain.enums.custom_answer_enum import CustomAnswer
from src.domain.entities.qc_checklist.stage_approval_label_mapping import (
    StageApprovalLabelMapping,
)
from src.infrastructure.database.repositories.qc_checklist.question_answer_helper_repository_impl import (  # noqa: E501
    QuestionAnswerHelperRepositoryImpl,
)
from src.infrastructure.database.repositories.qc_checklist.question_answer_repository_impl import (
    QuestionAnswerRepositoryImpl,
)
from src.infrastructure.database.repositories.qc_checklist.stage_approval_label_mapping_repository_impl import (  # noqa: E501
    StageApprovalLabelMappingRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.test_master_repository_impl import (
    TestMasterRepositoryImpl,
)
from src.domain.exceptions.domain_exceptions import BusinessRuleViolationError, EntityNotFoundError
from src.infrastructure.database.models.masters.approval_label_model import (
    ApprovalLabelModel,
    ApprovalLabelUserRoleModel,
)
from src.infrastructure.database.models.masters.format_stage_mapping_model import (
    FormatStageMappingModel,
)
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.models.masters.stage_question_mapping_model import (
    StageQuestionMappingModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_request_model import (
    ChecklistRequestModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import (
    ChecklistStageModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_model import (
    QuestionAnswerModel,
)
from src.infrastructure.database.models.qc_checklist.stage_approval_label_mapping_model import (
    StageApprovalLabelMappingModel,
)
from src.infrastructure.database.models.role_model import RoleAssignmentModel
from src.infrastructure.security.auth_manager import AuthenticationError

VALID_ACTIONS = ("submit", "save_draft", "approve", "refer_back")
BASIC_DETAILS = "Basic Details"


@dataclass
class ResolvedStage:
    """A request + its target stage, resolved and (optionally) with answers
    already persisted — the common pre-amble every action needs."""
    request: ChecklistRequestModel
    stage: ChecklistStageModel


class StageActionBase:
    """Shared state and helpers for all stage-action services. Each concrete
    action service (submit / save-draft / approve / refer-back) subclasses this
    and implements execute()."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._request_creation = RequestCreationService(session)
        # Row inserts go through their repos (which own the flush), so the
        # service never adds/flushes raw ORM for new rows itself.
        self._qa_repo = QuestionAnswerRepositoryImpl(session)
        self._salm_repo = StageApprovalLabelMappingRepositoryImpl(session)
        self._helper_repo = QuestionAnswerHelperRepositoryImpl(session)
        self._test_master_repo = TestMasterRepositoryImpl(session)

    async def execute(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None,
    ) -> SubmitStageResult:
        raise NotImplementedError

    # ── role resolution ──────────────────────────────────────────────────────

    async def resolve_active_role_id(self, user_id: int) -> int | None:
        """The caller's active role id — kept in the service so the controller
        stays a thin HTTP layer (no ORM access)."""
        result = await self._session.execute(
            select(RoleAssignmentModel.role_id).where(
                RoleAssignmentModel.user_id == user_id,
                RoleAssignmentModel.is_active.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    # ── request / stage resolution + answer persistence (common pre-amble) ─────

    async def resolve(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None, now: datetime,
        *, authorize: bool,
    ) -> ResolvedStage:
        """Resolve (or create) the request, resolve the target stage, optionally
        authorize the role, and persist the primary stage's answers."""
        if request.checklist_request_id:
            cr_result = await self._session.execute(
                select(ChecklistRequestModel).where(
                    ChecklistRequestModel.id == request.checklist_request_id
                )
            )
            cr = cr_result.scalar_one_or_none()
            if not cr:
                raise EntityNotFoundError("ChecklistRequest", request.checklist_request_id)
        else:
            cr = await self._request_creation.create_request_with_stages(
                request.format_id, user_id, now
            )

        if request.checklist_stage_id:
            cs_result = await self._session.execute(
                select(ChecklistStageModel).where(
                    ChecklistStageModel.id == request.checklist_stage_id
                )
            )
            cs = cs_result.scalar_one_or_none()
            if not cs:
                raise EntityNotFoundError("ChecklistStage", request.checklist_stage_id)
        else:
            cs_result = await self._session.execute(
                select(ChecklistStageModel).where(
                    ChecklistStageModel.checklist_request_id == cr.id,
                    ChecklistStageModel.format_stage_mapping_id == request.format_stage_mapping_id,
                )
            )
            cs = cs_result.scalar_one_or_none()
            if not cs:
                raise EntityNotFoundError(
                    "ChecklistStage", f"fsm={request.format_stage_mapping_id}"
                )

        if authorize:
            await self._authorize_stage_action(cs, role_id)

        if request.answers:
            await self._persist_answers(cs.id, request.answers, user_id, now)

        return ResolvedStage(request=cr, stage=cs)

    # ── enforcement ────────────────────────────────────────────────────────────

    @staticmethod
    def _raise_if_invalid(validation_result: ValidationResult) -> None:
        """Block the action if any validation rule failed, surfacing the messages."""
        if validation_result.is_valid:
            return
        messages = [e.message for e in validation_result.errors]
        detail = "; ".join(dict.fromkeys(messages))  # de-dupe, keep order
        raise BusinessRuleViolationError(detail or "Validation failed.")

    async def _validate_stage(self, cr: ChecklistRequestModel, cs: ChecklistStageModel) -> None:
        validator = ValidateChecklistService(self._session)
        self._raise_if_invalid(await validator.validate_stage(cr.id, cs.id))

    async def _authorize_stage_action(self, cs: ChecklistStageModel, role_id: int | None) -> None:
        """Ensure the caller's role is configured to act on this stage. Stages
        with no approval labels (e.g. Basic Details) have no role gate."""
        if not cs.format_stage_mapping_id:
            return
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(
                FormatStageMappingModel.id == cs.format_stage_mapping_id
            )
        )
        fsm = fsm_result.scalar_one_or_none()
        if not fsm:
            return
        allowed_result = await self._session.execute(
            select(ApprovalLabelUserRoleModel.role_id)
            .join(
                ApprovalLabelModel,
                ApprovalLabelModel.id == ApprovalLabelUserRoleModel.approval_label_id,
            )
            .where(
                ApprovalLabelModel.stage_id == fsm.stage_id,
                ApprovalLabelModel.is_active.is_(True),
            )
        )
        allowed_role_ids = {r[0] for r in allowed_result.fetchall()}
        if not allowed_role_ids:
            return
        if role_id is None or role_id not in allowed_role_ids:
            raise AuthenticationError(
                "Your role is not authorized to act on this stage.",
                status_code=403,
            )

    # ── approval-label mapping bookkeeping ─────────────────────────────────────

    async def _record_approval_action(
        self, cs: ChecklistStageModel, user_id: int, role_id: int | None,
        remark_id, remark_text, now: datetime, is_refer_back: bool = False,
    ) -> None:
        """Fill the first unacted StageApprovalLabelMapping for this stage."""
        unacted_result = await self._session.execute(
            select(StageApprovalLabelMappingModel).where(
                StageApprovalLabelMappingModel.checklist_stage_id == cs.id,
                StageApprovalLabelMappingModel.date_of_action.is_(None),
                StageApprovalLabelMappingModel.user_id.is_(None),
            ).order_by(StageApprovalLabelMappingModel.id).limit(1)
        )
        mapping = unacted_result.scalar_one_or_none()
        if mapping:
            mapping.user_id = user_id
            mapping.role_id = role_id
            mapping.remark_id = remark_id
            mapping.remark = remark_text or ""
            mapping.date_of_action = now
            mapping.is_show = True
            mapping.is_refer_back = is_refer_back
            mapping.modified_by = str(user_id)
            mapping.modified_date = now
            return

        # Fallback: create a mapping if none was pre-created.
        fsm_id = cs.format_stage_mapping_id
        if not fsm_id:
            return
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(FormatStageMappingModel.id == fsm_id)
        )
        fsm = fsm_result.scalar_one_or_none()
        if not fsm:
            return
        al_result = await self._session.execute(
            select(ApprovalLabelModel).where(
                ApprovalLabelModel.stage_id == fsm.stage_id,
                ApprovalLabelModel.is_active.is_(True),
            ).order_by(ApprovalLabelModel.id).limit(1)
        )
        label = al_result.scalar_one_or_none()
        if not label:
            return
        await self._salm_repo.create(StageApprovalLabelMapping(
            checklist_stage_id=cs.id,
            approval_label_id=label.id,
            remark_id=remark_id,
            user_id=user_id,
            role_id=role_id,
            date_of_action=now,
            remark=remark_text or "",
            is_show=True,
            is_refer_back=is_refer_back,
            created_by=str(user_id),
            modified_by=str(user_id),
        ))

    async def _role_can_act_on_label(self, approval_label_id: int, role_id: int | None) -> bool:
        """Whether the caller's role is configured on a given approval label.
        A label with no roles configured is open to anyone (mirrors the stage
        gate's 'no roles → no restriction')."""
        result = await self._session.execute(
            select(ApprovalLabelUserRoleModel.role_id).where(
                ApprovalLabelUserRoleModel.approval_label_id == approval_label_id
            )
        )
        allowed = {r[0] for r in result.fetchall()}
        if not allowed:
            return True
        return role_id is not None and role_id in allowed

    async def _persist_question_approvals(
        self, stage_id: int, approvals: list[QuestionApprovalPayload] | None,
        user_id: int, role_id: int | None, now: datetime,
    ) -> None:
        """Record per-question approval-label remark picks (same mechanics as a
        stage approval, but keyed to the filled question's question_answer_id).

        For each pick: resolve the question_answer, enforce the label's role
        gate, then fill the first unacted mapping for that (question_answer,
        label) — creating one if none exists."""
        if not approvals:
            return
        for pick in approvals:
            # Only the role(s) configured on this label may act on it.
            if not await self._role_can_act_on_label(pick.approval_label_id, role_id):
                continue

            qa_result = await self._session.execute(
                select(QuestionAnswerModel.id).where(
                    QuestionAnswerModel.checklist_stage_id == stage_id,
                    QuestionAnswerModel.stage_question_mapping_id == pick.stage_question_mapping_id,
                )
            )
            qa_id = qa_result.scalar_one_or_none()
            if qa_id is None:
                continue

            # First unacted mapping for this question+label (if pre-created),
            # otherwise create one.
            mapping_result = await self._session.execute(
                select(StageApprovalLabelMappingModel).where(
                    StageApprovalLabelMappingModel.question_answer_id == qa_id,
                    StageApprovalLabelMappingModel.approval_label_id == pick.approval_label_id,
                    StageApprovalLabelMappingModel.date_of_action.is_(None),
                ).order_by(StageApprovalLabelMappingModel.id).limit(1)
            )
            mapping = mapping_result.scalar_one_or_none()
            if mapping:
                mapping.user_id = user_id
                mapping.role_id = role_id
                mapping.remark_id = pick.remark_id
                mapping.remark = pick.remark_text or ""
                mapping.date_of_action = now
                mapping.is_show = True
                mapping.modified_by = str(user_id)
                mapping.modified_date = now
            else:
                await self._salm_repo.create(StageApprovalLabelMapping(
                    checklist_stage_id=None,
                    question_answer_id=qa_id,
                    approval_label_id=pick.approval_label_id,
                    remark_id=pick.remark_id,
                    user_id=user_id,
                    role_id=role_id,
                    date_of_action=now,
                    remark=pick.remark_text or "",
                    is_show=True,
                    is_refer_back=False,
                    created_by=str(user_id),
                    modified_by=str(user_id),
                ))

    async def _reset_refer_back_mappings(self, cs: ChecklistStageModel) -> None:
        """Clear the approver's refer-back action(s) so the approval chain
        reopens when the initiator resubmits."""
        result = await self._session.execute(
            select(StageApprovalLabelMappingModel).where(
                StageApprovalLabelMappingModel.checklist_stage_id == cs.id,
                StageApprovalLabelMappingModel.is_refer_back.is_(True),
            )
        )
        for mapping in result.scalars().all():
            mapping.user_id = None
            mapping.role_id = None
            mapping.remark_id = None
            mapping.remark = ""
            mapping.date_of_action = None
            mapping.is_refer_back = False
            mapping.is_show = False

    async def _update_initiator_mapping(
        self, cs: ChecklistStageModel, user_id: int, role_id: int | None,
        remark_id, remark_text, now: datetime,
    ) -> None:
        """On a refer-back resubmit, update the initiator's already-acted mapping
        in place rather than opening a new one."""
        result = await self._session.execute(
            select(StageApprovalLabelMappingModel).where(
                StageApprovalLabelMappingModel.checklist_stage_id == cs.id,
                StageApprovalLabelMappingModel.date_of_action.is_not(None),
                StageApprovalLabelMappingModel.is_refer_back.is_(False),
            ).order_by(StageApprovalLabelMappingModel.id).limit(1)
        )
        mapping = result.scalar_one_or_none()
        if mapping:
            mapping.user_id = user_id
            mapping.role_id = role_id
            mapping.remark_id = remark_id
            mapping.remark = remark_text or ""
            mapping.date_of_action = now
            mapping.is_show = True
            mapping.modified_by = str(user_id)
            mapping.modified_date = now
        else:
            await self._record_approval_action(cs, user_id, role_id, remark_id, remark_text, now)

    # ── stage progression ──────────────────────────────────────────────────────

    async def _open_next_stage(
        self, cr: ChecklistRequestModel, current_stage: ChecklistStageModel,
        user_id: int, now: datetime,
    ) -> bool:
        """Open the next stage after approval. Returns True if one was opened."""
        stages_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == cr.id
            ).order_by(ChecklistStageModel.id)
        )
        all_stages = list(stages_result.scalars().all())
        current_idx = next((i for i, s in enumerate(all_stages) if s.id == current_stage.id), None)
        if current_idx is None or current_idx >= len(all_stages) - 1:
            return False
        next_stage = all_stages[current_idx + 1]
        next_stage.status = "Initial"
        next_stage.modified_by = str(user_id)
        next_stage.modified_date = now
        return True

    async def _approve_pending_stages(
        self, cr: ChecklistRequestModel, user_id: int, now: datetime,
    ) -> None:
        """At final approval, mark any still-Pending stages (notably Basic
        Details, which stays Pending the whole flow) as Approved."""
        pending_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == cr.id,
                ChecklistStageModel.status == "Pending",
            )
        )
        for stage in pending_result.scalars().all():
            stage.status = "Approved"
            stage.modified_by = str(user_id)
            stage.modified_date = now

    # ── answer persistence ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_date_time(value: str | None) -> datetime | None:
        """Parse an ISO-8601 date-time string (as sent by the fill page's date
        picker) into a datetime. Returns None for empty/invalid input so a blank
        value never overwrites an existing/stamped date."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    async def _persist_answers(
        self, stage_id: int, answers: list[QuestionAnswerPayload], user_id: int, now: datetime,
    ) -> None:
        """Persist or update question answers (and their helper sub-answers)."""
        for ans in answers:
            existing_result = await self._session.execute(
                select(QuestionAnswerModel).where(
                    QuestionAnswerModel.checklist_stage_id == stage_id,
                    QuestionAnswerModel.stage_question_mapping_id == ans.stage_question_mapping_id,
                )
            )
            existing = existing_result.scalar_one_or_none()
            # Date & Time answers arrive as an ISO string on the payload — parse
            # to a datetime so the picker value is actually persisted (and shows
            # when the request is reopened on the fill page).
            answer_dt = self._parse_date_time(ans.date_time)
            if existing:
                existing.textbox_value = ans.textbox_value
                existing.question_option_id = ans.question_option_id
                existing.response_question_option_id = ans.response_question_option_id
                existing.response_answer = ans.response_answer
                existing.product_id = ans.product_id
                existing.has_helper = ans.has_helper or bool(ans.helpers)
                existing.answer_total_vails = ans.answer_total_vails
                # Only overwrite when a value was sent — don't wipe a
                # system-stamped date (e.g. StartDate) on a blank resubmit.
                if answer_dt is not None:
                    existing.date_time = answer_dt
                existing.modified_by = str(user_id)
                existing.modified_date = now
                qa_id = existing.id
            else:
                # Insert via the repo so the flush (and id assignment) lives in
                # the repository layer, not the service.
                created = await self._qa_repo.create(QuestionAnswer(
                    checklist_stage_id=stage_id,
                    question_id=ans.question_id,
                    stage_question_mapping_id=ans.stage_question_mapping_id,
                    textbox_value=ans.textbox_value,
                    question_option_id=ans.question_option_id,
                    response_question_option_id=ans.response_question_option_id,
                    response_answer=ans.response_answer,
                    product_id=ans.product_id,
                    date_time=answer_dt,
                    has_helper=ans.has_helper or bool(ans.helpers),
                    answer_total_vails=ans.answer_total_vails,
                    created_by=str(user_id),
                    modified_by=str(user_id),
                ))
                qa_id = created.id

            # Helper ("+ Add") free-text values belong to this answer — the repo
            # replaces them (delete + insert) and owns the flush.
            if ans.helpers:
                await self._helper_repo.replace_for_answer(qa_id, ans.helpers, str(user_id))

            # Sub-question answers: each is its own QuestionAnswer row, linked to
            # the parent answer via the self-join. Rewritten each save.
            await self._persist_sub_answers(stage_id, qa_id, ans.sub_answers, user_id)

    async def _persist_sub_answers(
        self,
        stage_id: int,
        parent_qa_id: int,
        sub_answers: list[SubAnswerPayload] | None,
        user_id: int,
    ) -> None:
        """Persist a parent answer's sub-question answers as child QuestionAnswer
        rows, linked via question_answer_sub_question_answers. Rewritten on each
        save: the previous children + links for this parent are removed first.
        All persistence (delete / insert / link + flush) lives in the repo."""
        await self._qa_repo.delete_sub_answers_by_parent(parent_qa_id)

        if not sub_answers:
            return

        for sub in sub_answers:
            child = await self._qa_repo.create(QuestionAnswer(
                checklist_stage_id=stage_id,
                question_id=sub.question_id,
                stage_question_mapping_id=None,
                textbox_value=sub.textbox_value,
                question_option_id=sub.question_option_id,
                response_question_option_id=sub.response_question_option_id,
                response_answer=sub.response_answer,
                created_by=str(user_id),
                modified_by=str(user_id),
            ))
            await self._qa_repo.link_sub_answer(parent_qa_id, child.id, str(user_id))

    # ── product → test expansion ─────────────────────────────────────────────────

    async def _next_stage_after(
        self, cr: ChecklistRequestModel, basic_stage: ChecklistStageModel
    ) -> ChecklistStageModel | None:
        """The stage immediately after the Basic Details stage (ordered by id).
        Tests expanded from a product are created on this stage."""
        result = await self._session.execute(
            select(ChecklistStageModel)
            .where(ChecklistStageModel.checklist_request_id == cr.id)
            .order_by(ChecklistStageModel.id)
        )
        stages = list(result.scalars().all())
        idx = next((i for i, s in enumerate(stages) if s.id == basic_stage.id), None)
        if idx is None or idx >= len(stages) - 1:
            return None
        return stages[idx + 1]

    async def _expand_product_tests(
        self, cr: ChecklistRequestModel, basic_stage: ChecklistStageModel,
        user_id: int, now: datetime,
    ) -> None:
        """When a product is chosen on the Basic Details' Masters question,
        create one question_answer per test of that product on the NEXT stage,
        storing each test's name in test_title. Re-runs idempotently: the
        auto-generated test rows (stage_question_mapping_id NULL, non-empty
        test_title) on the next stage are cleared and recreated each submit."""
        # Product id(s) selected on this Basic Details stage.
        prod_result = await self._session.execute(
            select(QuestionAnswerModel.product_id).where(
                QuestionAnswerModel.checklist_stage_id == basic_stage.id,
                QuestionAnswerModel.product_id.is_not(None),
            )
        )
        product_ids = [pid for pid in prod_result.scalars().all() if pid]
        if not product_ids:
            return

        next_stage = await self._next_stage_after(cr, basic_stage)
        if next_stage is None:
            return

        # Clear previously auto-generated test rows on the next stage so a
        # changed product re-expands cleanly.
        old = await self._session.execute(
            select(QuestionAnswerModel).where(
                QuestionAnswerModel.checklist_stage_id == next_stage.id,
                QuestionAnswerModel.stage_question_mapping_id.is_(None),
                QuestionAnswerModel.test_title != "",
            )
        )
        for row in old.scalars().all():
            await self._session.delete(row)
        await self._session.flush()

        serial = 0
        total_sample_qty = 0
        for product_id in product_ids:
            tests = await self._test_master_repo.list_by_product(product_id)
            for test in tests:
                serial += 1
                total_sample_qty += test.sample_qty or 0
                # sample_vails holds the vial description text; has_vails is
                # whether any sample is issued for this test:
                #   sample_vails = test_masters.sample_description
                #   has_vails    = test_masters.sample_qty != 0
                await self._qa_repo.create(QuestionAnswer(
                    checklist_stage_id=next_stage.id,
                    stage_question_mapping_id=None,
                    product_id=product_id,
                    test_title=test.test_name,
                    sample_vails=test.sample_description,
                    has_vails=test.sample_qty != 0,
                    serial_number=serial,
                    created_by=str(user_id),
                    modified_by=str(user_id),
                ))

        # Populate the "Calculate_SampleConsumed" question on the next stage
        # with the total sample quantity across the product's tests.
        await self._populate_sample_consumed(next_stage, total_sample_qty, user_id, now)

    async def _populate_sample_consumed(
        self, stage: ChecklistStageModel, total_sample_qty: int,
        user_id: int, now: datetime,
    ) -> None:
        """Upsert the question_answer for the stage's question whose mapping has
        custom_answers = 'Calculate_SampleConsumed', setting its textbox_value to
        the total sample quantity (sum of the product's test sample_qty)."""
        if not stage.format_stage_mapping_id:
            return
        mapping_result = await self._session.execute(
            select(StageQuestionMappingModel).where(
                StageQuestionMappingModel.format_stage_mapping_id
                == stage.format_stage_mapping_id,
                StageQuestionMappingModel.custom_answers
                == CustomAnswer.CALCULATE_SAMPLE_CONSUMED.value,
            )
        )
        mapping = mapping_result.scalars().first()
        if mapping is None:
            return

        value = str(total_sample_qty)
        existing_result = await self._session.execute(
            select(QuestionAnswerModel).where(
                QuestionAnswerModel.checklist_stage_id == stage.id,
                QuestionAnswerModel.stage_question_mapping_id == mapping.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.textbox_value = value
            existing.modified_by = str(user_id)
            existing.modified_date = now
        else:
            await self._qa_repo.create(QuestionAnswer(
                checklist_stage_id=stage.id,
                question_id=mapping.question_id,
                stage_question_mapping_id=mapping.id,
                textbox_value=value,
                created_by=str(user_id),
                modified_by=str(user_id),
            ))
        await self._session.flush()

    async def _populate_start_date(
        self, stage: ChecklistStageModel, user_id: int, now: datetime,
    ) -> None:
        """Stamp the stage's question whose mapping has custom_answers =
        'StartDate' with the current date/time (analysis start date), set on
        submit. Upserts the question_answer's date_time."""
        if not stage.format_stage_mapping_id:
            return
        mapping_result = await self._session.execute(
            select(StageQuestionMappingModel).where(
                StageQuestionMappingModel.format_stage_mapping_id
                == stage.format_stage_mapping_id,
                StageQuestionMappingModel.custom_answers == CustomAnswer.START_DATE.value,
            )
        )
        mapping = mapping_result.scalars().first()
        if mapping is None:
            return

        existing_result = await self._session.execute(
            select(QuestionAnswerModel).where(
                QuestionAnswerModel.checklist_stage_id == stage.id,
                QuestionAnswerModel.stage_question_mapping_id == mapping.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            # Only set once — don't overwrite a previously stamped start date.
            if existing.date_time is None:
                existing.date_time = now
                existing.modified_by = str(user_id)
                existing.modified_date = now
        else:
            await self._qa_repo.create(QuestionAnswer(
                checklist_stage_id=stage.id,
                question_id=mapping.question_id,
                stage_question_mapping_id=mapping.id,
                date_time=now,
                created_by=str(user_id),
                modified_by=str(user_id),
            ))
        await self._session.flush()

    async def _populate_end_date(
        self, cr: ChecklistRequestModel, user_id: int, now: datetime,
    ) -> None:
        """Stamp the request's Basic Details question whose mapping has
        custom_answers = 'EndDate' (Analysis Completion Date) with the current
        date/time. Called on the analyst's final submit. Overwrites any previous
        value (the completion date reflects the latest submit)."""
        basic_result = await self._session.execute(
            select(ChecklistStageModel)
            .join(
                FormatStageMappingModel,
                FormatStageMappingModel.id == ChecklistStageModel.format_stage_mapping_id,
            )
            .join(StageModel, StageModel.id == FormatStageMappingModel.stage_id)
            .where(
                ChecklistStageModel.checklist_request_id == cr.id,
                StageModel.stage_name == BASIC_DETAILS,
            )
            .limit(1)
        )
        basic_stage = basic_result.scalar_one_or_none()
        if basic_stage is None or not basic_stage.format_stage_mapping_id:
            return

        mapping_result = await self._session.execute(
            select(StageQuestionMappingModel).where(
                StageQuestionMappingModel.format_stage_mapping_id
                == basic_stage.format_stage_mapping_id,
                StageQuestionMappingModel.custom_answers == CustomAnswer.END_DATE.value,
            )
        )
        mapping = mapping_result.scalars().first()
        if mapping is None:
            return

        existing_result = await self._session.execute(
            select(QuestionAnswerModel).where(
                QuestionAnswerModel.checklist_stage_id == basic_stage.id,
                QuestionAnswerModel.stage_question_mapping_id == mapping.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.date_time = now
            existing.modified_by = str(user_id)
            existing.modified_date = now
        else:
            await self._qa_repo.create(QuestionAnswer(
                checklist_stage_id=basic_stage.id,
                question_id=mapping.question_id,
                stage_question_mapping_id=mapping.id,
                date_time=now,
                created_by=str(user_id),
                modified_by=str(user_id),
            ))
        await self._session.flush()

    # ── status_format ──────────────────────────────────────────────────────────

    async def _stage_name(self, stage: ChecklistStageModel) -> str | None:
        if not stage.format_stage_mapping_id:
            return None
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(
                FormatStageMappingModel.id == stage.format_stage_mapping_id
            )
        )
        fsm = fsm_result.scalar_one_or_none()
        if not fsm:
            return None
        sm_result = await self._session.execute(
            select(StageModel).where(StageModel.id == fsm.stage_id)
        )
        sm = sm_result.scalar_one_or_none()
        return sm.stage_name if sm else None

    async def _update_status_format(self, cr: ChecklistRequestModel, format_type: str) -> None:
        """Set the request's status_format to reflect the active stage.

        - ReconcilationSheet → unchanged.
        - A ReferBack stage → "<Stage> - Referred Back".
        - Else a Pending approval stage (not Basic Details) → "<Stage> - Approval Pending".
        - Else "".
        """
        if format_type == "ReconcilationSheet":
            return

        refer_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == cr.id,
                ChecklistStageModel.status == "ReferBack",
            ).order_by(ChecklistStageModel.id.desc())
        )
        refer_stage = refer_result.scalars().first()
        if refer_stage:
            name = await self._stage_name(refer_stage)
            if name:
                cr.status_format = f"{name} - Referred Back"
                return

        if cr.status == "Pending":
            stages_result = await self._session.execute(
                select(ChecklistStageModel).where(
                    ChecklistStageModel.checklist_request_id == cr.id,
                    ChecklistStageModel.status == "Pending",
                ).order_by(ChecklistStageModel.id.desc())
            )
            for pending_stage in stages_result.scalars().all():
                name = await self._stage_name(pending_stage)
                if name and name != BASIC_DETAILS:
                    cr.status_format = f"{name} - Approval Pending"
                    return
        cr.status_format = ""

    # ── recon-sheet vial issuing ────────────────────────────────────────────────

    async def _is_submit_label_role(self, cs: ChecklistStageModel, role_id: int | None) -> bool:
        """True when `role_id` is a role configured on the stage's FIRST approval
        label (the SUBMIT label). For the recon Test stage this is the Analyst
        label — so this tells supervisor (approve label) from analyst (submit
        label) when both act while the stage is still Initial."""
        if role_id is None or not cs.format_stage_mapping_id:
            return False
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(
                FormatStageMappingModel.id == cs.format_stage_mapping_id
            )
        )
        fsm = fsm_result.scalar_one_or_none()
        if not fsm:
            return False
        first_label_result = await self._session.execute(
            select(ApprovalLabelModel.id).where(
                ApprovalLabelModel.stage_id == fsm.stage_id,
                ApprovalLabelModel.is_active.is_(True),
            ).order_by(ApprovalLabelModel.id).limit(1)
        )
        first_label_id = first_label_result.scalar_one_or_none()
        if first_label_id is None:
            return False
        roles_result = await self._session.execute(
            select(ApprovalLabelUserRoleModel.role_id).where(
                ApprovalLabelUserRoleModel.approval_label_id == first_label_id
            )
        )
        submit_role_ids = {r[0] for r in roles_result.fetchall()}
        return role_id in submit_role_ids

    async def _has_unissued_vials(self, stage: ChecklistStageModel) -> bool:
        """True when the stage still has vials to issue (recon sheet).

        Ports the Mendix check: on this stage, any question_answer that
          - is NOT a declaration question (mapping null, or is_declaration=false)
          - has_vails = true
          - received_by_date is empty
        means a vial is still unissued. If none exist, all vials are issued.
        """
        decl_subq = (
            select(StageQuestionMappingModel.id)
            .where(StageQuestionMappingModel.is_declaration_question.is_(True))
        )
        result = await self._session.execute(
            select(QuestionAnswerModel.id).where(
                QuestionAnswerModel.checklist_stage_id == stage.id,
                QuestionAnswerModel.has_vails.is_(True),
                QuestionAnswerModel.received_by_date.is_(None),
                QuestionAnswerModel.stage_question_mapping_id.notin_(decl_subq)
                | QuestionAnswerModel.stage_question_mapping_id.is_(None),
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    # ── utilities ────────────────────────────────────────────────────────────────

    async def _get_format_type(self, format_id: int | None) -> str:
        """Format type — delegated to RequestCreationService."""
        return await self._request_creation.get_format_type(format_id)
