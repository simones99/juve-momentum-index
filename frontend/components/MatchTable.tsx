"use client";

import { useRouter } from "next/navigation";
import type { MatchOut } from "@/lib/types";
import { ResultBadge } from "./ResultBadge";
import { TeamCrest } from "./TeamCrest";
import { useLocale } from "@/lib/i18n/LocaleProvider";

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function MatchTable({ matches }: { matches: MatchOut[] }) {
  const router = useRouter();
  const { locale, dict } = useLocale();

  if (matches.length === 0) {
    return <div className="empty-state">{dict.matches.emptyState}</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>{dict.matches.table.date}</th>
          <th>{dict.matches.table.competition}</th>
          <th>{dict.matches.table.home}</th>
          <th>{dict.matches.table.away}</th>
          <th>{dict.matches.table.result}</th>
          <th>{dict.matches.table.outcome}</th>
        </tr>
      </thead>
      <tbody>
        {matches.map((m) => (
          <tr key={m.id} onClick={() => router.push(`/matches/${m.id}`)}>
            <td>
              {formatDate(m.match_date, locale)}
              {m.is_approximate_date && (
                <span className="badge badge--approx" style={{ marginLeft: 6 }} title={dict.matches.table.approximateDate}>
                  {dict.matches.table.approximateDate}
                </span>
              )}
            </td>
            <td>{m.competition_code}</td>
            <td>
              <TeamCrest url={m.home_crest_url} name={m.home_team} />
              {m.home_team}
            </td>
            <td>
              <TeamCrest url={m.away_crest_url} name={m.away_team} />
              {m.away_team}
            </td>
            <td>
              {m.home_goals !== null && m.away_goals !== null ? `${m.home_goals}-${m.away_goals}` : "—"}
            </td>
            <td>
              <ResultBadge result={m.result} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
