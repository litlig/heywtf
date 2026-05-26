"""OpenAI API client with streaming support."""

from __future__ import annotations

import os
from typing import Generator
from heywtf.providers import Provider, ProviderError


class OpenAIProvider(Provider):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ProviderError(
                "OpenAI API key not found.\n"
                "Set it with: hey config set openai_api_key <key>\n"
                "Or set the OPENAI_API_KEY environment variable."
            )

        try:
            from openai import OpenAI, APIError
        except ImportError:
            raise ProviderError(
                "OpenAI library not installed. Try: pip install --upgrade heywtf"
            )

        self._client = OpenAI(api_key=self.api_key)
        self._api_error = APIError

    def chat_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except self._api_error as e:
            raise ProviderError(f"OpenAI API error: {e}")
        except Exception as e:
            raise ProviderError(f"OpenAI request failed: {e}")
