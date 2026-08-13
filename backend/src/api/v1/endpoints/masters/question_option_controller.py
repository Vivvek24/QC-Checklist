"""QuestionOption Master — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.question_option_schema import (
    QuestionOptionCreate,
    QuestionOptionListResponse,
    QuestionOptionResponse,
    QuestionOptionUpdate,
)
from src.application.dtos.masters.question_option_dtos import CreateQuestionOptionDTO, UpdateQuestionOptionDTO
from src.application.services.masters.question_option_service import QuestionOptionService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.question_option_repository_impl import QuestionOptionRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/question-options", tags=["Masters - Question Option"])
RESOURCE = "question_options"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> QuestionOptionService:
    return QuestionOptionService(repo=QuestionOptionRepositoryImpl(session))


@router.get("", response_model=QuestionOptionListResponse, summary="List question options",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_question_options(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None), is_active: bool | None = Query(None),
    question_id: int | None = Query(None),
    service: QuestionOptionService = Depends(_get_service),
) -> QuestionOptionListResponse:
    if question_id is not None:
        items = await service.list_by_question(question_id)
        return QuestionOptionListResponse(
            items=[QuestionOptionResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_question_options(skip=skip, limit=limit, search=search, is_active=is_active)
    return QuestionOptionListResponse(
        items=[QuestionOptionResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a question option",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_question_option(
    request: QuestionOptionCreate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionOptionService = Depends(_get_service),
) -> QuestionOptionResponse:
    try:
        dto = CreateQuestionOptionDTO(
            option_title=request.option_title,
            is_response_option=request.is_response_option,
            question_id=request.question_id,
            is_active=request.is_active,
        )
        return QuestionOptionResponse(**(await service.create_question_option(dto, current_user)).__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{option_id}", response_model=QuestionOptionResponse, summary="Get a question option",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_question_option(option_id: int, service: QuestionOptionService = Depends(_get_service)) -> QuestionOptionResponse:
    try:
        return QuestionOptionResponse(**(await service.get_question_option(option_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{option_id}", response_model=QuestionOptionResponse, summary="Update a question option",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_question_option(
    option_id: int, request: QuestionOptionUpdate,
    current_user: User = Depends(get_current_active_user),
    service: QuestionOptionService = Depends(_get_service),
) -> QuestionOptionResponse:
    try:
        dto = UpdateQuestionOptionDTO(
            option_title=request.option_title,
            is_response_option=request.is_response_option,
            question_id=request.question_id,
            is_active=request.is_active,
        )
        return QuestionOptionResponse(**(await service.update_question_option(option_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{option_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a question option",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_question_option(option_id: int, service: QuestionOptionService = Depends(_get_service)) -> None:
    try:
        await service.delete_question_option(option_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
