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
            from google import genai
        except ImportError:
            raise ProviderError(
                "google-genai library not installed. Try: pip install --upgrade heywtf"
            )

        self._client = genai.Client(api_key=self.api_key)

    def chat_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        from google.genai import types

        system_parts = []
        contents = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(content)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        config = None
        if system_parts:
            config = types.GenerateContentConfig(
                system_instruction="\n".join(system_parts)
            )

        try:
            response = self._client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            raise ProviderError(f"Gemini API error: {e}")
