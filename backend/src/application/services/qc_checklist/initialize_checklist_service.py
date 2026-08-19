"""Initialize Checklist — application service for previewing checklist structure from a format."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.masters.format_model import FormatModel
from src.infrastructure.database.models.masters.format_stage_mapping_model import FormatStageMappingModel
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.models.masters.stage_question_mapping_model import StageQuestionMappingModel
from src.infrastructure.database.models.masters.question_model import QuestionModel, QuestionSubQuestionModel
from src.infrastructure.database.models.masters.question_option_model import QuestionOptionModel
from src.infrastructure.database.models.masters.approval_label_model import ApprovalLabelModel
from src.infrastructure.database.models.masters.section_model import SectionModel
from src.infrastructure.database.models.masters.unit_model import UnitModel
from src.domain.exceptions.domain_exceptions import EntityNotFoundError


@dataclass
class QuestionOptionPreviewDTO:
    id: int
    label: str


@dataclass
class QuestionAnswerPreviewDTO:
    stage_question_mapping_id: int
    question_id: int
    question_title: str
    serial_number: int
    section_id: int | None
    section_name: str | None
    show_on_grid: bool
    answer_type: str
    has_text_box: bool
    has_multiple_text_box: bool
    has_sub_question: bool
    is_declaration_question: bool
    aql_limit: str
    sub_questions: list['QuestionAnswerPreviewDTO']
    options: list[QuestionOptionPreviewDTO]
    response_options: list[QuestionOptionPreviewDTO]


@dataclass
class ApprovalLabelPreviewDTO:
    approval_label_id: int
    label: str


@dataclass
class SectionPreviewDTO:
    section_id: int
    section_name: str
    questions: list[QuestionAnswerPreviewDTO]


@dataclass
class ChecklistStagePreviewDTO:
    format_stage_mapping_id: int
    stage_id: int
    stage_name: str
    is_approvable: bool
    has_section: bool
    status: str
    questions: list[QuestionAnswerPreviewDTO]
    sections: list[SectionPreviewDTO]
    approval_labels: list[ApprovalLabelPreviewDTO]


@dataclass
class ChecklistPreviewDTO:
    format_id: int
    format_name: str
    format_no: str
    format_type: str
    has_declaration_question: bool
    unit_name: str
    stages: list[ChecklistStagePreviewDTO]


def build_question_answer_preview(
    sqm: StageQuestionMappingModel,
    question_map: dict[int, str],
    question_answer_type_map: dict[int, str],
    question_has_text_box_map: dict[int, bool],
    question_has_multiple_text_box_map: dict[int, bool],
    question_has_sub_question_map: dict[int, bool],
    question_options_map: dict[int, list[QuestionOptionPreviewDTO]],
    response_options_map: dict[int, list[QuestionOptionPreviewDTO]] | None = None,
    sub_questions_map: dict[int, list['QuestionAnswerPreviewDTO']] | None = None,
    section_name: str | None = None,
) -> QuestionAnswerPreviewDTO:
    """
    Reusable factory: builds a QuestionAnswerPreviewDTO from a StageQuestionMapping
    and pre-fetched question metadata. Can be used anywhere question answers need to be created.
    """
    qid = sqm.question_id
    return QuestionAnswerPreviewDTO(
        stage_question_mapping_id=sqm.id,
        question_id=qid,
        question_title=question_map.get(qid, ""),
        serial_number=sqm.serial_number,
        section_id=sqm.section_id,
        section_name=section_name,
        show_on_grid=sqm.show_on_grid,
        answer_type=question_answer_type_map.get(qid, ""),
        has_text_box=question_has_text_box_map.get(qid, False),
        has_multiple_text_box=question_has_multiple_text_box_map.get(qid, False),
        has_sub_question=question_has_sub_question_map.get(qid, False),
        is_declaration_question=sqm.is_declaration_question if hasattr(sqm, 'is_declaration_question') else False,
        aql_limit=sqm.aql_limit if hasattr(sqm, 'aql_limit') else "",
        sub_questions=(sub_questions_map or {}).get(qid, []),
        options=question_options_map.get(qid, []),
        response_options=(response_options_map or {}).get(qid, []),
    )


class InitializeChecklistService:
    """Builds a full checklist preview from master data without persisting anything."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fetch_question_metadata(self, question_ids: list[int]) -> tuple[
        dict[int, str], dict[int, str], dict[int, bool], dict[int, bool], dict[int, bool],
        dict[int, list[QuestionOptionPreviewDTO]], dict[int, list[QuestionOptionPreviewDTO]]
    ]:
        """
        Reusable: fetches question title, answer_type, has_text_box, has_multiple_text_box, has_sub_question, options, and response_options.
        Returns: (question_map, answer_type_map, has_text_box_map, has_multiple_text_box_map, has_sub_question_map, options_map, response_options_map)
        """
        question_map: dict[int, str] = {}
        answer_type_map: dict[int, str] = {}
        has_text_box_map: dict[int, bool] = {}
        has_multiple_text_box_map: dict[int, bool] = {}
        has_sub_question_map: dict[int, bool] = {}
        options_map: dict[int, list[QuestionOptionPreviewDTO]] = {}
        response_options_map: dict[int, list[QuestionOptionPreviewDTO]] = {}

        if not question_ids:
            return question_map, answer_type_map, has_text_box_map, has_multiple_text_box_map, has_sub_question_map, options_map, response_options_map

        # Fetch question details
        q_result = await self._session.execute(
            select(QuestionModel).where(QuestionModel.id.in_(question_ids))
        )
        for q in q_result.scalars().all():
            question_map[q.id] = q.title
            answer_type_map[q.id] = q.answer_type
            has_text_box_map[q.id] = q.has_text_box
            has_multiple_text_box_map[q.id] = q.has_multiple_text_box
            has_sub_question_map[q.id] = q.has_sub_question

        # Fetch all options (active) — split into regular and response
        opts_result = await self._session.execute(
            select(QuestionOptionModel).where(
                QuestionOptionModel.question_id.in_(question_ids),
                QuestionOptionModel.is_active.is_(True),
            ).order_by(QuestionOptionModel.id)
        )
        for opt in opts_result.scalars().all():
            if opt.is_response_option:
                if opt.question_id not in response_options_map:
                    response_options_map[opt.question_id] = []
                response_options_map[opt.question_id].append(
                    QuestionOptionPreviewDTO(id=opt.id, label=opt.option_title)
                )
            else:
                if opt.question_id not in options_map:
                    options_map[opt.question_id] = []
                options_map[opt.question_id].append(
                    QuestionOptionPreviewDTO(id=opt.id, label=opt.option_title)
                )

        return question_map, answer_type_map, has_text_box_map, has_multiple_text_box_map, has_sub_question_map, options_map, response_options_map

    async def build_questions_for_stage(
        self, fsm_id: int, has_section: bool
    ) -> tuple[list[QuestionAnswerPreviewDTO], list[SectionPreviewDTO]]:
        """
        Reusable: given a format_stage_mapping_id, builds:
        - questions list (non-sectioned questions)
        - sections list (each section with its questions)
        """
        # Fetch StageQuestionMappings
        sqm_result = await self._session.execute(
            select(StageQuestionMappingModel).where(
                StageQuestionMappingModel.format_stage_mapping_id == fsm_id
            ).order_by(StageQuestionMappingModel.serial_number)
        )
        sqm_list = sqm_result.scalars().all()

        # Fetch question metadata
        q_ids = [sqm.question_id for sqm in sqm_list if sqm.question_id]
        question_map, answer_type_map, has_text_box_map, has_multiple_text_box_map, has_sub_question_map, options_map, response_options_map = await self.fetch_question_metadata(q_ids)

        # Fetch sub-questions for questions that have them
        sub_questions_map: dict[int, list[QuestionAnswerPreviewDTO]] = {}
        parent_ids_with_subs = [qid for qid in q_ids if has_sub_question_map.get(qid, False)]
        if parent_ids_with_subs:
            sub_junc_result = await self._session.execute(
                select(QuestionSubQuestionModel).where(
                    QuestionSubQuestionModel.question_id.in_(parent_ids_with_subs)
                ).order_by(QuestionSubQuestionModel.id)
            )
            sub_junctions = sub_junc_result.scalars().all()
            sub_q_ids = list({j.sub_question_id for j in sub_junctions})
            if sub_q_ids:
                sub_q_map, sub_at_map, sub_htb_map, sub_hmtb_map, sub_hsq_map, sub_opts_map, sub_resp_map = await self.fetch_question_metadata(sub_q_ids)
                for j in sub_junctions:
                    if j.question_id not in sub_questions_map:
                        sub_questions_map[j.question_id] = []
                    sub_questions_map[j.question_id].append(QuestionAnswerPreviewDTO(
                        stage_question_mapping_id=0,
                        question_id=j.sub_question_id,
                        question_title=sub_q_map.get(j.sub_question_id, ""),
                        serial_number=0,
                        section_id=None,
                        section_name=None,
                        show_on_grid=False,
                        answer_type=sub_at_map.get(j.sub_question_id, ""),
                        has_text_box=sub_htb_map.get(j.sub_question_id, False),
                        has_multiple_text_box=sub_hmtb_map.get(j.sub_question_id, False),
                        has_sub_question=False,
                        is_declaration_question=False,
                        aql_limit="",
                        sub_questions=[],
                        options=sub_opts_map.get(j.sub_question_id, []),
                        response_options=sub_resp_map.get(j.sub_question_id, []),
                    ))

        # Sections
        section_map: dict[int, str] = {}
        sections_preview: list[SectionPreviewDTO] = []

        if has_section:
            sec_result = await self._session.execute(
                select(SectionModel).where(
                    SectionModel.format_stage_mapping_id == fsm_id
                ).order_by(SectionModel.id)
            )
            all_sections = sec_result.scalars().all()
            for sec in all_sections:
                section_map[sec.id] = sec.section_name

            # Build questions per section
            for sec in all_sections:
                sec_questions = [
                    build_question_answer_preview(
                        sqm, question_map, answer_type_map, has_text_box_map, has_multiple_text_box_map, has_sub_question_map, options_map,
                        response_options_map=response_options_map,
                        sub_questions_map=sub_questions_map,
                        section_name=sec.section_name,
                    )
                    for sqm in sqm_list if sqm.section_id == sec.id
                ]
                sections_preview.append(SectionPreviewDTO(
                    section_id=sec.id,
                    section_name=sec.section_name,
                    questions=sec_questions,
                ))

        # Build non-sectioned questions
        questions: list[QuestionAnswerPreviewDTO] = []
        for sqm in sqm_list:
            if has_section and sqm.section_id:
                continue
            questions.append(build_question_answer_preview(
                sqm, question_map, answer_type_map, has_text_box_map, has_multiple_text_box_map, has_sub_question_map, options_map,
                response_options_map=response_options_map,
                sub_questions_map=sub_questions_map,
                section_name=section_map.get(sqm.section_id, None) if sqm.section_id else None,
            ))

        return questions, sections_preview

    async def get_preview(self, format_id: int) -> ChecklistPreviewDTO:
        """
        Returns the complete checklist structure for a given format.
        Nothing is persisted.
        """
        # Fetch format
        fmt_result = await self._session.execute(
            select(FormatModel).where(FormatModel.id == format_id)
        )
        fmt = fmt_result.scalar_one_or_none()
        if not fmt:
            raise EntityNotFoundError("Format", format_id)

        # Fetch unit name from format's unit_id
        unit_name = ""
        if fmt.unit_id:
            unit_result = await self._session.execute(
                select(UnitModel).where(UnitModel.id == fmt.unit_id)
            )
            unit = unit_result.scalar_one_or_none()
            if unit:
                unit_name = unit.name

        # Fetch FormatStageMappings
        fsm_result = await self._session.execute(
            select(FormatStageMappingModel).where(
                FormatStageMappingModel.format_id == format_id
            ).order_by(FormatStageMappingModel.id)
        )
        format_stage_mappings = fsm_result.scalars().all()

        # Fetch all stages for name lookup
        stage_ids = [fsm.stage_id for fsm in format_stage_mappings]
        stage_map: dict[int, str] = {}
        if stage_ids:
            stages_result = await self._session.execute(
                select(StageModel).where(StageModel.id.in_(stage_ids))
            )
            for s in stages_result.scalars().all():
                stage_map[s.id] = s.stage_name

        checklist_stages: list[ChecklistStagePreviewDTO] = []

        for idx, fsm in enumerate(format_stage_mappings):
            # Build questions and sections using reusable method
            questions, sections_preview = await self.build_questions_for_stage(fsm.id, fsm.has_section)

            # Fetch ApprovalLabels for this stage
            al_result = await self._session.execute(
                select(ApprovalLabelModel).where(
                    ApprovalLabelModel.stage_id == fsm.stage_id,
                    ApprovalLabelModel.is_active.is_(True),
                ).order_by(ApprovalLabelModel.id)
            )
            approval_labels = [
                ApprovalLabelPreviewDTO(approval_label_id=al.id, label=al.label)
                for al in al_result.scalars().all()
            ]

            checklist_stages.append(ChecklistStagePreviewDTO(
                format_stage_mapping_id=fsm.id,
                stage_id=fsm.stage_id,
                stage_name=stage_map.get(fsm.stage_id, f"Stage {fsm.stage_id}"),
                is_approvable=fsm.is_approvable,
                has_section=fsm.has_section,
                status="Initial" if idx < 2 else "",
                questions=questions,
                sections=sections_preview,
                approval_labels=approval_labels,
            ))

        return ChecklistPreviewDTO(
            format_id=fmt.id,
            format_name=fmt.format_name,
            format_no=fmt.format_no,
            format_type=fmt.format_type,
            has_declaration_question=fmt.has_declaration_question,
            unit_name=unit_name,
            stages=checklist_stages,
        )
