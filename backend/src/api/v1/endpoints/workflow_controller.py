"""
Workflow configuration API endpoints.

Covers the definition and the state machine wired under it. Runtime execution
lives in `workflow_instance_controller` so that permission to design a workflow
is separable from permission to act on one.

Thin controller — maps HTTP schemas to/from application DTOs, delegates to
WorkflowService. All business logic sits in the service.
"""


from fastapi import APIRouter, Depends, Query, status

from src.api.v1.dependencies import (
    get_approval_matrix_repository,
    get_current_active_user,
    get_role_assignment_repository,
    get_workflow_definition_repository,
    get_workflow_instance_repository,
)
from src.api.v1.schemas.workflow_schema import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionDetailResponse,
    WorkflowDefinitionListResponse,
    WorkflowDefinitionResponse,
    WorkflowDefinitionUpdate,
    WorkflowStatusCreate,
    WorkflowStatusResponse,
    WorkflowStatusUpdate,
    WorkflowTransitionCreate,
    WorkflowTransitionResponse,
)
from src.application.dtos.workflow_dtos import (
    CreateWorkflowDefinitionDTO,
    CreateWorkflowStatusDTO,
    CreateWorkflowTransitionDTO,
    UpdateWorkflowDefinitionDTO,
    UpdateWorkflowStatusDTO,
    WorkflowDefinitionDTO,
    WorkflowDefinitionDetailDTO,
    WorkflowDefinitionListDTO,
    WorkflowStatusDTO,
    WorkflowTransitionDTO,
)
from src.application.services.workflow_service import WorkflowService
from src.domain.entities.user import User
from src.domain.repositories.approval_matrix_repository import IApprovalMatrixRepository
from src.domain.repositories.role_assignment_repository import IRoleAssignmentRepository
from src.domain.repositories.workflow_definition_repository import (
    IWorkflowDefinitionRepository,
)
from src.domain.repositories.workflow_instance_repository import (
    IWorkflowInstanceRepository,
)
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/workflow", tags=["Workflow - Configuration"])

RESOURCE = "workflows"


def get_workflow_service(
    workflow_definition_repo: IWorkflowDefinitionRepository = Depends(
        get_workflow_definition_repository
    ),
    workflow_instance_repo: IWorkflowInstanceRepository = Depends(
        get_workflow_instance_repository
    ),
    approval_matrix_repo: IApprovalMatrixRepository = Depends(
        get_approval_matrix_repository
    ),
    role_assignment_repo: IRoleAssignmentRepository = Depends(
        get_role_assignment_repository
    ),
) -> WorkflowService:
    """
    FastAPI dependency — creates WorkflowService with injected repositories.
    Shared with workflow_instance_controller.
    """
    return WorkflowService(
        workflow_definition_repo=workflow_definition_repo,
        workflow_instance_repo=workflow_instance_repo,
        approval_matrix_repo=approval_matrix_repo,
        role_assignment_repo=role_assignment_repo,
    )


# ─── Schema ↔ DTO mappers ───

def _definition_dto_to_response(dto: WorkflowDefinitionDTO) -> WorkflowDefinitionResponse:
    return WorkflowDefinitionResponse(
        id=dto.id, code=dto.code, name=dto.name, description=dto.description,
        entity_type=dto.entity_type, version=dto.version, is_active=dto.is_active,
        created_by=dto.created_by, created_date=dto.created_date,
        modified_by=dto.modified_by, modified_date=dto.modified_date,
    )


def _definition_list_dto_to_response(dto: WorkflowDefinitionListDTO) -> WorkflowDefinitionListResponse:
    return WorkflowDefinitionListResponse(
        definitions=[_definition_dto_to_response(d) for d in dto.definitions],
        total=dto.total, skip=dto.skip, limit=dto.limit,
    )


def _status_dto_to_response(dto: WorkflowStatusDTO) -> WorkflowStatusResponse:
    return WorkflowStatusResponse(
        id=dto.id, workflow_definition_id=dto.workflow_definition_id,
        code=dto.code, name=dto.name, is_initial=dto.is_initial,
        is_terminal=dto.is_terminal, sequence=dto.sequence,
    )


def _transition_dto_to_response(dto: WorkflowTransitionDTO) -> WorkflowTransitionResponse:
    return WorkflowTransitionResponse(
        id=dto.id, workflow_definition_id=dto.workflow_definition_id,
        from_status_id=dto.from_status_id, to_status_id=dto.to_status_id,
        action_code=dto.action_code, action_type=dto.action_type,
        guard_expression=dto.guard_expression, requires_comment=dto.requires_comment,
        auto_execute=dto.auto_execute, priority=dto.priority,
    )


def _detail_dto_to_response(dto: WorkflowDefinitionDetailDTO) -> WorkflowDefinitionDetailResponse:
    return WorkflowDefinitionDetailResponse(
        definition=_definition_dto_to_response(dto.definition),
        statuses=[_status_dto_to_response(s) for s in dto.statuses],
        transitions=[_transition_dto_to_response(t) for t in dto.transitions],
    )


# ─── Definitions ───

