import { ExternalLink } from "lucide-react";
import type { AssessmentResponse } from "../types";

export function ReportPreview({ assessment }: { assessment: AssessmentResponse }) {
  return (
    <section className="report-preview">
      <div className="report-brand">
        <img src="/infinite-logo.png" alt="INFINITE Managed by MEDELITE" />
        <h2>FACILITY ASSESSMENT SNAPSHOT</h2>
        <strong>{assessment.facility.state}</strong>
      </div>
      <div className="preview-table">
        {assessment.report_rows
          .filter((row) => row.source !== "Source")
          .map((row) => (
            <div className="preview-row" key={row.label}>
              <strong>{row.label}</strong>
              <span>{row.value}</span>
            </div>
          ))}
      </div>
      <a className="source-link" href={assessment.facility.medicare_url} target="_blank" rel="noreferrer">
        <ExternalLink size={16} aria-hidden="true" />
        Medicare Care Compare source profile
      </a>
    </section>
  );
}

