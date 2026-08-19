"""Dashboard Repository — holds all raw SQL queries for the dashboard feature."""

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class DashboardQueryRow:
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


class DashboardRepository:
    """Infrastructure layer — raw SQL queries for dashboard data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fetch_dashboard_rows(
        self,
        is_last_stage: bool,
        pending_statuses: bool,
        from_date: date | None,
        to_date: date | None,
        role_id: int | None,
        is_admin: bool,
    ) -> list[DashboardQueryRow]:
        """Execute the main dashboard query (port of Mendix JA_Dashboard SQL).
        
        Key difference from old version: uses LEFT JOIN on validation_types so ALL
        requests appear. The validation_type is only used to extract grid column values,
        not to filter rows.
        """

        sql = """
SELECT
    x.request_number, x.format_name, x.format_type, x.status_format, x.created_date, x.stage_status,
    x.requested_by, x.request_status, x.is_last_stage,
    COALESCE(MAX(CASE WHEN x.validation_type = 'Batch No' THEN x.qa_pair END), 'NA') AS batch_no,
    COALESCE(
        MAX(CASE
            WHEN x.format_type = 'ReconcilationSheet' THEN x.recon_product_name
            ELSE CASE WHEN x.validation_type = 'Product Name' THEN x.qa_pair END
        END),
        'NA'
    ) AS product_name,
    COALESCE(MAX(CASE WHEN x.validation_type = 'Test Name' THEN x.qa_pair END), 'NA') AS test_name
FROM (
    SELECT
        cr.request_number,
        f.format_name,
        f.format_type,
        cr.status_format,
        cr.created_date,
        u.username              AS requested_by,
        cr.status               AS request_status,
        cs.status               AS stage_status,
        cr.is_last_stage,
        vt.name                 AS validation_type,
        COALESCE(qa.textbox_value, qah.text_box_value, qo.option_title) AS qa_pair,
        p.product_name          AS recon_product_name,
        ROW_NUMBER() OVER (PARTITION BY cr.request_number ORDER BY q.id) AS rn
    FROM checklist_requests cr
    JOIN checklist_stages cs
        ON cs.checklist_request_id = cr.id
    JOIN format_stage_mappings fsm
        ON fsm.id = cs.format_stage_mapping_id
    JOIN formats f
        ON f.id = cr.format_id
    JOIN stages s
        ON s.id = fsm.stage_id
        AND s.stage_name = 'Basic Details'
    LEFT JOIN users u
        ON u.username = cr.created_by OR CAST(u.id AS TEXT) = cr.created_by
    JOIN stage_question_mappings sqm
        ON sqm.format_stage_mapping_id = fsm.id
        AND sqm.show_on_grid = true
    JOIN questions q
        ON q.id = sqm.question_id
    JOIN validation_types vt
        ON vt.id = q.validation_type_id
    JOIN question_answers qa
        ON qa.checklist_stage_id = cs.id
        AND qa.question_id = q.id
    LEFT JOIN question_answer_sub_question_answers qasqa
        ON qasqa.question_answer_id = qa.id
    LEFT JOIN question_answer_helpers qah
        ON qah.id = qasqa.question_answer_helper_id
    LEFT JOIN question_options qo
        ON qo.id = qa.question_option_id
    LEFT JOIN products p
        ON p.id = qa.product_id
        AND q.answer_type = 'Masters'
        AND q.master_type = 'ProductMaster'
    WHERE cr.is_removed = false
        AND cr.is_last_stage = :is_last_stage
"""
        params: dict = {"is_last_stage": is_last_stage}

        if pending_statuses:
            sql += "        AND cs.status IN ('Pending', 'ReferBack', 'Draft', 'SaveAsDraft', 'Saved')\n"

        if from_date:
            sql += "        AND cr.created_date >= :from_date\n"
            params["from_date"] = from_date

        if to_date:
            sql += "        AND cr.created_date < :to_date\n"
            params["to_date"] = to_date

        if not is_admin and role_id:
            sql += """        AND EXISTS (
            SELECT 1
            FROM checklist_stages cs2
            JOIN format_stage_mappings fsm2 ON fsm2.id = cs2.format_stage_mapping_id
            JOIN stages s2 ON s2.id = fsm2.stage_id
            JOIN approval_labels al ON al.stage_id = s2.id AND al.is_active = true
            JOIN approval_label_user_roles alur ON alur.approval_label_id = al.id
            WHERE cs2.checklist_request_id = cr.id
                AND alur.role_id = :role_id
        )
"""
            params["role_id"] = role_id

        sql += """) x
