"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MomentumPoint } from "@/lib/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
}

export function MomentumChart({ series }: { series: MomentumPoint[] }) {
  if (series.length === 0) {
    return <div className="empty-state">Nessun dato disponibile per questa selezione.</div>;
  }

  const data = series.map((p) => ({
    date: formatDate(p.match_date),
    opponent: p.opponent,
    momentum: Math.round(p.momentum_index * 10) / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e2e6" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value) => [`${value}`, "Momentum Index"]}
          labelFormatter={(_, payload) => {
            const p = payload?.[0]?.payload as { date: string; opponent: string } | undefined;
            return p ? `${p.date} vs ${p.opponent}` : "";
          }}
        />
        <Line type="monotone" dataKey="momentum" stroke="#1f6feb" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
