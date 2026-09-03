import { getMomentumOverview, getSeasons } from "@/lib/api";
import { KpiCard } from "@/components/KpiCard";
import { SeasonFilter } from "@/components/Filters";
import { MomentumChart } from "@/components/charts/MomentumChart";

export default async function OverviewPage({
  searchParams,
}: {
  searchParams: Promise<{ season?: string }>;
}) {
  const params = await searchParams;
  const [overview, seasons] = await Promise.all([
    getMomentumOverview(params.season),
    getSeasons(),
  ]);

  const { series, kpi } = overview;

  return (
    <>
      <h1>Overview</h1>
      <p className="subtitle">Andamento del Momentum Index della Juventus nel tempo.</p>

      <SeasonFilter seasons={seasons} current={params.season} />

      <div className="kpi-row">
        <KpiCard label="Momentum massimo" value={kpi.max_momentum !== null ? kpi.max_momentum.toFixed(1) : "—"} />
        <KpiCard label="Momentum minimo" value={kpi.min_momentum !== null ? kpi.min_momentum.toFixed(1) : "—"} />
        <KpiCard label="Serie vittorie più lunga" value={String(kpi.longest_win_streak)} />
        <KpiCard label="Striscia attuale" value={kpi.current_streak ?? "—"} />
      </div>

      <div className="card section">
        <h2>Momentum Index nel tempo</h2>
        <MomentumChart series={series} />
      </div>
    </>
  );
}
