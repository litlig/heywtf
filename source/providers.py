"""Abstract provider interface for AI chat models.

This module defines a base provider interface that all AI backends must implement.
Enables pluggable model providers: Ollama, OpenAI, Gemini, ChatGPT Web, etc.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    pass


class Backend(str, Enum):
    """Supported AI backends. Values match the keys used in config/CLI."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    CHATGPT_WEB = "chatgpt-web"

    @classmethod
    def from_str(cls, value: str) -> "Backend":
        """Parse a backend name, raising ProviderError on an unknown value."""
        try:
            return cls(value)
        except ValueError:
            supported = ", ".join(b.value for b in cls)
            raise ProviderError(
                f"Unknown backend: {value!r}. Supported: {supported}"
            )


class Provider(ABC):
    """Abstract base class for AI model providers."""

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict],
    ) -> Generator[str, None, None]:
        """Stream chat response, yielding content chunks.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Yields:
            Content string chunks as they arrive.

        Raises:
            ProviderError: If chat fails.
        """
        pass

    def chat(self, messages: list[dict]) -> str:
        """Non-streaming chat — collects full response as a string.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Full response string.
        """
        chunks = []
        for chunk in self.chat_stream(messages):
            chunks.append(chunk)
        return "".join(chunks)
