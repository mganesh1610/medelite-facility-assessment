from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.mapping import build_assessment
from app.schemas import AssessmentRequest, ManualInputs


def test_ccn_must_preserve_six_digit_text() -> None:
    assert AssessmentRequest(ccn="015009").ccn == "015009"
    with pytest.raises(ValidationError):
        AssessmentRequest(ccn="15009")


def test_build_assessment_includes_required_and_bonus_rows() -> None:
    request = AssessmentRequest(
        ccn="686123",
        manual=ManualInputs(
            facility_name_override="Kendall Lakes Internal Name",
            emr="PCC",
            current_census=112,
            patient_type="Long-term & Short-term",
            previous_coverage="Yes",
            previous_provider_performance="About 30 patients/day",
            medical_coverage="Optometry, PCP, Podiatry",
        ),
    )
    provider = {
        "provider_name": "KENDALL LAKES HEALTHCARE AND REHAB CENTER",
        "provider_address": "5280 SW 157 AVENUE",
        "citytown": "MIAMI",
        "state": "FL",
        "zip_code": "33185",
        "number_of_certified_beds": "150",
        "average_number_of_residents_per_day": "142.4",
        "overall_rating": "5",
        "health_inspection_rating": "5",
        "staffing_rating": "2",
        "qm_rating": "5",
        "processing_date": "2026-05-01",
    }
    claims = [
        {"measure_code": "521", "adjusted_score": "25.575578"},
        {"measure_code": "522", "adjusted_score": "8.094575"},
        {"measure_code": "551", "adjusted_score": "2.752503"},
        {"measure_code": "552", "adjusted_score": "0.910105"},
    ]
    state_avg = {
        "percentage_of_short_stay_residents_who_were_rehospitalized__1d02": "26.203324",
        "percentage_of_short_stay_residents_who_had_an_outpatient_em_d911": "9.157686",
        "number_of_hospitalizations_per_1000_longstay_resident_days": "2.147753",
        "number_of_outpatient_emergency_department_visits_per_1000_l_de9d": "1.156036",
    }
    national_avg = {
        "percentage_of_short_stay_residents_who_were_rehospitalized__1d02": "23.875617",
        "percentage_of_short_stay_residents_who_had_an_outpatient_em_d911": "12.013574",
        "number_of_hospitalizations_per_1000_longstay_resident_days": "1.897659",
        "number_of_outpatient_emergency_department_visits_per_1000_l_de9d": "1.798049",
    }

    assessment = build_assessment(
        request=request,
        provider=provider,
        claims_rows=claims,
        state_avg=state_avg,
        national_avg=national_avg,
        api_latency_ms=123,
        cms_request_count=3,
        bigquery_logging="disabled",
    )

    rows = {row.label: row.value for row in assessment.report_rows}
    assert assessment.facility.display_name == "Kendall Lakes Internal Name"
    assert assessment.facility.provider_name == "Kendall Lakes Healthcare And Rehab Center"
    assert rows["Name of Facility"] == "Kendall Lakes Internal Name"
    assert rows["Short Term Hospitalization"] == "25.6%"
    assert rows["STR State Avg. for Hospitalization"] == "26.2%"
    assert rows["LT Hospitalization"] == "2.75"
    assert rows["Medicare Care Compare Source"].endswith("/686123/view-all?state=FL")
    assert len(assessment.metrics) == 4
    assert assessment.opportunity.score >= 0
    assert len(assessment.data_quality_checks) == 8
    assert all(check.status == "pass" for check in assessment.data_quality_checks)
    assert assessment.data_quality == []


def test_data_quality_checks_put_missing_items_first() -> None:
    request = AssessmentRequest(
        ccn="686123",
        manual=ManualInputs(
            emr="",
            current_census=None,
            patient_type="Long-term",
            previous_coverage="",
            previous_provider_performance="",
            medical_coverage="",
        ),
    )
    provider = {
        "provider_name": "KENDALL LAKES HEALTHCARE AND REHAB CENTER",
        "provider_address": "5280 SW 157 AVENUE",
        "citytown": "MIAMI",
        "state": "FL",
        "zip_code": "33185",
        "number_of_certified_beds": "",
        "overall_rating": "",
        "health_inspection_rating": "5",
        "staffing_rating": "2",
        "qm_rating": "5",
        "processing_date": "",
    }
    assessment = build_assessment(
        request=request,
        provider=provider,
        claims_rows=[{"measure_code": "521", "adjusted_score": "25.5"}],
        state_avg={},
        national_avg={},
        api_latency_ms=123,
        cms_request_count=3,
        bigquery_logging="disabled",
    )

    statuses = [check.status for check in assessment.data_quality_checks]
    first_pass_index = statuses.index("pass")
    assert all(status == "fail" for status in statuses[:first_pass_index])
    assert all(status == "pass" for status in statuses[first_pass_index:])
    assert assessment.data_quality_checks[0].key == "processing_date"
    assert {issue.field for issue in assessment.data_quality} == {
        check.key for check in assessment.data_quality_checks if check.status == "fail"
    }
