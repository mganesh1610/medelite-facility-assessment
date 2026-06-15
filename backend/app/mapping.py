from __future__ import annotations

import math
from typing import Any

from .schemas import (
    AssessmentRequest,
    AssessmentResponse,
    DataQualityIssue,
    ExportLinks,
    FacilitySource,
    MetricComparison,
    OpportunityScore,
    OpportunitySignal,
    RatingCard,
    ReportRow,
)


CLAIMS_FIELD_MAP = {
    "521": {
        "key": "str_hospitalization",
        "label": "Short Term Hospitalization",
        "unit": "percent",
        "state_field": "percentage_of_short_stay_residents_who_were_rehospitalized__1d02",
        "description": "Percentage of short-stay residents rehospitalized after nursing home admission",
    },
    "522": {
        "key": "str_ed_visit",
        "label": "STR ED Visit",
        "unit": "percent",
        "state_field": "percentage_of_short_stay_residents_who_had_an_outpatient_em_d911",
        "description": "Percentage of short-stay residents with outpatient emergency department visit",
    },
    "551": {
        "key": "lt_hospitalization",
        "label": "LT Hospitalization",
        "unit": "rate",
        "state_field": "number_of_hospitalizations_per_1000_longstay_resident_days",
        "description": "Hospitalizations per 1,000 long-stay resident days",
    },
    "552": {
        "key": "lt_ed_visit",
        "label": "LT ED Visit",
        "unit": "rate",
        "state_field": "number_of_outpatient_emergency_department_visits_per_1000_l_de9d",
        "description": "Outpatient ED visits per 1,000 long-stay resident days",
    },
}


def build_assessment(
    request: AssessmentRequest,
    provider: dict[str, Any],
    claims_rows: list[dict[str, Any]],
    state_avg: dict[str, Any] | None,
    national_avg: dict[str, Any] | None,
    api_latency_ms: int,
    cms_request_count: int,
    bigquery_logging: str,
) -> AssessmentResponse:
    manual = request.manual
    official_name = clean_name(provider.get("provider_name", ""))
    display_name = manual.facility_name_override.strip() or official_name
    location = format_location(provider)
    state_code = str(provider.get("state", "")).strip()
    facility = FacilitySource(
        ccn=request.ccn,
        provider_name=official_name,
        display_name=display_name,
        address=clean_title(provider.get("provider_address", "")),
        city=clean_title(provider.get("citytown", "")),
        state=state_code,
        zip_code=str(provider.get("zip_code", "")).strip(),
        location=location,
        certified_beds=parse_int(provider.get("number_of_certified_beds")),
        average_residents_per_day=parse_float(provider.get("average_number_of_residents_per_day")),
        processing_date=str(provider.get("processing_date", "")),
        medicare_url=f"https://www.medicare.gov/care-compare/details/nursing-home/{request.ccn}/view-all?state={state_code}",
    )

    ratings = [
        RatingCard(label="Overall Star Rating", value=parse_int(provider.get("overall_rating")), source_field="overall_rating"),
        RatingCard(label="Health Inspection", value=parse_int(provider.get("health_inspection_rating")), source_field="health_inspection_rating"),
        RatingCard(label="Staffing", value=parse_int(provider.get("staffing_rating")), source_field="staffing_rating"),
        RatingCard(label="Quality of Resident Care", value=parse_int(provider.get("qm_rating")), source_field="qm_rating"),
    ]

    metrics = build_metric_comparisons(claims_rows, state_avg, national_avg)
    report_rows = build_report_rows(facility, ratings, metrics, request)
    quality_issues = build_data_quality_issues(request, facility, ratings, metrics, provider)
    opportunity = calculate_opportunity(facility, ratings, metrics, request)

    return AssessmentResponse(
        facility=facility,
        ratings=ratings,
        metrics=metrics,
        report_rows=report_rows,
        opportunity=opportunity,
        data_quality=quality_issues,
        exports=ExportLinks(
            pdf=f"/api/reports/pdf?ccn={request.ccn}",
            docx=f"/api/reports/docx?ccn={request.ccn}",
        ),
        cms_request_count=cms_request_count,
        api_latency_ms=api_latency_ms,
        bigquery_logging=bigquery_logging,
    )


