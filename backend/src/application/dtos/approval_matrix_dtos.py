"""Approval matrix application DTOs. ids are int (BigInt)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.enums.workflow_enums import (
    ApprovalTaskStatus,
    AssignmentType,
    RuleDataType,
    RuleOperator,
)


@dataclass(frozen=True)
class ApprovalRuleDTO:
    field: str
    value: str
    operator: RuleOperator = RuleOperator.EQ
    data_type: RuleDataType = RuleDataType.STRING
    logical_group: str = "default"


@dataclass(frozen=True)
class ApprovalAssignmentDTO:
    level: int = 1
    assignment_type: AssignmentType = AssignmentType.ROLE
    user_id: int | None = None
    role_id: int | None = None


@dataclass(frozen=True)
class CreateApprovalMatrixDTO:
    code: str
    name: str
    entity_type: str
    priority: int = 0
    is_active: bool = True
    rules: list[ApprovalRuleDTO] = field(default_factory=list)
    assignments: list[ApprovalAssignmentDTO] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateApprovalMatrixDTO:
    name: str | None = None
    entity_type: str | None = None
    priority: int | None = None
    is_active: bool | None = None
    rules: list[ApprovalRuleDTO] | None = None
    assignments: list[ApprovalAssignmentDTO] | None = None


@dataclass(frozen=True)
class ApprovalRuleResultDTO:
    id: int
    field: str
    operator: RuleOperator
    value: str
    data_type: RuleDataType
    logical_group: str


@dataclass(frozen=True)
class ApprovalAssignmentResultDTO:
    id: int
    level: int
    assignment_type: AssignmentType
    user_id: int | None
    role_id: int | None


@dataclass(frozen=True)
class ApprovalMatrixDTO:
    id: int
    code: str
    name: str
    entity_type: str
    priority: int
    is_active: bool
    rules: list[ApprovalRuleResultDTO]
    assignments: list[ApprovalAssignmentResultDTO]
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class ApprovalMatrixListDTO:
    matrices: list[ApprovalMatrixDTO]
    total: int
    skip: int
    limit: int


@dataclass(frozen=True)
class ResolveApprovalMatrixDTO:
    entity_type: str
    entity_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApprovalResolutionDTO:
    matched: bool
    matrix: ApprovalMatrixDTO | None = None
    levels: list[int] = field(default_factory=list)
    assignments: list[ApprovalAssignmentResultDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ApprovalTaskDTO:
    id: int
    instance_id: int
    assignee_id: int
    level: int
    status: ApprovalTaskStatus
    created_date: datetime
    matrix_id: int | None = None
    action_taken: str | None = None
    due_date: datetime | None = None
    comments: str | None = None
