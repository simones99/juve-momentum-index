import type { BriefResponse } from "@/lib/types";
import { ResultBadge } from "./ResultBadge";

const TREND_LABELS: Record<string, string> = { up: "in crescita", down: "in calo", flat: "stabile" };

export function MatchBriefCard({ brief }: { brief: BriefResponse }) {
  const { data } = brief;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <h2 style={{ margin: 0 }}>
          {data.kind === "pre" ? "Brief pre-partita" : "Brief post-partita"}
          {data.opponent ? ` — vs ${data.opponent}` : ""}
        </h2>
        <span className={`badge ${brief.llm_used ? "badge--ai" : "badge--template"}`}>
          {brief.llm_used ? "AI-enhanced" : "Template"}
        </span>
      </div>

      <div className="brief-text">
        {brief.display_text.map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>

      <div className="kpi-row" style={{ marginTop: 18 }}>
        {data.result && (
          <div className="kpi-card">
            <div className="kpi-card__label">Risultato</div>
            <div className="kpi-card__value">
              {data.goals_for}-{data.goals_against} <ResultBadge result={data.result} />
            </div>
          </div>
        )}
        {data.avg_momentum !== null && (
          <div className="kpi-card">
            <div className="kpi-card__label">Momentum Index</div>
            <div className="kpi-card__value">{data.avg_momentum.toFixed(1)}</div>
          </div>
        )}
        {data.elo_before !== null && data.elo_after !== null && (
          <div className="kpi-card">
            <div className="kpi-card__label">Elo</div>
            <div className="kpi-card__value">
              {Math.round(data.elo_before)} → {Math.round(data.elo_after)}
            </div>
          </div>
        )}
        {data.elo_trend && (
          <div className="kpi-card">
            <div className="kpi-card__label">Trend Elo</div>
            <div className="kpi-card__value">{TREND_LABELS[data.elo_trend]}</div>
          </div>
        )}
      </div>

      {brief.llm_error && (
        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 10 }}>
          Nota: generazione AI non disponibile in questo momento, mostrato il testo template.
        </p>
      )}
    </div>
  );
}