def build_metric_comparisons(
    claims_rows: list[dict[str, Any]],
    state_avg: dict[str, Any] | None,
    national_avg: dict[str, Any] | None,
) -> list[MetricComparison]:
    by_code = {str(row.get("measure_code")): row for row in claims_rows}
    comparisons: list[MetricComparison] = []
    for code, config in CLAIMS_FIELD_MAP.items():
        row = by_code.get(code, {})
        field = config["state_field"]
        unit = config["unit"]
        facility = parse_float(row.get("adjusted_score"))
        state = parse_float((state_avg or {}).get(field))
        national = parse_float((national_avg or {}).get(field))
        comparisons.append(
            MetricComparison(
                key=config["key"],
                label=config["label"],
                unit=unit,  # type: ignore[arg-type]
                facility=facility,
                state=state,
                national=national,
                facility_display=format_metric(facility, unit),
                state_display=format_metric(state, unit),
                national_display=format_metric(national, unit),
                measure_code=code,
                source_description=config["description"],
            )
        )
    return comparisons


def build_report_rows(
    facility: FacilitySource,
    ratings: list[RatingCard],
    metrics: list[MetricComparison],
    request: AssessmentRequest,
) -> list[ReportRow]:
    manual = request.manual
    rows = [
        ReportRow(label="Name of Facility", value=facility.display_name, source="CMS + Manual Override"),
        ReportRow(label="Location", value=facility.location, source="CMS"),
        ReportRow(label="EMR", value=manual.emr or "Not provided", source="Manual"),
        ReportRow(label="Census Capacity", value=format_value(facility.certified_beds), source="CMS"),
        ReportRow(label="Current Census", value=format_value(manual.current_census), source="Manual"),
        ReportRow(label="Type of Patient", value=manual.patient_type or "Not provided", source="Manual"),
        ReportRow(label="Previous Coverage from Medelite", value=manual.previous_coverage or "Not provided", source="Manual"),
        ReportRow(label="Previous Provider Performance from Medelite", value=manual.previous_provider_performance or "Not provided", source="Manual"),
        ReportRow(label="Medical Coverage", value=manual.medical_coverage or "Not provided", source="Manual"),
    ]
    rows.extend(ReportRow(label=rating.label, value=format_value(rating.value), source="CMS") for rating in ratings)
    metric_lookup = {metric.key: metric for metric in metrics}
    rows.extend(
        [
            ReportRow(label="Short Term Hospitalization", value=metric_lookup["str_hospitalization"].facility_display, source="CMS"),
            ReportRow(label="STR National Avg. for Hospitalization", value=metric_lookup["str_hospitalization"].national_display, source="CMS"),
            ReportRow(label="STR State Avg. for Hospitalization", value=metric_lookup["str_hospitalization"].state_display, source="CMS"),
            ReportRow(label="STR ED Visit", value=metric_lookup["str_ed_visit"].facility_display, source="CMS"),
            ReportRow(label="STR ED Visits National Avg.", value=metric_lookup["str_ed_visit"].national_display, source="CMS"),
            ReportRow(label="STR ED Visits State Avg.", value=metric_lookup["str_ed_visit"].state_display, source="CMS"),
            ReportRow(label="LT Hospitalization", value=metric_lookup["lt_hospitalization"].facility_display, source="CMS"),
            ReportRow(label="LT National Avg. for Hospitalization", value=metric_lookup["lt_hospitalization"].national_display, source="CMS"),
            ReportRow(label="LT State Avg. for Hospitalization", value=metric_lookup["lt_hospitalization"].state_display, source="CMS"),
            ReportRow(label="ED Visit", value=metric_lookup["lt_ed_visit"].facility_display, source="CMS"),
            ReportRow(label="LT ED Visits National Avg.", value=metric_lookup["lt_ed_visit"].national_display, source="CMS"),
            ReportRow(label="LT ED Visits State Avg.", value=metric_lookup["lt_ed_visit"].state_display, source="CMS"),
            ReportRow(label="Medicare Care Compare Source", value=facility.medicare_url, source="Source"),
        ]
    )
    return rows


