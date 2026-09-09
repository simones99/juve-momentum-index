export function ProbabilityBar({
  win,
  draw,
  loss,
  opponentLabel,
  title,
  footnote,
  drawLabel,
}: {
  win: number;
  draw: number;
  loss: number;
  opponentLabel: string;
  title: string;
  footnote?: string;
  drawLabel: string;
}) {
  const winPct = win * 100;
  const drawPct = draw * 100;
  const lossPct = loss * 100;

  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 6 }}>{title}</div>
      <div style={{ display: "flex", height: 10, borderRadius: 999, overflow: "hidden" }}>
        <div style={{ width: `${winPct}%`, background: "var(--win)" }} title={`Juve ${winPct.toFixed(0)}%`} />
        <div
          style={{ width: `${drawPct}%`, background: "var(--draw)" }}
          title={`${drawLabel} ${drawPct.toFixed(0)}%`}
        />
        <div
          style={{ width: `${lossPct}%`, background: "var(--loss)" }}
          title={`${opponentLabel} ${lossPct.toFixed(0)}%`}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: "0.8rem" }}>
        <span>Juve {winPct.toFixed(0)}%</span>
        <span style={{ color: "var(--text-muted)" }}>
          {drawLabel} {drawPct.toFixed(0)}%
        </span>
        <span>
          {opponentLabel} {lossPct.toFixed(0)}%
        </span>
      </div>
      {footnote && <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 6 }}>{footnote}</div>}
    </div>
  );
}
