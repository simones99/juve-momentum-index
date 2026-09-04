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
import { useLocale } from "@/lib/i18n/LocaleProvider";

const ACCENT = "#cdb079";
const ELO_LINE = "rgba(245, 245, 247, 0.6)";
const GRID_LINE = "rgba(255, 255, 255, 0.08)";
const TICK_COLOR = "rgba(245, 245, 247, 0.4)";

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
    day: "2-digit",
    month: "short",
    year: "2-digit",
  });
}

export function EloMomentumChart({ series }: { series: MomentumPoint[] }) {
  const { locale, dict } = useLocale();

  if (series.length === 0) {
    return <div className="empty-state">{dict.common.noDataForSelection}</div>;
  }

  const data = series.map((p) => ({
    date: formatDate(p.match_date, locale),
    elo: Math.round(p.elo_after),
    momentum: Math.round(p.momentum_index * 10) / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_LINE} />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: TICK_COLOR }} axisLine={{ stroke: GRID_LINE }} tickLine={false} />
        <YAxis
          yAxisId="momentum"
          domain={[0, 100]}
          tick={{ fontSize: 12, fill: TICK_COLOR }}
          axisLine={{ stroke: GRID_LINE }}
          tickLine={false}
        />
        <YAxis
          yAxisId="elo"
          orientation="right"
          domain={["auto", "auto"]}
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
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "var(--text-muted)" }} />
        <Line
          yAxisId="momentum"
          type="monotone"
          dataKey="momentum"
          name="Momentum Index"
          stroke={ACCENT}
          strokeWidth={2.5}
          dot={false}
        />
        <Line
          yAxisId="elo"
          type="monotone"
          dataKey="elo"
          name="Elo"
          stroke={ELO_LINE}
          strokeWidth={1.5}
          strokeDasharray="4 3"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
