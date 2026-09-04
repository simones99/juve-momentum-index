"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AwayFixtureOut } from "@/lib/types";
import { useLocale } from "@/lib/i18n/LocaleProvider";

const WIN = "#34c759";
const LOSS = "#ff453a";
const GRID_LINE = "rgba(255, 255, 255, 0.08)";
const TICK_COLOR = "rgba(245, 245, 247, 0.4)";

export function AwayTripsChart({ fixtures }: { fixtures: AwayFixtureOut[] }) {
  const { dict } = useLocale();
  const scored = fixtures.filter((f) => f.effort_score !== null);
  if (scored.length === 0) {
    return <div className="empty-state">{dict.trasferte.noTripDataAvailable}</div>;
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
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fontSize: 12, fill: TICK_COLOR }}
          axisLine={{ stroke: GRID_LINE }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="opponent"
          width={110}
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
          formatter={(value, _name, item) => [
            `${value} — ${item.payload.feasible ? dict.trasferte.feasible : dict.trasferte.notFeasible}`,
            dict.trasferte.difficultyTitle,
          ]}
        />
        <Bar dataKey="effort" radius={[0, 6, 6, 0]}>
          {data.map((d) => (
            <Cell key={d.opponent} fill={d.feasible ? WIN : LOSS} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
