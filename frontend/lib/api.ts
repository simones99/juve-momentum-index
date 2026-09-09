import type {
  AwayFixturesResponse,
  BriefResponse,
  CompetitionOut,
  LiveMatchOut,
  MatchListResponse,
  MatchOut,
  MomentumOverview,
  MomentumPoint,
  PredictionCommunityStats,
  PredictionOut,
  PredictionOutcome,
  PredictionStats,
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

async function apiFetch<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  headers?: Record<string, string>
): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
  }
  const response = await fetch(url.toString(), { cache: "no-store", headers });
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

async function apiPost<T>(path: string, body: unknown, headers?: Record<string, string>): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = `${path} failed with status ${response.status}`;
    try {
      const responseBody = await response.json();
      if (typeof responseBody?.detail === "string") detail = responseBody.detail;
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

export function getLiveMatch(): Promise<LiveMatchOut | null> {
  return apiFetch<LiveMatchOut | null>("/api/v1/matches/live");
}

export function subscribeToPush(subscription: PushSubscription, locale: string): Promise<{ status: string }> {
  const json = subscription.toJSON();
  return apiPost<{ status: string }>("/api/v1/push/subscribe", {
    endpoint: json.endpoint,
    keys: json.keys,
    device_id: null,
    locale,
  });
}

export function unsubscribeFromPush(endpoint: string): Promise<{ status: string }> {
  return apiPost<{ status: string }>("/api/v1/push/unsubscribe", { endpoint });
}

export function getPredictionForMatch(matchId: number, deviceId: string): Promise<PredictionOut | null> {
  return apiFetch<PredictionOut | null>("/api/v1/predictions/mine", { match_id: matchId }, { "X-Device-Id": deviceId });
}

export function getPredictionStats(deviceId: string): Promise<PredictionStats> {
  return apiFetch<PredictionStats>("/api/v1/predictions/stats", undefined, { "X-Device-Id": deviceId });
}

export function getCommunityPredictionStats(): Promise<PredictionCommunityStats> {
  return apiFetch<PredictionCommunityStats>("/api/v1/predictions/community-stats");
}

export function submitPrediction(
  matchId: number,
  predictedOutcome: PredictionOutcome,
  deviceId: string
): Promise<PredictionOut> {
  return apiPost<PredictionOut>(
    "/api/v1/predictions",
    { match_id: matchId, predicted_outcome: predictedOutcome },
    { "X-Device-Id": deviceId }
  );
}

export { ApiError };
