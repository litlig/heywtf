"""Factory for creating provider instances based on backend configuration."""

from source.providers import Backend, Provider, ProviderError
from source.ollama_client import OllamaProvider
from source.chatgpt_client import ChatGPTProvider
from source.openai_provider import OpenAIProvider
from source.gemini_provider import GeminiProvider
def create_provider(backend: Backend, config: dict) -> Provider:
    """Create a provider instance for the given backend.

    Args:
        backend: The backend to instantiate.
        config: Configuration dict with necessary credentials and settings.

    Returns:
        Initialized Provider instance.

    Raises:
        ProviderError: If backend is invalid or required config is missing.
    """
    if backend == Backend.OLLAMA:
        return OllamaProvider(
            model=config.get("model"),
            ollama_url=config.get("ollama_url", "http://localhost:11434"),
        )

    elif backend == Backend.CHATGPT_WEB:
        return ChatGPTProvider(
            model=config.get("model"),
            headless=True,
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
