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
    PdfDocument,
    PdfRowGroup,
    PdfSection,
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

        if section.signatures:
            flow.append(Spacer(1, 6))
            flow.append(self._build_remarks(section))
        flow.append(Spacer(1, 10))
        return flow

    def _build_table(self, group: PdfRowGroup) -> Table:
        head = self._styles["cell_header"]
        columns = group.columns

        data = [[Paragraph(_esc(c.header), head) for c in columns]]
        for row in group.rows:
            data.append([self._render_cell(c, row) for c in columns])

        col_widths = self._column_widths(columns)
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

    def _render_cell(self, column: PdfColumn, row):
        """Render one cell for the given template column type."""
        ctype = (column.column_type or "ANSWER").upper()
        value = row.values.get(ctype, "")

        if ctype == "QUESTION":
            return self._question_cell(value, row.sub_questions)

        if ctype == "SERIAL":
            return Paragraph(_esc(value), self._styles["cell"])

        # OPTION / ANSWER / RESPONSE / AQL_LIMIT and any custom type: show the
        # value, or N/A when the question didn't carry one.
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

    def _question_cell(self, question: str, sub_questions: list[str]) -> list:
        """The Question cell: the question text plus any sub-questions nested
        underneath as bulleted lines (mirrors the fill UI)."""
        flow: list = [Paragraph(_esc(question), self._styles["cell"])]
        for sub in sub_questions:
            if sub.strip():
                flow.append(Paragraph(f"&bull; {_esc(sub)}", self._styles["sub_item"]))
        return flow

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
