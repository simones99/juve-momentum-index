import logging

from sqlalchemy.orm import Session

from app.briefs.openrouter_client import OpenRouterClient, OpenRouterError
from app.briefs.template_brief import (
    build_post_match_brief_data,
    build_pre_match_brief_data,
    render_template_text,
)
from app.config import get_settings
from app.schemas.brief import BriefData, BriefResponse

logger = logging.getLogger(__name__)


def _llm_enhance(data: BriefData, template_lines: list[str]) -> tuple[str | None, str | None]:
    settings = get_settings()
    if not (settings.enable_llm_brief and settings.openrouter_api_key):
        return None, None

    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        timeout=settings.llm_timeout_seconds,
    )
    try:
        return client.generate_brief_text(data, template_lines), None
    except OpenRouterError as exc:
        logger.warning("OpenRouter brief generation failed, falling back to template: %s", exc)
        return None, str(exc)


def _to_response(data: BriefData, template_lines: list[str]) -> BriefResponse:
    llm_text, llm_error = _llm_enhance(data, template_lines)
    return BriefResponse(
        data=data,
        template_text=template_lines,
        display_text=[llm_text] if llm_text else template_lines,
        llm_used=llm_text is not None,
        llm_error=llm_error,
    )


def get_pre_match_brief(db: Session, opponent: str | None, n: int = 5) -> BriefResponse:
    data = build_pre_match_brief_data(db, opponent, n)
    return _to_response(data, render_template_text(data))


def get_post_match_brief(db: Session, match_id: int, n: int = 5) -> BriefResponse:
    data = build_post_match_brief_data(db, match_id, n)
    return _to_response(data, render_template_text(data))
