"""Checklist PDF Renderer — turns a PdfDocument into PDF bytes with ReportLab.

Layout (matches the sample report):
  * Every page carries a header (company name in red + location, a centered
    report title, and the request number) and a footer (the format/SOP code
    plus 'Page X of Y').
  * The body flows one section per stage: a bold section title, a table with
    columns Sr.No. | Question | Selected Values | Entered Values | [Response],
    then the stage's signature blocks laid out two-per-row.

The renderer is pure presentation — it reads only the PdfDocument, so the same
code renders any format's report.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from src.domain.entities.qc_checklist.checklist_pdf_document import (
    PdfColumn,
    PdfDeclaration,
    PdfDocument,
    PdfRowGroup,
    PdfSection,
    PdfSubAnswer,
)

# Palette — a muted blue header band on tables + Emcure red for the brand.
_BRAND_RED = colors.HexColor("#C0392B")
_HEADER_BG = colors.HexColor("#DCE3F0")
_GRID = colors.HexColor("#9AA7BD")
_TEXT = colors.HexColor("#1F2933")

_PAGE_W, _PAGE_H = A4
_MARGIN = 18 * mm


class _NumberedCanvas(Canvas):
    """Two-pass canvas that stamps 'Page X of Y' once the total is known.

    ReportLab doesn't know the page count until the whole story is laid out, so
    each page is buffered on showPage() and the page-number footer is drawn in
    save(), when len(pages) is the real total.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_states: list[dict] = []

    def showPage(self) -> None:  # noqa: N802  (ReportLab API name)
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_page_number(total)
            super().showPage()
        super().save()

    def _draw_page_number(self, total: int) -> None:
        self.setFont("Helvetica", 8)
        self.setFillColor(_TEXT)
        self.drawRightString(_PAGE_W - _MARGIN, 10 * mm, f"Page {self._pageNumber} of {total}")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontName="Helvetica",
            fontSize=8.5, leading=11, textColor=_TEXT,
        ),
        "cell_header": ParagraphStyle(
            "cell_header", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=_TEXT,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, spaceBefore=8, spaceAfter=4, textColor=_TEXT,
        ),
        "subsection": ParagraphStyle(
            "subsection", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9, leading=12, spaceBefore=6, spaceAfter=3, textColor=_BRAND_RED,
        ),
        "sub_item": ParagraphStyle(
            "sub_item", parent=base["Normal"], fontName="Helvetica",
            fontSize=8, leading=10, textColor=colors.HexColor("#64748B"),
            leftIndent=6,
        ),
        "sig": ParagraphStyle(
            "sig", parent=base["Normal"], fontName="Helvetica",
            fontSize=8.5, leading=12, textColor=_TEXT,
        ),
    }


