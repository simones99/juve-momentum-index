import { getCommunityPredictionStats, getPredictionStats } from "@/lib/api";
import { KpiCard } from "@/components/KpiCard";
import { getDeviceId } from "@/lib/deviceId";
import { getDictionary } from "@/lib/i18n/server";

function formatAccuracy(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

export default async function PredictionsPage() {
  const { dict } = await getDictionary();
  const deviceId = await getDeviceId();
  const [stats, communityStats] = await Promise.all([
    deviceId ? getPredictionStats(deviceId).catch(() => null) : Promise.resolve(null),
    getCommunityPredictionStats().catch(() => null),
  ]);

  return (
    <>
      <h1>{dict.predictions.pageTitle}</h1>
      <p className="subtitle">{dict.predictions.pageSubtitle}</p>

      {!stats || stats.total_resolved === 0 ? (
        <div className="card empty-state">{dict.predictions.noStatsYet}</div>
      ) : (
        <div className="kpi-row">
          <KpiCard label={dict.predictions.totalResolved} value={String(stats.total_resolved)} />
          <KpiCard label={dict.predictions.userAccuracy} value={formatAccuracy(stats.user_accuracy)} />
          <KpiCard label={dict.predictions.modelAccuracy} value={formatAccuracy(stats.model_accuracy)} />
        </div>
      )}

      {communityStats && communityStats.total_resolved > 0 && (
        <>
          <h2>{dict.predictions.communityTitle}</h2>
          <div className="kpi-row">
            <KpiCard label={dict.predictions.totalPredictors} value={String(communityStats.total_predictors)} />
            <KpiCard
              label={dict.predictions.communityAccuracy}
              value={formatAccuracy(communityStats.community_accuracy)}
            />
            <KpiCard label={dict.predictions.modelAccuracy} value={formatAccuracy(communityStats.model_accuracy)} />
          </div>
        </>
      )}
    </>
  );
}
