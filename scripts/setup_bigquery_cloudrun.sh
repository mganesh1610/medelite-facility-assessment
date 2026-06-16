#!/usr/bin/env bash
set -euo pipefail

REGION="${REGION:-europe-west1}"
SERVICE="${SERVICE:-medelite-facility-assessment}"
DATASET="${DATASET:-medelite_case}"
TABLE="${TABLE:-facility_assessment_runs}"
LOCATION="${LOCATION:-EU}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "No Google Cloud project is configured. Run: gcloud config set project YOUR_PROJECT_ID" >&2
  exit 1
fi

echo "Project: ${PROJECT_ID}"
echo "Cloud Run service: ${SERVICE} (${REGION})"
echo "BigQuery table: ${PROJECT_ID}.${DATASET}.${TABLE}"

gcloud services enable bigquery.googleapis.com run.googleapis.com

if ! bq show --dataset "${PROJECT_ID}:${DATASET}" >/dev/null 2>&1; then
  bq --location="${LOCATION}" mk \
    --dataset \
    --description "Medelite facility assessment audit logs" \
    "${PROJECT_ID}:${DATASET}"
else
  echo "Dataset already exists: ${PROJECT_ID}:${DATASET}"
fi

if ! bq show "${PROJECT_ID}:${DATASET}.${TABLE}" >/dev/null 2>&1; then
  bq mk --table "${PROJECT_ID}:${DATASET}.${TABLE}" \
    run_id:STRING,created_at:TIMESTAMP,ccn:STRING,facility_name:STRING,state:STRING,cms_processing_date:STRING,overall_rating:INT64,health_inspection_rating:INT64,staffing_rating:INT64,qm_rating:INT64,str_hospitalization:FLOAT64,str_ed_visit:FLOAT64,lt_hospitalization:FLOAT64,lt_ed_visit:FLOAT64,opportunity_score:INT64,opportunity_tier:STRING,pdf_generated:BOOL,docx_generated:BOOL,api_latency_ms:INT64,api_status:STRING,missing_fields_json:STRING
else
  echo "Table already exists: ${PROJECT_ID}:${DATASET}.${TABLE}"
fi

RUN_SA="$(gcloud run services describe "${SERVICE}" \
  --region "${REGION}" \
  --format "value(spec.template.spec.serviceAccountName)" 2>/dev/null || true)"

if [[ -z "${RUN_SA}" ]]; then
  PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format "value(projectNumber)")"
  RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

echo "Granting BigQuery write permissions to: ${RUN_SA}"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${RUN_SA}" \
  --role "roles/bigquery.dataEditor" \
  --quiet >/dev/null

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${RUN_SA}" \
  --role "roles/bigquery.jobUser" \
  --quiet >/dev/null

gcloud run services update "${SERVICE}" \
  --region "${REGION}" \
  --update-env-vars "BIGQUERY_ENABLED=true,GCP_PROJECT_ID=${PROJECT_ID},BIGQUERY_DATASET=${DATASET},BIGQUERY_TABLE=${TABLE}"

SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format "value(status.url)")"

cat <<EOF

BigQuery logging is configured.

App URL:
${SERVICE_URL}

After running an assessment in the app, verify rows with:

bq query --use_legacy_sql=false '
SELECT created_at, ccn, facility_name, opportunity_score, opportunity_tier, api_status
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
ORDER BY created_at DESC
LIMIT 10
'
EOF
