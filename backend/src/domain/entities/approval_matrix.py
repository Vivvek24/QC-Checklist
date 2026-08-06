"""Approval matrix domain entities."""

import dataclasses
from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.workflow_enums import (
    ApprovalTaskStatus,
    AssignmentType,
    RuleDataType,
    RuleOperator,
)


@dataclass(kw_only=True)
class ApprovalRule(BaseEntity):
    matrix_id: int | None = None
    field: str = ""
    operator: RuleOperator = RuleOperator.EQ
    value: str = ""
    data_type: RuleDataType = RuleDataType.STRING
    logical_group: str = "default"


@dataclass(kw_only=True)
class ApprovalAssignment(BaseEntity):
    matrix_id: int | None = None
    assignment_type: AssignmentType = AssignmentType.ROLE
    user_id: int | None = None
    role_id: int | None = None
    level: int = 1


@dataclass(kw_only=True)
class ApprovalMatrix(BaseEntity):
    code: str = ""
    name: str = ""
    entity_type: str = ""
    priority: int = 0
    is_active: bool = True
    rules: list[ApprovalRule] = dataclasses.field(default_factory=list)
    assignments: list[ApprovalAssignment] = dataclasses.field(default_factory=list)

    @property
    def levels(self) -> list[int]:
        return sorted({a.level for a in self.assignments})

    def assignments_for_level(self, level: int) -> list[ApprovalAssignment]:
        return [a for a in self.assignments if a.level == level]


@dataclass(kw_only=True)
class ApprovalTask(BaseEntity):
    instance_id: int = 0
    assignee_id: int = 0
    matrix_id: int | None = None
    level: int = 1
    status: ApprovalTaskStatus = ApprovalTaskStatus.PENDING
    action_taken: str | None = None
    due_date: datetime | None = None
    comments: str | None = None

    @property
    def is_open(self) -> bool:
        return self.status == ApprovalTaskStatus.PENDING
