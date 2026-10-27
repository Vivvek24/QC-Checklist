"""QuestionAnswer — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.question_answer_schema import (
    ParentSubAnswers,
    QuestionAnswerCreate,
    QuestionAnswerListResponse,
    QuestionAnswerResponse,
    QuestionAnswerUpdate,
    SubAnswerItem,
    SubAnswersResponse,
)
from src.application.dtos.qc_checklist.question_answer_dtos import (
    CreateQuestionAnswerDTO,
    UpdateQuestionAnswerDTO,
)
from src.application.services.qc_checklist.issue_vials_service import IssueVialsService
from src.application.services.qc_checklist.question_answer_service import QuestionAnswerService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import (
    BusinessRuleViolationError,
    EntityNotFoundError,
)
from src.infrastructure.database.models.qc_checklist.question_answer_model import (
    QuestionAnswerModel,
)
from src.infrastructure.database.repositories.qc_checklist.question_answer_repository_impl import (
    QuestionAnswerRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(
    prefix="/qc-checklist/question-answers", tags=["QC Checklist - Question Answers"]
)
RESOURCE = "question_answers"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> QuestionAnswerService:
    return QuestionAnswerService(repo=QuestionAnswerRepositoryImpl(session))


@router.get("/sub-answers", response_model=SubAnswersResponse,
            summary="Saved sub-question answers for a stage, grouped by parent question",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_sub_answers(
    checklist_stage_id: int = Query(..., description="Stage to load sub-answers for"),
    service: QuestionAnswerService = Depends(_get_service),
) -> SubAnswersResponse:
    groups = await service.list_sub_answers(checklist_stage_id)
    return SubAnswersResponse(
        items=[
            ParentSubAnswers(
                parent_question_id=g.parent_question_id,
                sub_answers=[SubAnswerItem(**vars(s)) for s in g.sub_answers],
            )
            for g in groups
        ]
    )


@router.get("", response_model=QuestionAnswerListResponse, summary="List question answers",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_answers(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    checklist_stage_id: int | None = Query(None),
    stage_question_mapping_id: int | None = Query(None),
    service: QuestionAnswerService = Depends(_get_service),
) -> QuestionAnswerListResponse:
    if checklist_stage_id is not None:
        stage_items = await service.list_stage_answers(checklist_stage_id)
        return QuestionAnswerListResponse(
            items=[
                QuestionAnswerResponse(**{**vars(i), "helpers": list(i.helpers)})
                for i in stage_items
            ],
            total=len(stage_items), skip=0, limit=len(stage_items),
        )
    if stage_question_mapping_id is not None:
        mapped_items = await service.list_by_stage_question_mapping(stage_question_mapping_id)
        return QuestionAnswerListResponse(
            items=[QuestionAnswerResponse(**i.__dict__) for i in mapped_items],
            total=len(mapped_items), skip=0, limit=len(mapped_items),
        )
    result = await service.list_answers(skip=skip, limit=limit)
    return QuestionAnswerListResponse(
        items=[QuestionAnswerResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=QuestionAnswerResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a question answer",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_answer(
    request: QuestionAnswerCreate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionAnswerService = Depends(_get_service),
) -> QuestionAnswerResponse:
    dto = CreateQuestionAnswerDTO(**request.model_dump())
    return QuestionAnswerResponse(**(await service.create_answer(dto, current_user)).__dict__)


@router.get("/{answer_id}", response_model=QuestionAnswerResponse, summary="Get a question answer",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_answer(
    answer_id: int, service: QuestionAnswerService = Depends(_get_service),
) -> QuestionAnswerResponse:
    try:
        return QuestionAnswerResponse(**(await service.get_answer(answer_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


class IssueVialsRequest(BaseModel):
    """Payload for the supervisor "Issue Vials" action on a test row.

    `receiver_user_id` is the analyst the vials are issued to (picked in the
    dialog). The issue timestamp and the issuer's name are set server-side."""
    receiver_user_id: int | None = None


