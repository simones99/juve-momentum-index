import type {
  BriefResponse,
  CompetitionOut,
  MatchListResponse,
  MatchOut,
  MomentumOverview,
  MomentumPoint,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
    throw new ApiError(response.status, `${path} failed with status ${response.status}`);
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

export function getMatchBrief(id: number): Promise<BriefResponse> {
  return apiFetch<BriefResponse>(`/api/v1/matches/${id}/brief`);
}

export function getNextMatchBrief(): Promise<BriefResponse> {
  return apiFetch<BriefResponse>("/api/v1/brief/next");
}

export function getSeasons(): Promise<string[]> {
  return apiFetch<string[]>("/api/v1/seasons");
}

export function getCompetitions(): Promise<CompetitionOut[]> {
  return apiFetch<CompetitionOut[]>("/api/v1/competitions");
}

export { ApiError };
