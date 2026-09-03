"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { CompetitionOut } from "@/lib/types";

function useUpdateParam() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  return (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.push(`${pathname}?${params.toString()}`);
  };
}

export function SeasonFilter({ seasons, current }: { seasons: string[]; current?: string }) {
  const updateParam = useUpdateParam();
  return (
    <div className="filters">
      <select value={current ?? ""} onChange={(e) => updateParam("season", e.target.value)}>
        <option value="">Tutte le stagioni</option>
        {seasons.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
    </div>
  );
}

export function MatchFilters({
  seasons,
  competitions,
  current,
}: {
  seasons: string[];
  competitions: CompetitionOut[];
  current: { season?: string; competition?: string; home_away?: string; result?: string; opponent?: string };
}) {
  const updateParam = useUpdateParam();

  return (
    <div className="filters">
      <select value={current.season ?? ""} onChange={(e) => updateParam("season", e.target.value)}>
        <option value="">Tutte le stagioni</option>
        {seasons.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <select value={current.competition ?? ""} onChange={(e) => updateParam("competition", e.target.value)}>
        <option value="">Tutte le competizioni</option>
        {competitions.map((c) => (
          <option key={c.code} value={c.code}>
            {c.name}
          </option>
        ))}
      </select>
      <select value={current.home_away ?? ""} onChange={(e) => updateParam("home_away", e.target.value)}>
        <option value="">Casa/Trasferta</option>
        <option value="H">Casa</option>
        <option value="A">Trasferta</option>
      </select>
      <select value={current.result ?? ""} onChange={(e) => updateParam("result", e.target.value)}>
        <option value="">Tutti i risultati</option>
        <option value="W">Vittoria</option>
        <option value="D">Pareggio</option>
        <option value="L">Sconfitta</option>
      </select>
      <input
        type="text"
        placeholder="Avversario"
        defaultValue={current.opponent ?? ""}
        onBlur={(e) => updateParam("opponent", e.target.value)}
      />
    </div>
  );
}
