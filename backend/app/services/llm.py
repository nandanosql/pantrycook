"""Optional cook tip via any OpenAI-compatible chat endpoint.

If no API key is configured, or the call fails, suggestions still return.
"""

from __future__ import annotations

import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are PantryCook, a practical home-cooking assistant. "
    "Reply with one or two short sentences: a cook tip and at most two substitutions "
    "for missing items. No preamble, no list, no hashtags."
)


def _prompt(suggestion: dict) -> str:
    missing = ", ".join(item["name"] for item in suggestion.get("missing_ingredients") or []) or "nothing"
    matched = ", ".join(item["name"] for item in suggestion.get("matched_ingredients") or []) or "nothing"
    soon = ", ".join(suggestion.get("use_soon") or []) or "none"
    return (
        f"Recipe: {suggestion.get('title')}\n"
        f"Already in the pantry: {matched}\n"
        f"Missing: {missing}\n"
        f"Use soon: {soon}\n"
        "Give one practical tip."
    )


async def generate_tip(suggestion: dict, settings: Settings, client: httpx.AsyncClient | None = None) -> str | None:
    if not settings.llm_configured:
        return None
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.openai_model,
        "temperature": 0.4,
        "max_tokens": 120,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _prompt(suggestion)},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key.strip()}"}
    owns_client = client is None
    http = client or httpx.AsyncClient(timeout=8.0)
    try:
        response = await http.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        text = (content or "").strip()
        return text or None
    except Exception as exc:  # network, auth, and shape errors should not fail Cook tonight
        logger.warning("LLM tip skipped: %s", exc.__class__.__name__)
        return None
    finally:
        if owns_client:
            await http.aclose()


async def attach_tips(suggestions: list[dict], settings: Settings, *, max_tips: int = 3) -> None:
    if not settings.llm_configured or not suggestions:
        return
    async with httpx.AsyncClient(timeout=8.0) as client:
        for suggestion in suggestions[:max_tips]:
            suggestion["llm_tip"] = await generate_tip(suggestion, settings, client)
