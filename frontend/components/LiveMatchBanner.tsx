"use client";

import { useEffect, useState } from "react";
import { getLiveMatch } from "@/lib/api";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import type { LiveMatchOut } from "@/lib/types";
import { ProbabilityBar } from "./ProbabilityBar";

const POLL_INTERVAL_MS = 35_000;

export function LiveMatchBanner() {
  const { dict } = useLocale();
  const [match, setMatch] = useState<LiveMatchOut | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const result = await getLiveMatch();
        if (!cancelled) setMatch(result);
      } catch {
        // A failed poll (e.g. backend cold start) just skips this tick —
        // the banner keeps showing its last known state until it recovers.
      }
    }

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (!match) return null;

  const opponentLabel = match.opponent;
  const scoreLabel =
    match.home_away === "H" ? `Juventus ${match.home_goals}-${match.away_goals} ${opponentLabel}` : `${opponentLabel} ${match.home_goals}-${match.away_goals} Juventus`;

  return (
    <div className="card live-banner">
      <div className="live-banner__header">
        <span className="live-banner__score">{scoreLabel}</span>
        <span className="badge badge--live">{match.status === "PAUSED" ? dict.live.halftime : dict.live.badge}</span>
      </div>
      <ProbabilityBar
        win={match.probabilities.win}
        draw={match.probabilities.draw}
        loss={match.probabilities.loss}
        opponentLabel={opponentLabel}
        title={dict.live.probTitle}
        footnote={dict.live.approxNote}
        drawLabel={dict.brief.drawLabel}
      />
    </div>
  );
}
