"""QuestionAnswer — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.question_answer_schema import (
    QuestionAnswerCreate,
    QuestionAnswerListResponse,
    QuestionAnswerResponse,
    QuestionAnswerUpdate,
)
from src.application.dtos.qc_checklist.question_answer_dtos import CreateQuestionAnswerDTO, UpdateQuestionAnswerDTO
from src.application.services.qc_checklist.question_answer_service import QuestionAnswerService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.qc_checklist.question_answer_repository_impl import QuestionAnswerRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/question-answers", tags=["QC Checklist - Question Answers"])
RESOURCE = "question_answers"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> QuestionAnswerService:
    return QuestionAnswerService(repo=QuestionAnswerRepositoryImpl(session))


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
