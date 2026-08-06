"""Workflow engine domain entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.workflow_enums import WorkflowActionType


@dataclass(kw_only=True)
class WorkflowDefinition(BaseEntity):
    code: str = ""
    name: str = ""
    entity_type: str = ""
    description: str = ""
    version: int = 1
    is_active: bool = True

    def deactivate(self) -> None:
        self.is_active = False


@dataclass(kw_only=True)
class WorkflowStatus(BaseEntity):
    workflow_definition_id: int = 0
    code: str = ""
    name: str = ""
    is_initial: bool = False
    is_terminal: bool = False
    sequence: int = 0


@dataclass(kw_only=True)
class WorkflowTransition(BaseEntity):
    workflow_definition_id: int = 0
    from_status_id: int = 0
    to_status_id: int = 0
    action_code: str = ""
    action_type: WorkflowActionType = WorkflowActionType.CUSTOM
    guard_expression: str | None = None
    requires_comment: bool = False
    auto_execute: bool = False
    priority: int = 0


@dataclass(kw_only=True)
class WorkflowInstance(BaseEntity):
    workflow_definition_id: int = 0
    entity_type: str = ""
    entity_id: int = 0
    current_status_id: int = 0
    initiated_by: int = 0
    priority: int = 0
    due_date: datetime | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)
    approval_level: int = 0

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @property
    def is_awaiting_approval(self) -> bool:
        return self.approval_level > 0

    def move_to(self, status_id: int, *, is_terminal: bool) -> None:
        self.current_status_id = status_id
        if is_terminal:
            self.completed_at = datetime.now(UTC)


@dataclass(kw_only=True)
class WorkflowHistoryEntry:
    """Immutable record of one executed transition. id is DB-generated."""

    instance_id: int
    to_status_id: int
    action_code: str
    id: int = field(default=0)
    from_status_id: int | None = None
    actor_id: int | None = None
    actor_username: str = ""
    comments: str = ""
    extra_data: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
