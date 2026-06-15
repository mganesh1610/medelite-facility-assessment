import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MetricComparison } from "../types";

export function MetricChart({ metrics }: { metrics: MetricComparison[] }) {
  const rows = metrics.map((metric) => ({
    label: shortLabel(metric.label),
    Facility: metric.facility,
    State: metric.state,
    National: metric.national,
    unit: metric.unit
  }));

  return (
    <section className="analytics-card chart-card">
      <div className="section-heading">
        <span className="kicker">Bonus Analytics</span>
        <h2>Facility vs State vs National</h2>
      </div>
      <div className="chart-wrap" role="img" aria-label="Grouped bar chart comparing facility hospitalization and ED metrics against state and national benchmarks">
        <ResponsiveContainer width="100%" height={330}>
          <BarChart data={rows} margin={{ top: 16, right: 8, left: -12, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip formatter={(value, name, item) => [formatValue(toNumber(value), item.payload.unit), name]} />
            <Legend />
            <Bar dataKey="Facility" fill="#1e40af" radius={[6, 6, 0, 0]} barSize={18} minPointSize={3} isAnimationActive={false} />
            <Bar dataKey="State" fill="#3b82f6" radius={[6, 6, 0, 0]} barSize={18} minPointSize={3} isAnimationActive={false} />
            <Bar dataKey="National" fill="#d97706" radius={[6, 6, 0, 0]} barSize={18} minPointSize={3} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function shortLabel(label: string) {
  return label.replace("Short Term ", "STR ").replace("Hospitalization", "Hosp.").replace("LT ", "LT ");
}

function formatValue(value: number | null, unit: "percent" | "rate") {
  if (value == null) return "Not available";
  return unit === "percent" ? `${value.toFixed(1)}%` : value.toFixed(2);
}

function toNumber(value: unknown) {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}
