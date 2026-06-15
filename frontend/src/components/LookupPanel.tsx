import { Search, ShieldCheck } from "lucide-react";
import type { ManualInputs } from "../types";

type LookupPanelProps = {
  ccn: string;
  manual: ManualInputs;
  loading: boolean;
  onCcnChange: (value: string) => void;
  onManualChange: <K extends keyof ManualInputs>(key: K, value: ManualInputs[K]) => void;
  onSubmit: () => void;
};

export function LookupPanel({ ccn, manual, loading, onCcnChange, onManualChange, onSubmit }: LookupPanelProps) {
  return (
    <aside className="lookup-panel">
      <div className="panel-heading">
        <div>
          <span className="kicker">Report Inputs</span>
          <h2>Facility Lookup</h2>
        </div>
        <ShieldCheck size={22} aria-hidden="true" />
      </div>

      <label className="field">
        <span>CMS Certification Number</span>
        <input
          value={ccn}
          inputMode="numeric"
          maxLength={6}
          pattern="[0-9]{6}"
          onChange={(event) => onCcnChange(event.target.value.replace(/\D/g, "").slice(0, 6))}
          placeholder="686123"
        />
      </label>

      <button className="lookup-button" type="button" onClick={onSubmit} disabled={loading || ccn.length !== 6}>
        <Search size={18} aria-hidden="true" />
        {loading ? "Fetching CMS data" : "Run Assessment"}
      </button>

      <div className="field-group">
        <label className="field">
          <span>Facility Name Override</span>
          <input
            value={manual.facility_name_override}
            onChange={(event) => onManualChange("facility_name_override", event.target.value)}
            placeholder="Optional internal display name"
          />
        </label>
        <label className="field">
          <span>EMR</span>
          <input value={manual.emr} onChange={(event) => onManualChange("emr", event.target.value)} />
        </label>
        <label className="field">
          <span>Current Census</span>
          <input
            type="number"
            min={0}
            value={manual.current_census ?? ""}
            onChange={(event) => onManualChange("current_census", event.target.value ? Number(event.target.value) : null)}
          />
        </label>
        <label className="field">
          <span>Type of Patient</span>
          <input value={manual.patient_type} onChange={(event) => onManualChange("patient_type", event.target.value)} />
        </label>
        <label className="field">
          <span>Previous Coverage from Medelite</span>
          <select value={manual.previous_coverage} onChange={(event) => onManualChange("previous_coverage", event.target.value as ManualInputs["previous_coverage"])}>
            <option value="">Select</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </label>
        <label className="field">
          <span>Previous Provider Performance</span>
          <input
            value={manual.previous_provider_performance}
            onChange={(event) => onManualChange("previous_provider_performance", event.target.value)}
          />
        </label>
        <label className="field">
          <span>Medical Coverage</span>
          <input value={manual.medical_coverage} onChange={(event) => onManualChange("medical_coverage", event.target.value)} />
        </label>
      </div>
    </aside>
  );
}

