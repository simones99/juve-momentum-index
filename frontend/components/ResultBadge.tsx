"use client";

import type { ResultLetter } from "@/lib/types";
import { useLocale } from "@/lib/i18n/LocaleProvider";

export function ResultBadge({ result }: { result: ResultLetter | null }) {
  const { dict } = useLocale();
  if (!result) return <span className="badge" style={{ background: "rgba(245,245,247,0.25)" }}>-</span>;
  return <span className={`badge badge--${result}`}>{dict.resultBadge[result]}</span>;
}
