import Link from "next/link";
import { getCompetitions, getMatches, getSeasons } from "@/lib/api";
import { MatchFilters } from "@/components/Filters";
import { MatchTable } from "@/components/MatchTable";

const PAGE_SIZE = 20;

export default async function MatchesPage({
  searchParams,
}: {
  searchParams: Promise<{
    season?: string;
    competition?: string;
    home_away?: string;
    result?: string;
    opponent?: string;
    page?: string;
  }>;
}) {
  const sp = await searchParams;
  const page = Number(sp.page ?? "1") || 1;

  const [matches, seasons, competitions] = await Promise.all([
    getMatches({
      season: sp.season,
      competition: sp.competition,
      home_away: sp.home_away,
      result: sp.result,
      opponent: sp.opponent,
      page,
      page_size: PAGE_SIZE,
    }),
    getSeasons(),
    getCompetitions(),
  ]);

  const totalPages = Math.max(1, Math.ceil(matches.total / PAGE_SIZE));

  const buildPageHref = (targetPage: number) => {
    const urlParams = new URLSearchParams();
    if (sp.season) urlParams.set("season", sp.season);
    if (sp.competition) urlParams.set("competition", sp.competition);
    if (sp.home_away) urlParams.set("home_away", sp.home_away);
    if (sp.result) urlParams.set("result", sp.result);
    if (sp.opponent) urlParams.set("opponent", sp.opponent);
    urlParams.set("page", String(targetPage));
    return `/matches?${urlParams.toString()}`;
  };

  return (
    <>
      <h1>Matches</h1>
      <p className="subtitle">Tutte le partite della Juventus nel dataset ({matches.total} totali).</p>

      <MatchFilters
        seasons={seasons}
        competitions={competitions}
        current={{
          season: sp.season,
          competition: sp.competition,
          home_away: sp.home_away,
          result: sp.result,
          opponent: sp.opponent,
        }}
      />

      <div className="card">
        <MatchTable matches={matches.items} />
      </div>

      {totalPages > 1 && (
        <div style={{ display: "flex", gap: 8, marginTop: 16, alignItems: "center" }}>
          {page > 1 && <Link href={buildPageHref(page - 1)}>&larr; Precedente</Link>}
          <span className="subtitle" style={{ margin: 0 }}>
            Pagina {page} di {totalPages}
          </span>
          {page < totalPages && <Link href={buildPageHref(page + 1)}>Successiva &rarr;</Link>}
        </div>
      )}
    </>
  );
}
