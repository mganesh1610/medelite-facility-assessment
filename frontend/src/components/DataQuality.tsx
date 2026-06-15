import { Info, ShieldAlert } from "lucide-react";
import type { DataQualityIssue } from "../types";

export function DataQuality({ issues }: { issues: DataQualityIssue[] }) {
  if (!issues.length) {
    return (
      <section className="quality-card clean">
        <Info size={18} aria-hidden="true" />
        <span>No data quality warnings detected.</span>
      </section>
    );
  }
  return (
    <section className="quality-card">
      <div className="section-heading inline">
        <div>
          <span className="kicker">QA</span>
          <h2>Data Quality</h2>
        </div>
        <ShieldAlert size={22} aria-hidden="true" />
      </div>
      <ul>
        {issues.map((issue) => (
          <li className={issue.severity} key={`${issue.field}-${issue.message}`}>
            <strong>{issue.field}</strong>
            <span>{issue.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

