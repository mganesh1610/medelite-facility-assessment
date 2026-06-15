from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from .schemas import AssessmentResponse
from .settings import settings


def log_assessment(assessment: AssessmentResponse) -> str:
    if not settings.bigquery_enabled:
        return "disabled"
    if not settings.gcp_project_id:
        return "skipped: missing GCP_PROJECT_ID"

    try:
        from google.cloud import bigquery
    except Exception as exc:  # pragma: no cover - optional integration
        return f"skipped: BigQuery client unavailable ({exc})"

    try:  # pragma: no cover - requires external credentials
        client = bigquery.Client(project=settings.gcp_project_id)
        table_id = f"{settings.gcp_project_id}.{settings.bigquery_dataset}.{settings.bigquery_table}"
        metrics = {metric.key: metric.model_dump() for metric in assessment.metrics}
        row: dict[str, Any] = {
            "run_id": str(uuid.uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "ccn": assessment.facility.ccn,
            "facility_name": assessment.facility.display_name,
            "state": assessment.facility.state,
            "cms_processing_date": assessment.facility.processing_date,
            "overall_rating": rating_value(assessment, "Overall Star Rating"),
            "health_inspection_rating": rating_value(assessment, "Health Inspection"),
            "staffing_rating": rating_value(assessment, "Staffing"),
            "qm_rating": rating_value(assessment, "Quality of Resident Care"),
            "str_hospitalization": metric_value(metrics, "str_hospitalization"),
            "str_ed_visit": metric_value(metrics, "str_ed_visit"),
            "lt_hospitalization": metric_value(metrics, "lt_hospitalization"),
            "lt_ed_visit": metric_value(metrics, "lt_ed_visit"),
            "opportunity_score": assessment.opportunity.score,
            "opportunity_tier": assessment.opportunity.tier,
            "pdf_generated": True,
            "docx_generated": True,
            "api_latency_ms": assessment.api_latency_ms,
            "api_status": "success",
            "missing_fields_json": json.dumps([issue.model_dump() for issue in assessment.data_quality]),
        }
        errors = client.insert_rows_json(table_id, [row])
        if errors:
            return f"failed: {errors}"
        return "logged"
    except Exception as exc:
        return f"failed: {exc}"


def rating_value(assessment: AssessmentResponse, label: str) -> int | None:
    for rating in assessment.ratings:
        if rating.label == label:
            return rating.value
    return None


def metric_value(metrics: dict[str, dict[str, Any]], key: str) -> float | None:
    metric = metrics.get(key)
    if not metric:
        return None
    return metric.get("facility")

