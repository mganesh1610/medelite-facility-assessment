from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .schemas import AssessmentResponse


ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = ROOT / "assets" / "infinite-logo.png"

INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
PRIMARY = colors.HexColor("#1e40af")
PRIMARY_LIGHT = colors.HexColor("#eff6ff")
BORDER = colors.HexColor("#bfdbfe")
FILL = colors.HexColor("#f8fafc")
ACCENT = colors.HexColor("#d97706")
SUCCESS_FILL = colors.HexColor("#ecfdf5")
SUCCESS = colors.HexColor("#15803d")
CONTENT_WIDTH = 7.35 * inch


def build_pdf(assessment: AssessmentResponse) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.42 * inch,
        leftMargin=0.42 * inch,
        topMargin=0.34 * inch,
        bottomMargin=0.34 * inch,
        title=f"{assessment.facility.display_name} Facility Assessment",
    )

    styles = build_styles()
    story = [
        build_header(assessment, styles),
        Spacer(1, 0.08 * inch),
        build_facility_summary(assessment, styles),
        Spacer(1, 0.08 * inch),
        section_title("Facility Profile", styles),
        build_profile_table(assessment, styles),
        Spacer(1, 0.08 * inch),
        section_title("Quality & Safety Ratings", styles),
        build_rating_cards(assessment, styles),
        Spacer(1, 0.08 * inch),
        section_title("Hospitalization & ED Performance", styles),
        build_metric_table(assessment, styles),
        Spacer(1, 0.08 * inch),
        build_footer_summary(assessment, styles),
    ]

    document.build(story)
    return buffer.getvalue()


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=2,
            textColor=INK,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            alignment=2,
            textColor=MUTED,
        ),
        "section": ParagraphStyle(
            "SectionTitle",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=PRIMARY,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.7,
            leading=9.4,
            textColor=INK,
        ),
        "value": ParagraphStyle(
            "Value",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.7,
            leading=9.4,
            textColor=INK,
        ),
        "hero": ParagraphStyle(
            "Hero",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=INK,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=8.6,
            textColor=MUTED,
        ),
        "card_value": ParagraphStyle(
            "CardValue",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=19,
            alignment=1,
            textColor=INK,
        ),
        "card_label": ParagraphStyle(
            "CardLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.1,
            leading=13,
            alignment=1,
            textColor=MUTED,
        ),
        "link": ParagraphStyle(
            "Link",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=8.6,
            textColor=PRIMARY,
            alignment=2,
        ),
    }