GROUP BY x.request_number, x.format_name, x.format_type, x.status_format, x.created_date,
         x.requested_by, x.request_status, x.stage_status, x.is_last_stage
ORDER BY x.created_date DESC
"""

        result = await self._session.execute(text(sql), params)
        rows = result.fetchall()

        return [
            DashboardQueryRow(
                request_number=row.request_number or "",
                format_name=row.format_name or "",
                status_format=row.status_format or "",
                created_date=row.created_date,
                stage_status=row.stage_status or "",
                requested_by=row.requested_by or "",
                request_status=row.request_status or "",
                is_last_stage=row.is_last_stage or False,
                batch_no=row.batch_no or "NA",
                product_name=row.product_name or "NA",
                test_name=row.test_name or "NA",
            )
            for row in rows
        ]

    async def get_request_by_number(self, request_number: str) -> tuple | None:
        """Get checklist request id and format_id by request_number."""
        result = await self._session.execute(text(
            "SELECT id, format_id FROM checklist_requests WHERE request_number = :rn"
        ), {"rn": request_number})
        return result.fetchone()

    async def get_format_type(self, format_id: int) -> str:
        """Get format_type by format id."""
        result = await self._session.execute(text(
            "SELECT format_type FROM formats WHERE id = :fid"
        ), {"fid": format_id})
        row = result.fetchone()
        return row[0] if row else ""

    async def get_latest_active_stage(self, request_id: int) -> tuple | None:
        """Get latest active stage (id, status, user_id) for a request."""
        result = await self._session.execute(text("""
            SELECT cs.id, cs.status, cs.user_id
            FROM checklist_stages cs
            WHERE cs.checklist_request_id = :rid
                AND cs.status IN ('Pending', 'Draft', 'SaveAsDraft', 'ReferBack', 'Initial', 'Saved')
            ORDER BY cs.id DESC
            LIMIT 1
        """), {"rid": request_id})
        return result.fetchone()

    async def get_stage_approval_label_mappings(self, stage_id: int) -> list[tuple]:
        """Get all StageApprovalLabelMappings for a stage, ordered by id."""
        result = await self._session.execute(text("""
            SELECT salm.id, salm.approval_label_id, salm.user_id, salm.date_of_action
            FROM stage_approval_label_mappings salm
            WHERE salm.checklist_stage_id = :sid
            ORDER BY salm.id
        """), {"sid": stage_id})
        return result.fetchall()

    async def get_approval_label_role_ids(self, approval_label_id: int) -> list[int]:
        """Get role ids linked to an approval label."""
        result = await self._session.execute(text("""
            SELECT alur.role_id
            FROM approval_label_user_roles alur
            WHERE alur.approval_label_id = :alid
        """), {"alid": approval_label_id})
        return [r[0] for r in result.fetchall()]

    async def get_sibling_mapping_acted(self, stage_id: int, mapping_id: int) -> bool:
        """Check if a sibling mapping has a date_of_action set."""
        result = await self._session.execute(text("""
            SELECT date_of_action FROM stage_approval_label_mappings
            WHERE checklist_stage_id = :sid AND id != :mid
            LIMIT 1
        """), {"sid": stage_id, "mid": mapping_id})
        row = result.fetchone()
        return row is not None and row[0] is not None

    async def get_stage_user_id(self, stage_id: int) -> int | None:
        """Get the user_id assigned to a checklist stage."""
        result = await self._session.execute(text(
            "SELECT user_id FROM checklist_stages WHERE id = :sid"
        ), {"sid": stage_id})
        row = result.fetchone()
        return row[0] if row else None

    async def has_not_issued_vails(self, stage_id: int) -> bool:
        """Check if stage has question answers with hasVails=true but no receivedByDate (not issued)."""
        result = await self._session.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM question_answers qa
                JOIN stage_question_mappings sqm ON sqm.id = qa.stage_question_mapping_id
                WHERE qa.checklist_stage_id = :sid
                    AND sqm.is_declaration_question = false
                    AND qa.received_by_date IS NULL
                    AND qa.has_vails = true
            )
        """), {"sid": stage_id})
        return result.scalar() or False
