"""Dashboard — API controller for QC Checklist dashboard data."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.application.services.qc_checklist.dashboard_service import DashboardService
from src.infrastructure.database.repositories.qc_checklist.dashboard_repository_impl import DashboardRepository
from src.domain.entities.user import User
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - Dashboard"])


class DashboardRowSchema(BaseModel):
    request_number: str
    format_name: str
    status_format: str
    created_date: str | None = None
    stage_status: str
    requested_by: str
    request_status: str
    is_last_stage: bool
    batch_no: str
    product_name: str
    test_name: str
    action_flag: bool = False


class DashboardResponse(BaseModel):
    pending: list[DashboardRowSchema]
    approved: list[DashboardRowSchema]


@router.get("/dashboard", response_model=DashboardResponse,
            summary="Dashboard data — pending and approved checklist requests",
            dependencies=[Depends(require_api_permission("dashboard", "READ"))])
async def get_dashboard(
    from_date: date | None = Query(None, description="Filter from date (inclusive)"),
    to_date: date | None = Query(None, description="Filter to date (exclusive)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    """Returns the dashboard grid data split into pending and approved tabs."""
    from sqlalchemy import select
    from src.infrastructure.database.models.role_model import RoleModel, RoleAssignmentModel

    service = DashboardService(DashboardRepository(session))

    # Get user's role
    role_id: int | None = None
    is_admin = False
    ra_result = await session.execute(
        select(RoleAssignmentModel.role_id).where(
            RoleAssignmentModel.user_id == current_user.id,
            RoleAssignmentModel.is_active.is_(True),
        ).limit(1)
    )
    role_id = ra_result.scalar_one_or_none()

    if role_id:
        role_result = await session.execute(
            select(RoleModel.name).where(RoleModel.id == role_id)
        )
        role_name = role_result.scalar_one_or_none()
        is_admin = role_name in ("Administrator", "UnitAdmin") if role_name else False

    data = await service.get_dashboard(
        from_date=from_date,
        to_date=to_date,
        role_id=role_id,
        is_admin=is_admin,
    )

    def serialize(row) -> DashboardRowSchema:
        return DashboardRowSchema(
            request_number=row.request_number,
            format_name=row.format_name,
            status_format=row.status_format,
            created_date=row.created_date.isoformat() if row.created_date else None,
            stage_status=row.stage_status,
            requested_by=row.requested_by,
            request_status=row.request_status,
            is_last_stage=row.is_last_stage,
            batch_no=row.batch_no,
            product_name=row.product_name,
            test_name=row.test_name,
            action_flag=row.action_flag,
        )

    return DashboardResponse(
        pending=[serialize(r) for r in data["pending"]],
        approved=[serialize(r) for r in data["approved"]],
    )


async def _is_admin_role(session: AsyncSession, role_id: int) -> bool:
    """Check if the user's role is Administrator or UnitAdmin."""
    from sqlalchemy import select, BigInteger
    from src.infrastructure.database.models.role_model import RoleModel
    result = await session.execute(
        select(RoleModel.name).where(RoleModel.id == role_id)
    )
    role_name = result.scalar_one_or_none()
    return role_name in ("Administrator", "UnitAdmin") if role_name else False
