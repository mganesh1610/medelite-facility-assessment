import { Download, FileText, RefreshCcw } from "lucide-react";
import type { AssessmentResponse } from "../types";

type HeaderProps = {
  assessment: AssessmentResponse | null;
  loading: boolean;
  onExport: (kind: "pdf" | "docx") => void;
};

export function Header({ assessment, loading, onExport }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand-lockup">
        <img src="/infinite-logo.png" alt="INFINITE Managed by MEDELITE" />
        <div>
          <p className="eyeline">FACILITY ASSESSMENT SNAPSHOT</p>
          <h1>Report Generator</h1>
        </div>
      </div>
      <div className="header-status" aria-live="polite">
        <div>
          <span className="status-label">CMS Data</span>
          <strong>{assessment?.facility.processing_date || "Awaiting lookup"}</strong>
        </div>
        <div>
          <span className="status-label">BigQuery</span>
          <strong>{assessment?.bigquery_logging || "Not run"}</strong>
        </div>
      </div>
      <div className="header-actions">
        <button className="secondary-button" type="button" disabled={!assessment || loading} onClick={() => onExport("docx")}>
          <FileText size={18} aria-hidden="true" />
          DOCX
        </button>
        <button className="primary-button" type="button" disabled={!assessment || loading} onClick={() => onExport("pdf")}>
          {loading ? <RefreshCcw className="spin" size={18} aria-hidden="true" /> : <Download size={18} aria-hidden="true" />}
          PDF
        </button>
      </div>
    </header>
  );
}
