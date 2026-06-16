export type ManualInputs = {
  facility_name_override: string;
  emr: string;
  current_census: number | null;
  patient_type: string;
  previous_coverage: "" | "Yes" | "No";
  previous_provider_performance: string;
  medical_coverage: string;
};

export type AssessmentRequest = {
  ccn: string;
  manual: ManualInputs;
};

export type FacilitySource = {
  ccn: string;
  provider_name: string;
  display_name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  location: string;
  certified_beds: number | null;
  average_residents_per_day: number | null;
  processing_date: string;
  medicare_url: string;
};

export type RatingCard = {
  label: string;
  value: number | null;
  source_field: string;
};

export type MetricComparison = {
  key: string;
  label: string;
  unit: "percent" | "rate";
  facility: number | null;
  state: number | null;
  national: number | null;
  facility_display: string;
  state_display: string;
  national_display: string;
  measure_code: string;
  source_description: string;
};

export type ReportRow = {
  label: string;
  value: string;
  source: "CMS" | "Manual" | "CMS + Manual Override" | "Derived" | "Source";
};

export type OpportunitySignal = {
  label: string;
  value: string;
  severity: "positive" | "neutral" | "warning" | "critical";
};

export type OpportunityScore = {
  score: number;
  tier: "High Outreach Priority" | "Moderate Outreach Priority" | "Monitor" | "Low Priority";
  rationale: string[];
  signals: OpportunitySignal[];
};

export type DataQualityIssue = {
  field: string;
  message: string;
  severity: "info" | "warning" | "error";
};

export type DataQualityCheck = {
  key: string;
  label: string;
  status: "pass" | "fail";
  message: string;
  severity: "success" | "warning" | "error";
};

export type AssessmentResponse = {
  facility: FacilitySource;
  ratings: RatingCard[];
  metrics: MetricComparison[];
  report_rows: ReportRow[];
  opportunity: OpportunityScore;
  data_quality: DataQualityIssue[];
  data_quality_checks: DataQualityCheck[];
  exports: {
    pdf: string;
    docx: string;
  };
  cms_request_count: number;
  api_latency_ms: number;
  bigquery_logging: string;
};
