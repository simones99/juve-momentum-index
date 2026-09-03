"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MomentumPoint } from "@/lib/types";

const ACCENT = "#cdb079";
const GRID_LINE = "rgba(255, 255, 255, 0.08)";
const TICK_COLOR = "rgba(245, 245, 247, 0.4)";

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
      <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <defs>
          <linearGradient id="momentumFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={ACCENT} stopOpacity={0.3} />
            <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_LINE} />
        <XAxis dataKey="date" tick={{ fontSize: 12, fill: TICK_COLOR }} axisLine={{ stroke: GRID_LINE }} tickLine={false} />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 12, fill: TICK_COLOR }}
          axisLine={{ stroke: GRID_LINE }}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "rgba(20, 20, 23, 0.92)",
            border: "1px solid rgba(255,255,255,0.14)",
            borderRadius: 10,
            fontSize: 12,
          }}
          labelStyle={{ color: "#f5f5f7" }}
          itemStyle={{ color: ACCENT }}
          formatter={(value) => [`${value}`, "Momentum Index"]}
          labelFormatter={(_, payload) => {
            const p = payload?.[0]?.payload as { date: string; opponent: string } | undefined;
            return p ? `${p.date} vs ${p.opponent}` : "";
          }}
        />
        <Area
          type="monotone"
          dataKey="momentum"
          stroke={ACCENT}
          strokeWidth={2.5}
          fill="url(#momentumFill)"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
