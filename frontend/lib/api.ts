import type {
  AwayFixturesResponse,
  BriefResponse,
  CompetitionOut,
  MatchListResponse,
  MatchOut,
  MomentumOverview,
  MomentumPoint,
} from "./types";

// Server-rendered pages run inside the Next.js server process, which — in Docker
// Compose — is a different container from the browser. There, `localhost` must
// point at the backend container's Docker network name, not back at itself.
// `API_INTERNAL_BASE_URL` (server-only, not NEXT_PUBLIC_) covers that case; the
// browser always uses the public NEXT_PUBLIC_API_BASE_URL.
const API_BASE_URL =
  typeof window === "undefined"
    ? (process.env.API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000")
    : (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000");

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
  }
  const response = await fetch(url.toString(), { cache: "no-store" });
  if (!response.ok) {
    let detail = `${path} failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // response body wasn't JSON (or empty) — keep the generic message
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export function getMomentumOverview(season?: string): Promise<MomentumOverview> {
  return apiFetch<MomentumOverview>("/api/v1/momentum/overview", { season });
}

export function getMomentumSeries(params: {
  season?: string;
  competition?: string;
  from?: string;
  to?: string;
}): Promise<MomentumPoint[]> {
  return apiFetch<MomentumPoint[]>("/api/v1/momentum/series", params);
}

export function getMatches(params: {
  season?: string;
  competition?: string;
  home_away?: string;
  opponent?: string;
  result?: string;
  page?: number;
  page_size?: number;
}): Promise<MatchListResponse> {
  return apiFetch<MatchListResponse>("/api/v1/matches", params);
}

export function getMatch(id: number): Promise<MatchOut> {
  return apiFetch<MatchOut>(`/api/v1/matches/${id}`);
}

export function getUpcomingMatches(limit = 5): Promise<MatchOut[]> {
  return apiFetch<MatchOut[]>("/api/v1/matches/upcoming", { limit });
}

export function getRecentMatches(limit = 5): Promise<MatchOut[]> {
  return apiFetch<MatchOut[]>("/api/v1/matches/recent", { limit });
}

export function getMatchBrief(id: number, lang?: string): Promise<BriefResponse> {
  return apiFetch<BriefResponse>(`/api/v1/matches/${id}/brief`, { lang });
}

export function getNextMatchBrief(lang?: string): Promise<BriefResponse> {
  return apiFetch<BriefResponse>("/api/v1/brief/next", { lang });
}

export function getSeasons(): Promise<string[]> {
  return apiFetch<string[]>("/api/v1/seasons");
}

export function getCompetitions(): Promise<CompetitionOut[]> {
  return apiFetch<CompetitionOut[]>("/api/v1/competitions");
}

export function getAwayFixtures(fromCity: string): Promise<AwayFixturesResponse> {
  return apiFetch<AwayFixturesResponse>("/api/v1/travel/away-fixtures", { from_city: fromCity });
}

export { ApiError };
