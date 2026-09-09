import { ApiError, getNextMatchBrief, getPredictionForMatch, getUpcomingMatches } from "@/lib/api";
import { MatchBriefCard } from "@/components/MatchBriefCard";
import { PredictionForm } from "@/components/PredictionForm";
import { getDeviceId } from "@/lib/deviceId";
import { getDictionary } from "@/lib/i18n/server";

export default async function NextMatchBriefPage() {
  const { locale, dict } = await getDictionary();

  let brief;
  try {
    brief = await getNextMatchBrief(locale);
  } catch (err) {
    if (err instanceof ApiError) {
      return (
        <>
          <h1>{dict.brief.title}</h1>
          <div className="card empty-state">{dict.brief.noBriefFound}</div>
        </>
      );
    }
    throw err;
  }

  const deviceId = await getDeviceId();
  const [nextMatch] = await getUpcomingMatches(1).catch(() => []);
  const existingPrediction =
    nextMatch && deviceId ? await getPredictionForMatch(nextMatch.id, deviceId).catch(() => null) : null;

  return (
    <>
      <h1>{dict.brief.title}</h1>
      <p className="subtitle">{dict.brief.subtitle}</p>
      <MatchBriefCard brief={brief} />
      {nextMatch && deviceId && (
        <PredictionForm matchId={nextMatch.id} deviceId={deviceId} existingPrediction={existingPrediction} />
      )}
    </>
  );
}
