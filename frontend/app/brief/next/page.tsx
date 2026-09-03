import { ApiError, getNextMatchBrief } from "@/lib/api";
import { MatchBriefCard } from "@/components/MatchBriefCard";

export default async function NextMatchBriefPage() {
  let brief;
  try {
    brief = await getNextMatchBrief();
  } catch (err) {
    if (err instanceof ApiError) {
      return (
        <>
          <h1>Match Brief</h1>
          <div className="card empty-state">
            Nessuna partita programmata trovata nel dataset al momento.
          </div>
        </>
      );
    }
    throw err;
  }

  return (
    <>
      <h1>Match Brief</h1>
      <p className="subtitle">Anteprima basata sulle ultime partite della Juventus.</p>
      <MatchBriefCard brief={brief} />
    </>
  );
}
