"""Gemini client abstractions."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

try:  # pragma: no cover - optional import
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore

from config import CHAT_MODEL, get_google_api_key


class GeminiClient:
    """Wrapper around the Gemini API with graceful degradation."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        if self.api_key is None:
            try:
                self.api_key = get_google_api_key()
            except RuntimeError:
                self.api_key = None
        if self.api_key and genai:
            genai.configure(api_key=self.api_key)
        self._offline = not (self.api_key and genai)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Gemini or an offline fallback."""
        if self._offline:
            return self._offline_response(prompt)
        assert genai is not None
        model = genai.GenerativeModel(model_name=CHAT_MODEL)
        response = model.generate_content(prompt, **kwargs)
        return response.text or ""

    def structured_json(self, prompt: str) -> Dict[str, Any]:
        """Return structured JSON output."""
        text = self.generate_text(prompt)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text, "error": "Failed to parse JSON"}

    def _offline_response(self, prompt: str) -> str:
        """Deterministic offline answer for testing."""
        if "calorie" in prompt.lower():
            return json.dumps(
                {
                    "description": "Sample meal",
                    "meal_type": "lunch",
                    "meal_date": "2024-01-01",
                    "items": [
                        {
                            "name": "Test Food",
                            "qty": 1,
                            "unit": "serving",
                            "calories": 250,
                            "protein_g": 20,
                            "carb_g": 15,
                            "fat_g": 10,
                            "estimated": True,
                        }
                    ],
                }
            )
        return "NutriTrackAI offline response."


__all__ = ["GeminiClient"]
