import asyncio

from app.config import Settings
from app.services.llm import generate_tip


def test_llm_skips_when_key_missing():
    settings = Settings(openai_api_key="  ", openai_base_url="https://example.invalid/v1", openai_model="test")
    tip = asyncio.run(generate_tip({"title": "Soup", "missing_ingredients": [], "matched_ingredients": []}, settings))
    assert tip is None
