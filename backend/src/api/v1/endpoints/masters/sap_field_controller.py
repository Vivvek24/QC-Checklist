from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.sap_field_schema import *
from src.application.dtos.masters.sap_field_dtos import CreateSapFieldDTO, UpdateSapFieldDTO
from src.application.services.masters.sap_field_service import SapFieldService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.sap_field_repository_impl import SapFieldRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/sap-fields", tags=["Masters - SAP Field"])
R = "sap_fields"
def _svc(s: AsyncSession = Depends(get_db_session)) -> SapFieldService: return SapFieldService(repo=SapFieldRepositoryImpl(s))

@router.get("", response_model=SapFieldListResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def list_all(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), search: str | None = Query(None), is_active: bool | None = Query(None), svc: SapFieldService = Depends(_svc)):
    r = await svc.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
    return SapFieldListResponse(items=[SapFieldResponse(**i.__dict__) for i in r.items], total=r.total, skip=r.skip, limit=r.limit)

@router.post("", response_model=SapFieldResponse, status_code=201, dependencies=[Depends(require_api_permission(R, "CREATE"))])
async def create(req: SapFieldCreate, user: User = Depends(get_current_active_user), svc: SapFieldService = Depends(_svc)):
    try: return SapFieldResponse(**(await svc.create(CreateSapFieldDTO(field_name=req.field_name, is_active=req.is_active), user)).__dict__)
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.get("/{id}", response_model=SapFieldResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def get(id: int, svc: SapFieldService = Depends(_svc)):
    try: return SapFieldResponse(**(await svc.get(id)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e

@router.patch("/{id}", response_model=SapFieldResponse, dependencies=[Depends(require_api_permission(R, "UPDATE"))])
async def update(id: int, req: SapFieldUpdate, user: User = Depends(get_current_active_user), svc: SapFieldService = Depends(_svc)):
    try: return SapFieldResponse(**(await svc.update(id, UpdateSapFieldDTO(field_name=req.field_name, is_active=req.is_active), user)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.delete("/{id}", status_code=204, dependencies=[Depends(require_api_permission(R, "DELETE"))])
async def delete(id: int, svc: SapFieldService = Depends(_svc)):
    try: await svc.delete(id)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
