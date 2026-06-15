from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    cms_timeout_seconds: float = float(os.getenv("CMS_API_TIMEOUT_SECONDS", "10"))
    cms_cache_ttl_seconds: int = int(os.getenv("CMS_CACHE_TTL_SECONDS", "21600"))
    bigquery_enabled: bool = os.getenv("BIGQUERY_ENABLED", "false").lower() == "true"
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "medelite_case")
    bigquery_table: str = os.getenv("BIGQUERY_TABLE", "facility_assessment_runs")


settings = Settings()

