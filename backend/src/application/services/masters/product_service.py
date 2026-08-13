"""Product Master — application service."""
from src.application.dtos.masters.product_dtos import CreateProductDTO, ProductDTO, ProductListDTO, UpdateProductDTO
from src.domain.entities.masters.product import Product
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.product_repository import IProductRepository

ENTITY = "Product"

class ProductService:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    async def list_products(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> ProductListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return ProductListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def get_product(self, product_id: int) -> ProductDTO:
        return self._to_dto(await self._require(product_id))

    async def create_product(self, dto: CreateProductDTO, actor: User) -> ProductDTO:
        if await self._repo.exists_by_name(dto.product_name):
            raise DuplicateEntityError(ENTITY, "product_name", dto.product_name)
        return self._to_dto(await self._repo.create(Product(
            product_name=dto.product_name.strip(), storage_conditions=dto.storage_conditions.strip(),
            is_active=dto.is_active, created_by=actor.username, modified_by=actor.username,
        )))

    async def update_product(self, product_id: int, dto: UpdateProductDTO, actor: User) -> ProductDTO:
        p = await self._require(product_id)
        if dto.product_name is not None and dto.product_name.strip() != p.product_name:
            if await self._repo.exists_by_name(dto.product_name, exclude_id=product_id):
                raise DuplicateEntityError(ENTITY, "product_name", dto.product_name)
            p.product_name = dto.product_name.strip()
        if dto.storage_conditions is not None: p.storage_conditions = dto.storage_conditions.strip()
        if dto.is_active is not None: p.is_active = dto.is_active
        p.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(p))

    async def delete_product(self, product_id: int) -> None:
        await self._require(product_id); await self._repo.delete(product_id)

    async def _require(self, product_id: int) -> Product:
        p = await self._repo.get_by_id(product_id)
        if p is None: raise EntityNotFoundError(ENTITY, product_id)
        return p

    @staticmethod
    def _to_dto(p: Product) -> ProductDTO:
        return ProductDTO(id=p.id, product_name=p.product_name, storage_conditions=p.storage_conditions,
                          is_active=p.is_active, created_by=p.created_by, created_date=p.created_date,
                          modified_by=p.modified_by, modified_date=p.modified_date)
