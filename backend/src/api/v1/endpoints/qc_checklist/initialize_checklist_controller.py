"""Initialize Checklist - API controller (thin layer delegating to service)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.application.services.qc_checklist.initialize_checklist_service import InitializeChecklistService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - Initialize"])


# --- Response schemas ---

class QuestionOptionSchema(BaseModel):
    id: int
    label: str


class QuestionAnswerPreview(BaseModel):
    stage_question_mapping_id: int
    question_id: int
    question_title: str
    serial_number: int
    section_id: int | None = None
    section_name: str | None = None
    show_on_grid: bool = False
    answer_type: str = ""
    has_text_box: bool = False
    has_multiple_text_box: bool = False
    has_sub_question: bool = False
    is_declaration_question: bool = False
    aql_limit: str = ""
    sub_questions: list['QuestionAnswerPreview'] = []
    options: list[QuestionOptionSchema] = []
    response_options: list[QuestionOptionSchema] = []


class ApprovalLabelPreview(BaseModel):
    approval_label_id: int
    label: str


class SectionPreview(BaseModel):
    section_id: int
    section_name: str
    questions: list[QuestionAnswerPreview]


class ChecklistStagePreview(BaseModel):
    format_stage_mapping_id: int
    stage_id: int
    stage_name: str
    is_approvable: bool
    has_section: bool
    status: str
    questions: list[QuestionAnswerPreview]
    sections: list[SectionPreview]
    approval_labels: list[ApprovalLabelPreview]


class ChecklistPreviewResponse(BaseModel):
    format_id: int
    format_name: str
    format_no: str
    format_type: str
    has_declaration_question: bool
    unit_name: str
    stages: list[ChecklistStagePreview]


def _get_service(session: AsyncSession = Depends(get_db_session)) -> InitializeChecklistService:
    return InitializeChecklistService(session)


def _serialize_question(q) -> QuestionAnswerPreview:
    """Recursively serialize a QuestionAnswerPreviewDTO into response schema."""
    return QuestionAnswerPreview(
        stage_question_mapping_id=q.stage_question_mapping_id,
        question_id=q.question_id,
        question_title=q.question_title,
        serial_number=q.serial_number,
        section_id=q.section_id,
        section_name=q.section_name,
        show_on_grid=q.show_on_grid,
        answer_type=q.answer_type,
        has_text_box=q.has_text_box,
        has_multiple_text_box=q.has_multiple_text_box,
        has_sub_question=q.has_sub_question,
        is_declaration_question=q.is_declaration_question,
        aql_limit=q.aql_limit,
        sub_questions=[_serialize_question(sq) for sq in (q.sub_questions or [])],
        options=[QuestionOptionSchema(id=o.id, label=o.label) for o in q.options],
        response_options=[QuestionOptionSchema(id=o.id, label=o.label) for o in (q.response_options or [])],
    )


@router.get("/preview", response_model=ChecklistPreviewResponse,
            summary="Preview checklist structure for a format (no DB write)",
            dependencies=[Depends(require_api_permission("checklist_requests", "READ"))])
async def preview_checklist(
    format_id: int = Query(..., gt=0),
    service: InitializeChecklistService = Depends(_get_service),
) -> ChecklistPreviewResponse:
    """Returns the full checklist structure in memory for a given format. Nothing is persisted."""
    try:
        dto = await service.get_preview(format_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return ChecklistPreviewResponse(
        format_id=dto.format_id,
        format_name=dto.format_name,
        format_no=dto.format_no,
        format_type=dto.format_type,
        has_declaration_question=dto.has_declaration_question,
        unit_name=dto.unit_name,
        stages=[
            ChecklistStagePreview(
                format_stage_mapping_id=s.format_stage_mapping_id,
                stage_id=s.stage_id,
                stage_name=s.stage_name,
                is_approvable=s.is_approvable,
                has_section=s.has_section,
                status=s.status,
                questions=[_serialize_question(q) for q in s.questions],
                sections=[
                    SectionPreview(
                        section_id=sec.section_id,
                        section_name=sec.section_name,
                        questions=[_serialize_question(q) for q in sec.questions],
                    ) for sec in s.sections
                ],
                approval_labels=[
                    ApprovalLabelPreview(approval_label_id=al.approval_label_id, label=al.label)
                    for al in s.approval_labels
                ],
            ) for s in dto.stages
        ],
    )
