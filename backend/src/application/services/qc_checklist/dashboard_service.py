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

    async def get_dashboard_for_user(
        self,
        user_id: int,
        from_date: date | None,
        to_date: date | None,
    ) -> dict:
        """Resolve the acting user's role context (role_id + admin flag) and
        build the dashboard data for them. The controller passes only the
        authenticated user; all role lookups happen in the repository."""
        role_id, is_admin = await self._repo.get_user_role_context(user_id)
        return await self.get_dashboard(
            from_date=from_date,
            to_date=to_date,
            role_id=role_id,
            is_admin=is_admin,
            user_id=user_id,
        )

    async def get_dashboard(
        self,
        from_date: date | None,
        to_date: date | None,
        role_id: int | None,
        is_admin: bool,
        user_id: int | None = None,
    ) -> dict:
        """Returns { pending: [...], approved: [...], total: int }."""
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

        # Compute action_flag for pending requests. Prime the repo's batch cache
        # once (a few queries for ALL pending requests) so the per-request
        # visibility logic reads from memory instead of issuing N+1 queries.
        if role_id:
            await self._repo.prime_button_visibility([dr.request_number for dr in pending])
            for dr in pending:
                dr.action_flag = await self._control_button_visibility(
                    dr.request_number, role_id, user_id
                )

        total = await self._repo.count_requests_in_range(
            from_date=from_date, to_date=to_date,
            role_id=role_id, is_admin=is_admin,
        )

        return {"pending": pending, "approved": approved, "total": total}

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

    async def _control_button_visibility(
        self, request_number: str, user_role_id: int, user_id: int | None = None
    ) -> bool:
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
            approval_label_id = mapping[1]
            mapping_user_id = mapping[2]
            date_of_action = mapping[3]
            mapping_is_refer_back = mapping[4] if len(mapping) > 4 else False

            # A referred-back stage goes back to the FILLER, not the approver who
            # referred it. The approver's own refer-back mapping must not grant
            # them the button — skip it so only the filling label's role matches.
            if stage_status == "ReferBack" and mapping_is_refer_back:
                continue

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

            # ReconcilationSheet special logic — driven by whether all vials are
            # issued, NOT by the analyst mapping being acted (the analyst's first
            # submit no longer records an approval action).
            #
            #   - Vials still unissued  → the SUPERVISOR (the last/APPROVE label's
            #     role) gets the "Fill Next Stage" button so they can issue vials.
            #     The analyst must NOT see it during this phase.
            #   - All vials issued      → the ANALYST (the first/SUBMIT label's
            #     role) gets the button to calculate destroyed samples + submit.
            if format_type == "ReconcilationSheet":
                has_unissued = await self._repo.has_not_issued_vails(stage_id)
                if has_unissued:
                    # Supervisor phase: only the APPROVE-label role (supervisor),
                    # and only while the stage is still open (not yet Pending).
                    if booltype == "APPROVE" and stage_status != "Pending":
                        return True
                    continue
                # Analyst phase (all vials issued): the SUBMIT-label role acts
                # until it's submitted for approval; the APPROVE-label role acts
                # once it's Pending.
                if booltype != "APPROVE" and date_of_action is None and stage_status != "Pending":
                    return True
                if booltype == "APPROVE" and stage_status == "Pending":
                    return True
                continue

            # A referred-back stage goes back ONLY to the analyst who originally
            # filled it (the stage's user_id) — not every analyst sharing that
            # role. Skip the button for anyone else. (When user_id is unknown,
            # fall back to role-only, preserving prior behavior.)
            if (
                stage_status == "ReferBack"
                and user_id is not None
                and stage_user_id is not None
                and stage_user_id != user_id
            ):
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
