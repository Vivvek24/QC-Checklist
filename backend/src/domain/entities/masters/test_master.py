"""TestMaster — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class TestMaster(BaseEntity):
    """Test master linked to a Product."""

    test_name: str = field(default="")
    no_of_samples_issued: int = field(default=0)
    sample_qty: int = field(default=0)
    product_id: int = field(default=0)
    is_active: bool = field(default=True)
