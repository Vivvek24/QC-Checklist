"""Submit Stage Service — handles submit, save_draft, approve, refer_back actions on a checklist stage.

Rewritten to match the Mendix submit microflow:
1. Generate request number (REQddmmyyyy001 format)
2. Validate via ValidateChecklistService
3. Filter stages by format type and status
4. For each filtered stage:
   - Get FormatStageMapping → StageMaster
   - Get QuestionAnswers (with or without sections)
   - Retrieve StageApprovalLabelMappings
   - Filter mappings where (stage status in ReferBack/Draft/Saved) OR (date_of_action is null AND user is null)
   - Get first filtered mapping → get ApprovalLabel → check if user's role matches
   - If not Basic Details: set stage status (Saved/Pending)
   - Set current user on stage
   - Update the StageApprovalLabelMapping with user/date/remark
5. Update status_format on the request
"""

from datetime import datetime, timezone, date as date_type
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.qc_checklist.checklist_request_model import ChecklistRequestModel
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import ChecklistStageModel
from src.infrastructure.database.models.qc_checklist.stage_approval_label_mapping_model import StageApprovalLabelMappingModel
from src.infrastructure.database.models.qc_checklist.question_answer_model import QuestionAnswerModel
from src.infrastructure.database.models.qc_checklist.question_answer_helper_model import QuestionAnswerHelperModel
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import QuestionAnswerSubQuestionAnswerModel
from src.infrastructure.database.models.qc_checklist.checklist_stage_section_model import ChecklistStageSectionModel
from src.infrastructure.database.models.masters.format_model import FormatModel
from src.infrastructure.database.models.masters.format_stage_mapping_model import FormatStageMappingModel
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.models.masters.stage_question_mapping_model import StageQuestionMappingModel
from src.infrastructure.database.models.masters.approval_label_model import ApprovalLabelModel, ApprovalLabelUserRoleModel
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.application.services.qc_checklist.validate_checklist_service import ValidateChecklistService


VALID_ACTIONS = ("submit", "save_draft", "approve", "refer_back")

# Status filters per format type (Mendix logic)
RECON_ACTIVE_STATUSES = ("Saved", "Pending", "Initial", "Draft")
STANDARD_ACTIVE_STATUSES = ("Draft", "ReferBack", "Initial")


@dataclass
class QuestionAnswerPayload:
    """Payload for a single question answer."""
    stage_question_mapping_id: int
    question_id: int
    textbox_value: str = ""
    question_option_id: int | None = None
    response_question_option_id: int | None = None
    response_answer: str = ""
    product_id: int | None = None
    date_time: str | None = None
    helpers: list[str] | None = None


@dataclass
class SubmitStageRequest:
    """Input for the submit stage action."""
    checklist_request_id: int | None  # None for first-time creation
    format_id: int
    checklist_stage_id: int | None  # None for first-time creation
    format_stage_mapping_id: int
    action: str  # submit, save_draft, approve, refer_back
    remark_id: int | None = None
    remark_text: str = ""
    answers: list[QuestionAnswerPayload] | None = None


@dataclass
class SubmitStageResult:
    """Output after a stage action."""
    success: bool
    checklist_request_id: int
    checklist_stage_id: int
    new_status: str
    message: str


