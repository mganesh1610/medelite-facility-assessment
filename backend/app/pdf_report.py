from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .schemas import AssessmentResponse


ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = ROOT / "assets" / "infinite-logo.png"


def build_pdf(assessment: AssessmentResponse) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.32 * inch,
        bottomMargin=0.32 * inch,
        title=f"{assessment.facility.display_name} Facility Assessment",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCompact",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=1,
    )
    state = ParagraphStyle(
        "State",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=11,
        alignment=1,
        textColor=colors.black,
        spaceAfter=4,
    )
    normal = ParagraphStyle(
        "NormalCompact",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.2,
        textColor=colors.HexColor("#0f172a"),
    )
    label = ParagraphStyle(
        "Label",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=8.8,
    )
    value = ParagraphStyle(
        "Value",
        parent=normal,
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=8.8,
    )
    source = ParagraphStyle(
        "Source",
        parent=normal,
        fontSize=7.2,
        leading=8.6,
        textColor=colors.HexColor("#1e40af"),
        alignment=1,
    )

    story = []
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=2.35 * inch, height=0.46 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.04 * inch))
    else:
        story.append(Paragraph("INFINITE - Managed by MEDELITE", title))

    story.append(Paragraph("FACILITY ASSESSMENT SNAPSHOT", title))
    story.append(Paragraph(assessment.facility.state, state))

    data = [[Paragraph(row.label, label), Paragraph(row.value, value)] for row in assessment.report_rows if row.source != "Source"]
    table = Table(data, colWidths=[3.55 * inch, 3.2 * inch], repeatRows=0)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.55, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 3.1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.1),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("LINEBEFORE", (1, 0), (1, -1), 0.9, colors.black),
                ("LINEABOVE", (0, 9), (-1, 9), 1.0, colors.black),
                ("LINEABOVE", (0, 13), (-1, 13), 1.0, colors.black),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph(f"Opportunity Score: {assessment.opportunity.score}/100 - {assessment.opportunity.tier}", normal))
    story.append(
        Paragraph(
            f'<link href="{assessment.facility.medicare_url}">Medicare Care Compare source profile</link>',
            source,
        )
    )
    story.append(Paragraph(f"CMS processing date: {assessment.facility.processing_date or 'Unknown'}", source))

    document.build(story)
    return buffer.getvalue()
