import { getCompetitions, getMomentumSeries, getSeasons } from "@/lib/api";
import { EloMomentumChart } from "@/components/charts/EloMomentumChart";
import { ResultBadge } from "@/components/ResultBadge";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" });
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
  const [series, seasons, competitions] = await Promise.all([
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
      <h1>Momentum Details</h1>
      <p className="subtitle">Elo, forma recente e Momentum Index partita per partita.</p>

      <form method="GET" className="filters">
        <select name="season" defaultValue={params.season ?? ""}>
          <option value="">Tutte le stagioni</option>
          {seasons.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select name="competition" defaultValue={params.competition ?? ""}>
          <option value="">Tutte le competizioni</option>
          {competitions.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name}
            </option>
          ))}
        </select>
        <select name="home_away" defaultValue={params.home_away ?? ""}>
          <option value="">Casa/Trasferta</option>
          <option value="H">Casa</option>
          <option value="A">Trasferta</option>
        </select>
        <button type="submit">Filtra</button>
      </form>

      <div className="card section">
        <h2>Elo vs Momentum Index</h2>
        <EloMomentumChart series={filtered} />
      </div>

      <div className="card">
        <h2>Dettaglio partite</h2>
        {filtered.length === 0 ? (
          <div className="empty-state">Nessun dato per questa selezione.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Avversario</th>
                <th>C/T</th>
                <th>Esito</th>
                <th>Elo prima → dopo</th>
                <th>Momentum</th>
              </tr>
            </thead>
            <tbody>
              {[...filtered].reverse().map((p) => (
                <tr key={p.match_id}>
                  <td>{formatDate(p.match_date)}</td>
                  <td>{p.opponent}</td>
                  <td>{p.home_away === "H" ? "Casa" : "Trasferta"}</td>
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
