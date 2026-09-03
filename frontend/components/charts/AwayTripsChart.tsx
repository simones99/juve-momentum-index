"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AwayFixtureOut } from "@/lib/types";

export function AwayTripsChart({ fixtures }: { fixtures: AwayFixtureOut[] }) {
  const scored = fixtures.filter((f) => f.effort_score !== null);
  if (scored.length === 0) {
    return <div className="empty-state">Nessuna trasferta con dati di viaggio disponibili.</div>;
  }

  const data = [...scored]
    .sort((a, b) => (a.effort_score as number) - (b.effort_score as number))
    .map((f) => ({
      opponent: f.opponent,
      effort: Math.round((f.effort_score as number) * 10) / 10,
      feasible: f.day_trip_feasible,
    }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 44)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 4 }}>
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="opponent" width={110} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value, _name, item) => [
            `${value} — ${item.payload.feasible ? "andata/ritorno in giornata" : "richiede pernottamento"}`,
            "Difficoltà",
          ]}
        />
        <Bar dataKey="effort" radius={[0, 6, 6, 0]}>
          {data.map((d) => (
            <Cell key={d.opponent} fill={d.feasible ? "#1a7f37" : "#cf222e"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
