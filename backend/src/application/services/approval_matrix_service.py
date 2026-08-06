"""
Approval matrix application service.

Owns the routing configuration: which matrix applies to which entity type, the
conditions that select it, and the approval levels it routes to. Matrices are
treated as whole documents — an update replaces the rule set and the level set
rather than patching them row by row, because that is how the screen edits them.

`resolve` is the dry run: feed it a sample record and it reports which matrix
would win and who would be asked to approve, without writing anything.
"""

from typing import Any

from src.application.dtos.approval_matrix_dtos import (
    ApprovalAssignmentDTO,
    ApprovalAssignmentResultDTO,
    ApprovalMatrixDTO,
    ApprovalMatrixListDTO,
    ApprovalResolutionDTO,
    ApprovalRuleDTO,
    ApprovalRuleResultDTO,
    ApprovalTaskDTO,
    CreateApprovalMatrixDTO,
    UpdateApprovalMatrixDTO,
)
from src.application.services.workflow.approval_matrix_resolver import (
    ApprovalMatrixResolver,
)
from src.domain.entities.approval_matrix import (
    ApprovalAssignment,
    ApprovalMatrix,
    ApprovalRule,
    ApprovalTask,
)
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from src.domain.repositories.approval_matrix_repository import IApprovalMatrixRepository

ENTITY = "ApprovalMatrix"