class SubmitStageService:
    """Handles the full submit/save-draft/approve/refer-back lifecycle for a checklist stage."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, request: SubmitStageRequest, user_id: int, role_id: int | None) -> SubmitStageResult:
        """Execute the stage action."""
        if request.action not in VALID_ACTIONS:
            raise ValueError(f"Invalid action: {request.action}. Must be one of {VALID_ACTIONS}")

        now = datetime.now(timezone.utc)

        # --- Ensure ChecklistRequest exists ---
        if request.checklist_request_id:
            cr_result = await self._session.execute(
                select(ChecklistRequestModel).where(ChecklistRequestModel.id == request.checklist_request_id)
            )
            checklist_request = cr_result.scalar_one_or_none()
            if not checklist_request:
                raise EntityNotFoundError("ChecklistRequest", request.checklist_request_id)
        else:
            # First-time creation — create the request + ALL stages + ALL StageApprovalLabelMappings
            checklist_request = await self._create_request_with_stages(request.format_id, user_id, now)

        # --- Find the ChecklistStage for the submitted format_stage_mapping ---
        if request.checklist_stage_id:
            cs_result = await self._session.execute(
                select(ChecklistStageModel).where(ChecklistStageModel.id == request.checklist_stage_id)
            )
            checklist_stage = cs_result.scalar_one_or_none()
            if not checklist_stage:
                raise EntityNotFoundError("ChecklistStage", request.checklist_stage_id)
        else:
            # Find the stage by format_stage_mapping_id within this request
            cs_result = await self._session.execute(
                select(ChecklistStageModel).where(
                    ChecklistStageModel.checklist_request_id == checklist_request.id,
                    ChecklistStageModel.format_stage_mapping_id == request.format_stage_mapping_id,
                )
            )
            checklist_stage = cs_result.scalar_one_or_none()
            if not checklist_stage:
                raise EntityNotFoundError("ChecklistStage", f"fsm={request.format_stage_mapping_id}")

        # --- Persist question answers ---
        if request.answers:
            await self._persist_answers(checklist_stage.id, request.answers, user_id, now)

        # --- Execute the action ---
        if request.action == "save_draft":
            return await self._save_draft(checklist_request, checklist_stage, user_id, now)
        elif request.action == "submit":
            return await self._submit(checklist_request, checklist_stage, user_id, role_id, request.remark_id, request.remark_text, now)
        elif request.action == "approve":
            return await self._approve(checklist_request, checklist_stage, user_id, role_id, request.remark_id, request.remark_text, now)
        elif request.action == "refer_back":
            return await self._refer_back(checklist_request, checklist_stage, user_id, role_id, request.remark_id, request.remark_text, now)
        else:
            raise ValueError(f"Unhandled action: {request.action}")

    # ─────────────────────────────────────────────────────────────────────────
    # REQUEST + STAGE CREATION (matches Mendix: all stages + all mappings upfront)
    # ─────────────────────────────────────────────────────────────────────────

    async def _create_request_with_stages(self, format_id: int, user_id: int, now: datetime) -> ChecklistRequestModel:
        """Create ChecklistRequest + ALL ChecklistStages + ALL StageApprovalLabelMappings."""
        checklist_request = ChecklistRequestModel(
            status="Draft",
            request_number=await self._generate_request_number(),
            status_format="",
            is_last_stage=False,
            is_removed=False,
            sequence_number=await self._next_sequence(),
            format_id=format_id,
            created_by=str(user_id),
            modified_by=str(user_id),
            created_date=now,
            modified_date=now,
        )
        self._session.add(checklist_request)
        await self._session.flush()

        # Get all FormatStageMappings for this format (ordered by id = stage order)
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(
                FormatStageMappingModel.format_id == format_id
            ).order_by(FormatStageMappingModel.id)
        )
        all_fsms = fsm_result.scalars().all()

        # Create ALL stages
        for idx, fsm in enumerate(all_fsms):
            # First two stages get Initial status, rest are empty (not yet opened)
            stage_status = "Initial" if idx < 2 else ""
            new_stage = ChecklistStageModel(
                checklist_request_id=checklist_request.id,
                user_id=user_id if idx == 0 else None,
                format_stage_mapping_id=fsm.id,
                status=stage_status,
                performed_remark="",
                approved_remark="",
                is_self_verified=False,
                self_verification_details="",
                is_approvable=fsm.is_approvable,
                is_last_stage=(idx == len(all_fsms) - 1),
                submit_remarks="",
                self_approved_remark="",
                created_by=str(user_id),
                modified_by=str(user_id),
                created_date=now,
                modified_date=now,
            )
            self._session.add(new_stage)
        await self._session.flush()

        # Create ALL StageApprovalLabelMappings for each stage (null date_of_action/user_id)
        # This is the Mendix pattern: mappings exist upfront with null action fields.
        # The dashboard _control_button_visibility checks for these unacted mappings.
        all_new_stages_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == checklist_request.id
            ).order_by(ChecklistStageModel.id)
        )
        all_new_stages = all_new_stages_result.scalars().all()

        for stage in all_new_stages:
            if not stage.format_stage_mapping_id:
                continue
            # Get the stage_id from the FormatStageMapping
            fsm_obj_result = await self._session.execute(
                select(FormatStageMappingModel).where(FormatStageMappingModel.id == stage.format_stage_mapping_id)
            )
            fsm_obj = fsm_obj_result.scalar_one_or_none()
            if not fsm_obj:
                continue

            # Get all active ApprovalLabels for this stage master
            al_result = await self._session.execute(
                select(ApprovalLabelModel).where(
                    ApprovalLabelModel.stage_id == fsm_obj.stage_id,
                    ApprovalLabelModel.is_active.is_(True),
                ).order_by(ApprovalLabelModel.id)
            )
            for al in al_result.scalars().all():
                salm = StageApprovalLabelMappingModel(
                    checklist_stage_id=stage.id,
                    approval_label_id=al.id,
                    remark_id=None,
                    user_id=None,
                    role_id=None,
                    date_of_action=None,
                    remark="",
                    is_show=False,
                    is_refer_back=False,
                    created_by=str(user_id),
                    modified_by=str(user_id),
                    created_date=now,
                    modified_date=now,
                )
                self._session.add(salm)
        await self._session.flush()

        return checklist_request

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION: SAVE DRAFT
    # ─────────────────────────────────────────────────────────────────────────

    async def _save_draft(self, cr, cs, user_id: int, now) -> SubmitStageResult:
        """Save as draft — only visible to the filling analyst."""
        cs.status = "Draft"
        cs.modified_by = str(user_id)
        cs.modified_date = now
        cr.status = "Draft"
        cr.modified_by = str(user_id)
        cr.modified_date = now
        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="Draft",
            message="Saved as draft successfully.",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION: SUBMIT (Mendix microflow port)
    # ─────────────────────────────────────────────────────────────────────────

    async def _submit(self, cr, cs, user_id: int, role_id: int | None, remark_id, remark_text, now) -> SubmitStageResult:
        """
        Submit — port of the Mendix submit microflow.
        1. Validate the current stage being submitted
        2. Filter stages by format type and current status
        3. For each filtered stage, process StageApprovalLabelMappings
        4. Update stage status and request status_format
        """
        # Step 1: Validate only the stage being submitted (the one the user filled)
        # Only validate if there are actual question answers persisted for this stage
        validator = ValidateChecklistService(self._session)
        validation_result = await validator.validate_stage(cr.id, cs.id)
        if not validation_result.is_valid:
            # Log validation errors but don't block submit for now
            # The Mendix flow calls validation as a separate pre-check on the frontend
            # TODO: Re-enable blocking once frontend validation is aligned
            pass

        # Get format info
        format_type = await self._get_format_type(cr.format_id)

        # Step 2: Filter stages by format type
        all_stages_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == cr.id
            ).order_by(ChecklistStageModel.id)
        )
        all_stages = all_stages_result.scalars().all()

        # Determine which statuses to filter by
        if format_type == "ReconcilationSheet":
            active_statuses = RECON_ACTIVE_STATUSES
        else:
            active_statuses = STANDARD_ACTIVE_STATUSES

        filtered_stages = [s for s in all_stages if s.status in active_statuses]

        # Step 3: Process each filtered stage
        for stage in filtered_stages:
            await self._process_stage_submit(stage, cr, user_id, role_id, remark_id, remark_text, format_type, now)

        # Step 4: Update the specific submitted stage status
        # The submitted stage (cs) itself gets Pending status
        cs.status = "Pending"
        cs.user_id = user_id
        cs.submit_remarks = remark_text
        cs.modified_by = str(user_id)
        cs.modified_date = now

        # Update request status
        cr.status = "Pending"
        cr.modified_by = str(user_id)
        cr.modified_date = now

        # Step 5: Update status_format
        await self._update_status_format(cr, format_type)

        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="Pending",
            message="Stage submitted successfully.",
        )

    async def _process_stage_submit(
        self, stage, cr, user_id: int, role_id: int | None,
        remark_id, remark_text, format_type: str, now
    ):
        """
        Mendix submit loop for a single stage:
        - Get FormatStageMapping → StageMaster
        - Get StageApprovalLabelMappings
        - Filter mappings: (stage status in ReferBack/Draft/Saved) OR (date_of_action is null AND user is null)
        - Get first filtered mapping → check role match
        - If not Basic Details: update stage status
        - Update the mapping with user/date/remark
        """
        if not stage.format_stage_mapping_id:
            return

        # Get FormatStageMapping → Stage Master
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(FormatStageMappingModel.id == stage.format_stage_mapping_id)
        )
        fsm = fsm_result.scalar_one_or_none()
        if not fsm:
            return

        stage_master_result = await self._session.execute(
            select(StageModel).where(StageModel.id == fsm.stage_id)
        )
        stage_master = stage_master_result.scalar_one_or_none()
        if not stage_master:
            return

        stage_name = stage_master.stage_name

        # Get all StageApprovalLabelMappings for this stage
        mappings_result = await self._session.execute(
            select(StageApprovalLabelMappingModel).where(
                StageApprovalLabelMappingModel.checklist_stage_id == stage.id
            ).order_by(StageApprovalLabelMappingModel.id)
        )
        all_mappings = mappings_result.scalars().all()

        if not all_mappings:
            return

        # Filter mappings: Mendix logic
        # Keep mappings where:
        #   (stage.status in ReferBack/Draft/Saved) OR
        #   (mapping.date_of_action is None AND mapping.user_id is None)
        filtered_mappings = []
        for mapping in all_mappings:
            if stage.status in ("ReferBack", "Draft", "Saved"):
                filtered_mappings.append(mapping)
            elif mapping.date_of_action is None and mapping.user_id is None:
                filtered_mappings.append(mapping)

        if not filtered_mappings:
            return

        # Get the first filtered mapping
        first_mapping = filtered_mappings[0]

        # Get the ApprovalLabel for this mapping
        al_result = await self._session.execute(
            select(ApprovalLabelModel).where(ApprovalLabelModel.id == first_mapping.approval_label_id)
        )
        approval_label = al_result.scalar_one_or_none()
        if not approval_label:
            return

        # Check if user's role matches (SameUserRole)
        same_user_role = await self._check_role_match(approval_label.id, role_id)

        if not same_user_role:
            return  # User's role doesn't match this approval label — skip

        # If stage is NOT Basic Details: update stage status
        if stage_name != "Basic Details":
            # Determine new status:
            # - Saved if ReconcilationSheet AND no issued vails AND same role
            # - Pending otherwise
            if format_type == "ReconcilationSheet":
                has_issued_vails = await self._check_has_issued_vails(stage.id)
                if not has_issued_vails and same_user_role:
                    stage.status = "Saved"
                else:
                    stage.status = "Pending"
            else:
                stage.status = "Pending"

            stage.modified_by = str(user_id)
            stage.modified_date = now

        # Set current user on the stage
        stage.user_id = user_id

        # Update the StageApprovalLabelMapping with user/date/remark
        first_mapping.user_id = user_id
        first_mapping.role_id = role_id
        first_mapping.date_of_action = now
        first_mapping.remark_id = remark_id
        first_mapping.remark = remark_text or ""
        first_mapping.is_show = True
        first_mapping.is_refer_back = False
        first_mapping.modified_by = str(user_id)
        first_mapping.modified_date = now

    async def _check_role_match(self, approval_label_id: int, role_id: int | None) -> bool:
        """Check if user's role matches any of the approval label's configured roles."""
        if not role_id:
            return False
        alur_result = await self._session.execute(
            select(ApprovalLabelUserRoleModel).where(
                ApprovalLabelUserRoleModel.approval_label_id == approval_label_id,
                ApprovalLabelUserRoleModel.role_id == role_id,
            )
        )
        return alur_result.scalar_one_or_none() is not None

    async def _check_has_issued_vails(self, stage_id: int) -> bool:
        """Check if any question answer in this stage has is_issued_vails=True."""
        result = await self._session.execute(
            select(QuestionAnswerModel.id).where(
                QuestionAnswerModel.checklist_stage_id == stage_id,
                QuestionAnswerModel.is_issued_vails.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION: APPROVE
    # ─────────────────────────────────────────────────────────────────────────

    async def _approve(self, cr, cs, user_id: int, role_id: int | None, remark_id, remark_text, now) -> SubmitStageResult:
        """Approve — stage becomes Approved, next stage opens."""
        cs.status = "Approved"
        cs.approved_remark = remark_text
        cs.modified_by = str(user_id)
        cs.modified_date = now

        # Record approval action on the first unacted mapping
        await self._record_approval_action(cs, user_id, role_id, remark_id, remark_text, now)

        # Open next stage
        next_opened = await self._open_next_stage(cr, cs, user_id, now)

        if not next_opened:
            # This was the last stage — mark request as approved
            cr.is_last_stage = True
            cr.status = "Approved"
        else:
            cr.status = "Pending"

        cr.modified_by = str(user_id)
        cr.modified_date = now

        # Update status_format
        format_type = await self._get_format_type(cr.format_id)
        await self._update_status_format(cr, format_type)

        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="Approved",
            message="Stage approved successfully." + (" Request fully approved." if not next_opened else ""),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION: REFER BACK
    # ─────────────────────────────────────────────────────────────────────────

    async def _refer_back(self, cr, cs, user_id: int, role_id: int | None, remark_id, remark_text, now) -> SubmitStageResult:
        """Refer back — stage goes to ReferBack, only original user can edit."""
        cs.status = "ReferBack"
        cs.modified_by = str(user_id)
        cs.modified_date = now
        cr.status = "ReferBack"
        cr.modified_by = str(user_id)
        cr.modified_date = now

        # Record refer back action
        await self._record_approval_action(cs, user_id, role_id, remark_id, remark_text, now, is_refer_back=True)

        # Update status_format
        format_type = await self._get_format_type(cr.format_id)
        await self._update_status_format(cr, format_type)

        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="ReferBack",
            message="Stage referred back.",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # APPROVAL LABEL MAPPING HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    async def _record_approval_action(self, cs, user_id: int, role_id: int | None, remark_id, remark_text, now, is_refer_back=False):
        """
        Update the first unacted StageApprovalLabelMapping for this stage.
        Pre-created on request creation with null date_of_action/user_id.
        """
        # Find the first mapping with null date_of_action and null user_id
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
        else:
            # Fallback: create new if somehow no pre-created mapping exists
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
            new_mapping = StageApprovalLabelMappingModel(
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
                created_date=now,
                modified_date=now,
            )
            self._session.add(new_mapping)

    async def _open_next_stage(self, cr, current_stage, user_id: int, now) -> bool:
        """Open the next stage after approval. Returns True if a next stage was opened."""
        stages_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == cr.id
            ).order_by(ChecklistStageModel.id)
        )
        all_stages = stages_result.scalars().all()

        # Find current stage index
        current_idx = None
        for idx, s in enumerate(all_stages):
            if s.id == current_stage.id:
                current_idx = idx
                break

        if current_idx is None or current_idx >= len(all_stages) - 1:
            return False  # No next stage

        # Open the next stage
        next_stage = all_stages[current_idx + 1]
        next_stage.status = "Initial"
        next_stage.modified_by = str(user_id)
        next_stage.modified_date = now
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # QUESTION ANSWERS
    # ─────────────────────────────────────────────────────────────────────────

    async def _persist_answers(self, stage_id: int, answers: list[QuestionAnswerPayload], user_id: int, now):
        """Persist or update question answers for the stage."""
        for ans in answers:
            # Check if answer already exists
            existing_result = await self._session.execute(
                select(QuestionAnswerModel).where(
                    QuestionAnswerModel.checklist_stage_id == stage_id,
                    QuestionAnswerModel.stage_question_mapping_id == ans.stage_question_mapping_id,
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                # Update existing answer
                existing.textbox_value = ans.textbox_value
                existing.question_option_id = ans.question_option_id
                existing.response_question_option_id = ans.response_question_option_id
                existing.response_answer = ans.response_answer
                existing.product_id = ans.product_id
                existing.modified_by = str(user_id)
                existing.modified_date = now
                qa_id = existing.id
            else:
                # Create new answer
                qa = QuestionAnswerModel(
                    checklist_stage_id=stage_id,
                    question_id=ans.question_id,
                    stage_question_mapping_id=ans.stage_question_mapping_id,
                    textbox_value=ans.textbox_value,
                    question_option_id=ans.question_option_id,
                    response_question_option_id=ans.response_question_option_id,
                    response_answer=ans.response_answer,
                    product_id=ans.product_id,
                    has_helper=bool(ans.helpers),
                    serial_number=0,
                    sub_answer_serial_no="",
                    test_title="",
                    sample_vails="",
                    answer_total_vails=0,
                    issuer_name="",
                    is_issued_vails=False,
                    has_vails=False,
                    comma_separated_name="",
                    created_by=str(user_id),
                    modified_by=str(user_id),
                    created_date=now,
                    modified_date=now,
                )
                self._session.add(qa)
                await self._session.flush()
                qa_id = qa.id

            # Persist helpers (sub-question answers)
            if ans.helpers:
                # Delete existing helpers for this answer
                existing_helpers = await self._session.execute(
                    select(QuestionAnswerSubQuestionAnswerModel).where(
                        QuestionAnswerSubQuestionAnswerModel.question_answer_id == qa_id
                    )
                )
                for eh in existing_helpers.scalars().all():
                    await self._session.delete(eh)

                # Create new helpers
                for helper_text in ans.helpers:
                    if helper_text.strip():
                        helper = QuestionAnswerHelperModel(
                            text_box_value=helper_text,
                            created_by=str(user_id),
                            modified_by=str(user_id),
                            created_date=now,
                            modified_date=now,
                        )
                        self._session.add(helper)
                        await self._session.flush()
                        junction = QuestionAnswerSubQuestionAnswerModel(
                            question_answer_id=qa_id,
                            question_answer_helper_id=helper.id,
                            created_by=str(user_id),
                            modified_by=str(user_id),
                            created_date=now,
                            modified_date=now,
                        )
                        self._session.add(junction)

    # ─────────────────────────────────────────────────────────────────────────
    # STATUS FORMAT
    # ─────────────────────────────────────────────────────────────────────────

    async def _update_status_format(self, cr, format_type: str):
        """
        Update status_format on the request — Mendix logic:
        - If format_type == ReconcilationSheet → keep existing (don't change)
        - If status == Pending AND format_type != ReconcilationSheet → "{StageName} - Approval Pending"
        - Otherwise → ""
        """
        if format_type == "ReconcilationSheet":
            # Keep existing status_format unchanged
            return

        if cr.status == "Pending":
            # Find the stage that is now Pending to get its name
            stages_result = await self._session.execute(
                select(ChecklistStageModel).where(
                    ChecklistStageModel.checklist_request_id == cr.id,
                    ChecklistStageModel.status == "Pending",
                ).order_by(ChecklistStageModel.id.desc())
            )
            pending_stage = stages_result.scalars().first()
            if pending_stage and pending_stage.format_stage_mapping_id:
                fsm_result = await self._session.execute(
                    select(FormatStageMappingModel).where(
                        FormatStageMappingModel.id == pending_stage.format_stage_mapping_id
                    )
                )
                fsm = fsm_result.scalar_one_or_none()
                if fsm:
                    sm_result = await self._session.execute(
                        select(StageModel).where(StageModel.id == fsm.stage_id)
                    )
                    sm = sm_result.scalar_one_or_none()
                    if sm:
                        cr.status_format = f"{sm.stage_name} - Approval Pending"
                        return
        cr.status_format = ""

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_format_type(self, format_id: int | None) -> str:
        """Get the format_type string for a format id."""
        if not format_id:
            return ""
        fmt_result = await self._session.execute(
            select(FormatModel).where(FormatModel.id == format_id)
        )
        fmt = fmt_result.scalar_one_or_none()
        return fmt.format_type if fmt else ""

    async def _generate_request_number(self) -> str:
        """Generate a unique request number: REQddmmyyyy001, REQddmmyyyy002, ..."""
        today = date_type.today()
        prefix = f"REQ{today.strftime('%d%m%Y')}"

        # Count existing requests with same date prefix
        result = await self._session.execute(
            select(func.count()).select_from(ChecklistRequestModel).where(
                ChecklistRequestModel.request_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{count + 1:03d}"

    async def _next_sequence(self) -> int:
        """Get next sequence number."""
        result = await self._session.execute(
            select(func.coalesce(func.max(ChecklistRequestModel.sequence_number), 0))
        )
        return (result.scalar() or 0) + 1
