from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.approval_label_schema import *
from src.application.dtos.masters.approval_label_dtos import CreateApprovalLabelDTO, UpdateApprovalLabelDTO
from src.application.services.masters.approval_label_service import ApprovalLabelService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.approval_label_repository_impl import ApprovalLabelRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/approval-labels", tags=["Masters - Approval Label"])
R = "approval_labels"
def _svc(s: AsyncSession = Depends(get_db_session)) -> ApprovalLabelService: return ApprovalLabelService(repo=ApprovalLabelRepositoryImpl(s))

@router.get("", response_model=ApprovalLabelListResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def list_all(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), search: str | None = Query(None), is_active: bool | None = Query(None), stage_id: int | None = Query(None), svc: ApprovalLabelService = Depends(_svc)):
    r = await svc.list_all(skip=skip, limit=limit, search=search, is_active=is_active, stage_id=stage_id)
    return ApprovalLabelListResponse(items=[ApprovalLabelResponse(**i.__dict__) for i in r.items], total=r.total, skip=r.skip, limit=r.limit)

@router.post("", response_model=ApprovalLabelResponse, status_code=201, dependencies=[Depends(require_api_permission(R, "CREATE"))])
async def create(req: ApprovalLabelCreate, user: User = Depends(get_current_active_user), svc: ApprovalLabelService = Depends(_svc)):
    try: return ApprovalLabelResponse(**(await svc.create(CreateApprovalLabelDTO(label=req.label, stage_id=req.stage_id, role_ids=req.role_ids, is_active=req.is_active), user)).__dict__)
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.get("/{id}", response_model=ApprovalLabelResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def get(id: int, svc: ApprovalLabelService = Depends(_svc)):
    try: return ApprovalLabelResponse(**(await svc.get(id)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e

@router.patch("/{id}", response_model=ApprovalLabelResponse, dependencies=[Depends(require_api_permission(R, "UPDATE"))])
async def update(id: int, req: ApprovalLabelUpdate, user: User = Depends(get_current_active_user), svc: ApprovalLabelService = Depends(_svc)):
    try: return ApprovalLabelResponse(**(await svc.update(id, UpdateApprovalLabelDTO(label=req.label, stage_id=req.stage_id, role_ids=req.role_ids, is_active=req.is_active), user)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.delete("/{id}", status_code=204, dependencies=[Depends(require_api_permission(R, "DELETE"))])
async def delete(id: int, svc: ApprovalLabelService = Depends(_svc)):
    try: await svc.delete(id)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
