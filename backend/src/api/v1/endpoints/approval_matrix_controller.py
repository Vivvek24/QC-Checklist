"""
Approval matrix API endpoints.

Thin controller — maps HTTP schemas to/from application DTOs, delegates to
ApprovalMatrixService. All business logic sits in the service.
"""


from fastapi import APIRouter, Depends, Query, status

from src.api.v1.dependencies import (
    get_approval_matrix_repository,
    get_current_active_user,
)
from src.api.v1.schemas.approval_matrix_schema import (
    ApprovalAssignmentInput,
    ApprovalAssignmentResponse,
    ApprovalMatrixCreate,
    ApprovalMatrixListResponse,
    ApprovalMatrixResponse,
    ApprovalMatrixUpdate,
    ApprovalResolveRequest,
    ApprovalResolveResponse,
    ApprovalRuleInput,
    ApprovalRuleResponse,
)
from src.application.dtos.approval_matrix_dtos import (
    ApprovalAssignmentDTO,
    ApprovalMatrixDTO,
    ApprovalMatrixListDTO,
    ApprovalResolutionDTO,
    ApprovalRuleDTO,
    CreateApprovalMatrixDTO,
    UpdateApprovalMatrixDTO,
)
from src.application.services.approval_matrix_service import ApprovalMatrixService
from src.domain.entities.user import User
from src.domain.repositories.approval_matrix_repository import IApprovalMatrixRepository
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(
    prefix="/workflow/approval-matrices", tags=["Workflow - Approval Matrix"]
)

RESOURCE = "approval_matrices"


def _get_approval_matrix_service(
    approval_matrix_repo: IApprovalMatrixRepository = Depends(
        get_approval_matrix_repository
    ),
) -> ApprovalMatrixService:
    return ApprovalMatrixService(approval_matrix_repo=approval_matrix_repo)


# ─── Schema ↔ DTO mappers ───

def _rule_input_to_dto(r: ApprovalRuleInput) -> ApprovalRuleDTO:
    return ApprovalRuleDTO(
        field=r.field, operator=r.operator, value=r.value,
        data_type=r.data_type, logical_group=r.logical_group,
    )


def _assignment_input_to_dto(a: ApprovalAssignmentInput) -> ApprovalAssignmentDTO:
    return ApprovalAssignmentDTO(
        level=a.level, assignment_type=a.assignment_type,
        user_id=a.user_id, role_id=a.role_id,
    )


def _matrix_dto_to_response(dto: ApprovalMatrixDTO) -> ApprovalMatrixResponse:
    return ApprovalMatrixResponse(
        id=dto.id, code=dto.code, name=dto.name, entity_type=dto.entity_type,
        priority=dto.priority, is_active=dto.is_active,
        rules=[
            ApprovalRuleResponse(
                id=r.id, field=r.field, operator=r.operator, value=r.value,
                data_type=r.data_type, logical_group=r.logical_group,
            )
            for r in dto.rules
        ],
        assignments=[
            ApprovalAssignmentResponse(
                id=a.id, level=a.level, assignment_type=a.assignment_type,
                user_id=a.user_id, role_id=a.role_id,
            )
            for a in dto.assignments
        ],
        created_by=dto.created_by, created_date=dto.created_date,
        modified_by=dto.modified_by, modified_date=dto.modified_date,
    )


def _list_dto_to_response(dto: ApprovalMatrixListDTO) -> ApprovalMatrixListResponse:
    return ApprovalMatrixListResponse(
        matrices=[_matrix_dto_to_response(m) for m in dto.matrices],
        total=dto.total, skip=dto.skip, limit=dto.limit,
    )


def _resolution_dto_to_response(dto: ApprovalResolutionDTO) -> ApprovalResolveResponse:
    return ApprovalResolveResponse(
        matched=dto.matched,
        matrix=_matrix_dto_to_response(dto.matrix) if dto.matrix else None,
        levels=dto.levels,
        assignments=[
            ApprovalAssignmentResponse(
                id=a.id, level=a.level, assignment_type=a.assignment_type,
                user_id=a.user_id, role_id=a.role_id,
            )
            for a in dto.assignments
        ],
    )


# ─── Endpoints ───

@router.get(
    "",
    response_model=ApprovalMatrixListResponse,
    summary="List approval matrices",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_matrices(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    service: ApprovalMatrixService = Depends(_get_approval_matrix_service),
) -> ApprovalMatrixListResponse:
    """GET /api/v1/workflow/approval-matrices"""
    result = await service.list_matrices(
        skip=skip, limit=limit, search=search,
        is_active=is_active, entity_type=entity_type,
    )
    return _list_dto_to_response(result)


@router.post(
    "",
    response_model=ApprovalMatrixResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an approval matrix",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def create_matrix(
    request: ApprovalMatrixCreate,
    current_user: User = Depends(get_current_active_user),
    service: ApprovalMatrixService = Depends(_get_approval_matrix_service),
) -> ApprovalMatrixResponse:
    """POST /api/v1/workflow/approval-matrices"""
    dto = CreateApprovalMatrixDTO(
        code=request.code, name=request.name, entity_type=request.entity_type,
        priority=request.priority, is_active=request.is_active,
        rules=[_rule_input_to_dto(r) for r in request.rules],
        assignments=[_assignment_input_to_dto(a) for a in request.assignments],
    )
    return _matrix_dto_to_response(await service.create_matrix(dto=dto, actor=current_user))


@router.post(
    "/resolve",
    response_model=ApprovalResolveResponse,
    summary="Preview which matrix would route a sample record",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def resolve_matrix(
    request: ApprovalResolveRequest,
    service: ApprovalMatrixService = Depends(_get_approval_matrix_service),
) -> ApprovalResolveResponse:
    """POST /api/v1/workflow/approval-matrices/resolve"""
    result = await service.resolve(
        entity_type=request.entity_type, entity_data=request.entity_data
    )
    return _resolution_dto_to_response(result)


@router.get(
    "/{matrix_id}",
    response_model=ApprovalMatrixResponse,
    summary="Get an approval matrix",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_matrix(
    matrix_id: int,
    service: ApprovalMatrixService = Depends(_get_approval_matrix_service),
) -> ApprovalMatrixResponse:
    """GET /api/v1/workflow/approval-matrices/{matrix_id}"""
    return _matrix_dto_to_response(await service.get_matrix(matrix_id))


@router.patch(
    "/{matrix_id}",
    response_model=ApprovalMatrixResponse,
    summary="Update an approval matrix",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def update_matrix(
    matrix_id: int,
    request: ApprovalMatrixUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ApprovalMatrixService = Depends(_get_approval_matrix_service),
) -> ApprovalMatrixResponse:
    """PATCH /api/v1/workflow/approval-matrices/{matrix_id}"""
    dto = UpdateApprovalMatrixDTO(
        name=request.name, entity_type=request.entity_type,
        priority=request.priority, is_active=request.is_active,
        rules=[_rule_input_to_dto(r) for r in request.rules] if request.rules is not None else None,
        assignments=(
            [_assignment_input_to_dto(a) for a in request.assignments]
            if request.assignments is not None else None
        ),
    )
    return _matrix_dto_to_response(
        await service.update_matrix(matrix_id=matrix_id, dto=dto, actor=current_user)
    )


@router.delete(
    "/{matrix_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an approval matrix",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_matrix(
    matrix_id: int,
    service: ApprovalMatrixService = Depends(_get_approval_matrix_service),
) -> None:
    """DELETE /api/v1/workflow/approval-matrices/{matrix_id}"""
    await service.delete_matrix(matrix_id)

