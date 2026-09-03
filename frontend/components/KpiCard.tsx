export function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card__label">{label}</div>
      <div className="kpi-card__value">{value}</div>
    </div>
  );
}
