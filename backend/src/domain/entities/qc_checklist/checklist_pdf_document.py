"""Checklist PDF document — domain entities.

The format-agnostic structure of a rendered checklist report. The application
service assembles one of these from the repository's read models; the renderer
turns it into bytes. Keeping the structure in the domain means neither the data
assembly nor the layout owns the shape — they share this vocabulary.

Mirrors the report:
  * a document header (company + title + request number)
  * one section per stage, each with grouped tables (optionally per section
    heading) and a set of signature / remark blocks underneath.
"""

from dataclasses import dataclass, field


@dataclass
class PdfColumn:
    """A column in a group's table, as configured in Template Studio.

    `column_type` is one of SERIAL / QUESTION / OPTION / ANSWER / RESPONSE /
    AQL_LIMIT — it tells the renderer which value to pull for each row.
    """

    header: str
    column_type: str


@dataclass
class PdfRow:
    """One question row in a group's table.

    `values` holds the row's value for each column_type (SERIAL / QUESTION /
    OPTION / ANSWER / RESPONSE / AQL_LIMIT). `sub_questions` are display-only
    child questions shown nested under the QUESTION cell, mirroring the fill UI.
    """

    values: dict[str, str] = field(default_factory=dict)
    sub_questions: list[str] = field(default_factory=list)


@dataclass
class PdfRowGroup:
    """A block of rows under an optional section heading within a stage.

    `columns` are this group's template-configured columns (in display order).
    A stage without configured sections has a single group with an empty
    `section_name` (no heading drawn).
    """

    section_name: str
    columns: list[PdfColumn] = field(default_factory=list)
    rows: list[PdfRow] = field(default_factory=list)


@dataclass
class PdfSignatureBlock:
    """One signature line under a section (e.g. 'Analyzed By : <name>')."""

    label: str
    user_name: str
    time_stamp: str          # pre-formatted for display (e.g. '08-May-2026 15:24')
    remark: str


@dataclass
class PdfSection:
    """A stage rendered as one or more grouped tables + its signatures."""

    title: str
    groups: list[PdfRowGroup] = field(default_factory=list)
    signatures: list[PdfSignatureBlock] = field(default_factory=list)


@dataclass
class PdfDocument:
    """The whole report."""

    company_name: str
    company_location: str
    title: str
    request_number: str
    footer_code: str
    sections: list[PdfSection] = field(default_factory=list)
