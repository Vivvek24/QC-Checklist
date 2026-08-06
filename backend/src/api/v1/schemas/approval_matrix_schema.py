"""Pydantic schemas for the approval matrix API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.domain.enums.workflow_enums import (
    ApprovalTaskStatus,
    AssignmentType,
    RuleDataType,
    RuleOperator,
)


class ApprovalRuleInput(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)
    operator: RuleOperator = Field(default=RuleOperator.EQ)
    value: str = Field(..., min_length=1, max_length=500)
    data_type: RuleDataType = Field(default=RuleDataType.STRING)
    logical_group: str = Field(default="default", min_length=1, max_length=50)

    @field_validator("field", "logical_group")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class ApprovalRuleResponse(BaseModel):
    id: int
    field: str
    operator: RuleOperator
    value: str
    data_type: RuleDataType
    logical_group: str

    model_config = {"from_attributes": True}


class ApprovalAssignmentInput(BaseModel):
    level: int = Field(default=1, ge=1, le=99)
    assignment_type: AssignmentType = Field(default=AssignmentType.ROLE)
    user_id: int | None = Field(default=None)
    role_id: int | None = Field(default=None)

    @model_validator(mode="after")
    def _require_matching_target(self) -> "ApprovalAssignmentInput":
        if self.assignment_type == AssignmentType.USER and self.user_id is None:
            raise ValueError("assignment_type 'USER' requires user_id")
        if self.assignment_type == AssignmentType.ROLE and self.role_id is None:
            raise ValueError("assignment_type 'ROLE' requires role_id")
        return self


class ApprovalAssignmentResponse(BaseModel):
    id: int
    level: int
    assignment_type: AssignmentType
    user_id: int | None
    role_id: int | None

    model_config = {"from_attributes": True}


class ApprovalMatrixCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    entity_type: str = Field(..., min_length=2, max_length=100)
    priority: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    rules: list[ApprovalRuleInput] = Field(default_factory=list)
    assignments: list[ApprovalAssignmentInput] = Field(default_factory=list)

    @field_validator("code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_").replace("-", "_")

    @field_validator("name", "entity_type")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class ApprovalMatrixUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    entity_type: str | None = Field(default=None, min_length=2, max_length=100)
    priority: int | None = Field(default=None, ge=0)
    is_active: bool | None = Field(default=None)
    rules: list[ApprovalRuleInput] | None = Field(default=None)
    assignments: list[ApprovalAssignmentInput] | None = Field(default=None)

    @field_validator("name", "entity_type")
    @classmethod
    def _trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class ApprovalMatrixResponse(BaseModel):
    id: int
    code: str
    name: str
    entity_type: str
    priority: int
    is_active: bool
    rules: list[ApprovalRuleResponse]
    assignments: list[ApprovalAssignmentResponse]
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime

    model_config = {"from_attributes": True}


class ApprovalMatrixListResponse(BaseModel):
    matrices: list[ApprovalMatrixResponse]
    total: int
    skip: int
    limit: int


class ApprovalResolveRequest(BaseModel):
    entity_type: str = Field(..., min_length=2, max_length=100)
    entity_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entity_type")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class ApprovalResolveResponse(BaseModel):
    matched: bool
    matrix: ApprovalMatrixResponse | None = None
    levels: list[int] = Field(default_factory=list)
    assignments: list[ApprovalAssignmentResponse] = Field(default_factory=list)


class ApprovalTaskResponse(BaseModel):
    id: int
    instance_id: int
    matrix_id: int | None
    assignee_id: int
    level: int
    status: ApprovalTaskStatus
    action_taken: str | None
    due_date: datetime | None
    comments: str | None
    created_date: datetime

    model_config = {"from_attributes": True}
