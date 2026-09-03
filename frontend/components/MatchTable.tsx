"use client";

import { useRouter } from "next/navigation";
import type { MatchOut } from "@/lib/types";
import { ResultBadge } from "./ResultBadge";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" });
}

export function MatchTable({ matches }: { matches: MatchOut[] }) {
  const router = useRouter();

  if (matches.length === 0) {
    return <div className="empty-state">Nessuna partita trovata con questi filtri.</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Data</th>
          <th>Competizione</th>
          <th>Casa</th>
          <th>Trasferta</th>
          <th>Risultato</th>
          <th>Esito</th>
        </tr>
      </thead>
      <tbody>
        {matches.map((m) => (
          <tr key={m.id} onClick={() => router.push(`/matches/${m.id}`)}>
            <td>{formatDate(m.match_date)}</td>
            <td>{m.competition_code}</td>
            <td>{m.home_team}</td>
            <td>{m.away_team}</td>
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
