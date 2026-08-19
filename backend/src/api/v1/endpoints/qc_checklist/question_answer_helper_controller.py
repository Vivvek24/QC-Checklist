"""QuestionAnswerHelper — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.question_answer_helper_schema import (
    QuestionAnswerHelperCreate,
    QuestionAnswerHelperListResponse,
    QuestionAnswerHelperResponse,
    QuestionAnswerHelperUpdate,
)
from src.application.dtos.qc_checklist.question_answer_helper_dtos import CreateQuestionAnswerHelperDTO, UpdateQuestionAnswerHelperDTO
from src.application.services.qc_checklist.question_answer_helper_service import QuestionAnswerHelperService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.qc_checklist.question_answer_helper_repository_impl import QuestionAnswerHelperRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/question-answer-helpers", tags=["QC Checklist - Question Answer Helpers"])
RESOURCE = "question_answer_helpers"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> QuestionAnswerHelperService:
    return QuestionAnswerHelperService(repo=QuestionAnswerHelperRepositoryImpl(session))


@router.get("", response_model=QuestionAnswerHelperListResponse, summary="List question answer helpers",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_helpers(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    question_answer_id: int | None = Query(None),
    service: QuestionAnswerHelperService = Depends(_get_service),
) -> QuestionAnswerHelperListResponse:
    if question_answer_id is not None:
        items = await service.list_by_question_answer(question_answer_id)
        return QuestionAnswerHelperListResponse(
            items=[QuestionAnswerHelperResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_helpers(skip=skip, limit=limit)
    return QuestionAnswerHelperListResponse(
        items=[QuestionAnswerHelperResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=QuestionAnswerHelperResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a question answer helper",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_helper(
    request: QuestionAnswerHelperCreate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionAnswerHelperService = Depends(_get_service),
    session: AsyncSession = Depends(get_db_session),
) -> QuestionAnswerHelperResponse:
    dto = CreateQuestionAnswerHelperDTO(text_box_value=request.text_box_value)
    result = await service.create_helper(dto, current_user)

    # If question_answer_id provided, link via junction table
    if request.question_answer_id:
        repo = QuestionAnswerHelperRepositoryImpl(session)
        await repo.link_to_question_answer(request.question_answer_id, result.id, current_user.username)

    return QuestionAnswerHelperResponse(**result.__dict__)


@router.get("/{helper_id}", response_model=QuestionAnswerHelperResponse, summary="Get a question answer helper",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_helper(helper_id: int, service: QuestionAnswerHelperService = Depends(_get_service)) -> QuestionAnswerHelperResponse:
    try:
        return QuestionAnswerHelperResponse(**(await service.get_helper(helper_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{helper_id}", response_model=QuestionAnswerHelperResponse, summary="Update a question answer helper",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_helper(
    helper_id: int, request: QuestionAnswerHelperUpdate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionAnswerHelperService = Depends(_get_service),
) -> QuestionAnswerHelperResponse:
    try:
        dto = UpdateQuestionAnswerHelperDTO(text_box_value=request.text_box_value)
        return QuestionAnswerHelperResponse(**(await service.update_helper(helper_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{helper_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a question answer helper",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_helper(helper_id: int, service: QuestionAnswerHelperService = Depends(_get_service)) -> None:
    try:
        await service.delete_helper(helper_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
