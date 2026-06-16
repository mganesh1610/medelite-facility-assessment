from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ManualInputs(BaseModel):
    facility_name_override: str = ""
    emr: str = ""
    current_census: int | None = Field(default=None, ge=0)
    patient_type: str = ""
    previous_coverage: Literal["", "Yes", "No"] = ""
    previous_provider_performance: str = ""
    medical_coverage: str = ""


class AssessmentRequest(BaseModel):
    ccn: str
    manual: ManualInputs = Field(default_factory=ManualInputs)

    @field_validator("ccn")
    @classmethod
    def validate_ccn(cls, value: str) -> str:
        normalized = value.strip()
        if not re.fullmatch(r"\d{6}", normalized):
            raise ValueError("CCN must be exactly 6 digits.")
        return normalized


class FacilitySource(BaseModel):
    ccn: str
    provider_name: str
    display_name: str
    address: str
    city: str
    state: str
    zip_code: str
    location: str
    certified_beds: int | None
    average_residents_per_day: float | None
    processing_date: str
    medicare_url: str


class RatingCard(BaseModel):
    label: str
    value: int | None
    source_field: str


class MetricComparison(BaseModel):
    key: str
    label: str
    unit: Literal["percent", "rate"]
    facility: float | None
    state: float | None
    national: float | None
    facility_display: str
    state_display: str
    national_display: str
    measure_code: str
    source_description: str


class ReportRow(BaseModel):
    label: str
    value: str
    source: Literal["CMS", "Manual", "CMS + Manual Override", "Derived", "Source"]


class OpportunitySignal(BaseModel):
    label: str
    value: str
    severity: Literal["positive", "neutral", "warning", "critical"]


class OpportunityScore(BaseModel):
    score: int
    tier: Literal["High Outreach Priority", "Moderate Outreach Priority", "Monitor", "Low Priority"]
    rationale: list[str]
    signals: list[OpportunitySignal]


class DataQualityIssue(BaseModel):
    field: str
    message: str
    severity: Literal["info", "warning", "error"]


class DataQualityCheck(BaseModel):
    key: str
    label: str
    status: Literal["pass", "fail"]
    message: str
    severity: Literal["success", "warning", "error"]


class ExportLinks(BaseModel):
    pdf: str
    docx: str


class AssessmentResponse(BaseModel):
    facility: FacilitySource
    ratings: list[RatingCard]
    metrics: list[MetricComparison]
    report_rows: list[ReportRow]
    opportunity: OpportunityScore
    data_quality: list[DataQualityIssue]
    data_quality_checks: list[DataQualityCheck]
    exports: ExportLinks
    cms_request_count: int
    api_latency_ms: int
    bigquery_logging: str
