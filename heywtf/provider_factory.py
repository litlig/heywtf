"""Factory for creating provider instances based on backend configuration."""

from heywtf.providers import Backend, Provider, ProviderError
from heywtf.ollama_client import OllamaProvider
from heywtf.openai_provider import OpenAIProvider
from heywtf.gemini_provider import GeminiProvider


def create_provider(backend: Backend, config: dict) -> Provider:
    if backend == Backend.OLLAMA:
        return OllamaProvider(
            model=config.get("model"),
            ollama_url=config.get("ollama_url", "http://localhost:11434"),
        )
    elif backend == Backend.OPENAI:
        return OpenAIProvider(
            model=config.get("model"),
            api_key=config.get("openai_api_key"),
        )
    elif backend == Backend.GEMINI:
        return GeminiProvider(
            model=config.get("model"),
            api_key=config.get("gemini_api_key"),
        )
    else:
        supported = ", ".join(b.value for b in Backend)
        raise ProviderError(f"Unknown backend: {backend!r}. Supported: {supported}")
