"""Template Stage Save — Pydantic request/response schemas.

Each schema owns its own translation to/from the application layer's DTOs
(to_dto / from_dto) so the controller stays a pure HTTP layer: parse
request, call the service, translate the result, map domain errors to HTTP
status codes — no DTO field-by-field mapping there.
"""

from pydantic import BaseModel, Field

from src.application.dtos.masters.template_stage_save_dtos import (
    StageSaveColumnDTO,
    StageSaveRowDTO,
    StageSaveRowResultDTO,
    StageSaveSectionDTO,
    StageSaveSectionResultDTO,
    TemplateStageSaveDTO,
    TemplateStageSaveResultDTO,
)
from src.domain.enums.custom_answer_enum import CustomAnswer
from src.domain.enums.template_enums import ColumnType


class StageSaveColumnInput(BaseModel):
    header: str = Field(default="", max_length=255)
    column_type: ColumnType
    width: str | None = Field(default=None, max_length=30)
    is_required: bool = Field(default=False)

    def to_dto(self) -> StageSaveColumnDTO:
        return StageSaveColumnDTO(
            header=self.header,
            column_type=self.column_type,
            width=self.width,
            is_required=self.is_required,
        )


class StageSaveRowInput(BaseModel):
    question_id: int = Field(..., gt=0)
    mapping_id: int | None = Field(default=None)
    show_on_grid: bool = Field(default=False)
    sap_field_id: int | None = Field(default=None)
    is_editable: bool = Field(default=True)
    is_declaration_question: bool = Field(default=False)
    custom_answers: CustomAnswer | None = Field(default=None)
    aql_limit: str = Field(default="", max_length=100)
    is_active: bool = Field(default=True)

    def to_dto(self) -> StageSaveRowDTO:
        return StageSaveRowDTO(
            question_id=self.question_id,
            mapping_id=self.mapping_id,
            show_on_grid=self.show_on_grid,
            sap_field_id=self.sap_field_id,
            is_editable=self.is_editable,
            is_declaration_question=self.is_declaration_question,
            custom_answers=self.custom_answers,
            aql_limit=self.aql_limit,
            is_active=self.is_active,
        )


class StageSaveSectionInput(BaseModel):
    section_name: str = Field(default="", max_length=255)
    section_id: int | None = Field(default=None)
    rows: list[StageSaveRowInput] = Field(default_factory=list)
    columns: list[StageSaveColumnInput] = Field(default_factory=list)

    def to_dto(self) -> StageSaveSectionDTO:
        return StageSaveSectionDTO(
            section_name=self.section_name,
            section_id=self.section_id,
            rows=[r.to_dto() for r in self.rows],
            columns=[c.to_dto() for c in self.columns],
        )


class TemplateStageSaveRequest(BaseModel):
    format_id: int = Field(..., gt=0)
    stage_id: int = Field(..., gt=0)
    rows: list[StageSaveRowInput] = Field(default_factory=list)
    columns: list[StageSaveColumnInput] = Field(default_factory=list)
    sections: list[StageSaveSectionInput] = Field(default_factory=list)
    deleted_mapping_ids: list[int] = Field(default_factory=list)
    deleted_section_ids: list[int] = Field(default_factory=list)

    def to_dto(self) -> TemplateStageSaveDTO:
        return TemplateStageSaveDTO(
            format_id=self.format_id,
            stage_id=self.stage_id,
            rows=[r.to_dto() for r in self.rows],
            columns=[c.to_dto() for c in self.columns],
            sections=[s.to_dto() for s in self.sections],
            deleted_mapping_ids=self.deleted_mapping_ids,
            deleted_section_ids=self.deleted_section_ids,
        )


class StageSaveRowResult(BaseModel):
    id: int
    question_id: int
    serial_number: int

    @classmethod
    def from_dto(cls, dto: StageSaveRowResultDTO) -> "StageSaveRowResult":
        return cls(id=dto.id, question_id=dto.question_id, serial_number=dto.serial_number)


class StageSaveSectionResult(BaseModel):
    id: int
    section_name: str
    rows: list[StageSaveRowResult] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: StageSaveSectionResultDTO) -> "StageSaveSectionResult":
        return cls(
            id=dto.id,
            section_name=dto.section_name,
            rows=[StageSaveRowResult.from_dto(r) for r in dto.rows],
        )


class TemplateStageSaveResponse(BaseModel):
    format_stage_mapping_id: int
    rows: list[StageSaveRowResult] = Field(default_factory=list)
    sections: list[StageSaveSectionResult] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: TemplateStageSaveResultDTO) -> "TemplateStageSaveResponse":
        return cls(
            format_stage_mapping_id=dto.format_stage_mapping_id,
            rows=[StageSaveRowResult.from_dto(r) for r in dto.rows],
            sections=[StageSaveSectionResult.from_dto(s) for s in dto.sections],
        )
