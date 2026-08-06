"""Approval matrix repository implementation."""

from collections import defaultdict
from typing import Any

from sqlalchemy import ColumnElement, Select, delete, func, or_, select

from src.domain.entities.approval_matrix import (
    ApprovalAssignment,
    ApprovalMatrix,
    ApprovalRule,
    ApprovalTask,
)
from src.domain.enums.workflow_enums import (
    ApprovalTaskStatus,
    AssignmentType,
    RuleDataType,
    RuleOperator,
)
from src.domain.repositories.approval_matrix_repository import IApprovalMatrixRepository
from src.infrastructure.database.models.approval_matrix_model import (
    ApprovalAssignmentModel,
    ApprovalMatrixModel,
    ApprovalRuleModel,
    ApprovalTaskModel,
)
from src.infrastructure.database.repositories.base_repository_impl import (
    SqlAlchemyRepository,
)


class ApprovalMatrixRepositoryImpl(
    SqlAlchemyRepository[ApprovalMatrix, ApprovalMatrixModel],
    IApprovalMatrixRepository,
):
    _model = ApprovalMatrixModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return ApprovalMatrixModel.code == code

    # ─── Matrix reads ───

    async def get_by_id(self, entity_id: int) -> ApprovalMatrix | None:
        model = await self._get_model(entity_id)
        if model is None:
            return None
        return (await self._hydrate([model]))[0]

    async def get_by_code(self, code: str) -> ApprovalMatrix | None:
        stmt = select(ApprovalMatrixModel).where(self._code_equals(code))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return (await self._hydrate([model]))[0]

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> list[ApprovalMatrix]:
        stmt = self._apply_filters(select(ApprovalMatrixModel), search, is_active, entity_type)
        stmt = stmt.order_by(ApprovalMatrixModel.priority, ApprovalMatrixModel.code).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return await self._hydrate(list(result.scalars().all()))

    async def count(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> int:
        stmt = self._apply_filters(
            select(func.count()).select_from(ApprovalMatrixModel),
            search, is_active, entity_type,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(ApprovalMatrixModel.id).where(
            func.lower(ApprovalMatrixModel.name) == name.lower()
        )
        if exclude_id is not None:
            stmt = stmt.where(ApprovalMatrixModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_active_for_entity_type(self, entity_type: str) -> list[ApprovalMatrix]:
        stmt = (
            select(ApprovalMatrixModel)
            .where(
                ApprovalMatrixModel.entity_type == entity_type,
                ApprovalMatrixModel.is_active.is_(True),
            )
            .order_by(ApprovalMatrixModel.priority, ApprovalMatrixModel.code)
        )
        result = await self._session.execute(stmt)
        return await self._hydrate(list(result.scalars().all()))

    # ─── Matrix writes ───

    async def create(self, entity: ApprovalMatrix) -> ApprovalMatrix:
        model = ApprovalMatrixModel(
            code=entity.code,
            name=entity.name,
            entity_type=entity.entity_type,
            priority=entity.priority,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        # Update entity id from DB
        entity.id = model.id
        self._add_children(entity)
        await self._session.flush()
        return (await self._hydrate([model]))[0]

    async def update(self, entity: ApprovalMatrix) -> ApprovalMatrix:
        model = await self._require_model(entity.id)

        model.code = entity.code
        model.name = entity.name
        model.entity_type = entity.entity_type
        model.priority = entity.priority
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date

        await self._session.execute(
            delete(ApprovalRuleModel).where(ApprovalRuleModel.matrix_id == entity.id)
        )
        await self._session.execute(
            delete(ApprovalAssignmentModel).where(ApprovalAssignmentModel.matrix_id == entity.id)
        )
        await self._session.flush()

        self._add_children(entity)
        await self._session.flush()
        return (await self._hydrate([model]))[0]

    # ─── Approval tasks ───

    async def create_task(self, task: ApprovalTask) -> ApprovalTask:
        model = ApprovalTaskModel(
            instance_id=task.instance_id,
            matrix_id=task.matrix_id,
            assignee_id=task.assignee_id,
            level=task.level,
            status=task.status.value,
            action_taken=task.action_taken,
            due_date=task.due_date,
            comments=task.comments,
            created_by=task.created_by,
            modified_by=task.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._task_to_entity(model)

    async def get_task(self, task_id: int) -> ApprovalTask | None:
        model = await self._get_task_model(task_id)
        return self._task_to_entity(model) if model else None

    async def update_task(self, task: ApprovalTask) -> ApprovalTask:
        model = await self._get_task_model(task.id)
        if model is None:
            raise ValueError(f"ApprovalTask with id {task.id} not found")

        model.level = task.level
        model.status = task.status.value
        model.action_taken = task.action_taken
        model.due_date = task.due_date
        model.comments = task.comments
        model.modified_by = task.modified_by
        model.modified_date = task.modified_date

        await self._session.flush()
        return self._task_to_entity(model)

    async def list_tasks_for_instance(self, instance_id: int) -> list[ApprovalTask]:
        stmt = (
            select(ApprovalTaskModel)
            .where(ApprovalTaskModel.instance_id == instance_id)
            .order_by(ApprovalTaskModel.level, ApprovalTaskModel.created_date)
        )
        result = await self._session.execute(stmt)
        return [self._task_to_entity(m) for m in result.scalars().all()]

    async def list_pending_tasks_for_user(self, user_id: int) -> list[ApprovalTask]:
        stmt = (
            select(ApprovalTaskModel)
            .where(
                ApprovalTaskModel.assignee_id == user_id,
                ApprovalTaskModel.status == ApprovalTaskStatus.PENDING.value,
            )
            .order_by(
                ApprovalTaskModel.due_date.asc().nullslast(),
                ApprovalTaskModel.created_date,
            )
        )
        result = await self._session.execute(stmt)
        return [self._task_to_entity(m) for m in result.scalars().all()]

    async def list_tasks_for_user(self, user_id: int) -> list[ApprovalTask]:
        """All tasks (open and closed) assigned to a user."""
        stmt = (
            select(ApprovalTaskModel)
            .where(ApprovalTaskModel.assignee_id == user_id)
            .order_by(ApprovalTaskModel.created_date.desc())
        )
        result = await self._session.execute(stmt)
        return [self._task_to_entity(m) for m in result.scalars().all()]

    async def cancel_open_tasks_for_instance(self, instance_id: int) -> int:
        stmt = select(ApprovalTaskModel).where(
            ApprovalTaskModel.instance_id == instance_id,
            ApprovalTaskModel.status == ApprovalTaskStatus.PENDING.value,
        )
        result = await self._session.execute(stmt)
        models = list(result.scalars().all())
        for model in models:
            model.status = ApprovalTaskStatus.CANCELLED.value
        if models:
            await self._session.flush()
        return len(models)

    # ─── Internals ───

    def _add_children(self, entity: ApprovalMatrix) -> None:
        for rule in entity.rules:
            self._session.add(
                ApprovalRuleModel(
                    matrix_id=entity.id,
                    field=rule.field,
                    operator=rule.operator.value,
                    value=rule.value,
                    data_type=rule.data_type.value,
                    logical_group=rule.logical_group,
                    created_by=entity.modified_by,
                    modified_by=entity.modified_by,
                )
            )
        for assignment in entity.assignments:
            self._session.add(
                ApprovalAssignmentModel(
                    matrix_id=entity.id,
                    assignment_type=assignment.assignment_type.value,
                    user_id=assignment.user_id,
                    role_id=assignment.role_id,
                    level=assignment.level,
                    created_by=entity.modified_by,
                    modified_by=entity.modified_by,
                )
            )

    async def _hydrate(self, models: list[ApprovalMatrixModel]) -> list[ApprovalMatrix]:
        if not models:
            return []

        matrix_ids = [m.id for m in models]

        rules_result = await self._session.execute(
            select(ApprovalRuleModel)
            .where(ApprovalRuleModel.matrix_id.in_(matrix_ids))
            .order_by(ApprovalRuleModel.logical_group, ApprovalRuleModel.field)
        )
        rules_by_matrix: dict[int, list[ApprovalRule]] = defaultdict(list)
        for rule_model in rules_result.scalars().all():
            rules_by_matrix[rule_model.matrix_id].append(self._rule_to_entity(rule_model))

        assign_result = await self._session.execute(
            select(ApprovalAssignmentModel)
            .where(ApprovalAssignmentModel.matrix_id.in_(matrix_ids))
            .order_by(ApprovalAssignmentModel.level)
        )
        assignments_by_matrix: dict[int, list[ApprovalAssignment]] = defaultdict(list)
        for assign_model in assign_result.scalars().all():
            assignments_by_matrix[assign_model.matrix_id].append(
                self._assignment_to_entity(assign_model)
            )

        aggregates = []
        for model in models:
            matrix = self._to_entity(model)
            matrix.rules = rules_by_matrix.get(model.id, [])
            matrix.assignments = assignments_by_matrix.get(model.id, [])
            aggregates.append(matrix)
        return aggregates

    async def _get_task_model(self, task_id: int) -> ApprovalTaskModel | None:
        stmt = select(ApprovalTaskModel).where(ApprovalTaskModel.id == task_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _apply_filters(
        stmt: Select[Any],
        search: str | None,
        is_active: bool | None,
        entity_type: str | None,
    ) -> Select[Any]:
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ApprovalMatrixModel.code.ilike(pattern),
                    ApprovalMatrixModel.name.ilike(pattern),
                    ApprovalMatrixModel.entity_type.ilike(pattern),
                )
            )
        if is_active is not None:
            stmt = stmt.where(ApprovalMatrixModel.is_active.is_(is_active))
        if entity_type:
            stmt = stmt.where(ApprovalMatrixModel.entity_type == entity_type)
        return stmt

    @staticmethod
    def _to_entity(model: ApprovalMatrixModel) -> ApprovalMatrix:
        return ApprovalMatrix(
            id=model.id,
            code=model.code,
            name=model.name,
            entity_type=model.entity_type,
            priority=model.priority,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )

    @staticmethod
    def _rule_to_entity(model: ApprovalRuleModel) -> ApprovalRule:
        return ApprovalRule(
            id=model.id,
            matrix_id=model.matrix_id,
            field=model.field,
            operator=RuleOperator(model.operator),
            value=model.value,
            data_type=RuleDataType(model.data_type),
            logical_group=model.logical_group,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )

    @staticmethod
    def _assignment_to_entity(model: ApprovalAssignmentModel) -> ApprovalAssignment:
        return ApprovalAssignment(
            id=model.id,
            matrix_id=model.matrix_id,
            assignment_type=AssignmentType(model.assignment_type),
            user_id=model.user_id,
            role_id=model.role_id,
            level=model.level,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )

    @staticmethod
    def _task_to_entity(model: ApprovalTaskModel) -> ApprovalTask:
        return ApprovalTask(
            id=model.id,
            instance_id=model.instance_id,
            matrix_id=model.matrix_id,
            assignee_id=model.assignee_id,
            level=model.level,
            status=ApprovalTaskStatus(model.status),
            action_taken=model.action_taken,
            due_date=model.due_date,
            comments=model.comments,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
