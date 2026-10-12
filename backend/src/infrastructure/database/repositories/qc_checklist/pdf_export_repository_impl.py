"""PDF Export Repository — reads everything needed to render a checklist
request and assembles the PdfDocument domain entity, for ANY format.

One public method (get_document) runs the queries — the request header, the
per-stage question rows, each question's sub-questions, the template-configured
columns, and the acted-on signatures — then groups them (by stage, then by
section) into the PdfDocument the renderer draws. Nothing here is
format-specific: stages, questions, columns and labels are whatever the
format's configuration produced, so the same code renders any format.
"""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.domain.entities.qc_checklist.checklist_pdf_document import (
    PdfColumn,
    PdfDocument,
    PdfRow,
    PdfRowGroup,
    PdfSection,
    PdfSignatureBlock,
    PdfSubAnswer,
)
from src.domain.repositories.qc_checklist.pdf_export_repository import IPdfExportRepository
from src.infrastructure.database.models.masters.approval_label_model import ApprovalLabelModel
from src.infrastructure.database.models.masters.format_model import FormatModel
from src.infrastructure.database.models.masters.format_stage_mapping_model import (
    FormatStageMappingModel,
)
from src.infrastructure.database.models.masters.question_model import QuestionModel
from src.infrastructure.database.models.masters.question_option_model import QuestionOptionModel
from src.infrastructure.database.models.masters.remark_model import RemarkModel
from src.infrastructure.database.models.masters.section_model import SectionModel
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.models.masters.stage_question_mapping_model import (
    StageQuestionMappingModel,
)
from src.infrastructure.database.models.masters.template_model import TemplateLayoutColumnModel
from src.infrastructure.database.models.qc_checklist.checklist_pdf_export_model import (
    ChecklistPdfExportModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_request_model import (
    ChecklistRequestModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import (
    ChecklistStageModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_helper_model import (
    QuestionAnswerHelperModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_model import (
    QuestionAnswerModel,
)
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import (  # noqa: E501
    QuestionAnswerSubQuestionAnswerModel,
)
from src.infrastructure.database.models.qc_checklist.stage_approval_label_mapping_model import (
    StageApprovalLabelMappingModel,
)
from src.infrastructure.database.models.user_details_model import UserDetailsModel
from src.infrastructure.database.models.user_model import UserModel

# Company identity shown in the page header. Static for now; promote to the
# unit / tenant record if multi-company branding is ever needed.
_COMPANY_NAME = "Emcure"
_COMPANY_LOCATION = "SANAND, AHEMDABAD"

# Fallback columns when a stage/section has no Template Studio layout saved —
# the generic Sr.No. / Question / Answer so the data is never lost.
_FALLBACK_COLUMNS: list[PdfColumn] = [
    PdfColumn(header="Sr.No.", column_type="SERIAL"),
    PdfColumn(header="Question", column_type="QUESTION"),
    PdfColumn(header="Answer", column_type="ANSWER"),
]


class PdfExportRepository(IPdfExportRepository):
    """Infrastructure layer — ORM queries + PdfDocument assembly for the PDF."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_document(self, request_number: str) -> PdfDocument | None:
        header = await self._fetch_header(request_number)
        if header is None:
            return None

        question_rows = await self._fetch_question_rows(request_number)
        columns = await self._fetch_columns(request_number)
        sub_answers = await self._fetch_sub_answers(request_number)
        signatures = await self._fetch_signatures(request_number)

        sections = self._build_sections(question_rows, columns, sub_answers, signatures)

        # Title: prefer the format's human title; fall back to its name. Shown
        # uppercased like the sample report.
        title = (header.format_title or header.format_name or "Checklist Report").upper()

        return PdfDocument(
            company_name=_COMPANY_NAME,
            company_location=_COMPANY_LOCATION,
            title=title,
            request_number=header.request_number,
            footer_code=header.format_no or "",
            sections=sections,
        )

    async def record_export(self, request_number: str, actor: str) -> None:
        """Insert an audit row — who (actor) exported which request, and when
        (created_date is set by the BaseModel default). get_db_session commits."""
        self._session.add(
            ChecklistPdfExportModel(
                request_number=request_number,
                created_by=actor,
                modified_by=actor,
            )
        )
        await self._session.flush()

    # ─── Queries ──────────────────────────────────────────────────────────
    async def _fetch_header(self, request_number: str) -> Row | None:
        """Request header: number, format name/title/no/type, created date, status."""
        stmt = (
            select(
                ChecklistRequestModel.request_number,
                FormatModel.format_name,
                FormatModel.format_title,
                FormatModel.format_no,
                FormatModel.format_type,
                ChecklistRequestModel.created_date,
                ChecklistRequestModel.status,
            )
            .outerjoin(FormatModel, FormatModel.id == ChecklistRequestModel.format_id)
            .where(
                ChecklistRequestModel.request_number == request_number,
                ChecklistRequestModel.is_removed.is_(False),
            )
            .limit(1)
        )
        return (await self._session.execute(stmt)).first()

    async def _fetch_question_rows(self, request_number: str) -> list[Row]:
        """Every stage's question rows, in display order, with each possible
        per-column-type value:
          * option   = the chosen option's title (question_option_id).
          * answer   = free text — textbox_value, else the helper text.
          * response = the response option's title, else response_answer.
          * aql_limit = the question's configured AQL limit.

        Stages order by format_stage_mapping id; questions by serial_number.
        Declaration questions are excluded (not shown on the form).
        """
        selected_opt = aliased(QuestionOptionModel)
        response_opt = aliased(QuestionOptionModel)

        option_value = func.coalesce(selected_opt.option_title, "")
        answer_value = func.coalesce(
            func.nullif(QuestionAnswerModel.textbox_value, ""),
            QuestionAnswerHelperModel.text_box_value,
            "",
        )
        response_value = func.coalesce(
            response_opt.option_title,
            func.nullif(QuestionAnswerModel.response_answer, ""),
            "",
        )

        stmt = (
            select(
                StageModel.stage_name.label("stage_name"),
                FormatStageMappingModel.id.label("stage_order"),
                StageQuestionMappingModel.section_id.label("section_id"),
                func.coalesce(SectionModel.section_name, "").label("section_name"),
                QuestionModel.id.label("question_id"),
                StageQuestionMappingModel.serial_number.label("serial_number"),
                QuestionModel.title.label("question"),
                option_value.label("option"),
                answer_value.label("answer"),
                response_value.label("response"),
                func.coalesce(StageQuestionMappingModel.aql_limit, "").label("aql_limit"),
            )
            .select_from(ChecklistRequestModel)
            .join(
                ChecklistStageModel,
                ChecklistStageModel.checklist_request_id == ChecklistRequestModel.id,
            )
            .join(
                FormatStageMappingModel,
                FormatStageMappingModel.id == ChecklistStageModel.format_stage_mapping_id,
            )
            .join(StageModel, StageModel.id == FormatStageMappingModel.stage_id)
            .join(
                StageQuestionMappingModel,
                (StageQuestionMappingModel.format_stage_mapping_id == FormatStageMappingModel.id)
                & (StageQuestionMappingModel.is_active.is_(True))
                & (StageQuestionMappingModel.is_declaration_question.is_(False)),
            )
            .join(QuestionModel, QuestionModel.id == StageQuestionMappingModel.question_id)
            .outerjoin(SectionModel, SectionModel.id == StageQuestionMappingModel.section_id)
            .outerjoin(
                QuestionAnswerModel,
                (QuestionAnswerModel.checklist_stage_id == ChecklistStageModel.id)
                & (QuestionAnswerModel.stage_question_mapping_id == StageQuestionMappingModel.id),
            )
            .outerjoin(
                QuestionAnswerHelperModel,
                QuestionAnswerHelperModel.question_answer_id == QuestionAnswerModel.id,
            )
            .outerjoin(selected_opt, selected_opt.id == QuestionAnswerModel.question_option_id)
            .outerjoin(
                response_opt,
                response_opt.id == QuestionAnswerModel.response_question_option_id,
            )
            .where(
                ChecklistRequestModel.request_number == request_number,
                ChecklistRequestModel.is_removed.is_(False),
            )
            .order_by(
                FormatStageMappingModel.id,
                StageQuestionMappingModel.section_id,
                StageQuestionMappingModel.serial_number,
                QuestionModel.id,
            )
        )
        return list((await self._session.execute(stmt)).all())

    async def _fetch_columns(self, request_number: str) -> list[Row]:
        """The template-configured columns for every stage, scoped by (stage,
        section): section_id NULL = flat-stage column, a value = per-section.
        Ordered by display_order so the PDF lays them out exactly as Template
        Studio configured them — this is what makes the export format-agnostic.
        """
        stmt = (
            select(
                FormatStageMappingModel.id.label("stage_order"),
                TemplateLayoutColumnModel.section_id.label("section_id"),
                TemplateLayoutColumnModel.header.label("header"),
                TemplateLayoutColumnModel.column_type.label("column_type"),
            )
            .select_from(ChecklistRequestModel)
            .join(
                ChecklistStageModel,
                ChecklistStageModel.checklist_request_id == ChecklistRequestModel.id,
            )
            .join(
                FormatStageMappingModel,
                FormatStageMappingModel.id == ChecklistStageModel.format_stage_mapping_id,
            )
            .join(
                TemplateLayoutColumnModel,
                TemplateLayoutColumnModel.format_stage_mapping_id == FormatStageMappingModel.id,
            )
            .where(
                ChecklistRequestModel.request_number == request_number,
                ChecklistRequestModel.is_removed.is_(False),
            )
            .order_by(
                FormatStageMappingModel.id,
                TemplateLayoutColumnModel.section_id,
                TemplateLayoutColumnModel.display_order,
            )
        )
        return list((await self._session.execute(stmt)).all())

    async def _fetch_sub_answers(self, request_number: str) -> dict[int, list[Row]]:
        """Map each parent question's id to its answered sub-questions.

        Sub-answers are child question_answers rows linked to the parent answer
        via the self-join. Each carries the sub-question title and its resolved
        value (chosen option title, else textbox / helper text, else response
        option title / response_answer), ordered by the join id. Keyed by the
        PARENT's question_id so the service can attach them to the parent row.
        """
        parent_qa = aliased(QuestionAnswerModel)
        child_qa = aliased(QuestionAnswerModel)
        sub_q = aliased(QuestionModel)
        selected_opt = aliased(QuestionOptionModel)
        response_opt = aliased(QuestionOptionModel)

        value = func.coalesce(
            selected_opt.option_title,
            func.nullif(child_qa.textbox_value, ""),
            QuestionAnswerHelperModel.text_box_value,
            response_opt.option_title,
            func.nullif(child_qa.response_answer, ""),
            "",
        )

        stmt = (
            select(
                parent_qa.question_id.label("parent_question_id"),
                sub_q.title.label("sub_title"),
                value.label("sub_value"),
            )
            .select_from(ChecklistRequestModel)
            .join(
                ChecklistStageModel,
                ChecklistStageModel.checklist_request_id == ChecklistRequestModel.id,
            )
            .join(parent_qa, parent_qa.checklist_stage_id == ChecklistStageModel.id)
            .join(
                QuestionAnswerSubQuestionAnswerModel,
                QuestionAnswerSubQuestionAnswerModel.question_answer_parent_id == parent_qa.id,
            )
            .join(child_qa, child_qa.id == QuestionAnswerSubQuestionAnswerModel.question_answer_id)
            .join(sub_q, sub_q.id == child_qa.question_id)
            .outerjoin(selected_opt, selected_opt.id == child_qa.question_option_id)
            .outerjoin(response_opt, response_opt.id == child_qa.response_question_option_id)
            .outerjoin(
                QuestionAnswerHelperModel,
                QuestionAnswerHelperModel.question_answer_id == child_qa.id,
            )
            .where(
                ChecklistRequestModel.request_number == request_number,
                ChecklistRequestModel.is_removed.is_(False),
            )
            .order_by(parent_qa.question_id, QuestionAnswerSubQuestionAnswerModel.id)
        )
        rows = (await self._session.execute(stmt)).all()
        result: dict[int, list[Row]] = {}
        for r in rows:
            result.setdefault(r.parent_question_id, []).append(r)
        return result

    async def _fetch_signatures(self, request_number: str) -> list[Row]:
        """Every acted-on approval label across the request's stages (label,
        acting employee name, date, remark). Only labels with a date_of_action.
        """
        user_name = func.coalesce(UserDetailsModel.employee_name, UserModel.username, "")

        stmt = (
            select(
                FormatStageMappingModel.id.label("stage_order"),
                ApprovalLabelModel.label.label("label"),
                user_name.label("user_name"),
                StageApprovalLabelMappingModel.date_of_action.label("date_of_action"),
                func.coalesce(StageApprovalLabelMappingModel.remark, "").label("remark_text"),
                func.coalesce(RemarkModel.remark, "").label("remark_master"),
            )
            .select_from(ChecklistRequestModel)
            .join(
                ChecklistStageModel,
                ChecklistStageModel.checklist_request_id == ChecklistRequestModel.id,
            )
            .join(
                FormatStageMappingModel,
                FormatStageMappingModel.id == ChecklistStageModel.format_stage_mapping_id,
            )
            .join(
                StageApprovalLabelMappingModel,
                (StageApprovalLabelMappingModel.checklist_stage_id == ChecklistStageModel.id)
                & (StageApprovalLabelMappingModel.date_of_action.is_not(None)),
            )
            .join(
                ApprovalLabelModel,
                ApprovalLabelModel.id == StageApprovalLabelMappingModel.approval_label_id,
            )
            .outerjoin(UserModel, UserModel.id == StageApprovalLabelMappingModel.user_id)
            .outerjoin(
                UserDetailsModel,
                UserDetailsModel.user_id == StageApprovalLabelMappingModel.user_id,
            )
            .outerjoin(RemarkModel, RemarkModel.id == StageApprovalLabelMappingModel.remark_id)
            .where(
                ChecklistRequestModel.request_number == request_number,
                ChecklistRequestModel.is_removed.is_(False),
            )
            .order_by(FormatStageMappingModel.id, StageApprovalLabelMappingModel.id)
        )
        return list((await self._session.execute(stmt)).all())

    # ─── Assembly ─────────────────────────────────────────────────────────
    def _build_sections(
        self,
        question_rows: list[Row],
        columns: list[Row],
        sub_answers: dict[int, list[Row]],
        signatures: list[Row],
    ) -> list[PdfSection]:
        """Group rows + signatures by stage, then by section within a stage,
        attaching each group's template-configured columns.

        Within a stage, rows are grouped by their section (first-seen order);
        rows without a section fall into one unheaded group.
        """
        columns_by_scope = self._index_columns(columns)

        stage_order: list[int] = []
        stage_titles: dict[int, str] = {}
        group_order: dict[int, list[int | None]] = {}
        group_name: dict[int, dict[int | None, str]] = {}
        group_rows: dict[int, dict[int | None, list[PdfRow]]] = {}

        for r in question_rows:
            stage = r.stage_order
            if stage not in stage_titles:
                stage_order.append(stage)
                stage_titles[stage] = r.stage_name or ""
                group_order[stage] = []
                group_name[stage] = {}
                group_rows[stage] = {}

            sec_key = r.section_id
            if sec_key not in group_name[stage]:
                group_order[stage].append(sec_key)
                group_name[stage][sec_key] = r.section_name or ""
                group_rows[stage][sec_key] = []

            group_rows[stage][sec_key].append(
                PdfRow(
                    values={
                        "SERIAL": str(r.serial_number or 0),
                        "QUESTION": r.question or "",
                        "OPTION": r.option or "",
                        "ANSWER": r.answer or "",
                        "RESPONSE": r.response or "",
                        "AQL_LIMIT": self._format_number(r.aql_limit or ""),
                    },
                    sub_answers=[
                        PdfSubAnswer(question=sa.sub_title or "", answer=sa.sub_value or "")
                        for sa in sub_answers.get(r.question_id or 0, [])
                    ],
                )
            )

        sigs_by_stage: dict[int, list[PdfSignatureBlock]] = {}
        for s in signatures:
            sigs_by_stage.setdefault(s.stage_order, []).append(
                PdfSignatureBlock(
                    label=s.label or "",
                    user_name=s.user_name or "",
                    time_stamp=self._format_timestamp(s.date_of_action),
                    remark=self._resolve_remark(s.remark_master or "", s.remark_text or ""),
                )
            )

        sections: list[PdfSection] = []
        for stage in stage_order:
            groups = [
                PdfRowGroup(
                    section_name=group_name[stage][sec_key],
                    columns=self._columns_for(columns_by_scope, stage, sec_key),
                    rows=group_rows[stage][sec_key],
                )
                for sec_key in group_order.get(stage, [])
            ]
            sections.append(
                PdfSection(
                    title=stage_titles.get(stage, ""),
                    groups=groups,
                    signatures=sigs_by_stage.get(stage, []),
                )
            )
        return sections

    @staticmethod
    def _index_columns(columns: list[Row]) -> dict[tuple[int, int | None], list[PdfColumn]]:
        """Group the flat column rows by (stage_order, section_id), preserving
        the query's display_order."""
        by_scope: dict[tuple[int, int | None], list[PdfColumn]] = {}
        for c in columns:
            by_scope.setdefault((c.stage_order, c.section_id), []).append(
                PdfColumn(header=c.header or "", column_type=(c.column_type or "ANSWER").upper())
            )
        return by_scope

    @staticmethod
    def _columns_for(
        by_scope: dict[tuple[int, int | None], list[PdfColumn]],
        stage_order: int,
        section_id: int | None,
    ) -> list[PdfColumn]:
        """Columns for a (stage, section) scope: a section's own columns, else
        the stage-level columns, else a generic layout so answers always show."""
        cols = by_scope.get((stage_order, section_id))
        if not cols and section_id is not None:
            cols = by_scope.get((stage_order, None))
        return cols or list(_FALLBACK_COLUMNS)

    @staticmethod
    def _format_timestamp(value: datetime | None) -> str:
        """Format the signature timestamp in IST, 12-hour with AM/PM
        (e.g. '08-May-2026 03:24 PM'). Stored timestamps are UTC-aware; a naive
        value is assumed UTC before converting."""
        if value is None:
            return ""
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        ist = value.astimezone(timezone(timedelta(hours=5, minutes=30)))
        # %I is zero-padded 12-hour; strip the leading zero for a cleaner look.
        return ist.strftime("%d-%b-%Y %I:%M %p").replace(" 0", " ", 1)

    @staticmethod
    def _format_number(value: str) -> str:
        """Normalise a stored numeric string for display, mirroring the fill
        UI's parseFloat(...).toString(): drop trailing zeros and scientific
        notation ('1.00000000' → '1', '0.40000000' → '0.4', '0E-8' → '0'),
        keeping meaningful decimals ('0.25'). Non-numeric/blank left as-is.
        """
        text = (value or "").strip()
        if not text:
            return ""
        try:
            number = Decimal(text)
        except (InvalidOperation, ValueError):
            return text
        formatted = format(number.normalize(), "f")
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted or "0"

    @staticmethod
    def _resolve_remark(remark_master: str, remark_text: str) -> str:
        """What to show for a signature's remark — mirrors the UI rule.

        A standard remark stores only the master label (remark_text blank); the
        'Others' remark stores master label 'Others' plus free text. So:
          * 'Others'  → the free text (fall back to 'Others').
          * a master  → the master label.
          * nothing   → whatever free text exists.
        """
        if remark_master.strip().lower() == "others":
            return remark_text.strip() or remark_master
        if remark_master.strip():
            return remark_master
        return remark_text