class ApprovalMatrixService:
    """Application service for approval matrix configuration and resolution."""

    def __init__(self, approval_matrix_repo: IApprovalMatrixRepository) -> None:
        self._repo = approval_matrix_repo
        self._resolver = ApprovalMatrixResolver(approval_matrix_repo)

    # ─── List ───

    async def list_matrices(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> ApprovalMatrixListDTO:
        """Get a page of matrices plus the total match count."""
        matrices = await self._repo.list_all(
            skip=skip, limit=limit, search=search,
            is_active=is_active, entity_type=entity_type,
        )
        total = await self._repo.count(
            search=search, is_active=is_active, entity_type=entity_type
        )
        return ApprovalMatrixListDTO(
            matrices=[self._to_dto(m) for m in matrices],
            total=total,
            skip=skip,
            limit=limit,
        )

    # ─── Get ───

    async def get_matrix(self, matrix_id: int) -> ApprovalMatrixDTO:
        """Get one matrix with its rules and levels."""
        return self._to_dto(await self._require(matrix_id))

    # ─── Create ───

    async def create_matrix(
        self, dto: CreateApprovalMatrixDTO, actor: User
    ) -> ApprovalMatrixDTO:
        """Create a matrix together with its rules and approval levels."""
        if await self._repo.exists_by_code(dto.code):
            raise DuplicateEntityError(ENTITY, "code", dto.code)
        if await self._repo.exists_by_name(dto.name):
            raise DuplicateEntityError(ENTITY, "name", dto.name)

        matrix_id = 0
        matrix = ApprovalMatrix(
            id=matrix_id,
            code=dto.code,
            name=dto.name,
            entity_type=dto.entity_type,
            priority=dto.priority,
            is_active=dto.is_active,
            rules=self._rules_to_entities(dto.rules, matrix_id, actor.username),
            assignments=self._assignments_to_entities(dto.assignments, matrix_id, actor.username),
            created_by=actor.username,
            modified_by=actor.username,
        )
        return self._to_dto(await self._repo.create(matrix))

    # ─── Update ───

    async def update_matrix(
        self, matrix_id: int, dto: UpdateApprovalMatrixDTO, actor: User
    ) -> ApprovalMatrixDTO:
        """
        Apply a partial update to a matrix.

        `rules` and `assignments` are replace-if-supplied: passing a list swaps the
        stored collection for it, omitting the key leaves it alone.
        """
        matrix = await self._require(matrix_id)

        if dto.name is not None and dto.name != matrix.name:
            if await self._repo.exists_by_name(dto.name, exclude_id=matrix_id):
                raise DuplicateEntityError(ENTITY, "name", dto.name)
            matrix.name = dto.name

        if dto.entity_type is not None:
            matrix.entity_type = dto.entity_type
        if dto.priority is not None:
            matrix.priority = dto.priority
        if dto.is_active is not None:
            matrix.is_active = dto.is_active

        if dto.rules is not None:
            matrix.rules = self._rules_to_entities(dto.rules, matrix_id, actor.username)
        if dto.assignments is not None:
            matrix.assignments = self._assignments_to_entities(
                dto.assignments, matrix_id, actor.username
            )

        matrix.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(matrix))

    # ─── Delete ───

    async def delete_matrix(self, matrix_id: int) -> None:
        """Delete a matrix; its rules and levels go with it."""
        await self._require(matrix_id)
        await self._repo.delete(matrix_id)

    # ─── Resolve ───

    async def resolve(
        self, entity_type: str, entity_data: dict[str, Any]
    ) -> ApprovalResolutionDTO:
        """
        Report which matrix would route a sample record, and to whom.

        A miss is a normal answer, not an error: `matched` is False and the rest
        of the response is empty.
        """
        resolved = await self._resolver.resolve(entity_type, entity_data)
        if resolved is None:
            return ApprovalResolutionDTO(matched=False)

        return ApprovalResolutionDTO(
            matched=True,
            matrix=self._to_dto(resolved.matrix),
            levels=resolved.levels,
            assignments=[self._assignment_to_result_dto(a) for a in resolved.assignments],
        )

    # ─── Tasks ───

    async def list_tasks_for_user(self, user_id: int) -> list[ApprovalTaskDTO]:
        """Open approval tasks assigned to a user."""
        tasks = await self._repo.list_tasks_for_user(user_id)
        return [self._task_to_dto(t) for t in tasks]

    async def list_tasks_for_instance(self, instance_id: int) -> list[ApprovalTaskDTO]:
        """Every approval task raised for an instance."""
        tasks = await self._repo.list_tasks_for_instance(instance_id)
        return [self._task_to_dto(t) for t in tasks]

    # ─── Internals ───

    async def _require(self, matrix_id: int) -> ApprovalMatrix:
        matrix = await self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise EntityNotFoundError(ENTITY, matrix_id)
        return matrix

    @staticmethod
    def _rules_to_entities(
        inputs: list[ApprovalRuleDTO], matrix_id: int, actor_username: str
    ) -> list[ApprovalRule]:
        return [
            ApprovalRule(
                id=0,
                matrix_id=matrix_id,
                field=item.field,
                operator=item.operator,
                value=item.value,
                data_type=item.data_type,
                logical_group=item.logical_group,
                created_by=actor_username,
                modified_by=actor_username,
            )
            for item in inputs
        ]

    @staticmethod
    def _assignments_to_entities(
        inputs: list[ApprovalAssignmentDTO], matrix_id: int, actor_username: str
    ) -> list[ApprovalAssignment]:
        return [
            ApprovalAssignment(
                id=0,
                matrix_id=matrix_id,
                assignment_type=item.assignment_type,
                user_id=item.user_id,
                role_id=item.role_id,
                level=item.level,
                created_by=actor_username,
                modified_by=actor_username,
            )
            for item in inputs
        ]

    @staticmethod
    def _rule_to_result_dto(rule: ApprovalRule) -> ApprovalRuleResultDTO:
        return ApprovalRuleResultDTO(
            id=rule.id,
            field=rule.field,
            operator=rule.operator,
            value=rule.value,
            data_type=rule.data_type,
            logical_group=rule.logical_group,
        )

    @staticmethod
    def _assignment_to_result_dto(a: ApprovalAssignment) -> ApprovalAssignmentResultDTO:
        return ApprovalAssignmentResultDTO(
            id=a.id,
            level=a.level,
            assignment_type=a.assignment_type,
            user_id=a.user_id,
            role_id=a.role_id,
        )

    @classmethod
    def _to_dto(cls, matrix: ApprovalMatrix) -> ApprovalMatrixDTO:
        return ApprovalMatrixDTO(
            id=matrix.id,
            code=matrix.code,
            name=matrix.name,
            entity_type=matrix.entity_type,
            priority=matrix.priority,
            is_active=matrix.is_active,
            rules=[cls._rule_to_result_dto(r) for r in matrix.rules],
            assignments=[cls._assignment_to_result_dto(a) for a in matrix.assignments],
            created_by=matrix.created_by,
            created_date=matrix.created_date,
            modified_by=matrix.modified_by,
            modified_date=matrix.modified_date,
        )

    @staticmethod
    def _task_to_dto(task: ApprovalTask) -> ApprovalTaskDTO:
        return ApprovalTaskDTO(
            id=task.id,
            instance_id=task.instance_id,
            matrix_id=task.matrix_id,
            assignee_id=task.assignee_id,
            level=task.level,
            status=task.status,
            action_taken=task.action_taken,
            due_date=task.due_date,
            comments=task.comments,
            created_date=task.created_date,
        )



