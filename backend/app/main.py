from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .bigquery_logger import log_assessment
from .cms_client import CmsClient, timed_assessment_fetch
from .docx_report import build_docx
from .mapping import build_assessment
from .pdf_report import build_pdf
from .schemas import AssessmentRequest, AssessmentResponse, ManualInputs


app = FastAPI(
    title="Medelite Facility Assessment API",
    version="1.0.0",
    description="CMS-backed facility assessment report generator.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cms_client = CmsClient()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/assessments", response_model=AssessmentResponse)
async def create_assessment(request: AssessmentRequest) -> AssessmentResponse:
    return await hydrate_assessment(request)


@app.post("/api/reports/pdf")
async def create_pdf_report(request: AssessmentRequest) -> Response:
    assessment = await hydrate_assessment(request)
    payload = build_pdf(assessment)
    filename = safe_filename(assessment.facility.display_name, "pdf")
    return Response(
        payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/reports/docx")
async def create_docx_report(request: AssessmentRequest) -> Response:
    assessment = await hydrate_assessment(request)
    payload = build_docx(assessment)
    filename = safe_filename(assessment.facility.display_name, "docx")
    return Response(
        payload,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/demo/{ccn}", response_model=AssessmentResponse)
async def demo_assessment(
    ccn: str,
    emr: str = Query(default="PCC"),
    current_census: int = Query(default=112),
    patient_type: str = Query(default="Long-term & Short-term"),
    previous_coverage: str = Query(default="Yes"),
    previous_provider_performance: str = Query(default="About 30 patients/day"),
    medical_coverage: str = Query(default="Optometry, PCP, Podiatry"),
) -> AssessmentResponse:
    request = AssessmentRequest(
        ccn=ccn,
        manual=ManualInputs(
            emr=emr,
            current_census=current_census,
            patient_type=patient_type,
            previous_coverage=previous_coverage if previous_coverage in {"Yes", "No"} else "",
            previous_provider_performance=previous_provider_performance,
            medical_coverage=medical_coverage,
        ),
    )
    return await hydrate_assessment(request)


async def hydrate_assessment(request: AssessmentRequest) -> AssessmentResponse:
    latency, request_count, provider, claims, state_avg, national_avg = await timed_assessment_fetch(request.ccn, cms_client)
    if not provider:
        raise HTTPException(status_code=404, detail=f"No active CMS provider found for CCN {request.ccn}.")
    assessment = build_assessment(
        request=request,
        provider=provider,
        claims_rows=claims,
        state_avg=state_avg,
        national_avg=national_avg,
        api_latency_ms=latency,
        cms_request_count=request_count,
        bigquery_logging="pending",
    )
    logging_status = log_assessment(assessment)
    assessment.bigquery_logging = logging_status
    return assessment


def safe_filename(name: str, extension: str) -> str:
    stem = "".join(char if char.isalnum() else "_" for char in name).strip("_") or "facility_assessment"
    return f"{stem[:80]}_assessment.{extension}"


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
