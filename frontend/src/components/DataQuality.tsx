import { CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import type { CSSProperties } from "react";
import type { DataQualityCheck } from "../types";

export function DataQuality({ checks, maxHeight }: { checks: DataQualityCheck[]; maxHeight?: number | null }) {
  const orderedChecks = [...checks].sort((a, b) => {
    if (a.status === b.status) return 0;
    return a.status === "fail" ? -1 : 1;
  });
  const failedCount = orderedChecks.filter((check) => check.status === "fail").length;
  const summary = failedCount ? `${failedCount} item${failedCount === 1 ? "" : "s"} need review` : "All checks passed";
  const style = maxHeight ? ({ "--quality-card-height": `${maxHeight}px` } as CSSProperties) : undefined;

  return (
    <section className="quality-card" style={style}>
      <div className="section-heading inline">
        <div>
          <span className="kicker">QA</span>
          <h2>Data Quality Checklist</h2>
        </div>
        <ShieldCheck size={22} aria-hidden="true" />
      </div>

      <div className={`quality-summary ${failedCount ? "needs-review" : "clean"}`}>
        <strong>{summary}</strong>
        <span>{orderedChecks.length} source and manual-input checks</span>
      </div>

      <ul className="qa-check-list" aria-label="Data quality checks">
        {orderedChecks.map((check) => {
          const passed = check.status === "pass";
          const Icon = passed ? CheckCircle2 : XCircle;
          return (
            <li className={`qa-check ${check.status}`} key={check.key}>
              <span className="qa-check-icon" aria-hidden="true">
                <Icon size={18} />
              </span>
              <span className="qa-check-copy">
                <span className="qa-check-title">
                  <strong>{check.label}</strong>
                  <span>{passed ? "Available" : "Missing"}</span>
                </span>
                <span className="qa-check-message">{check.message}</span>
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
