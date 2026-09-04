import { getCompetitions, getMomentumSeries, getSeasons } from "@/lib/api";
import { EloMomentumChart } from "@/components/charts/EloMomentumChart";
import { ResultBadge } from "@/components/ResultBadge";
import { getDictionary } from "@/lib/i18n/server";

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default async function MomentumDetailsPage({
  searchParams,
}: {
  searchParams: Promise<{
    season?: string;
    competition?: string;
    home_away?: string;
    from?: string;
    to?: string;
  }>;
}) {
  const params = await searchParams;
  const [{ locale, dict }, series, seasons, competitions] = await Promise.all([
    getDictionary(),
    getMomentumSeries({
      season: params.season,
      competition: params.competition,
      from: params.from,
      to: params.to,
    }),
    getSeasons(),
    getCompetitions(),
  ]);

  const filtered = params.home_away
    ? series.filter((p) => p.home_away === params.home_away)
    : series;

  return (
    <>
      <h1>{dict.nav.momentumDetails}</h1>
      <p className="subtitle">{dict.momentum.subtitle}</p>

      <form method="GET" className="filters">
        <select name="season" defaultValue={params.season ?? ""}>
          <option value="">{dict.common.allSeasons}</option>
          {seasons.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select name="competition" defaultValue={params.competition ?? ""}>
          <option value="">{dict.common.allCompetitions}</option>
          {competitions.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name}
            </option>
          ))}
        </select>
        <select name="home_away" defaultValue={params.home_away ?? ""}>
          <option value="">{dict.momentum.homeAwaySelect}</option>
          <option value="H">{dict.common.home}</option>
          <option value="A">{dict.common.away}</option>
        </select>
        <button type="submit">{dict.common.filter}</button>
      </form>

      <div className="card section">
        <h2>{dict.momentum.eloVsMomentum}</h2>
        <EloMomentumChart series={filtered} />
      </div>

      <div className="card">
        <h2>{dict.momentum.matchDetailTitle}</h2>
        {filtered.length === 0 ? (
          <div className="empty-state">{dict.momentum.emptyState}</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>{dict.momentum.table.date}</th>
                <th>{dict.momentum.table.opponent}</th>
                <th>{dict.momentum.table.homeAway}</th>
                <th>{dict.momentum.table.result}</th>
                <th>{dict.momentum.table.eloBeforeAfter}</th>
                <th>{dict.momentum.table.momentum}</th>
              </tr>
            </thead>
            <tbody>
              {[...filtered].reverse().map((p) => (
                <tr key={p.match_id}>
                  <td>{formatDate(p.match_date, locale)}</td>
                  <td>{p.opponent}</td>
                  <td>{p.home_away === "H" ? dict.common.home : dict.common.away}</td>
                  <td>
                    <ResultBadge result={p.result} />
                  </td>
                  <td>
                    {Math.round(p.elo_before)} → {Math.round(p.elo_after)}
                  </td>
                  <td>{p.momentum_index.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
