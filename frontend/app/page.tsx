import { getMomentumOverview, getRecentMatches, getSeasons, getUpcomingMatches } from "@/lib/api";
import { KpiCard } from "@/components/KpiCard";
import { SeasonFilter } from "@/components/Filters";
import { MomentumChart } from "@/components/charts/MomentumChart";
import { UpcomingMatches } from "@/components/UpcomingMatches";
import { RecentMatches } from "@/components/RecentMatches";
import { getDictionary } from "@/lib/i18n/server";

export default async function OverviewPage({
  searchParams,
}: {
  searchParams: Promise<{ season?: string }>;
}) {
  const params = await searchParams;
  const [{ dict }, overview, seasons, recent, upcoming] = await Promise.all([
    getDictionary(),
    getMomentumOverview(params.season),
    getSeasons(),
    getRecentMatches(5),
    getUpcomingMatches(5),
  ]);

  const { series, kpi } = overview;

  return (
    <>
      <h1>{dict.nav.overview}</h1>
      <p className="subtitle">{dict.overview.subtitle}</p>

      <div className="grid-2">
        <RecentMatches matches={recent} />
        <UpcomingMatches matches={upcoming} />
      </div>

      <SeasonFilter seasons={seasons} current={params.season} />

      <div className="kpi-row">
        <KpiCard
          label={dict.overview.kpi.maxMomentum}
          value={kpi.max_momentum !== null ? kpi.max_momentum.toFixed(1) : "—"}
        />
        <KpiCard
          label={dict.overview.kpi.minMomentum}
          value={kpi.min_momentum !== null ? kpi.min_momentum.toFixed(1) : "—"}
        />
        <KpiCard label={dict.overview.kpi.longestWinStreak} value={String(kpi.longest_win_streak)} />
        <KpiCard label={dict.overview.kpi.currentStreak} value={kpi.current_streak ?? "—"} />
      </div>

      <div className="card section">
        <h2>{dict.overview.momentumOverTime}</h2>
        <MomentumChart series={series} />
      </div>
    </>
  );
}
