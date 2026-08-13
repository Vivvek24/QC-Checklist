"""Product Master — application DTOs."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateProductDTO:
    product_name: str
    storage_conditions: str = ""
    is_active: bool = True

@dataclass(frozen=True)
class UpdateProductDTO:
    product_name: str | None = None
    storage_conditions: str | None = None
    is_active: bool | None = None

@dataclass(frozen=True)
class ProductDTO:
    id: int
    product_name: str
    storage_conditions: str
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime

@dataclass(frozen=True)
class ProductListDTO:
    items: list[ProductDTO]
    total: int
    skip: int
    limit: int