async def _serialize_model(
    session: AsyncSession, answer: QuestionAnswerModel,
) -> QuestionAnswerResponse:
    """Map an issued/calculated QuestionAnswer ORM row to the API response,
    resolving the receiver's display name via the repository (no DB access in
    the controller itself)."""
    repo = QuestionAnswerRepositoryImpl(session)
    names = await repo.resolve_user_names(
        {answer.receiver_user_id} if answer.receiver_user_id else set()
    )
    return QuestionAnswerResponse(
        id=answer.id,
        checklist_stage_id=answer.checklist_stage_id,
        checklist_stage_section_id=answer.checklist_stage_section_id,
        product_id=answer.product_id,
        question_id=answer.question_id,
        question_option_id=answer.question_option_id,
        receiver_user_id=answer.receiver_user_id,
        response_question_option_id=answer.response_question_option_id,
        stage_question_mapping_id=answer.stage_question_mapping_id,
        textbox_value=answer.textbox_value,
        response_answer=answer.response_answer,
        comma_separated_name=answer.comma_separated_name,
        has_helper=answer.has_helper,
        serial_number=answer.serial_number,
        sub_answer_serial_no=answer.sub_answer_serial_no,
        date_time=answer.date_time,
        test_title=answer.test_title,
        sample_vails=answer.sample_vails,
        answer_total_vails=answer.answer_total_vails,
        issued_by_date=answer.issued_by_date,
        received_by_date=answer.received_by_date,
        issuer_name=answer.issuer_name,
        is_issued_vails=answer.is_issued_vails,
        has_vails=answer.has_vails,
        receiver_name=names.get(answer.receiver_user_id or 0, ""),
        created_by=answer.created_by,
        created_date=answer.created_date,
        modified_by=answer.modified_by,
        modified_date=answer.modified_date,
    )


@router.post("/{answer_id}/issue-vials", response_model=QuestionAnswerResponse,
             summary="Issue vials for a test row (supervisor action)",
             dependencies=[Depends(require_api_permission("qc_checklist", "EXECUTE"))])
async def issue_vials(
    answer_id: int, request: IssueVialsRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> QuestionAnswerResponse:
    """Persist the "Issue Vials" action (ports the Mendix save microflow):

    - require a selected analyst (else 400 'Please Select Analyst Name!');
    - stamp the Basic Details StartDate answer with now if it's still empty;
    - set issued_by_date / received_by_date = now, is_issued_vails = true, and
      issuer_name = the acting user's full name on the clicked answer.

    Authorised by the `qc_checklist:EXECUTE` grant — the same responsibility the
    UI gates the button on (seeded to SUPERVISOR + ADMINISTRATOR)."""
    service = IssueVialsService(session)
    try:
        answer = await service.issue_vials(
            answer_id=answer_id,
            user_id=current_user.id,
            receiver_user_id=request.receiver_user_id,
        )
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except BusinessRuleViolationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return await _serialize_model(session, answer)


@router.post("/{answer_id}/calculate-sample-destroyed", response_model=QuestionAnswerResponse,
             summary="Calculate 'Remaining Samples destroyed By' (analyst action)",
             dependencies=[Depends(require_api_permission("qc_checklist", "EXECUTE"))])
async def calculate_sample_destroyed(
    answer_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> QuestionAnswerResponse:
    """Compute the destroyed-samples value (ports the Mendix Calculate microflow):
    received_total (Basic Details is_calculated answer_total_vails) minus the
    Test stage's Sample Consumed. Blocks (400) when vials are unissued, the
    product isn't picked, or the result would be negative."""
    service = IssueVialsService(session)
    try:
        answer = await service.calculate_sample_destroyed(
            answer_id=answer_id, user_id=current_user.id,
        )
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except BusinessRuleViolationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return await _serialize_model(session, answer)


@router.patch("/{answer_id}", response_model=QuestionAnswerResponse,
              summary="Update a question answer",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_answer(
    answer_id: int, request: QuestionAnswerUpdate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionAnswerService = Depends(_get_service),
) -> QuestionAnswerResponse:
    try:
        dto = UpdateQuestionAnswerDTO(**request.model_dump(exclude_unset=True))
        updated = await service.update_answer(answer_id, dto, current_user)
        return QuestionAnswerResponse(**updated.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{answer_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a question answer",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_answer(
    answer_id: int, service: QuestionAnswerService = Depends(_get_service),
) -> None:
    try:
        await service.delete_answer(answer_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
