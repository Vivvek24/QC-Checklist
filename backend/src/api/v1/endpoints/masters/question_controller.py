"""Question Master — API controller."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.question_schema import QuestionCreate, QuestionListResponse, QuestionResponse, QuestionUpdate
from src.application.dtos.masters.question_dtos import CreateQuestionDTO, UpdateQuestionDTO
from src.application.services.masters.question_service import QuestionService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.question_repository_impl import QuestionRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/questions", tags=["Masters - Question"])
RESOURCE = "questions"

def _svc(s: AsyncSession = Depends(get_db_session)) -> QuestionService:
    return QuestionService(repo=QuestionRepositoryImpl(s))

@router.get("", response_model=QuestionListResponse, dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_questions(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                         search: str | None = Query(None), is_active: bool | None = Query(None),
                         svc: QuestionService = Depends(_svc)):
    r = await svc.list_questions(skip=skip, limit=limit, search=search, is_active=is_active)
    return QuestionListResponse(items=[QuestionResponse(**i.__dict__) for i in r.items], total=r.total, skip=r.skip, limit=r.limit)

@router.post("", response_model=QuestionResponse, status_code=201, dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_question(req: QuestionCreate, user: User = Depends(get_current_active_user), svc: QuestionService = Depends(_svc)):
    try:
        dto = CreateQuestionDTO(
            title=req.title, answer_type=req.answer_type,
            has_text_box=req.has_text_box, has_multiple_text_box=req.has_multiple_text_box,
            has_sub_question=req.has_sub_question, is_validation_required=req.is_validation_required,
            has_response_option=req.has_response_option, allow_multiple_input=req.allow_multiple_input,
            has_associated_master=req.has_associated_master, is_calculated=req.is_calculated,
            is_active=req.is_active, validation_type_id=req.validation_type_id,
            parent_question_id=req.parent_question_id, master_type=req.master_type,
            sub_question_ids=req.sub_question_ids,
        )
        return QuestionResponse(**(await svc.create_question(dto, user)).__dict__)
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.get("/{qid}", response_model=QuestionResponse, dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_question(qid: int, svc: QuestionService = Depends(_svc)):
    try: return QuestionResponse(**(await svc.get_question(qid)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e

@router.patch("/{qid}", response_model=QuestionResponse, dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_question(qid: int, req: QuestionUpdate, user: User = Depends(get_current_active_user), svc: QuestionService = Depends(_svc)):
    try:
        dto = UpdateQuestionDTO(
            title=req.title, answer_type=req.answer_type,
            has_text_box=req.has_text_box, has_multiple_text_box=req.has_multiple_text_box,
            has_sub_question=req.has_sub_question, is_validation_required=req.is_validation_required,
            has_response_option=req.has_response_option, allow_multiple_input=req.allow_multiple_input,
            has_associated_master=req.has_associated_master, is_calculated=req.is_calculated,
            is_active=req.is_active, validation_type_id=req.validation_type_id,
            parent_question_id=req.parent_question_id, master_type=req.master_type,
            sub_question_ids=req.sub_question_ids,
        )
        return QuestionResponse(**(await svc.update_question(qid, dto, user)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.delete("/{qid}", status_code=204, dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_question(qid: int, svc: QuestionService = Depends(_svc)):
    try: await svc.delete_question(qid)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
