"""Request creation — provisioning a brand-new checklist request.

Distinct from ChecklistRequestService (plain one-row CRUD): this provisions the
whole request TREE on first submit — the ChecklistRequest plus all its
ChecklistStages plus a StageApprovalLabelMapping per active approval label,
applying the "first two stages open (Initial), rest closed" rule. Also owns the
request-number / sequence generation and format-type lookup those need.

Composed by StageActionBase so the action services don't carry this.
"""

from datetime import date as date_type
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.masters.approval_label_model import ApprovalLabelModel
from src.infrastructure.database.models.masters.format_model import FormatModel
from src.infrastructure.database.models.masters.format_stage_mapping_model import (
    FormatStageMappingModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_request_model import (
    ChecklistRequestModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import (
    ChecklistStageModel,
)
from src.infrastructure.database.models.qc_checklist.stage_approval_label_mapping_model import (
    StageApprovalLabelMappingModel,
)


class RequestCreationService:
    """Provisions a new checklist request and its full stage/approval tree."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_format_type(self, format_id: int | None) -> str:
        if not format_id:
            return ""
        fmt_result = await self._session.execute(
            select(FormatModel).where(FormatModel.id == format_id)
        )
        fmt = fmt_result.scalar_one_or_none()
        return fmt.format_type if fmt else ""

    async def generate_request_number(self) -> str:
        today = date_type.today()
        prefix = f"REQ{today.strftime('%d%m%Y')}"
        result = await self._session.execute(
            select(func.count()).select_from(ChecklistRequestModel).where(
                ChecklistRequestModel.request_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{count + 1:03d}"

    async def next_sequence(self) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(ChecklistRequestModel.sequence_number), 0))
        )
        return (result.scalar() or 0) + 1

    async def create_request_with_stages(
        self, format_id: int, user_id: int, now: datetime,
    ) -> ChecklistRequestModel:
        """Create ChecklistRequest + ALL ChecklistStages + ALL StageApprovalLabelMappings."""
        checklist_request = ChecklistRequestModel(
            status="Draft",
            request_number=await self.generate_request_number(),
            status_format="",
            is_last_stage=False,
            is_removed=False,
            sequence_number=await self.next_sequence(),
            format_id=format_id,
            created_by=str(user_id),
            modified_by=str(user_id),
            created_date=now,
            modified_date=now,
        )
        self._session.add(checklist_request)
        await self._session.flush()

        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(
                FormatStageMappingModel.format_id == format_id
            ).order_by(FormatStageMappingModel.id)
        )
        all_fsms = fsm_result.scalars().all()

        for idx, fsm in enumerate(all_fsms):
            stage_status = "Initial" if idx < 2 else ""
            self._session.add(ChecklistStageModel(
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
            ))
        await self._session.flush()

        all_new_stages_result = await self._session.execute(
            select(ChecklistStageModel).where(
                ChecklistStageModel.checklist_request_id == checklist_request.id
            ).order_by(ChecklistStageModel.id)
        )
        for stage in all_new_stages_result.scalars().all():
            if not stage.format_stage_mapping_id:
                continue
            fsm_obj_result = await self._session.execute(
                select(FormatStageMappingModel).where(
                    FormatStageMappingModel.id == stage.format_stage_mapping_id
                )
            )
            fsm_obj = fsm_obj_result.scalar_one_or_none()
            if not fsm_obj:
                continue
            al_result = await self._session.execute(
                select(ApprovalLabelModel).where(
                    ApprovalLabelModel.stage_id == fsm_obj.stage_id,
                    ApprovalLabelModel.is_active.is_(True),
                ).order_by(ApprovalLabelModel.id)
            )
            for al in al_result.scalars().all():
                self._session.add(StageApprovalLabelMappingModel(
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
                ))
        await self._session.flush()
        return checklist_request
