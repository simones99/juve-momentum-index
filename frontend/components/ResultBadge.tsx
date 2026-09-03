import type { ResultLetter } from "@/lib/types";

const LABELS: Record<ResultLetter, string> = { W: "V", D: "N", L: "P" };

export function ResultBadge({ result }: { result: ResultLetter | null }) {
  if (!result) return <span className="badge" style={{ background: "rgba(245,245,247,0.25)" }}>-</span>;
  return <span className={`badge badge--${result}`}>{LABELS[result]}</span>;
}