def build_header(assessment: AssessmentResponse, styles: dict[str, ParagraphStyle]) -> Table:
    logo_cell: Image | Paragraph
    if LOGO_PATH.exists():
        logo_cell = Image(str(LOGO_PATH), width=2.15 * inch, height=0.42 * inch)
    else:
        logo_cell = Paragraph("<b>INFINITE</b><br/>Managed by MEDELITE", styles["hero"])
    title = Paragraph(
        "FACILITY ASSESSMENT SNAPSHOT"
        f"<br/><font color='#64748b'>State {safe(assessment.facility.state)} | CCN {safe(assessment.facility.ccn)} | CMS {safe(assessment.facility.processing_date or 'Unknown')}</font>",
        styles["title"],
    )
    table = Table([[logo_cell, title]], colWidths=[2.35 * inch, 5.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return table


def build_facility_summary(assessment: AssessmentResponse, styles: dict[str, ParagraphStyle]) -> Table:
    score_color = ACCENT if assessment.opportunity.score >= 45 else PRIMARY
    facility = Paragraph(
        f"<b>{safe(assessment.facility.display_name)}</b>"
        f"<br/><font color='#64748b'>{safe(assessment.facility.location)}</font>",
        styles["hero"],
    )
    opportunity = Paragraph(
        f"<font color='#64748b'>Opportunity Score</font><br/><font size='16' color='{score_color.hexval()}'><b>{assessment.opportunity.score}/100</b></font>"
        f"<br/><font color='#0f172a'>{safe(assessment.opportunity.tier)}</font>",
        styles["card_label"],
    )
    table = Table([[facility, opportunity]], colWidths=[5.35 * inch, 2.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_LIGHT),
                ("BACKGROUND", (1, 0), (1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 13),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
            ]
        )
    )
    return table


def section_title(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table([[Paragraph(safe(text).upper(), styles["section"])]], colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_profile_table(assessment: AssessmentResponse, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        ("EMR", value_for(assessment, "EMR"), "Certified Beds", value_for(assessment, "Census Capacity")),
        ("Current Census", value_for(assessment, "Current Census"), "Patient Type", value_for(assessment, "Type of Patient")),
        ("Previous Coverage", value_for(assessment, "Previous Coverage from Medelite"), "Medical Coverage", value_for(assessment, "Medical Coverage")),
        ("Provider Performance", value_for(assessment, "Previous Provider Performance from Medelite"), "CMS Date", assessment.facility.processing_date or "Unknown"),
    ]
    data = [
        [Paragraph(safe(a), styles["label"]), Paragraph(safe(b), styles["value"]), Paragraph(safe(c), styles["label"]), Paragraph(safe(d), styles["value"])]
        for a, b, c, d in rows
    ]
    table = Table(data, colWidths=[1.25 * inch, 2.45 * inch, 1.25 * inch, 2.40 * inch])
    table.setStyle(standard_grid_style())
    return table


def build_rating_cards(assessment: AssessmentResponse, styles: dict[str, ParagraphStyle]) -> Table:
    cells = []
    for rating in assessment.ratings:
        value = "N/A" if rating.value is None else f"{rating.value}/5"
        cells.append(
            Paragraph(
                f"{safe(rating.label)}<br/><font size='14'><b>{safe(value)}</b></font>",
                styles["card_label"],
            )
        )
    table = Table([cells], colWidths=[CONTENT_WIDTH / 4] * 4)
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    return table


def build_metric_table(assessment: AssessmentResponse, styles: dict[str, ParagraphStyle]) -> Table:
    data = [
        [
            Paragraph("Metric", styles["label"]),
            Paragraph("Facility", styles["label"]),
            Paragraph("State Avg.", styles["label"]),
            Paragraph("National Avg.", styles["label"]),
            Paragraph("Unit", styles["label"]),
        ]
    ]
    for metric in assessment.metrics:
        unit = "%" if metric.unit == "percent" else "per 1,000 resident days"
        data.append(
            [
                Paragraph(safe(metric.label), styles["value"]),
                Paragraph(safe(metric.facility_display), styles["value"]),
                Paragraph(safe(metric.state_display), styles["value"]),
                Paragraph(safe(metric.national_display), styles["value"]),
                Paragraph(safe(unit), styles["small"]),
            ]
        )
    table = Table(data, colWidths=[2.45 * inch, 1.05 * inch, 1.05 * inch, 1.15 * inch, 1.65 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_LIGHT),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def build_footer_summary(assessment: AssessmentResponse, styles: dict[str, ParagraphStyle]) -> Table:
    rationale = "<br/>".join(f"- {safe(item)}" for item in assessment.opportunity.rationale[:3])
    quality_text = "No data quality warnings detected." if not assessment.data_quality else "<br/>".join(
        f"- {safe(issue.field)}: {safe(issue.message)}" for issue in assessment.data_quality[:3]
    )
    left = Paragraph(
        f"<b>Action Priorities</b><br/>{rationale or 'No major benchmark gaps were detected.'}",
        styles["value"],
    )
    right = Paragraph(
        f"<b>Source</b><br/><link href='{safe_attr(assessment.facility.medicare_url)}'>Medicare Care Compare profile</link>"
        f"<br/><font color='#64748b'>{quality_text}</font>",
        styles["link"],
    )
    table = Table([[left, right]], colWidths=[4.55 * inch, 2.80 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("BACKGROUND", (0, 0), (0, 0), FILL),
                ("BACKGROUND", (1, 0), (1, 0), SUCCESS_FILL if not assessment.data_quality else colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def standard_grid_style() -> TableStyle:
    return TableStyle(
        [
            ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("BACKGROUND", (0, 0), (0, -1), FILL),
            ("BACKGROUND", (2, 0), (2, -1), FILL),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]
    )


def value_for(assessment: AssessmentResponse, label: str) -> str:
    for row in assessment.report_rows:
        if row.label == label:
            return row.value
    return "Not available"


def safe(value: object) -> str:
    return escape(str(value or ""))


def safe_attr(value: object) -> str:
    return safe(value).replace("'", "&apos;")
