"""OpenAI API client with streaming support."""

from __future__ import annotations

import os
from typing import Generator
from source.providers import Provider, ProviderError


class OpenAIProvider(Provider):
    """OpenAI API provider using official OpenAI Python library."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        """Initialize OpenAI provider.

        Args:
            model: OpenAI model name (e.g., 'gpt-4o-mini', 'gpt-4o').
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.

        Raises:
            ProviderError: If API key is not provided or invalid.
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ProviderError(
                "OpenAI API key not found.\n"
                "Add it to ~/.config/heywtf/config.json:\n"
                '  {"openai_api_key": "your-api-key"}'
            )

        try:
            from openai import OpenAI, APIError
        except ImportError:
            raise ProviderError(
                "OpenAI library not installed (required for the openai backend).\n"
                "Install it: pip install 'heywtf[openai]'"
            )

        self._client = OpenAI(api_key=self.api_key)
        self._api_error = APIError

    def chat_stream(
        self,
        messages: list[dict],
    ) -> Generator[str, None, None]:
        """Stream chat response from OpenAI, yielding content chunks.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Yields:
            Content string chunks as they arrive.

        Raises:
            ProviderError: If OpenAI API fails.
        """
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
