"use client";

import { useMemo, useState } from "react";
import { ApiError, getAwayFixtures } from "@/lib/api";
import type { AwayFixtureOut, AwayFixturesResponse } from "@/lib/types";
import { AwayTripsChart } from "@/components/charts/AwayTripsChart";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import { TeamCrest } from "@/components/TeamCrest";

type SortKey = "match_date" | "distance_km" | "effort_score";

function formatDateTime(iso: string, locale: string): string {
  return new Date(iso).toLocaleString(locale === "en" ? "en-GB" : "it-IT", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function TrasferteExplorer() {
  const { locale, dict } = useLocale();
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
      setError(err instanceof ApiError ? err.message : dict.trasferte.errorGeneric);
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
          placeholder={dict.trasferte.searchPlaceholder}
          value={city}
          onChange={(e) => setCity(e.target.value)}
          style={{ minWidth: 240 }}
        />
        <button type="submit" disabled={loading}>
          {loading ? dict.trasferte.searchingButton : dict.trasferte.searchButton}
        </button>
      </form>

      {error && (
        <div className="card" style={{ marginBottom: 20, color: "var(--loss)" }}>
          {error}
        </div>
      )}

      {!result && !error && !loading && <div className="empty-state">{dict.trasferte.promptEmptyState}</div>}

      {result && (
        <>
          <p className="subtitle">
            {dict.trasferte.departureLabel(result.from_location.display_name)} —{" "}
            {dict.trasferte.tripsCountLabel(result.fixtures.length)}
          </p>

          {result.fixtures.length === 0 ? (
            <div className="empty-state">{dict.trasferte.noTripsScheduled}</div>
          ) : (
            <>
              <div className="card section">
                <h2>{dict.trasferte.difficultyTitle}</h2>
                <AwayTripsChart fixtures={result.fixtures} />
              </div>

              <div className="card">
                <table>
                  <thead>
                    <tr>
                      <th onClick={() => toggleSort("match_date")} style={{ cursor: "pointer" }}>
                        {dict.trasferte.table.date} {sortKey === "match_date" ? (sortAsc ? "↑" : "↓") : ""}
                      </th>
                      <th>{dict.trasferte.table.opponent}</th>
                      <th>{dict.trasferte.table.stadium}</th>
                      <th onClick={() => toggleSort("distance_km")} style={{ cursor: "pointer" }}>
                        {dict.trasferte.table.distance} {sortKey === "distance_km" ? (sortAsc ? "↑" : "↓") : ""}
                      </th>
                      <th>{dict.trasferte.table.travelDuration}</th>
                      <th onClick={() => toggleSort("effort_score")} style={{ cursor: "pointer" }}>
                        {dict.trasferte.table.difficulty} {sortKey === "effort_score" ? (sortAsc ? "↑" : "↓") : ""}
                      </th>
                      <th>{dict.trasferte.table.dayTrip}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedFixtures.map((f) => (
                      <tr key={f.match_id}>
                        <td>{formatDateTime(f.match_date, locale)}</td>
                        <td>
                          <TeamCrest url={f.crest_url} name={f.opponent} />
                          {f.opponent}
                        </td>
                        <td>
                          {f.stadium ?? "—"}
                          {f.stadium_city ? `, ${f.stadium_city}` : ""}
                        </td>
                        <td>{f.distance_km !== null ? `${Math.round(f.distance_km)} km` : "—"}</td>
                        <td>
                          {f.duration_hours !== null
                            ? `${f.duration_hours.toFixed(1)} h${f.is_estimated ? dict.trasferte.estimateSuffix : ""}`
                            : "—"}
                        </td>
                        <td>{f.effort_score !== null ? Math.round(f.effort_score) : "—"}</td>
                        <td>
                          {f.day_trip_feasible === null ? (
                            "—"
                          ) : f.day_trip_feasible ? (
                            <span className="badge badge--W">{dict.trasferte.yes}</span>
                          ) : (
                            <span className="badge badge--L">{dict.trasferte.no}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 12 }}>
                {dict.trasferte.disclaimer}
              </p>
            </>
          )}
        </>
      )}
    </>
  );
}
