from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.validation_type_schema import *
from src.application.dtos.masters.validation_type_dtos import CreateValidationTypeDTO, UpdateValidationTypeDTO
from src.application.services.masters.validation_type_service import ValidationTypeService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.validation_type_repository_impl import ValidationTypeRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/validation-types", tags=["Masters - Validation Type"])
R = "validation_types"
def _svc(s: AsyncSession = Depends(get_db_session)) -> ValidationTypeService: return ValidationTypeService(repo=ValidationTypeRepositoryImpl(s))

@router.get("", response_model=ValidationTypeListResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def list_all(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), search: str | None = Query(None), is_active: bool | None = Query(None), svc: ValidationTypeService = Depends(_svc)):
    r = await svc.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
    return ValidationTypeListResponse(items=[ValidationTypeResponse(**i.__dict__) for i in r.items], total=r.total, skip=r.skip, limit=r.limit)

@router.post("", response_model=ValidationTypeResponse, status_code=201, dependencies=[Depends(require_api_permission(R, "CREATE"))])
async def create(req: ValidationTypeCreate, user: User = Depends(get_current_active_user), svc: ValidationTypeService = Depends(_svc)):
    try: return ValidationTypeResponse(**(await svc.create(CreateValidationTypeDTO(name=req.name, is_active=req.is_active), user)).__dict__)
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.get("/{id}", response_model=ValidationTypeResponse, dependencies=[Depends(require_api_permission(R, "READ"))])
async def get(id: int, svc: ValidationTypeService = Depends(_svc)):
    try: return ValidationTypeResponse(**(await svc.get(id)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e

@router.patch("/{id}", response_model=ValidationTypeResponse, dependencies=[Depends(require_api_permission(R, "UPDATE"))])
async def update(id: int, req: ValidationTypeUpdate, user: User = Depends(get_current_active_user), svc: ValidationTypeService = Depends(_svc)):
    try: return ValidationTypeResponse(**(await svc.update(id, UpdateValidationTypeDTO(name=req.name, is_active=req.is_active), user)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
    except DuplicateEntityError as e: raise HTTPException(409, detail=str(e)) from e

@router.delete("/{id}", status_code=204, dependencies=[Depends(require_api_permission(R, "DELETE"))])
async def delete(id: int, svc: ValidationTypeService = Depends(_svc)):
    try: await svc.delete(id)
    except EntityNotFoundError as e: raise HTTPException(404, detail=str(e)) from e
