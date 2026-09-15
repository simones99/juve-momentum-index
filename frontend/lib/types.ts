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
  venue: string | null;
  status: string;
  result: ResultLetter | null;
  is_approximate_date: boolean;
  home_crest_url: string | null;
  away_crest_url: string | null;
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
  win_probability: number | null;
  draw_probability: number | null;
  loss_probability: number | null;
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

export interface ResolvedLocation {
  query: string;
  display_name: string;
  lat: number;
  lon: number;
}

export interface AwayFixtureOut {
  match_id: number;
  opponent: string;
  match_date: string;
  competition: string;
  stadium: string | null;
  stadium_city: string | null;
  crest_url: string | null;
  distance_km: number | null;
  duration_hours: number | null;
  is_estimated: boolean;
  effort_score: number | null;
  day_trip_feasible: boolean | null;
}

export interface AwayFixturesResponse {
  from_location: ResolvedLocation;
  fixtures: AwayFixtureOut[];
}

export interface LiveProbabilities {
  win: number;
  draw: number;
  loss: number;
}

export interface LiveMatchOut {
  match_id: number;
  opponent: string;
  home_away: "H" | "A";
  status: string;
  home_goals: number;
  away_goals: number;
  probabilities: LiveProbabilities;
  is_approximate: boolean;
}

export type PredictionOutcome = "HOME" | "DRAW" | "AWAY";

export interface PredictionOut {
  id: number;
  match_id: number;
  predicted_outcome: PredictionOutcome;
  model_home_prob: number;
  model_draw_prob: number;
  model_away_prob: number;
  is_correct: boolean | null;
  model_was_correct: boolean | null;
  created_at: string;
  resolved_at: string | null;
}

export interface PredictionStats {
  total_resolved: number;
  user_correct: number;
  model_correct: number;
  user_accuracy: number | null;
  model_accuracy: number | null;
  current_streak: number;
  best_streak: number;
}

export interface PredictionCommunityStats {
  total_predictors: number;
  total_resolved: number;
  community_correct: number;
  model_correct: number;
  community_accuracy: number | null;
  model_accuracy: number | null;
}

export interface HealthzResponse {
  status: string;
  last_successful_ingest_at: string | null;
}
