"""
Workflow application service.
ids are int (BigInt auto-increment) throughout.
"""

from src.application.dtos.approval_matrix_dtos import ApprovalTaskDTO
from src.application.dtos.workflow_dtos import (
    CreateWorkflowDefinitionDTO,
    CreateWorkflowStatusDTO,
    CreateWorkflowTransitionDTO,
    ExecuteWorkflowActionDTO,
    StartWorkflowDTO,
    UpdateWorkflowDefinitionDTO,
    UpdateWorkflowStatusDTO,
    WorkflowAvailableActionDTO,
    WorkflowDefinitionDTO,
    WorkflowDefinitionDetailDTO,
    WorkflowDefinitionListDTO,
    WorkflowHistoryDTO,
    WorkflowInstanceDTO,
    WorkflowInstanceListDTO,
    WorkflowStatusDTO,
    WorkflowTransitionDTO,
)
from src.application.services.approval_matrix_service import ApprovalMatrixService
from src.application.services.workflow.state_machine_service import InstanceState
from src.application.services.workflow.workflow_engine import WorkflowEngine
from src.domain.entities.user import User
from src.domain.entities.workflow import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowTransition,
)
from src.domain.exceptions.domain_exceptions import (
    BusinessRuleViolationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from src.domain.repositories.approval_matrix_repository import IApprovalMatrixRepository
from src.domain.repositories.role_assignment_repository import IRoleAssignmentRepository
from src.domain.repositories.workflow_definition_repository import IWorkflowDefinitionRepository
from src.domain.repositories.workflow_instance_repository import IWorkflowInstanceRepository

DEFINITION = "WorkflowDefinition"
STATUS = "WorkflowStatus"
TRANSITION = "WorkflowTransition"
INSTANCE = "WorkflowInstance"


class WorkflowService:

    def __init__(
        self,
        workflow_definition_repo: IWorkflowDefinitionRepository,
        workflow_instance_repo: IWorkflowInstanceRepository,
        approval_matrix_repo: IApprovalMatrixRepository,
        role_assignment_repo: IRoleAssignmentRepository,
    ) -> None:
        self._definitions = workflow_definition_repo
        self._instances = workflow_instance_repo
        self._matrices = approval_matrix_repo
        self._matrix_service = ApprovalMatrixService(approval_matrix_repo)
        self._engine = WorkflowEngine(
            definition_repo=workflow_definition_repo,
            instance_repo=workflow_instance_repo,
            matrix_repo=approval_matrix_repo,
            role_assignment_repo=role_assignment_repo,
        )

    # ═══════════════════════════ Definitions ═══════════════════════════

    async def list_definitions(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
        entity_type: str | None = None,
    ) -> WorkflowDefinitionListDTO:
        definitions = await self._definitions.list_all(
            skip=skip, limit=limit, search=search,
            is_active=is_active, entity_type=entity_type,
        )
        total = await self._definitions.count(
            search=search, is_active=is_active, entity_type=entity_type
        )
        return WorkflowDefinitionListDTO(
            definitions=[self._definition_to_dto(d) for d in definitions],
            total=total, skip=skip, limit=limit,
        )

    async def get_definition(self, definition_id: int) -> WorkflowDefinitionDTO:
        return self._definition_to_dto(await self._require_definition(definition_id))

    async def get_definition_detail(self, definition_id: int) -> WorkflowDefinitionDetailDTO:
        definition = await self._require_definition(definition_id)
        statuses = await self._definitions.list_statuses(definition_id)
        transitions = await self._definitions.list_transitions(definition_id)
        return WorkflowDefinitionDetailDTO(
            definition=self._definition_to_dto(definition),
            statuses=[self._status_to_dto(s) for s in statuses],
            transitions=[self._transition_to_dto(t) for t in transitions],
        )

    async def create_definition(
        self, dto: CreateWorkflowDefinitionDTO, actor: User
    ) -> WorkflowDefinitionDTO:
        if await self._definitions.exists_by_code(dto.code):
            raise DuplicateEntityError(DEFINITION, "code", dto.code)
        if await self._definitions.exists_by_name(dto.name):
            raise DuplicateEntityError(DEFINITION, "name", dto.name)
        created = await self._definitions.create(
            WorkflowDefinition(
                code=dto.code, name=dto.name, description=dto.description,
                entity_type=dto.entity_type, version=1, is_active=dto.is_active,
                created_by=actor.username, modified_by=actor.username,
            )
        )
        return self._definition_to_dto(created)

    async def update_definition(
        self, definition_id: int, dto: UpdateWorkflowDefinitionDTO, actor: User
    ) -> WorkflowDefinitionDTO:
        definition = await self._require_definition(definition_id)
        if dto.code is not None and dto.code != definition.code:
            if await self._definitions.exists_by_code(dto.code, exclude_id=definition_id):
                raise DuplicateEntityError(DEFINITION, "code", dto.code)
            definition.code = dto.code
        if dto.name is not None and dto.name != definition.name:
            if await self._definitions.exists_by_name(dto.name, exclude_id=definition_id):
                raise DuplicateEntityError(DEFINITION, "name", dto.name)
            definition.name = dto.name
        if dto.entity_type is not None:
            definition.entity_type = dto.entity_type
        if dto.description is not None:
            definition.description = dto.description
        if dto.is_active is not None:
            definition.is_active = dto.is_active
        definition.mark_modified(actor.username)
        return self._definition_to_dto(await self._definitions.update(definition))

    async def delete_definition(self, definition_id: int) -> None:
        await self._require_definition(definition_id)
        in_use = await self._instances.count(definition_id=definition_id)
        if in_use:
            raise BusinessRuleViolationError(
                f"Workflow cannot be deleted: {in_use} instance(s) reference it."
            )
        await self._definitions.delete(definition_id)

    # ═══════════════════════════ Statuses ═══════════════════════════

    async def list_statuses(self, definition_id: int) -> list[WorkflowStatusDTO]:
        await self._require_definition(definition_id)
        statuses = await self._definitions.list_statuses(definition_id)
        return [self._status_to_dto(s) for s in statuses]

    async def create_status(
        self, definition_id: int, dto: CreateWorkflowStatusDTO, actor: User
    ) -> WorkflowStatusDTO:
        await self._require_definition(definition_id)
        self._reject_initial_and_terminal(is_initial=dto.is_initial, is_terminal=dto.is_terminal)
        if await self._definitions.exists_status_code(definition_id, dto.code):
            raise DuplicateEntityError(STATUS, "code", dto.code)
        if dto.is_initial:
            await self._reject_second_initial(definition_id)
        created = await self._definitions.create_status(
            WorkflowStatus(
                workflow_definition_id=definition_id, code=dto.code, name=dto.name,
                is_initial=dto.is_initial, is_terminal=dto.is_terminal, sequence=dto.sequence,
                created_by=actor.username, modified_by=actor.username,
            )
        )
        return self._status_to_dto(created)

    async def update_status(
        self, status_id: int, dto: UpdateWorkflowStatusDTO, actor: User
    ) -> WorkflowStatusDTO:
        status = await self._require_status(status_id)
        target_initial = dto.is_initial if dto.is_initial is not None else status.is_initial
        target_terminal = dto.is_terminal if dto.is_terminal is not None else status.is_terminal
        self._reject_initial_and_terminal(is_initial=target_initial, is_terminal=target_terminal)
        if dto.code is not None and dto.code != status.code:
            if await self._definitions.exists_status_code(
                status.workflow_definition_id, dto.code, exclude_id=status_id
            ):
                raise DuplicateEntityError(STATUS, "code", dto.code)
            status.code = dto.code
        if target_initial and not status.is_initial:
            await self._reject_second_initial(status.workflow_definition_id, exclude_id=status_id)
        if dto.name is not None:
            status.name = dto.name
        if dto.sequence is not None:
            status.sequence = dto.sequence
        status.is_initial = target_initial
        status.is_terminal = target_terminal
        status.mark_modified(actor.username)
        return self._status_to_dto(await self._definitions.update_status(status))

    async def delete_status(self, status_id: int) -> None:
        await self._require_status(status_id)
        wired = await self._definitions.count_transitions_touching_status(status_id)
        if wired:
            raise BusinessRuleViolationError(f"State cannot be deleted: {wired} transition(s) reference it")
        occupied = await self._definitions.count_instances_in_status(status_id)
        if occupied:
            raise BusinessRuleViolationError(f"State cannot be deleted: {occupied} instance(s) are currently in it")
        await self._definitions.delete_status(status_id)

    # ═══════════════════════════ Transitions ═══════════════════════════

    async def list_transitions(self, definition_id: int) -> list[WorkflowTransitionDTO]:
        await self._require_definition(definition_id)
        transitions = await self._definitions.list_transitions(definition_id)
        return [self._transition_to_dto(t) for t in transitions]

    async def create_transition(
        self, definition_id: int, dto: CreateWorkflowTransitionDTO, actor: User
    ) -> WorkflowTransitionDTO:
        await self._require_definition(definition_id)
        from_status = await self._require_status(dto.from_status_id)
        to_status = await self._require_status(dto.to_status_id)
        for status in (from_status, to_status):
            if status.workflow_definition_id != definition_id:
                raise BusinessRuleViolationError(f"State '{status.code}' belongs to a different workflow")
        if from_status.is_terminal:
            raise BusinessRuleViolationError(f"State '{from_status.code}' is terminal, so no action can leave it")
        if from_status.id == to_status.id:
            raise BusinessRuleViolationError("A transition must move between two different states")
        if await self._definitions.exists_transition(definition_id, dto.from_status_id, dto.action_code):
            raise DuplicateEntityError(TRANSITION, "action_code", f"{dto.action_code} from {from_status.code}")
        created = await self._definitions.create_transition(
            WorkflowTransition(
                workflow_definition_id=definition_id,
                from_status_id=dto.from_status_id, to_status_id=dto.to_status_id,
                action_code=dto.action_code, action_type=dto.action_type,
                guard_expression=dto.guard_expression, requires_comment=dto.requires_comment,
                auto_execute=dto.auto_execute, priority=dto.priority,
                created_by=actor.username, modified_by=actor.username,
            )
        )
        return self._transition_to_dto(created)

    async def delete_transition(self, transition_id: int) -> None:
        if await self._definitions.get_transition(transition_id) is None:
            raise EntityNotFoundError(TRANSITION, transition_id)
        await self._definitions.delete_transition(transition_id)

    # ═══════════════════════════ Runtime ═══════════════════════════

    async def start_workflow(self, dto: StartWorkflowDTO, actor: User) -> WorkflowInstanceDTO:
        state = await self._engine.start(
            definition_code=dto.definition_code, entity_type=dto.entity_type,
            entity_id=dto.entity_id, initiated_by=actor.id, actor_username=actor.username,
            priority=dto.priority, metadata=dto.metadata,
        )
        return self._instance_to_dto(state)

    async def execute_action(
        self, instance_id: int, dto: ExecuteWorkflowActionDTO, actor: User, ip_address: str = "",
    ) -> WorkflowInstanceDTO:
        result = await self._engine.execute_action(
            instance_id=instance_id, action_code=dto.action_code,
            actor_id=actor.id, actor_username=actor.username,
            comments=dto.comments, ip_address=ip_address,
        )
        definition = await self._require_definition(result.instance.workflow_definition_id)
        return self._build_instance_dto(instance=result.instance, status=result.to_status, definition=definition)

    async def get_instance(self, instance_id: int) -> WorkflowInstanceDTO:
        return self._instance_to_dto(await self._engine.get_state(instance_id))

    async def list_instances(
        self,
        skip: int = 0,
        limit: int = 100,
        entity_type: str | None = None,
        entity_id: int | None = None,
        definition_id: int | None = None,
        status_id: int | None = None,
        is_completed: bool | None = None,
    ) -> WorkflowInstanceListDTO:
        instances = await self._instances.list_all(
            skip=skip, limit=limit, entity_type=entity_type, entity_id=entity_id,
            definition_id=definition_id, status_id=status_id, is_completed=is_completed,
        )
        total = await self._instances.count(
            entity_type=entity_type, entity_id=entity_id, definition_id=definition_id,
            status_id=status_id, is_completed=is_completed,
        )
        definitions = {
            d.id: d for d in await self._definitions.get_definitions_by_ids(
                [i.workflow_definition_id for i in instances]
            )
        }
        statuses = {
            s.id: s for s in await self._definitions.get_statuses_by_ids(
                [i.current_status_id for i in instances]
            )
        }
        rows = []
        for instance in instances:
            definition = definitions.get(instance.workflow_definition_id)
            status = statuses.get(instance.current_status_id)
            if definition is None or status is None:
                continue
            rows.append(self._build_instance_dto(instance=instance, status=status, definition=definition))
        return WorkflowInstanceListDTO(instances=rows, total=total, skip=skip, limit=limit)

    async def available_actions(self, instance_id: int) -> list[WorkflowAvailableActionDTO]:
        transitions = await self._engine.available_actions(instance_id)
        statuses = {
            s.id: s for s in await self._definitions.get_statuses_by_ids(
                [t.to_status_id for t in transitions]
            )
        }
        actions = []
        for transition in transitions:
            target = statuses.get(transition.to_status_id)
            if target is None:
                continue
            actions.append(WorkflowAvailableActionDTO(
                action_code=transition.action_code, action_type=transition.action_type,
                to_status_id=target.id, to_status_code=target.code,
                to_status_name=target.name, requires_comment=transition.requires_comment,
                is_terminal=target.is_terminal,
            ))
        return actions

    async def instance_history(self, instance_id: int) -> list[WorkflowHistoryDTO]:
        if await self._instances.get_by_id(instance_id) is None:
            raise EntityNotFoundError(INSTANCE, instance_id)
        entries = await self._instances.list_history(instance_id)
        referenced = [e.to_status_id for e in entries]
        referenced += [e.from_status_id for e in entries if e.from_status_id]
        statuses = {s.id: s for s in await self._definitions.get_statuses_by_ids(referenced)}
        return [
            WorkflowHistoryDTO(
                id=entry.id, instance_id=entry.instance_id,
                from_status_id=entry.from_status_id,
                from_status_code=(statuses[entry.from_status_id].code if entry.from_status_id in statuses else None),
                to_status_id=entry.to_status_id,
                to_status_code=(statuses[entry.to_status_id].code if entry.to_status_id in statuses else None),
                action_code=entry.action_code, actor_id=entry.actor_id,
                actor_username=entry.actor_username, comments=entry.comments,
                ip_address=entry.ip_address, created_at=entry.created_at,
            )
            for entry in entries
        ]

    async def my_tasks(self, user_id: int) -> list[ApprovalTaskDTO]:
        return await self._matrix_service.list_tasks_for_user(user_id)

    async def instance_tasks(self, instance_id: int) -> list[ApprovalTaskDTO]:
        if await self._instances.get_by_id(instance_id) is None:
            raise EntityNotFoundError(INSTANCE, instance_id)
        return await self._matrix_service.list_tasks_for_instance(instance_id)

    # ═══════════════════════════ Internals ═══════════════════════════

    async def _require_definition(self, definition_id: int) -> WorkflowDefinition:
        definition = await self._definitions.get_by_id(definition_id)
        if definition is None:
            raise EntityNotFoundError(DEFINITION, definition_id)
        return definition

    async def _require_status(self, status_id: int) -> WorkflowStatus:
        status = await self._definitions.get_status(status_id)
        if status is None:
            raise EntityNotFoundError(STATUS, status_id)
        return status

    async def _reject_second_initial(
        self, definition_id: int, exclude_id: int | None = None
    ) -> None:
        existing = await self._definitions.get_initial_status(definition_id)
        if existing is not None and existing.id != exclude_id:
            raise BusinessRuleViolationError(
                f"Workflow already has an initial state ('{existing.code}'); clear it before setting another"
            )

    @staticmethod
    def _reject_initial_and_terminal(*, is_initial: bool, is_terminal: bool) -> None:
        if is_initial and is_terminal:
            raise BusinessRuleViolationError("A state cannot be both initial and terminal")

    @staticmethod
    def _definition_to_dto(d: WorkflowDefinition) -> WorkflowDefinitionDTO:
        return WorkflowDefinitionDTO(
            id=d.id, code=d.code, name=d.name, description=d.description,
            entity_type=d.entity_type, version=d.version, is_active=d.is_active,
            created_by=d.created_by, created_date=d.created_date,
            modified_by=d.modified_by, modified_date=d.modified_date,
        )

    @staticmethod
    def _status_to_dto(s: WorkflowStatus) -> WorkflowStatusDTO:
        return WorkflowStatusDTO(
            id=s.id, workflow_definition_id=s.workflow_definition_id,
            code=s.code, name=s.name, is_initial=s.is_initial,
            is_terminal=s.is_terminal, sequence=s.sequence,
        )

    @staticmethod
    def _transition_to_dto(t: WorkflowTransition) -> WorkflowTransitionDTO:
        return WorkflowTransitionDTO(
            id=t.id, workflow_definition_id=t.workflow_definition_id,
            from_status_id=t.from_status_id, to_status_id=t.to_status_id,
            action_code=t.action_code, action_type=t.action_type,
            guard_expression=t.guard_expression, requires_comment=t.requires_comment,
            auto_execute=t.auto_execute, priority=t.priority,
        )

    @staticmethod
    def _instance_to_dto(state: InstanceState) -> WorkflowInstanceDTO:
        return WorkflowService._build_instance_dto(
            instance=state.instance, status=state.status, definition=state.definition,
        )

    @staticmethod
    def _build_instance_dto(
        *, instance: WorkflowInstance, status: WorkflowStatus, definition: WorkflowDefinition,
    ) -> WorkflowInstanceDTO:
        return WorkflowInstanceDTO(
            id=instance.id, workflow_definition_id=definition.id,
            definition_code=definition.code, definition_name=definition.name,
            entity_type=instance.entity_type, entity_id=instance.entity_id,
            current_status_id=status.id, current_status_code=status.code,
            current_status_name=status.name, is_terminal=status.is_terminal,
            initiated_by=instance.initiated_by, priority=instance.priority,
            due_date=instance.due_date, started_at=instance.started_at,
            completed_at=instance.completed_at, is_completed=instance.is_completed,
            approval_level=instance.approval_level, is_awaiting_approval=instance.is_awaiting_approval,
            metadata=instance.extra_data,
        )
