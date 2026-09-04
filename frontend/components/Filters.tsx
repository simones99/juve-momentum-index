"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { CompetitionOut } from "@/lib/types";
import { useLocale } from "@/lib/i18n/LocaleProvider";

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
  const { dict } = useLocale();
  return (
    <div className="filters">
      <select value={current ?? ""} onChange={(e) => updateParam("season", e.target.value)}>
        <option value="">{dict.common.allSeasons}</option>
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
  const { dict } = useLocale();

  return (
    <div className="filters">
      <select value={current.season ?? ""} onChange={(e) => updateParam("season", e.target.value)}>
        <option value="">{dict.common.allSeasons}</option>
        {seasons.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <select value={current.competition ?? ""} onChange={(e) => updateParam("competition", e.target.value)}>
        <option value="">{dict.common.allCompetitions}</option>
        {competitions.map((c) => (
          <option key={c.code} value={c.code}>
            {c.name}
          </option>
        ))}
      </select>
      <select value={current.home_away ?? ""} onChange={(e) => updateParam("home_away", e.target.value)}>
        <option value="">{dict.momentum.homeAwaySelect}</option>
        <option value="H">{dict.common.home}</option>
        <option value="A">{dict.common.away}</option>
      </select>
      <select value={current.result ?? ""} onChange={(e) => updateParam("result", e.target.value)}>
        <option value="">{dict.matches.filters.allResults}</option>
        <option value="W">{dict.matches.filters.win}</option>
        <option value="D">{dict.matches.filters.draw}</option>
        <option value="L">{dict.matches.filters.loss}</option>
      </select>
      <input
        type="text"
        placeholder={dict.matches.filters.opponentPlaceholder}
        defaultValue={current.opponent ?? ""}
        onBlur={(e) => updateParam("opponent", e.target.value)}
      />
    </div>
  );
}
