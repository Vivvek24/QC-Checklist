from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.remark_schema import *
from src.application.dtos.masters.remark_dtos import CreateRemarkDTO, UpdateRemarkDTO
from src.application.services.masters.remark_service import RemarkService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.masters.remark_repository_impl import RemarkRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/remarks", tags=["Masters - Remark"])
R = "remarks"
def _svc(s: AsyncSession = Depends(get_db_session)) -> RemarkService: return RemarkService(repo=RemarkRepositoryImpl(s))

@router.get("", response_model=RemarkListResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def list_all(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), search: str | None = Query(None), is_active: bool | None = Query(None), svc: RemarkService = Depends(_svc)):
    r = await svc.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
    return RemarkListResponse(items=[RemarkResponse(**i.__dict__) for i in r.items], total=r.total, skip=r.skip, limit=r.limit)

@router.post("", response_model=RemarkResponse, status_code=201, dependencies=[Depends(require_api_permission(R, "CREATE"))])
async def create(req: RemarkCreate, user: User = Depends(get_current_active_user), svc: RemarkService = Depends(_svc)):
    return RemarkResponse(**(await svc.create(CreateRemarkDTO(remark=req.remark, role_ids=req.role_ids, is_active=req.is_active), user)).__dict__)

@router.get("/{id}", response_model=RemarkResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def get(id: int, svc: RemarkService = Depends(_svc)):
    try: return RemarkResponse(**(await svc.get(id)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e

@router.patch("/{id}", response_model=RemarkResponse, dependencies=[Depends(require_api_permission(R, "UPDATE"))])
async def update(id: int, req: RemarkUpdate, user: User = Depends(get_current_active_user), svc: RemarkService = Depends(_svc)):
    try: return RemarkResponse(**(await svc.update(id, UpdateRemarkDTO(remark=req.remark, role_ids=req.role_ids, is_active=req.is_active), user)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e

@router.delete("/{id}", status_code=204, dependencies=[Depends(require_api_permission(R, "DELETE"))])
async def delete(id: int, svc: RemarkService = Depends(_svc)):
    try: await svc.delete(id)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
