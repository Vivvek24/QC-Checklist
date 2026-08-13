"""Product Master — API controller."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.product_schema import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from src.application.dtos.masters.product_dtos import CreateProductDTO, UpdateProductDTO
from src.application.services.masters.product_service import ProductService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.product_repository_impl import ProductRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/products", tags=["Masters - Product"])
RESOURCE = "products"

def _svc(session: AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(repo=ProductRepositoryImpl(session))

@router.get("", response_model=ProductListResponse, dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_products(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                        search: str | None = Query(None), is_active: bool | None = Query(None),
                        svc: ProductService = Depends(_svc)) -> ProductListResponse:
    r = await svc.list_products(skip=skip, limit=limit, search=search, is_active=is_active)
    return ProductListResponse(items=[ProductResponse(**i.__dict__) for i in r.items], total=r.total, skip=r.skip, limit=r.limit)

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_product(req: ProductCreate, user: User = Depends(get_current_active_user), svc: ProductService = Depends(_svc)) -> ProductResponse:
    try: return ProductResponse(**(await svc.create_product(CreateProductDTO(product_name=req.product_name, storage_conditions=req.storage_conditions, is_active=req.is_active), user)).__dict__)
    except DuplicateEntityError as e: raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e

@router.get("/{pid}", response_model=ProductResponse, dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_product(pid: int, svc: ProductService = Depends(_svc)) -> ProductResponse:
    try: return ProductResponse(**(await svc.get_product(pid)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

@router.patch("/{pid}", response_model=ProductResponse, dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_product(pid: int, req: ProductUpdate, user: User = Depends(get_current_active_user), svc: ProductService = Depends(_svc)) -> ProductResponse:
    try: return ProductResponse(**(await svc.update_product(pid, UpdateProductDTO(product_name=req.product_name, storage_conditions=req.storage_conditions, is_active=req.is_active), user)).__dict__)
    except EntityNotFoundError as e: raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e: raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e

@router.delete("/{pid}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_product(pid: int, svc: ProductService = Depends(_svc)) -> None:
    try: await svc.delete_product(pid)
    except EntityNotFoundError as e: raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
