import type { BriefData, BriefResponse } from "@/lib/types";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { getDictionary } from "@/lib/i18n/server";
import { ResultBadge } from "./ResultBadge";
import { TrendIcon } from "./TrendIcon";

function ProbabilityBar({ data, dict }: { data: BriefData; dict: Dictionary }) {
  if (data.win_probability === null || data.draw_probability === null || data.loss_probability === null) {
    return null;
  }
  const win = data.win_probability * 100;
  const draw = data.draw_probability * 100;
  const loss = data.loss_probability * 100;
  const opponentLabel = data.opponent ?? "";
  const title = data.kind === "pre" ? dict.brief.probTitlePre : dict.brief.probTitlePost;

  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 6 }}>{title}</div>
      <div style={{ display: "flex", height: 10, borderRadius: 999, overflow: "hidden" }}>
        <div style={{ width: `${win}%`, background: "var(--win)" }} title={`Juve ${win.toFixed(0)}%`} />
        <div
          style={{ width: `${draw}%`, background: "var(--draw)" }}
          title={`${dict.brief.drawLabel} ${draw.toFixed(0)}%`}
        />
        <div style={{ width: `${loss}%`, background: "var(--loss)" }} title={`${opponentLabel} ${loss.toFixed(0)}%`} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: "0.8rem" }}>
        <span>Juve {win.toFixed(0)}%</span>
        <span style={{ color: "var(--text-muted)" }}>
          {dict.brief.drawLabel} {draw.toFixed(0)}%
        </span>
        <span>{opponentLabel} {loss.toFixed(0)}%</span>
      </div>
      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 6 }}>{dict.brief.basedOnHistory}</div>
    </div>
  );
}

export async function MatchBriefCard({ brief }: { brief: BriefResponse }) {
  const { data } = brief;
  const { dict } = await getDictionary();

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <h2 style={{ margin: 0 }}>
          {data.kind === "pre" ? dict.brief.preTitle : dict.brief.postTitle}
          {data.opponent ? ` — vs ${data.opponent}` : ""}
        </h2>
        <span className={`badge ${brief.llm_used ? "badge--ai" : "badge--template"}`}>
          {brief.llm_used ? dict.brief.aiEnhanced : dict.brief.template}
        </span>
      </div>

      <ProbabilityBar data={data} dict={dict} />

      <div className="brief-text">
        {brief.display_text.map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>

      <div className="kpi-row" style={{ marginTop: 18 }}>
        {data.result && (
          <div className="kpi-card">
            <div className="kpi-card__label">{dict.brief.resultLabel}</div>
            <div className="kpi-card__value">
              {data.goals_for}-{data.goals_against} <ResultBadge result={data.result} />
            </div>
          </div>
        )}
        {data.avg_momentum !== null && (
          <div className="kpi-card">
            <div className="kpi-card__label">{dict.brief.momentumIndexLabel}</div>
            <div className="kpi-card__value">{data.avg_momentum.toFixed(1)}</div>
          </div>
        )}
        {data.elo_before !== null && data.elo_after !== null && (
          <div className="kpi-card">
            <div className="kpi-card__label">{dict.brief.eloLabel}</div>
            <div className="kpi-card__value">
              {Math.round(data.elo_before)} → {Math.round(data.elo_after)}
            </div>
          </div>
        )}
        {data.elo_trend && (
          <div className="kpi-card">
            <div className="kpi-card__label">{dict.brief.trendEloLabel}</div>
            <div className="kpi-card__value" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <TrendIcon trend={data.elo_trend} />
              {dict.brief.trend[data.elo_trend]}
            </div>
          </div>
        )}
      </div>

      {brief.llm_error && (
        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 10 }}>{dict.brief.aiUnavailableNote}</p>
      )}
    </div>
  );
}
