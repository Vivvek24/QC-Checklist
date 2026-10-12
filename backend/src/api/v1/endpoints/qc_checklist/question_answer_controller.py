"""QuestionAnswer — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.question_answer_schema import (
    QuestionAnswerCreate,
    QuestionAnswerListResponse,
    QuestionAnswerResponse,
    QuestionAnswerUpdate,
)
from src.application.dtos.qc_checklist.question_answer_dtos import (
    CreateQuestionAnswerDTO,
    UpdateQuestionAnswerDTO,
)
from src.application.services.qc_checklist.question_answer_service import QuestionAnswerService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.models.qc_checklist.question_answer_model import (
    QuestionAnswerModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import (
    QuestionAnswerSubQuestionAnswerModel,
)
from src.infrastructure.database.repositories.qc_checklist.question_answer_repository_impl import (
    QuestionAnswerRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/question-answers", tags=["QC Checklist - Question Answers"])
RESOURCE = "question_answers"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> QuestionAnswerService:
    return QuestionAnswerService(repo=QuestionAnswerRepositoryImpl(session))


class SubAnswerItem(BaseModel):
    """One sub-question's saved answer under a parent question."""
    question_id: int
    question_option_id: int | None = None
    response_question_option_id: int | None = None
    textbox_value: str = ""
    response_answer: str = ""


class ParentSubAnswers(BaseModel):
    """A parent question's saved sub-answers (grouped for the fill page)."""
    parent_question_id: int
    sub_answers: list[SubAnswerItem]


class SubAnswersResponse(BaseModel):
    items: list[ParentSubAnswers]


@router.get("/sub-answers", response_model=SubAnswersResponse,
            summary="Saved sub-question answers for a stage, grouped by parent question",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_sub_answers(
    checklist_stage_id: int = Query(..., description="Stage to load sub-answers for"),
    session: AsyncSession = Depends(get_db_session),
) -> SubAnswersResponse:
    """For each parent answer in the stage, return its sub-answers keyed by the
    parent's question_id — so the fill page can repopulate each sub-question's
    input. Sub-answers are child question_answers rows linked via the self-join."""
    parent = aliased(QuestionAnswerModel)
    child = aliased(QuestionAnswerModel)
    stmt = (
        select(
            parent.question_id.label("parent_question_id"),
            child.question_id.label("question_id"),
            child.question_option_id.label("question_option_id"),
            child.response_question_option_id.label("response_question_option_id"),
            child.textbox_value.label("textbox_value"),
            child.response_answer.label("response_answer"),
        )
        .select_from(QuestionAnswerSubQuestionAnswerModel)
        .join(parent, parent.id == QuestionAnswerSubQuestionAnswerModel.question_answer_parent_id)
        .join(child, child.id == QuestionAnswerSubQuestionAnswerModel.question_answer_id)
        .where(parent.checklist_stage_id == checklist_stage_id)
        .order_by(parent.question_id, child.id)
    )
    rows = (await session.execute(stmt)).all()

    grouped: dict[int, list[SubAnswerItem]] = {}
    for r in rows:
        grouped.setdefault(r.parent_question_id, []).append(
            SubAnswerItem(
                question_id=r.question_id,
                question_option_id=r.question_option_id,
                response_question_option_id=r.response_question_option_id,
                textbox_value=r.textbox_value or "",
                response_answer=r.response_answer or "",
            )
        )
    return SubAnswersResponse(
        items=[
            ParentSubAnswers(parent_question_id=pid, sub_answers=subs)
            for pid, subs in grouped.items()
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
        items = await service.list_by_checklist_stage(checklist_stage_id)
        return QuestionAnswerListResponse(
            items=[QuestionAnswerResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    if stage_question_mapping_id is not None:
        items = await service.list_by_stage_question_mapping(stage_question_mapping_id)
        return QuestionAnswerListResponse(
            items=[QuestionAnswerResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
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
async def get_answer(answer_id: int, service: QuestionAnswerService = Depends(_get_service)) -> QuestionAnswerResponse:
    try:
        return QuestionAnswerResponse(**(await service.get_answer(answer_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{answer_id}", response_model=QuestionAnswerResponse, summary="Update a question answer",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_answer(
    answer_id: int, request: QuestionAnswerUpdate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionAnswerService = Depends(_get_service),
) -> QuestionAnswerResponse:
    try:
        dto = UpdateQuestionAnswerDTO(**request.model_dump(exclude_unset=True))
        return QuestionAnswerResponse(**(await service.update_answer(answer_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{answer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a question answer",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_answer(answer_id: int, service: QuestionAnswerService = Depends(_get_service)) -> None:
    try:
        await service.delete_answer(answer_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
