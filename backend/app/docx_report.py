from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from .schemas import AssessmentResponse


ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = ROOT / "assets" / "infinite-logo.png"


def build_docx(assessment: AssessmentResponse) -> bytes:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)

    styles = document.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    if LOGO_PATH.exists():
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(str(LOGO_PATH), width=Inches(2.75))
    else:
        centered(document, "INFINITE - Managed by MEDELITE", 16, bold=True)

    centered(document, "FACILITY ASSESSMENT SNAPSHOT", 14, bold=True)
    centered(document, assessment.facility.state, 12, bold=True)

    table = document.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    for row in assessment.report_rows:
        if row.source == "Source":
            continue
        cells = table.add_row().cells
        cells[0].text = row.label
        cells[1].text = row.value
        cells[0].paragraphs[0].runs[0].bold = True
        for cell in cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(9)

    document.add_paragraph()
    score = document.add_paragraph()
    score_run = score.add_run(f"Opportunity Score: {assessment.opportunity.score}/100 - {assessment.opportunity.tier}")
    score_run.bold = True
    score_run.font.size = Pt(10)

    source = document.add_paragraph("Medicare Care Compare source: ")
    add_hyperlink(source, assessment.facility.medicare_url, assessment.facility.medicare_url)
    document.add_paragraph(f"CMS processing date: {assessment.facility.processing_date or 'Unknown'}")

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def centered(document: Document, text: str, size: int, bold: bool = False) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(15, 23, 42)


def add_hyperlink(paragraph, url: str, text: str) -> None:
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1E40AF")
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    new_run.append(r_pr)
    text_element = OxmlElement("w:t")
    text_element.text = text
    new_run.append(text_element)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

