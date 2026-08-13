"""Product Master — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class Product(BaseEntity):
    product_name: str = field(default="")
    storage_conditions: str = field(default="")
    is_active: bool = field(default=True)
