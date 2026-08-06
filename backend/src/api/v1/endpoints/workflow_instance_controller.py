"""
Workflow runtime API endpoints.

Separate from `workflow_controller` because designing a workflow and acting on one
are different privileges. Thin controller — maps HTTP schemas to/from application
DTOs, delegates to WorkflowService.
"""


from fastapi import APIRouter, Depends, Query, Request, status

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.endpoints.workflow_controller import (
    get_workflow_service,
    _transition_dto_to_response,
)
from src.api.v1.schemas.approval_matrix_schema import (
    ApprovalAssignmentResponse,
    ApprovalTaskResponse,
)
from src.api.v1.schemas.workflow_schema import (
    WorkflowActionRequest,
    WorkflowAvailableActionResponse,
    WorkflowHistoryResponse,
    WorkflowInstanceListResponse,
    WorkflowInstanceResponse,
    WorkflowStartRequest,
)
from src.application.dtos.approval_matrix_dtos import ApprovalTaskDTO
from src.application.dtos.workflow_dtos import (
    ExecuteWorkflowActionDTO,
    StartWorkflowDTO,
    WorkflowAvailableActionDTO,
    WorkflowHistoryDTO,
    WorkflowInstanceDTO,
    WorkflowInstanceListDTO,
)
from src.application.services.workflow_service import WorkflowService
from src.domain.entities.user import User
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/workflow", tags=["Workflow - Runtime"])

RESOURCE = "workflow_instances"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.client.host[:45] if request.client else ""


# ─── Schema ↔ DTO mappers ───

def _instance_dto_to_response(dto: WorkflowInstanceDTO) -> WorkflowInstanceResponse:
    return WorkflowInstanceResponse(
        id=dto.id,
        workflow_definition_id=dto.workflow_definition_id,
        definition_code=dto.definition_code,
        definition_name=dto.definition_name,
        entity_type=dto.entity_type,
        entity_id=dto.entity_id,
        current_status_id=dto.current_status_id,
        current_status_code=dto.current_status_code,
        current_status_name=dto.current_status_name,
        is_terminal=dto.is_terminal,
        initiated_by=dto.initiated_by,
        priority=dto.priority,
        due_date=dto.due_date,
        started_at=dto.started_at,
        completed_at=dto.completed_at,
        is_completed=dto.is_completed,
        approval_level=dto.approval_level,
        is_awaiting_approval=dto.is_awaiting_approval,
        metadata=dto.metadata,
    )


def _instance_list_dto_to_response(dto: WorkflowInstanceListDTO) -> WorkflowInstanceListResponse:
    return WorkflowInstanceListResponse(
        instances=[_instance_dto_to_response(i) for i in dto.instances],
        total=dto.total, skip=dto.skip, limit=dto.limit,
    )


def _available_action_dto_to_response(dto: WorkflowAvailableActionDTO) -> WorkflowAvailableActionResponse:
    return WorkflowAvailableActionResponse(
        action_code=dto.action_code,
        action_type=dto.action_type,
        to_status_id=dto.to_status_id,
        to_status_code=dto.to_status_code,
        to_status_name=dto.to_status_name,
        requires_comment=dto.requires_comment,
        is_terminal=dto.is_terminal,
    )


def _history_dto_to_response(dto: WorkflowHistoryDTO) -> WorkflowHistoryResponse:
    return WorkflowHistoryResponse(
        id=dto.id,
        instance_id=dto.instance_id,
        from_status_id=dto.from_status_id,
        from_status_code=dto.from_status_code,
        to_status_id=dto.to_status_id,
        to_status_code=dto.to_status_code,
        action_code=dto.action_code,
        actor_id=dto.actor_id,
        actor_username=dto.actor_username,
        comments=dto.comments,
        ip_address=dto.ip_address,
        created_at=dto.created_at,
    )


