import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, Building2, Database, MapPin, RefreshCcw } from "lucide-react";
import { DataQuality } from "./components/DataQuality";
import { Header } from "./components/Header";
import { LookupPanel } from "./components/LookupPanel";
import { MetricChart } from "./components/MetricChart";
import { OpportunityPanel } from "./components/OpportunityPanel";
import { RatingCards } from "./components/RatingCards";
import { ReportPreview } from "./components/ReportPreview";
import { createAssessment, downloadReport } from "./lib/api";
import { defaultManualInputs } from "./lib/defaults";
import type { AssessmentRequest, AssessmentResponse, ManualInputs } from "./types";

export default function App() {
  const [ccn, setCcn] = useState("686123");
  const [manual, setManual] = useState<ManualInputs>(defaultManualInputs);
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const opportunityPanelRef = useRef<HTMLElement | null>(null);
  const [qualityPanelHeight, setQualityPanelHeight] = useState<number | null>(null);

  const payload = useMemo<AssessmentRequest>(() => ({ ccn, manual }), [ccn, manual]);

  function updateManual<K extends keyof ManualInputs>(key: K, value: ManualInputs[K]) {
    setManual((current) => ({ ...current, [key]: value }));
  }

  async function runAssessment() {
    setError("");
    setLoading(true);
    try {
      const result = await createAssessment(payload);
      setAssessment(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assessment failed.");
    } finally {
      setLoading(false);
    }
  }

  async function exportReport(kind: "pdf" | "docx") {
    if (!assessment) return;
    setError("");
    setExporting(true);
    try {
      await downloadReport(payload, kind, assessment.facility.display_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : `${kind.toUpperCase()} export failed.`);
    } finally {
      setExporting(false);
    }
  }

  const showDashboard = assessment && !loading;

  useLayoutEffect(() => {
    if (!showDashboard || !opportunityPanelRef.current) {
      setQualityPanelHeight(null);
      return;
    }

    const panel = opportunityPanelRef.current;
    const updateQualityHeight = () => {
      setQualityPanelHeight(Math.ceil(panel.getBoundingClientRect().height));
    };

    updateQualityHeight();
    const observer = new ResizeObserver(updateQualityHeight);
    observer.observe(panel);
    window.addEventListener("resize", updateQualityHeight);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateQualityHeight);
    };
  }, [showDashboard, assessment]);

  return (
    <div className="app-shell">
      <Header assessment={assessment} loading={loading || exporting} onExport={exportReport} />
      <main className="workspace">
        <LookupPanel
          ccn={ccn}
          manual={manual}
          loading={loading}
          onCcnChange={setCcn}
          onManualChange={updateManual}
          onSubmit={runAssessment}
        />

        <section className="dashboard" aria-live="polite">
          {error ? (
            <div className="error-banner" role="alert">
              <AlertCircle size={18} aria-hidden="true" />
              {error}
            </div>
          ) : null}

          {!showDashboard ? (
            <EmptyState loading={loading} />
          ) : (
            <>
              <section className="facility-hero">
                <div>
                  <span className="kicker">CMS Provider Information</span>
                  <h2>{assessment.facility.display_name}</h2>
                  <div className="facility-meta">
                    <span>
                      <MapPin size={16} aria-hidden="true" />
                      {assessment.facility.location}
                    </span>
                    <span>
                      <Building2 size={16} aria-hidden="true" />
                      {assessment.facility.certified_beds ?? "N/A"} certified beds
                    </span>
                    <span>
                      <Database size={16} aria-hidden="true" />
                      {assessment.cms_request_count} live CMS request{assessment.cms_request_count === 1 ? "" : "s"}
                    </span>
                  </div>
                </div>
                <a href={assessment.facility.medicare_url} target="_blank" rel="noreferrer" className="source-chip">
                  Medicare source
                </a>
              </section>

              <RatingCards ratings={assessment.ratings} />

              <div className="analytics-grid">
                <OpportunityPanel opportunity={assessment.opportunity} panelRef={opportunityPanelRef} />
                <DataQuality checks={assessment.data_quality_checks} maxHeight={qualityPanelHeight} />
              </div>

              <MetricChart metrics={assessment.metrics} />

              <ReportPreview assessment={assessment} />
            </>
          )}
        </section>
      </main>
    </div>
  );
}

function EmptyState({ loading }: { loading: boolean }) {
  return (
    <section className="empty-state">
      {loading ? <RefreshCcw className="spin" size={32} aria-hidden="true" /> : <Database size={32} aria-hidden="true" />}
      <h2>{loading ? "Fetching live CMS data" : "Assessment workbench ready"}</h2>
      <p>{loading ? "Provider, claims, and benchmark datasets are being queried server-side." : "Sample CCN 686123 is loaded with operational inputs from the case file."}</p>
    </section>
  );
}
