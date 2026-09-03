"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MomentumPoint } from "@/lib/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "2-digit" });
}

export function EloMomentumChart({ series }: { series: MomentumPoint[] }) {
  if (series.length === 0) {
    return <div className="empty-state">Nessun dato disponibile per questa selezione.</div>;
  }

  const data = series.map((p) => ({
    date: formatDate(p.match_date),
    elo: Math.round(p.elo_after),
    momentum: Math.round(p.momentum_index * 10) / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e2e6" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis yAxisId="momentum" domain={[0, 100]} tick={{ fontSize: 12 }} />
        <YAxis yAxisId="elo" orientation="right" domain={["auto", "auto"]} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Line
          yAxisId="momentum"
          type="monotone"
          dataKey="momentum"
          name="Momentum Index"
          stroke="#1f6feb"
          strokeWidth={2}
          dot={false}
        />
        <Line
          yAxisId="elo"
          type="monotone"
          dataKey="elo"
          name="Elo"
          stroke="#16171a"
          strokeWidth={1.5}
          strokeDasharray="4 3"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
