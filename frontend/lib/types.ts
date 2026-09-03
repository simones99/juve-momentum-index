export type ResultLetter = "W" | "D" | "L";

export interface MatchOut {
  id: number;
  season: string;
  competition: string;
  competition_code: string;
  match_date: string;
  home_team: string;
  away_team: string;
  home_goals: number | null;
  away_goals: number | null;
  status: string;
  result: ResultLetter | null;
}

export interface MatchListResponse {
  items: MatchOut[];
  page: number;
  page_size: number;
  total: number;
}

export interface MomentumPoint {
  match_id: number;
  match_date: string;
  season: string;
  opponent: string;
  home_away: "H" | "A";
  competition_code: string;
  result: ResultLetter | null;
  goals_for: number | null;
  goals_against: number | null;
  elo_before: number;
  elo_after: number;
  elo_normalized: number;
  points_rolling5: number | null;
  points_rolling10: number | null;
  goal_diff_rolling5: number | null;
  goal_diff_rolling10: number | null;
  momentum_index: number;
}

export interface MomentumKpi {
  max_momentum: number | null;
  min_momentum: number | null;
  longest_win_streak: number;
  current_streak: string | null;
}

export interface MomentumOverview {
  series: MomentumPoint[];
  kpi: MomentumKpi;
}

export interface BriefData {
  kind: "pre" | "post";
  opponent: string | null;
  match_id: number | null;
  matches_considered: number;
  avg_momentum: number | null;
  avg_points: number | null;
  avg_goal_diff: number | null;
  elo_trend: "up" | "down" | "flat" | null;
  result: ResultLetter | null;
  goals_for: number | null;
  goals_against: number | null;
  elo_before: number | null;
  elo_after: number | null;
  head_to_head_recent: string | null;
}

export interface BriefResponse {
  data: BriefData;
  template_text: string[];
  display_text: string[];
  llm_used: boolean;
  llm_error: string | null;
}

export interface CompetitionOut {
  code: string;
  name: string;
}
