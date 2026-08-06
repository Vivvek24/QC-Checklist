"""Pydantic schemas for the workflow engine API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.domain.enums.workflow_enums import WorkflowActionType


def _normalise_code(value: str) -> str:
    return value.strip().upper().replace(" ", "_").replace("-", "_")


class WorkflowDefinitionCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    entity_type: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="")
    is_active: bool = Field(default=True)

    @field_validator("code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return _normalise_code(value)

    @field_validator("name", "entity_type")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class WorkflowDefinitionUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=100)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    entity_type: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("code")
    @classmethod
    def _upper(cls, value: str | None) -> str | None:
        return _normalise_code(value) if value else value

    @field_validator("name", "entity_type")
    @classmethod
    def _trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class WorkflowDefinitionResponse(BaseModel):
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

    model_config = {"from_attributes": True}


class WorkflowDefinitionListResponse(BaseModel):
    definitions: list[WorkflowDefinitionResponse]
    total: int
    skip: int
    limit: int


class WorkflowStatusCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    is_initial: bool = Field(default=False)
    is_terminal: bool = Field(default=False)
    sequence: int = Field(default=0, ge=0)

    @field_validator("code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return _normalise_code(value)

    @field_validator("name")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class WorkflowStatusUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_initial: bool | None = Field(default=None)
    is_terminal: bool | None = Field(default=None)
    sequence: int | None = Field(default=None, ge=0)

    @field_validator("code")
    @classmethod
    def _upper(cls, value: str | None) -> str | None:
        return _normalise_code(value) if value else value

    @field_validator("name")
    @classmethod
    def _trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class WorkflowStatusResponse(BaseModel):
    id: int
    workflow_definition_id: int
    code: str
    name: str
    is_initial: bool
    is_terminal: bool
    sequence: int

    model_config = {"from_attributes": True}


class WorkflowTransitionCreate(BaseModel):
    from_status_id: int
    to_status_id: int
    action_code: str = Field(..., min_length=2, max_length=50)
    action_type: WorkflowActionType = Field(default=WorkflowActionType.CUSTOM)
    guard_expression: str | None = Field(default=None, max_length=2000)
    requires_comment: bool = Field(default=False)
    auto_execute: bool = Field(default=False)
    priority: int = Field(default=0, ge=0)

    @field_validator("action_code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return _normalise_code(value)


class WorkflowTransitionResponse(BaseModel):
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

    model_config = {"from_attributes": True}


class WorkflowDefinitionDetailResponse(BaseModel):
    definition: WorkflowDefinitionResponse
    statuses: list[WorkflowStatusResponse]
    transitions: list[WorkflowTransitionResponse]


class WorkflowStartRequest(BaseModel):
    definition_code: str = Field(..., min_length=2, max_length=100)
    entity_type: str = Field(..., min_length=2, max_length=100)
    entity_id: int
    priority: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("definition_code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return _normalise_code(value)

    @field_validator("entity_type")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class WorkflowActionRequest(BaseModel):
    action_code: str = Field(..., min_length=2, max_length=50)
    comments: str = Field(default="", max_length=4000)

    @field_validator("action_code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return _normalise_code(value)


class WorkflowInstanceResponse(BaseModel):
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
    due_date: datetime | None
    started_at: datetime
    completed_at: datetime | None
    is_completed: bool
    approval_level: int = Field(default=0)
    is_awaiting_approval: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowInstanceListResponse(BaseModel):
    instances: list[WorkflowInstanceResponse]
    total: int
    skip: int
    limit: int


class WorkflowAvailableActionResponse(BaseModel):
    action_code: str
    action_type: WorkflowActionType
    to_status_id: int
    to_status_code: str
    to_status_name: str
    requires_comment: bool
    is_terminal: bool


class WorkflowHistoryResponse(BaseModel):
    id: int
    instance_id: int
    from_status_id: int | None
    from_status_code: str | None
    to_status_id: int
    to_status_code: str | None
    action_code: str
    actor_id: int | None
    actor_username: str
    comments: str
    ip_address: str
    created_at: datetime