@router.get(
    "/definitions",
    response_model=WorkflowDefinitionListResponse,
    summary="List workflow definitions",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_definitions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinitionListResponse:
    """GET /api/v1/workflow/definitions"""
    result = await service.list_definitions(
        skip=skip, limit=limit, search=search,
        is_active=is_active, entity_type=entity_type,
    )
    return _definition_list_dto_to_response(result)


@router.post(
    "/definitions",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workflow definition",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def create_definition(
    request: WorkflowDefinitionCreate,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinitionResponse:
    """POST /api/v1/workflow/definitions"""
    dto = CreateWorkflowDefinitionDTO(
        code=request.code, name=request.name, entity_type=request.entity_type,
        description=request.description, is_active=request.is_active,
    )
    return _definition_dto_to_response(await service.create_definition(dto=dto, actor=current_user))


@router.get(
    "/definitions/{definition_id}",
    response_model=WorkflowDefinitionDetailResponse,
    summary="Get a workflow definition with its states and transitions",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_definition(
    definition_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinitionDetailResponse:
    """GET /api/v1/workflow/definitions/{definition_id}"""
    return _detail_dto_to_response(await service.get_definition_detail(definition_id))


@router.patch(
    "/definitions/{definition_id}",
    response_model=WorkflowDefinitionResponse,
    summary="Update a workflow definition",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def update_definition(
    definition_id: int,
    request: WorkflowDefinitionUpdate,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinitionResponse:
    """PATCH /api/v1/workflow/definitions/{definition_id}"""
    dto = UpdateWorkflowDefinitionDTO(
        code=request.code, name=request.name, entity_type=request.entity_type,
        description=request.description, is_active=request.is_active,
    )
    return _definition_dto_to_response(
        await service.update_definition(definition_id=definition_id, dto=dto, actor=current_user)
    )


@router.delete(
    "/definitions/{definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workflow definition",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_definition(
    definition_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """DELETE /api/v1/workflow/definitions/{definition_id}"""
    await service.delete_definition(definition_id)


# ─── States ───

@router.get(
    "/definitions/{definition_id}/statuses",
    response_model=list[WorkflowStatusResponse],
    summary="List states of a workflow",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_statuses(
    definition_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowStatusResponse]:
    """GET /api/v1/workflow/definitions/{definition_id}/statuses"""
    result = await service.list_statuses(definition_id)
    return [_status_dto_to_response(s) for s in result]


@router.post(
    "/definitions/{definition_id}/statuses",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a state to a workflow",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def create_status(
    definition_id: int,
    request: WorkflowStatusCreate,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStatusResponse:
    """POST /api/v1/workflow/definitions/{definition_id}/statuses"""
    dto = CreateWorkflowStatusDTO(
        code=request.code, name=request.name, is_initial=request.is_initial,
        is_terminal=request.is_terminal, sequence=request.sequence,
    )
    return _status_dto_to_response(
        await service.create_status(definition_id=definition_id, dto=dto, actor=current_user)
    )


@router.patch(
    "/statuses/{status_id}",
    response_model=WorkflowStatusResponse,
    summary="Update a workflow state",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def update_status(
    status_id: int,
    request: WorkflowStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStatusResponse:
    """PATCH /api/v1/workflow/statuses/{status_id}"""
    dto = UpdateWorkflowStatusDTO(
        code=request.code, name=request.name, is_initial=request.is_initial,
        is_terminal=request.is_terminal, sequence=request.sequence,
    )
    return _status_dto_to_response(
        await service.update_status(status_id=status_id, dto=dto, actor=current_user)
    )


@router.delete(
    "/statuses/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workflow state",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_status(
    status_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """DELETE /api/v1/workflow/statuses/{status_id}"""
    await service.delete_status(status_id)


# ─── Transitions ───

@router.get(
    "/definitions/{definition_id}/transitions",
    response_model=list[WorkflowTransitionResponse],
    summary="List transitions of a workflow",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_transitions(
    definition_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowTransitionResponse]:
    """GET /api/v1/workflow/definitions/{definition_id}/transitions"""
    result = await service.list_transitions(definition_id)
    return [_transition_dto_to_response(t) for t in result]


@router.post(
    "/definitions/{definition_id}/transitions",
    response_model=WorkflowTransitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a transition to a workflow",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def create_transition(
    definition_id: int,
    request: WorkflowTransitionCreate,
    current_user: User = Depends(get_current_active_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowTransitionResponse:
    """POST /api/v1/workflow/definitions/{definition_id}/transitions"""
    dto = CreateWorkflowTransitionDTO(
        from_status_id=request.from_status_id, to_status_id=request.to_status_id,
        action_code=request.action_code, action_type=request.action_type,
        guard_expression=request.guard_expression,
        requires_comment=request.requires_comment,
        auto_execute=request.auto_execute, priority=request.priority,
    )
    return _transition_dto_to_response(
        await service.create_transition(
            definition_id=definition_id, dto=dto, actor=current_user
        )
    )


@router.delete(
    "/transitions/{transition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transition",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_transition(
    transition_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """DELETE /api/v1/workflow/transitions/{transition_id}"""
    await service.delete_transition(transition_id)

