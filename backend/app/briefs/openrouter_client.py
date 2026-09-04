"""Client for OpenRouter's OpenAI-compatible chat completions endpoint,
used to turn the deterministic template brief into more natural prose.
Errors/timeouts are raised as OpenRouterError and MUST be caught by the
caller (see service.py) — this feature degrades to the template, it never
breaks the brief endpoint.
"""

import httpx

from app.schemas.brief import BriefData

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPTS = {
    "it": (
        "Sei un giornalista sportivo che scrive brevi recap in italiano su Juventus FC. "
        "Tono sobrio e concreto, massimo 4 frasi, non inventare fatti non presenti nei dati forniti."
    ),
    "en": (
        "You are a sports journalist writing short recaps in English about Juventus FC. "
        "Sober, concrete tone, at most 4 sentences, never invent facts not present in the given data."
    ),
}


class OpenRouterError(Exception):
    pass


class OpenRouterClient:
    def __init__(self, api_key: str, model: str, timeout: float = 8.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate_brief_text(self, data: BriefData, template_lines: list[str], lang: str = "it") -> str:
        prompt = self._build_prompt(data, template_lines, lang)
        try:
            response = httpx.post(
                BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["it"])},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OpenRouterError(str(exc)) from exc

        payload = response.json()
        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise OpenRouterError(f"unexpected OpenRouter response shape: {payload!r}") from exc

    @staticmethod
    def _build_prompt(data: BriefData, template_lines: list[str], lang: str = "it") -> str:
        facts = "\n".join(template_lines)
        if lang == "en":
            return (
                f"Rewrite this data recap ({data.kind}-match) about Juventus in a natural, "
                f"flowing way, without inventing facts not present:\n\n{facts}"
            )
        return (
            f"Riscrivi in modo naturale e scorrevole questo recap dati ({data.kind}-partita) "
            f"della Juventus, senza inventare fatti non presenti:\n\n{facts}"
        )
