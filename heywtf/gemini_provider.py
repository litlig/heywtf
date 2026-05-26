"""Google Gemini API client with streaming support."""

from __future__ import annotations

import os
from typing import Generator
from heywtf.providers import Provider, ProviderError


class GeminiProvider(Provider):
    def __init__(self, model: str = "gemini-2.0-flash", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        if not self.api_key:
            raise ProviderError(
                "Google API key not found.\n"
                "Set it with: hey config set gemini_api_key <key>\n"
                "Or set the GOOGLE_API_KEY environment variable."
            )

        try:
            import google.generativeai as genai
        except ImportError:
            raise ProviderError(
                "google-generativeai library not installed. Try: pip install --upgrade heywtf"
            )

        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model)

    def chat_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        system_parts = []
        gemini_history = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(content)
            elif role == "assistant":
                gemini_history.append({"role": "model", "parts": [content]})
            else:
                gemini_history.append({"role": "user", "parts": [content]})

        try:
            if system_parts:
                import google.generativeai as genai
                model = genai.GenerativeModel(
                    self.model,
                    system_instruction="\n".join(system_parts),
                )
            else:
                model = self._model

            response = model.generate_content(gemini_history, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            raise ProviderError(f"Gemini API error: {e}")
