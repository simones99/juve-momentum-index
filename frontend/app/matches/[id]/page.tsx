import { notFound } from "next/navigation";
import { ApiError, getMatch, getMatchBrief } from "@/lib/api";
import { MatchBriefCard } from "@/components/MatchBriefCard";
import { ResultBadge } from "@/components/ResultBadge";
import { getDictionary } from "@/lib/i18n/server";

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const matchId = Number(id);
  if (Number.isNaN(matchId)) notFound();

  const { locale, dict } = await getDictionary();

  let match;
  try {
    match = await getMatch(matchId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const isFinished = match.status === "FINISHED";
  const brief = isFinished ? await getMatchBrief(matchId, locale).catch(() => null) : null;

  return (
    <>
      <h1>
        {match.home_team} {match.home_goals ?? "-"}-{match.away_goals ?? "-"} {match.away_team}
      </h1>
      <p className="subtitle">
        {formatDate(match.match_date, locale)} · {match.competition} · {match.season}
        {match.venue ? ` · ${match.venue}` : ""}{" "}
        {match.result && <ResultBadge result={match.result} />}
      </p>

      {brief ? (
        <MatchBriefCard brief={brief} />
      ) : (
        <div className="card empty-state">
          {isFinished ? dict.matchDetail.briefNotAvailable : dict.matchDetail.matchNotPlayedYet}
        </div>
      )}
    </>
  );
}
