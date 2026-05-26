"""Abstract provider interface for AI chat models."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator


class ProviderError(Exception):
    pass


class Backend(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"

    @classmethod
    def from_str(cls, value: str) -> "Backend":
        try:
            return cls(value)
        except ValueError:
            supported = ", ".join(b.value for b in cls)
            raise ProviderError(f"Unknown backend: {value!r}. Supported: {supported}")


class Provider(ABC):
    @abstractmethod
    def chat_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        pass

    def chat(self, messages: list[dict]) -> str:
        return "".join(self.chat_stream(messages))
