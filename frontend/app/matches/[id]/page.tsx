import { notFound } from "next/navigation";
import { ApiError, getMatch, getMatchBrief } from "@/lib/api";
import { MatchBriefCard } from "@/components/MatchBriefCard";
import { ResultBadge } from "@/components/ResultBadge";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const matchId = Number(id);
  if (Number.isNaN(matchId)) notFound();

  let match;
  try {
    match = await getMatch(matchId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const isFinished = match.status === "FINISHED";
  const brief = isFinished ? await getMatchBrief(matchId).catch(() => null) : null;

  return (
    <>
      <h1>
        {match.home_team} {match.home_goals ?? "-"}-{match.away_goals ?? "-"} {match.away_team}
      </h1>
      <p className="subtitle">
        {formatDate(match.match_date)} · {match.competition} · {match.season}
        {match.venue ? ` · ${match.venue}` : ""}{" "}
        {match.result && <ResultBadge result={match.result} />}
      </p>

      {brief ? (
        <MatchBriefCard brief={brief} />
      ) : (
        <div className="card empty-state">
          {isFinished
            ? "Brief non ancora disponibile per questa partita."
            : "Partita non ancora giocata: consulta il Brief pre-partita nella sezione dedicata."}
        </div>
      )}
    </>
  );
}
