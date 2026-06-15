import { Gauge, TriangleAlert } from "lucide-react";
import type { OpportunityScore } from "../types";

export function OpportunityPanel({ opportunity }: { opportunity: OpportunityScore }) {
  return (
    <section className="analytics-card opportunity-card">
      <div className="section-heading inline">
        <div>
          <span className="kicker">Decision Support</span>
          <h2>Opportunity Score</h2>
        </div>
        <Gauge size={22} aria-hidden="true" />
      </div>
      <div className="score-row">
        <div className="score-number">{opportunity.score}</div>
        <div>
          <strong>{opportunity.tier}</strong>
          <div className="score-track" aria-label={`Opportunity score ${opportunity.score} out of 100`}>
            <span style={{ width: `${opportunity.score}%` }} />
          </div>
        </div>
      </div>
      <ul className="rationale-list">
        {opportunity.rationale.map((item) => (
          <li key={item}>
            <TriangleAlert size={15} aria-hidden="true" />
            {item}
          </li>
        ))}
      </ul>
      <div className="signal-grid">
        {opportunity.signals.map((signal) => (
          <div className={`signal ${signal.severity}`} key={signal.label}>
            <span>{signal.label}</span>
            <strong>{signal.value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

