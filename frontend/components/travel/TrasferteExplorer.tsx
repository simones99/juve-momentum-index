"use client";

import { useMemo, useState } from "react";
import { ApiError, getAwayFixtures } from "@/lib/api";
import type { AwayFixtureOut, AwayFixturesResponse } from "@/lib/types";
import { AwayTripsChart } from "@/components/charts/AwayTripsChart";

type SortKey = "match_date" | "distance_km" | "effort_score";

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("it-IT", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function TrasferteExplorer() {
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AwayFixturesResponse | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("effort_score");
  const [sortAsc, setSortAsc] = useState(true);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!city.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAwayFixtures(city.trim());
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Errore imprevisto durante la ricerca.");
    } finally {
      setLoading(false);
    }
  }

  const sortedFixtures = useMemo(() => {
    if (!result) return [];
    const withValue = (f: AwayFixtureOut): number => {
      if (sortKey === "match_date") return new Date(f.match_date).getTime();
      const v = f[sortKey];
      return v === null ? Number.POSITIVE_INFINITY : v;
    };
    return [...result.fixtures].sort((a, b) => (withValue(a) - withValue(b)) * (sortAsc ? 1 : -1));
  }, [result, sortKey, sortAsc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  return (
    <>
      <form onSubmit={handleSearch} className="filters" style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Città di partenza (es. Ancona)"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          style={{ minWidth: 240 }}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Cerco…" : "Cerca"}
        </button>
      </form>

      {error && (
        <div className="card" style={{ marginBottom: 20, color: "var(--loss)" }}>
          {error}
        </div>
      )}

      {!result && !error && !loading && (
        <div className="empty-state">
          Inserisci una città per vedere le prossime trasferte della Juve ordinate per difficoltà.
        </div>
      )}

      {result && (
        <>
          <p className="subtitle">
            Partenza: {result.from_location.display_name} — {result.fixtures.length} trasferte in programma
          </p>

          {result.fixtures.length === 0 ? (
            <div className="empty-state">
              Nessuna trasferta programmata nel dataset al momento (serve un&apos;ingestion con calendario
              reale — vedi README).
            </div>
          ) : (
            <>
              <div className="card section">
                <h2>Difficoltà per trasferta</h2>
                <AwayTripsChart fixtures={result.fixtures} />
              </div>

              <div className="card">
                <table>
                  <thead>
                    <tr>
                      <th onClick={() => toggleSort("match_date")} style={{ cursor: "pointer" }}>
                        Data {sortKey === "match_date" ? (sortAsc ? "↑" : "↓") : ""}
                      </th>
                      <th>Avversario</th>
                      <th>Stadio</th>
                      <th onClick={() => toggleSort("distance_km")} style={{ cursor: "pointer" }}>
                        Distanza {sortKey === "distance_km" ? (sortAsc ? "↑" : "↓") : ""}
                      </th>
                      <th>Durata viaggio</th>
                      <th onClick={() => toggleSort("effort_score")} style={{ cursor: "pointer" }}>
                        Difficoltà {sortKey === "effort_score" ? (sortAsc ? "↑" : "↓") : ""}
                      </th>
                      <th>Giornata?</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedFixtures.map((f) => (
                      <tr key={f.match_id}>
                        <td>{formatDateTime(f.match_date)}</td>
                        <td>{f.opponent}</td>
                        <td>
                          {f.stadium ?? "—"}
                          {f.stadium_city ? `, ${f.stadium_city}` : ""}
                        </td>
                        <td>{f.distance_km !== null ? `${Math.round(f.distance_km)} km` : "—"}</td>
                        <td>
                          {f.duration_hours !== null
                            ? `${f.duration_hours.toFixed(1)} h${f.is_estimated ? " (stima)" : ""}`
                            : "—"}
                        </td>
                        <td>{f.effort_score !== null ? Math.round(f.effort_score) : "—"}</td>
                        <td>
                          {f.day_trip_feasible === null ? (
                            "—"
                          ) : f.day_trip_feasible ? (
                            <span className="badge badge--W">Sì</span>
                          ) : (
                            <span className="badge badge--L">No</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 12 }}>
                Stima indicativa basata su distanza/tempo di guida in auto e orario della partita — non tiene
                conto di orari treni, traffico reale o eventi. &quot;Giornata&quot; = presumibilmente
                fattibile andata e ritorno in giornata partendo non prima delle 4:00 e rientrando entro le
                2:00 di notte.
              </p>
            </>
          )}
        </>
      )}
    </>
  );
}