def calculate_opportunity(
    facility: FacilitySource,
    ratings: list[RatingCard],
    metrics: list[MetricComparison],
    request: AssessmentRequest,
) -> OpportunityScore:
    score = 0
    rationale: list[str] = []
    rating_values = {rating.label: rating.value for rating in ratings}
    for label, weight in [
        ("Overall Star Rating", 7),
        ("Health Inspection", 6),
        ("Staffing", 7),
        ("Quality of Resident Care", 4),
    ]:
        value = rating_values.get(label)
        if value is not None:
            contribution = max(0, 5 - value) * weight
            score += contribution
            if contribution >= weight * 2:
                rationale.append(f"{label} is {value}/5, indicating visible performance headroom.")

    for metric in metrics:
        benchmark = first_number(metric.state, metric.national)
        if metric.facility is not None and benchmark is not None and metric.facility > benchmark:
            gap = metric.facility - benchmark
            contribution = min(12, math.ceil(gap * (2 if metric.unit == "percent" else 6)))
            score += contribution
            rationale.append(f"{metric.label} is above the closest benchmark by {format_metric(gap, metric.unit)}.")

    if request.manual.previous_coverage == "No":
        score += 8
        rationale.append("No previous Medelite coverage creates a new-service outreach opportunity.")

    if facility.certified_beds and request.manual.current_census is not None:
        occupancy = request.manual.current_census / max(facility.certified_beds, 1)
        if occupancy >= 0.85:
            score += 8
            rationale.append(f"Reported census implies {occupancy:.0%} occupancy, supporting operational impact.")

    score = max(0, min(100, score))
    tier = "Low Priority"
    if score >= 70:
        tier = "High Outreach Priority"
    elif score >= 45:
        tier = "Moderate Outreach Priority"
    elif score >= 25:
        tier = "Monitor"

    signals = [
        OpportunitySignal(label="CMS processing date", value=facility.processing_date or "Unknown", severity="neutral"),
        OpportunitySignal(label="Certified beds", value=format_value(facility.certified_beds), severity="neutral"),
        OpportunitySignal(label="Manual fields complete", value=f"{manual_completion_count(request)}/6", severity="positive" if manual_completion_count(request) >= 5 else "warning"),
    ]
    if not rationale:
        rationale.append("No major benchmark gaps were detected from the available CMS measures.")
    return OpportunityScore(score=score, tier=tier, rationale=rationale[:5], signals=signals)


def build_data_quality_issues(
    request: AssessmentRequest,
    facility: FacilitySource,
    ratings: list[RatingCard],
    metrics: list[MetricComparison],
    provider: dict[str, Any],
) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    if not facility.processing_date:
        issues.append(DataQualityIssue(field="processing_date", message="CMS processing date is missing.", severity="warning"))
    for rating in ratings:
        if rating.value is None:
            issues.append(DataQualityIssue(field=rating.source_field, message=f"{rating.label} is unavailable in CMS.", severity="warning"))
    for metric in metrics:
        if metric.facility is None:
            issues.append(DataQualityIssue(field=metric.measure_code, message=f"{metric.label} is missing from CMS claims data.", severity="warning"))
        if metric.state is None or metric.national is None:
            issues.append(DataQualityIssue(field=metric.key, message=f"{metric.label} benchmark data is incomplete.", severity="info"))
    if request.manual.current_census is None:
        issues.append(DataQualityIssue(field="current_census", message="Current census is manual and has not been entered.", severity="info"))
    if parse_int(provider.get("number_of_certified_beds")) is None:
        issues.append(DataQualityIssue(field="number_of_certified_beds", message="Certified bed count is missing from CMS.", severity="warning"))
    return issues


def format_location(provider: dict[str, Any]) -> str:
    parts = [
        clean_title(provider.get("provider_address", "")),
        clean_title(provider.get("citytown", "")),
        str(provider.get("state", "")).strip(),
        str(provider.get("zip_code", "")).strip(),
    ]
    return ", ".join(part for part in parts if part)


def clean_title(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    words = text.title().split()
    keep_upper = {"Nw", "Ne", "Sw", "Se", "N", "S", "E", "W", "Us", "Fl", "Al"}
    return " ".join(word.upper() if word in keep_upper else word for word in words)


def clean_name(value: Any) -> str:
    return clean_title(value)


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int(value: Any) -> int | None:
    parsed = parse_float(value)
    if parsed is None:
        return None
    return int(round(parsed))


def format_metric(value: float | None, unit: str) -> str:
    if value is None:
        return "Not available"
    if unit == "percent":
        return f"{value:.1f}%"
    return f"{value:.2f}"


def format_value(value: Any) -> str:
    if value in (None, ""):
        return "Not available"
    return str(value)


def first_number(*values: float | None) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None


def manual_completion_count(request: AssessmentRequest) -> int:
    manual = request.manual
    values = [
        manual.emr,
        manual.current_census,
        manual.patient_type,
        manual.previous_coverage,
        manual.previous_provider_performance,
        manual.medical_coverage,
    ]
    return sum(1 for value in values if value not in (None, ""))
