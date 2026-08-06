"""
Base domain entity with audit fields.
All domain entities inherit from this to ensure consistent audit tracking.
Primary key is int (BigInt auto-increment from DB), default 0 before persist.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class BaseEntity:
    """
    Base entity providing identity and audit fields.

    id is set by the database (BIGSERIAL). The default of 0 is a sentinel
    meaning "not yet persisted". Repositories flush immediately after add()
    so callers always receive the DB-assigned id.
    """

    id: int = field(default=0)
    created_by: str = field(default="system")
    created_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_by: str = field(default="system")
    modified_date: datetime = field(default_factory=lambda: datetime.now(UTC))

    def mark_modified(self, modified_by: str) -> None:
        """Update modification tracking fields."""
        self.modified_by = modified_by
        self.modified_date = datetime.now(UTC)
