import { TEAM_NAME } from "@/lib/constants";
import type { MatchOut } from "@/lib/types";
import { ResultBadge } from "@/components/ResultBadge";
import { getDictionary } from "@/lib/i18n/server";
import { TeamCrest } from "@/components/TeamCrest";

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
}

export async function RecentMatches({ matches }: { matches: MatchOut[] }) {
  const { locale, dict } = await getDictionary();

  if (matches.length === 0) {
    return (
      <div className="card section">
        <h2>{dict.recentMatches.title}</h2>
        <div className="empty-state">{dict.recentMatches.emptyState}</div>
      </div>
    );
  }

  return (
    <div className="card section">
      <h2>{dict.recentMatches.title}</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {matches.map((m, i) => {
          const opponent = m.home_team === TEAM_NAME ? m.away_team : m.home_team;
          const opponentCrest = m.home_team === TEAM_NAME ? m.away_crest_url : m.home_crest_url;
          const homeAway = m.home_team === TEAM_NAME ? dict.common.home : dict.common.away;
          const score = `${m.home_goals ?? "-"}-${m.away_goals ?? "-"}`;
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
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <ResultBadge result={m.result} />
                <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <span style={{ fontWeight: 600 }}>
                    <TeamCrest url={opponentCrest} name={opponent} />
                    vs {opponent}
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {m.competition} · {homeAway}
                  </span>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2, textAlign: "right" }}>
                <span style={{ fontWeight: 600 }}>{score}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {formatDate(m.match_date, locale)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
