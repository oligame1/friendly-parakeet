"""Gemini client wrapper with graceful fallback for offline testing."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeminiResponse:
    """Represents the response from Gemini."""

    text: str


class GeminiClient:
    """Wrapper around the ``google-generativeai`` SDK with an offline fallback."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "models/gemini-pro",
        temperature: float = 0.2,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature
        self._model = None
        if self.api_key and model != "mock":
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(model_name=self.model)
            except Exception as exc:  # pragma: no cover - defensive programming
                raise RuntimeError("Failed to initialise Gemini client") from exc

    def generate(self, prompt: str) -> GeminiResponse:
        """Generate text from Gemini or fallback to a deterministic response."""

        if self._model is None or self.model == "mock":
            # Offline fallback: return the prompt's context portion.
            return GeminiResponse(
                text=(
                    "[Mode hors ligne] Synthèse basée sur le contexte fourni :\n" + prompt
                )
            )

        response = self._model.generate_content(
            prompt,
            generation_config={
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 32,
            },
        )
        output_text = getattr(response, "text", None)
        if not output_text and hasattr(response, "candidates"):
            for candidate in response.candidates:
                if getattr(candidate, "content", None):
                    parts = getattr(candidate.content, "parts", [])
                    if parts:
                        output_text = getattr(parts[0], "text", None)
                        if output_text:
                            break
        if not output_text:
            raise RuntimeError("Gemini did not return any text content")
        return GeminiResponse(text=output_text)

    def build_prompt(self, *, question: str, context: str, instructions: Optional[str] = None) -> str:
        """Create a structured prompt for Gemini."""

        system_instructions = instructions or (
            "Tu es un assistant qui répond en français avec des références à la construction au Québec."
        )
        prompt = (
            f"{system_instructions}\n\n"
            "Contexte pertinent :\n"
            f"{context}\n\n"
            f"Question : {question}\n"
            "Réponds de manière concise tout en citant les extraits pertinents."
        )
        return prompt
