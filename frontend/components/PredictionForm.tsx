"use client";

import { useState, useTransition } from "react";
import { submitPrediction } from "@/lib/api";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import type { PredictionOut, PredictionOutcome } from "@/lib/types";

const OUTCOMES: PredictionOutcome[] = ["HOME", "DRAW", "AWAY"];

export function PredictionForm({
  matchId,
  deviceId,
  existingPrediction,
}: {
  matchId: number;
  deviceId: string;
  existingPrediction: PredictionOut | null;
}) {
  const { dict } = useLocale();
  const [prediction, setPrediction] = useState<PredictionOut | null>(existingPrediction);
  const [error, setError] = useState(false);
  const [isPending, startTransition] = useTransition();

  const outcomeLabel: Record<PredictionOutcome, string> = {
    HOME: dict.predictions.home,
    DRAW: dict.predictions.draw,
    AWAY: dict.predictions.away,
  };

  function handlePick(outcome: PredictionOutcome) {
    setError(false);
    startTransition(async () => {
      try {
        const result = await submitPrediction(matchId, outcome, deviceId);
        setPrediction(result);
      } catch {
        setError(true);
      }
    });
  }

  return (
    <div className="card">
      <span className="sidebar__widget-label">{dict.predictions.formTitle}</span>
      <div className="lang-toggle" role="group" aria-label={dict.predictions.formTitle} style={{ marginTop: 8 }}>
        {OUTCOMES.map((outcome) => (
          <button
            key={outcome}
            type="button"
            disabled={isPending}
            className={`lang-toggle__btn${prediction?.predicted_outcome === outcome ? " lang-toggle__btn--active" : ""}`}
            onClick={() => handlePick(outcome)}
          >
            {outcomeLabel[outcome]}
          </button>
        ))}
      </div>
      {prediction && !error && (
        <span style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6, display: "block" }}>
          {dict.predictions.submitted}
        </span>
      )}
      {error && (
        <span style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6, display: "block" }}>
          {dict.predictions.error}
        </span>
      )}
    </div>
  );
}
