"""Dashboard Service — builds the dashboard data from checklist requests.
Uses DashboardRepository for all DB queries (no raw SQL in service layer).
"""

from dataclasses import dataclass
from datetime import date, datetime

from src.infrastructure.database.repositories.qc_checklist.dashboard_repository_impl import (
    DashboardRepository,
    DashboardQueryRow,
)


@dataclass
class DashboardRow:
    request_number: str
    format_name: str
    status_format: str
    created_date: datetime | None
    stage_status: str
    requested_by: str
    request_status: str
    is_last_stage: bool
    batch_no: str
    product_name: str
    test_name: str
    action_flag: bool


class DashboardService:
    """Produces the dashboard grid data — pending and approved requests."""

    def __init__(self, repo: DashboardRepository) -> None:
        self._repo = repo

    async def get_dashboard(
        self,
        from_date: date | None,
        to_date: date | None,
        role_id: int | None,
        is_admin: bool,
    ) -> dict[str, list[DashboardRow]]:
        """Returns { pending: [...], approved: [...] }."""
        pending_rows = await self._repo.fetch_dashboard_rows(
            is_last_stage=False, pending_statuses=True,
            from_date=from_date, to_date=to_date,
            role_id=role_id, is_admin=is_admin,
        )
        approved_rows = await self._repo.fetch_dashboard_rows(
            is_last_stage=True, pending_statuses=False,
            from_date=from_date, to_date=to_date,
            role_id=role_id, is_admin=is_admin,
        )

        pending = [self._to_dashboard_row(r) for r in pending_rows]
        approved = [self._to_dashboard_row(r) for r in approved_rows]

        # Compute action_flag for pending requests
        if role_id:
            for dr in pending:
                dr.action_flag = await self._control_button_visibility(dr.request_number, role_id)

        return {"pending": pending, "approved": approved}

    def _to_dashboard_row(self, row: DashboardQueryRow) -> DashboardRow:
        return DashboardRow(
            request_number=row.request_number,
            format_name=row.format_name,
            status_format=row.status_format,
            created_date=row.created_date,
            stage_status=row.stage_status,
            requested_by=row.requested_by,
            request_status=row.request_status,
            is_last_stage=row.is_last_stage,
            batch_no=row.batch_no,
            product_name=row.product_name,
            test_name=row.test_name,
            action_flag=False,
        )

    async def _control_button_visibility(self, request_number: str, user_role_id: int) -> bool:
        """
        Port of Mendix controlButtonVisibility.
        Determines if the current user (by role) can act on this request.
        """
        if not request_number:
            return False

        cr_row = await self._repo.get_request_by_number(request_number)
        if not cr_row:
            return False

        request_id = cr_row[0]
        format_id = cr_row[1]

        format_type = await self._repo.get_format_type(format_id) if format_id else ""

        stage_row = await self._repo.get_latest_active_stage(request_id)
        if not stage_row:
            return False

        stage_id = stage_row[0]
        stage_status = stage_row[1]
        stage_user_id = stage_row[2]

        mappings = await self._repo.get_stage_approval_label_mappings(stage_id)
        if not mappings:
            return False

        count = len(mappings)

        for current_count, mapping in enumerate(mappings, 1):
            mapping_id = mapping[0]
            approval_label_id = mapping[1]
            mapping_user_id = mapping[2]
            date_of_action = mapping[3]

            # Determine booltype
            if stage_status == "ReferBack":
                booltype = "REFER"
            elif current_count == count:
                booltype = "APPROVE"
            elif current_count == 1:
                booltype = "SUBMIT"
            else:
                booltype = "APPROVE"

            label_role_ids = await self._repo.get_approval_label_role_ids(approval_label_id)
            if not label_role_ids:
                continue

            same_role = user_role_id in label_role_ids
            if not same_role:
                continue

            sibling_acted = await self._repo.get_sibling_mapping_acted(stage_id, mapping_id)

            # ReconcilationSheet special logic
            if format_type == "ReconcilationSheet":
                if date_of_action is None and booltype != "APPROVE":
                    return True
                if date_of_action is None and sibling_acted:
                    return True
                continue

            # Standard logic
            same_user = mapping_user_id is not None and mapping_user_id == stage_user_id

            if (booltype == "REFER" and date_of_action is not None) or \
               (same_user and date_of_action is not None) or \
               (mapping_user_id is None and date_of_action is None):

                is_submit = False
                if booltype == "SUBMIT" and stage_status != "Pending":
                    is_submit = True
                elif booltype == "REFER" and stage_status != "Pending":
                    is_submit = True

                is_approve = False
                if booltype == "APPROVE" and stage_status == "Pending":
                    is_approve = True
                elif booltype == "APPROVE" and count == 1:
                    is_approve = True

                if is_submit or is_approve:
                    return True

        return False
