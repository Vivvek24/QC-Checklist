"""Workflow application DTOs. ids are int (BigInt)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.enums.workflow_enums import WorkflowActionType


@dataclass(frozen=True)
class CreateWorkflowDefinitionDTO:
    code: str
    name: str
    entity_type: str
    description: str = ""
    is_active: bool = True


@dataclass(frozen=True)
class UpdateWorkflowDefinitionDTO:
    code: str | None = None
    name: str | None = None
    entity_type: str | None = None
    description: str | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class CreateWorkflowStatusDTO:
    code: str
    name: str
    is_initial: bool = False
    is_terminal: bool = False
    sequence: int = 0


@dataclass(frozen=True)
class UpdateWorkflowStatusDTO:
    code: str | None = None
    name: str | None = None
    is_initial: bool | None = None
    is_terminal: bool | None = None
    sequence: int | None = None


@dataclass(frozen=True)
class CreateWorkflowTransitionDTO:
    from_status_id: int
    to_status_id: int
    action_code: str
    action_type: WorkflowActionType = WorkflowActionType.CUSTOM
    guard_expression: str | None = None
    requires_comment: bool = False
    auto_execute: bool = False
    priority: int = 0


@dataclass(frozen=True)
class StartWorkflowDTO:
    definition_code: str
    entity_type: str
    entity_id: int
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecuteWorkflowActionDTO:
    action_code: str
    comments: str = ""


@dataclass(frozen=True)
class WorkflowDefinitionDTO:
    id: int
    code: str
    name: str
    description: str
    entity_type: str
    version: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class WorkflowDefinitionListDTO:
    definitions: list[WorkflowDefinitionDTO]
    total: int
    skip: int
    limit: int


@dataclass(frozen=True)
class WorkflowStatusDTO:
    id: int
    workflow_definition_id: int
    code: str
    name: str
    is_initial: bool
    is_terminal: bool
    sequence: int


@dataclass(frozen=True)
class WorkflowTransitionDTO:
    id: int
    workflow_definition_id: int
    from_status_id: int
    to_status_id: int
    action_code: str
    action_type: WorkflowActionType
    guard_expression: str | None
    requires_comment: bool
    auto_execute: bool
    priority: int


@dataclass(frozen=True)
class WorkflowDefinitionDetailDTO:
    definition: WorkflowDefinitionDTO
    statuses: list[WorkflowStatusDTO]
    transitions: list[WorkflowTransitionDTO]


@dataclass(frozen=True)
class WorkflowInstanceDTO:
    id: int
    workflow_definition_id: int
    definition_code: str
    definition_name: str
    entity_type: str
    entity_id: int
    current_status_id: int
    current_status_code: str
    current_status_name: str
    is_terminal: bool
    initiated_by: int
    priority: int
    started_at: datetime
    is_completed: bool
    approval_level: int = 0
    is_awaiting_approval: bool = False
    due_date: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowInstanceListDTO:
    instances: list[WorkflowInstanceDTO]
    total: int
    skip: int
    limit: int


@dataclass(frozen=True)
class WorkflowAvailableActionDTO:
    action_code: str
    action_type: WorkflowActionType
    to_status_id: int
    to_status_code: str
    to_status_name: str
    requires_comment: bool
    is_terminal: bool


@dataclass(frozen=True)
class WorkflowHistoryDTO:
    id: int
    instance_id: int
    to_status_id: int
    action_code: str
    actor_username: str
    comments: str
    ip_address: str
    created_at: datetime
    from_status_id: int | None = None
    from_status_code: str | None = None
    to_status_code: str | None = None
    actor_id: int | None = None
