import { TEAM_NAME } from "@/lib/constants";
import type { MatchOut } from "@/lib/types";

function formatDateTime(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString("it-IT", { weekday: "short", day: "2-digit", month: "short" }),
    time: d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" }),
  };
}

export function UpcomingMatches({ matches }: { matches: MatchOut[] }) {
  if (matches.length === 0) {
    return (
      <div className="card section">
        <h2>Prossime partite</h2>
        <div className="empty-state">Nessuna partita in programma nel dataset al momento.</div>
      </div>
    );
  }

  return (
    <div className="card section">
      <h2>Prossime partite</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {matches.map((m, i) => {
          const opponent = m.home_team === TEAM_NAME ? m.away_team : m.home_team;
          const homeAway = m.home_team === TEAM_NAME ? "Casa" : "Trasferta";
          const { date, time } = formatDateTime(m.match_date);
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 0",
                borderBottom: i < matches.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span style={{ fontWeight: 600 }}>vs {opponent}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {m.competition} · {homeAway}
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2, textAlign: "right" }}>
                <span style={{ fontWeight: 600 }}>
                  {date} · {time}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {m.venue ?? "Sede da confermare"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