class ChecklistPdfRenderer:
    """Renders a PdfDocument to PDF bytes."""

    def __init__(self) -> None:
        self._styles = _styles()

    def render(self, document: PdfDocument) -> bytes:
        buffer = BytesIO()
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=_MARGIN,
            rightMargin=_MARGIN,
            topMargin=30 * mm,
            bottomMargin=20 * mm,
            title=f"{document.title} - {document.request_number}",
        )

        frame = Frame(
            _MARGIN, 20 * mm,
            _PAGE_W - 2 * _MARGIN,
            _PAGE_H - 30 * mm - 20 * mm,
            id="body",
        )
        doc.addPageTemplates([
            PageTemplate(
                id="main",
                frames=[frame],
                onPage=lambda canvas, d: self._draw_page_furniture(canvas, d, document),
            )
        ])

        story = []
        for index, section in enumerate(document.sections):
            story.extend(self._render_section(section))
            # Each stage starts on its own page: break after every section
            # except the last one.
            if index < len(document.sections) - 1:
                story.append(PageBreak())
        if not story:
            story.append(Paragraph("No data available for this request.", self._styles["cell"]))

        doc.build(story, canvasmaker=_NumberedCanvas)
        return buffer.getvalue()

    # ─── Per-page header + footer ─────────────────────────────────────────
    def _draw_page_furniture(self, canvas, doc, document: PdfDocument) -> None:
        canvas.saveState()

        # Header — brand + location (left), centered title + request number.
        canvas.setFillColor(_BRAND_RED)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(_MARGIN, _PAGE_H - 15 * mm, document.company_name)
        canvas.setFillColor(_TEXT)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawString(_MARGIN, _PAGE_H - 18.5 * mm, document.company_location)

        center_x = _PAGE_W / 2
        canvas.setFont("Helvetica-Bold", 9.5)
        canvas.drawCentredString(center_x, _PAGE_H - 22.5 * mm, document.title)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawCentredString(
            center_x, _PAGE_H - 26.5 * mm, f"REQUEST NO - {document.request_number}"
        )

        # Footer — SOP code (right aligned). The 'Page X of Y' line is stamped
        # by _NumberedCanvas once the total page count is known.
        if document.footer_code:
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(_PAGE_W - _MARGIN, 14 * mm, document.footer_code)

        canvas.restoreState()

    # ─── Section = stage title + grouped tables + signatures ──────────────
    def _render_section(self, section: PdfSection) -> list:
        flow: list = [Paragraph(_esc(section.title), self._styles["section"])]

        for group in section.groups:
            # A configured section renders its name as a sub-heading; the
            # unheaded group (no section) renders just its table.
            if group.section_name.strip():
                flow.append(Paragraph(_esc(group.section_name), self._styles["subsection"]))
            if group.rows:
                flow.append(self._build_table(group))

        # Declaration questions (if any) render just above the remarks, under a
        # bold "Declaration" heading.
        if section.declarations:
            flow.append(Spacer(1, 6))
            flow.append(Paragraph("Declaration", self._styles["section"]))
            flow.append(self._build_declarations(section.declarations))

        if section.signatures:
            flow.append(Spacer(1, 6))
            flow.append(self._build_remarks(section))
        flow.append(Spacer(1, 10))
        return flow

    def _build_declarations(self, declarations: list[PdfDeclaration]) -> KeepTogether:
        """Declaration questions as a Question / Answer table under the stage."""
        head = self._styles["cell_header"]
        cell = self._styles["cell"]
        avail = _PAGE_W - 2 * _MARGIN
        col_widths = [avail * 0.65, avail * 0.35]

        data = [[Paragraph("Question", head), Paragraph("Selected Value", head)]]
        for d in declarations:
            data.append([
                Paragraph(_esc(d.question), cell),
                Paragraph(_esc(d.answer) or "N/A", cell),
            ])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return KeepTogether(table)

    def _build_table(self, group: PdfRowGroup) -> Table:
        head = self._styles["cell_header"]
        columns = group.columns
        col_widths = self._column_widths(columns)

        data = [[Paragraph(_esc(c.header), head) for c in columns]]
        for row in group.rows:
            data.append([
                self._render_cell(c, row, col_widths[i]) for i, c in enumerate(columns)
            ])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def _render_cell(self, column: PdfColumn, row, col_width: float):
        """Render one cell for the given template column type. `col_width` is
        this column's drawn width, so nested sub-tables fit inside it."""
        ctype = (column.column_type or "ANSWER").upper()
        value = row.values.get(ctype, "")

        if ctype == "QUESTION":
            # Question text + a Sr.No./Question sub-table (titles only).
            return self._question_cell(value, row.sub_answers, col_width)

        if ctype == "SERIAL":
            return Paragraph(_esc(value), self._styles["cell"])

        if ctype == "ANSWER":
            # Parent answer + an Answer-only sub-table (no Sr.No.), row-aligned
            # with the sub-questions listed in the Question column.
            return self._answer_cell(value, row.sub_answers, col_width)

        # OPTION / RESPONSE / AQL_LIMIT and any custom type: show the value, or
        # N/A when the question didn't carry one.
        return Paragraph(_esc(value) or "N/A", self._styles["cell"])

    def _column_widths(self, columns: list[PdfColumn]) -> list[float]:
        """Proportional widths — the QUESTION column takes the lion's share,
        the rest split the remainder evenly."""
        avail = _PAGE_W - 2 * _MARGIN
        weights: list[float] = []
        for c in columns:
            ctype = (c.column_type or "ANSWER").upper()
            if ctype == "SERIAL":
                weights.append(0.5)
            elif ctype == "QUESTION":
                weights.append(4.0)
            else:
                weights.append(1.6)
        total = sum(weights) or 1.0
        return [avail * w / total for w in weights]

    # The parent cell's own left+right padding (set on the outer table style).
    _CELL_PADDING = 10

    def _question_cell(
        self, question: str, sub_answers: list[PdfSubAnswer], col_width: float
    ) -> list:
        """The Question cell: the question text plus — when it has answered
        sub-questions — a Sr.No. / Question sub-table (titles), sized to fit
        within the Question column."""
        flow: list = [Paragraph(_esc(question), self._styles["cell"])]
        if sub_answers:
            flow.append(Spacer(1, 3))
            flow.append(self._build_sub_table(
                col_width,
                headers=["Sr.No.", "Question"],
                rows=[[str(i), sa.question] for i, sa in enumerate(sub_answers, start=1)],
                first_col_fixed=22,
            ))
        return flow

    def _answer_cell(self, answer: str, sub_answers: list[PdfSubAnswer], col_width: float) -> list:
        """The Answer cell: the parent answer plus — when it has answered
        sub-questions — an Answer-only sub-table (no Sr.No.), sized to fit within
        the Answer column and row-aligned with the Question column's sub-table."""
        flow: list = [Paragraph(_esc(answer) or "N/A", self._styles["cell"])]
        if sub_answers:
            flow.append(Spacer(1, 3))
            flow.append(self._build_sub_table(
                col_width,
                headers=["Answer"],
                rows=[[sa.answer] for sa in sub_answers],
            ))
        return flow

    def _build_sub_table(
        self,
        col_width: float,
        headers: list[str],
        rows: list[list[str]],
        first_col_fixed: float | None = None,
    ) -> Table:
        """A compact sub-table sized to fit inside its parent column.

        `first_col_fixed` reserves a fixed width for a leading Sr.No. column;
        the remaining columns share the rest. All widths are clamped to the
        column's inner width (col_width minus the parent cell padding) so the
        sub-table never overflows the column.
        """
        head = self._styles["cell_header"]
        cell = self._styles["sub_item"]

        inner = max(col_width - self._CELL_PADDING, 1.0)
        ncols = len(headers)
        if first_col_fixed is not None and ncols > 1:
            first = min(first_col_fixed, inner)
            rest = (inner - first) / (ncols - 1)
            col_widths = [first] + [rest] * (ncols - 1)
        else:
            col_widths = [inner / ncols] * ncols

        data = [[Paragraph(_esc(h), head) for h in headers]]
        for r in rows:
            data.append([Paragraph(_esc(c) or "N/A", cell) for c in r])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.4, _GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        return table

    def _build_remarks(self, section: PdfSection) -> KeepTogether:
        """Signatures laid out two per row, each a bordered cell."""
        style = self._styles["sig"]
        cells = []
        for sig in section.signatures:
            text = (
                f"<b>{_esc(sig.label)} :</b> {_esc(sig.user_name)}<br/>"
                f"<b>Time Stamp:</b> {_esc(sig.time_stamp)}<br/>"
                f"<b>Remark:</b> {_esc(sig.remark)}"
            )
            cells.append(Paragraph(text, style))

        avail = _PAGE_W - 2 * _MARGIN
        rows = []
        for i in range(0, len(cells), 2):
            pair = cells[i:i + 2]
            if len(pair) == 1:
                pair.append(Paragraph("", style))
            rows.append(pair)

        table = Table(rows, colWidths=[avail / 2, avail / 2])
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, _GRID),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, _GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return KeepTogether(table)


def _esc(value: str) -> str:
    """Escape the XML-ish markup Paragraph interprets."""
    if not value:
        return ""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