def _task_dto_to_response(dto: ApprovalTaskDTO) -> ApprovalTaskResponse:
    return ApprovalTaskResponse(
        id=dto.id,
        instance_id=dto.instance_id,
        matrix_id=dto.matrix_id,
        assignee_id=dto.assignee_id,
        level=dto.level,
        status=dto.status,
        action_taken=dto.action_taken,
        due_date=dto.due_date,
        comments=dto.comments,
        created_date=dto.created_date,
    )


# ─── Endpoints ───

@router.get(
    "/instances",
    response_model=WorkflowInstanceListResponse,
    summary="List workflow instances",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_instances(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    definition_id: int | None = Query(default=None),
    status_id: int | None = Query(default=None),
    is_completed: bool | None = Query(default=None),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowInstanceListResponse:
    """GET /api/v1/workflow/instances"""
    result = await service.list_instances(
        skip=skip, limit=limit, entity_type=entity_type,
        entity_id=entity_id, definition_id=definition_id,
        status_id=status_id, is_completed=is_completed,
    )
    return _instance_list_dto_to_response(result)


@router.post(
    "/instances",
    response_model=WorkflowInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a workflow instance",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def start_workflow(
    request: WorkflowStartRequest,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowInstanceResponse:
    """POST /api/v1/workflow/instances"""
    dto = StartWorkflowDTO(
        definition_code=request.definition_code,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        priority=request.priority,
        metadata=request.metadata,
    )
    return _instance_dto_to_response(await service.start_workflow(dto=dto, actor=current_user))


@router.get(
    "/instances/{instance_id}",
    response_model=WorkflowInstanceResponse,
    summary="Get a workflow instance",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_instance(
    instance_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowInstanceResponse:
    """GET /api/v1/workflow/instances/{instance_id}"""
    return _instance_dto_to_response(await service.get_instance(instance_id))


@router.post(
    "/instances/{instance_id}/actions",
    response_model=WorkflowInstanceResponse,
    summary="Execute an action on a workflow instance",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def execute_action(
    instance_id: int,
    request: WorkflowActionRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowInstanceResponse:
    """POST /api/v1/workflow/instances/{instance_id}/actions"""
    dto = ExecuteWorkflowActionDTO(
        action_code=request.action_code,
        comments=request.comments,
    )
    return _instance_dto_to_response(
        await service.execute_action(
            instance_id=instance_id, dto=dto,
            actor=current_user, ip_address=_client_ip(http_request),
        )
    )


@router.get(
    "/instances/{instance_id}/actions",
    response_model=list[WorkflowAvailableActionResponse],
    summary="List actions available from the instance's current state",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_available_actions(
    instance_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowAvailableActionResponse]:
    """GET /api/v1/workflow/instances/{instance_id}/actions"""
    result = await service.available_actions(instance_id)
    return [_available_action_dto_to_response(a) for a in result]


@router.get(
    "/instances/{instance_id}/history",
    response_model=list[WorkflowHistoryResponse],
    summary="Get the audit trail of a workflow instance",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_instance_history(
    instance_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowHistoryResponse]:
    """GET /api/v1/workflow/instances/{instance_id}/history"""
    result = await service.instance_history(instance_id)
    return [_history_dto_to_response(h) for h in result]


@router.get(
    "/instances/{instance_id}/tasks",
    response_model=list[ApprovalTaskResponse],
    summary="Get the approval chain of a workflow instance",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_instance_tasks(
    instance_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[ApprovalTaskResponse]:
    """GET /api/v1/workflow/instances/{instance_id}/tasks"""
    result = await service.instance_tasks(instance_id)
    return [_task_dto_to_response(t) for t in result]


@router.get(
    "/my-tasks",
    response_model=list[ApprovalTaskResponse],
    summary="List the current user's pending approval tasks",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_my_tasks(
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> list[ApprovalTaskResponse]:
    """GET /api/v1/workflow/my-tasks"""
    result = await service.my_tasks(current_user.id)
    return [_task_dto_to_response(t) for t in result]

