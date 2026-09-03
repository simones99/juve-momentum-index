from pydantic import BaseModel


class BriefData(BaseModel):
    kind: str  # "pre" | "post"
    opponent: str | None = None
    match_id: int | None = None
    matches_considered: int
    avg_momentum: float | None = None
    avg_points: float | None = None
    avg_goal_diff: float | None = None
    elo_trend: str | None = None  # "up" | "down" | "flat"
    result: str | None = None
    goals_for: int | None = None
    goals_against: int | None = None
    elo_before: float | None = None
    elo_after: float | None = None
    head_to_head_recent: str | None = None
    win_probability: float | None = None  # P(Juventus win), Elo-based heuristic
    draw_probability: float | None = None
    loss_probability: float | None = None  # P(Juventus loss)


class BriefResponse(BaseModel):
    data: BriefData
    template_text: list[str]
    display_text: list[str]
    llm_used: bool
    llm_error: str | None = None
