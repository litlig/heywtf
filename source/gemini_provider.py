"""Google Gemini API client with streaming support."""

from __future__ import annotations

import os
from typing import Generator
from source.providers import Provider, ProviderError


class GeminiProvider(Provider):
    """Google Gemini API provider."""

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str | None = None):
        """Initialize Gemini provider.

        Args:
            model: Gemini model name (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro').
            api_key: Google API key. If None, uses GOOGLE_API_KEY env var.

        Raises:
            ProviderError: If API key is not provided.
        """
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        if not self.api_key:
            raise ProviderError(
                "Google API key not found.\n"
                "Add it to ~/.config/heywtf/config.json:\n"
                '  {"gemini_api_key": "your-api-key"}'
            )

        try:
            import google.generativeai as genai
        except ImportError:
            raise ProviderError(
                "google-generativeai library not installed.\n"
                "Install it: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model)

    def chat_stream(
        self,
        messages: list[dict],
    ) -> Generator[str, None, None]:
        """Stream chat response from Gemini, yielding content chunks.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Yields:
            Content string chunks as they arrive.

        Raises:
            ProviderError: If Gemini API fails.
        """
        # Convert from OpenAI-style messages to Gemini format.
        # Gemini uses 'user'/'model' roles and a separate system_instruction.
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
            # Use system instruction if we have system messages
            if system_parts:
                import google.generativeai as genai

                model = genai.GenerativeModel(
                    self.model,
                    system_instruction="\n".join(system_parts),
                )
            else:
                model = self._model

            response = model.generate_content(
                gemini_history,
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            raise ProviderError(f"Gemini API error: {e}")
