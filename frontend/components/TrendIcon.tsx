type Trend = "up" | "down" | "flat";

const TREND_COLOR: Record<Trend, string> = {
  up: "var(--win)",
  down: "var(--loss)",
  flat: "var(--text-muted)",
};

const TREND_PATH: Record<Trend, string> = {
  up: "M4 15 L10 8 L14 12 L20 5 M14 5 H20 V11",
  down: "M4 9 L10 16 L14 12 L20 19 M14 19 H20 V13",
  flat: "M4 12 H20 M15 8 L20 12 L15 16",
};

export function TrendIcon({ trend, size = 18 }: { trend: Trend; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={TREND_COLOR[trend]}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label={`trend ${trend}`}
    >
      <path d={TREND_PATH[trend]} />
    </svg>
  );
}
