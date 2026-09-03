import type { ResultLetter } from "@/lib/types";

const LABELS: Record<ResultLetter, string> = { W: "V", D: "N", L: "P" };

export function ResultBadge({ result }: { result: ResultLetter | null }) {
  if (!result) return <span className="badge" style={{ background: "#9a9aa2" }}>-</span>;
  return <span className={`badge badge--${result}`}>{LABELS[result]}</span>;
}
