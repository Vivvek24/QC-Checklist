"""Dashboard — API controller for QC Checklist dashboard data."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.dashboard_schema import (
    DashboardResponse,
    DashboardRowSchema,
)
from src.application.services.qc_checklist.dashboard_service import (
    DashboardRow,
    DashboardService,
)
from src.domain.entities.user import User
from src.infrastructure.database.repositories.qc_checklist.dashboard_repository_impl import (
    DashboardRepository,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - Dashboard"])


def _serialize(row: DashboardRow) -> DashboardRowSchema:
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


@router.get("/dashboard", response_model=DashboardResponse,
            summary="Dashboard data — pending and approved checklist requests",
            dependencies=[Depends(require_api_permission("dashboard", "READ"))])
async def get_dashboard(
    from_date: date | None = Query(None, description="Filter from date (inclusive)"),
    to_date: date | None = Query(None, description="Filter to date (exclusive)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    """Returns the dashboard grid data split into pending and approved tabs.
    Role scoping (role_id + admin flag) is resolved inside the service."""
    service = DashboardService(DashboardRepository(session))
    data = await service.get_dashboard_for_user(
        user_id=current_user.id, from_date=from_date, to_date=to_date,
    )
    return DashboardResponse(
        pending=[_serialize(r) for r in data["pending"]],
        approved=[_serialize(r) for r in data["approved"]],
        total=data.get("total", 0),
    )
