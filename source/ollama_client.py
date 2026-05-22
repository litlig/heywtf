"""Ollama API client with streaming support."""

import requests
import json
from typing import Generator
from source.providers import Provider, ProviderError


# Keep backward-compatible exceptions
OllamaError = ProviderError


class OllamaProvider(Provider):
    """Ollama API provider for local model inference."""

    def __init__(self, model: str, ollama_url: str = "http://localhost:11434"):
        """Initialize Ollama provider.

        Args:
            model: Ollama model name (e.g., 'qwen2.5-coder:0.5b').
            ollama_url: Base URL for Ollama.
        """
        self.model = model
        self.ollama_url = ollama_url

    def chat_stream(
        self,
        messages: list[dict],
    ) -> Generator[str, None, None]:
        """Stream chat response from Ollama, yielding content chunks.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Yields:
            Content string chunks as they arrive.

        Raises:
            ProviderError: If the request fails or Ollama is unreachable.
        """
        url = f"{self.ollama_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            response.raise_for_status()
        except requests.ConnectionError:
            raise ProviderError(
                f"Cannot connect to Ollama at {self.ollama_url}.\n"
                "Make sure Ollama is running: ollama serve"
            )
        except requests.Timeout:
            raise ProviderError("Ollama request timed out after 30s.")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                raise ProviderError(
                    f"Model '{self.model}' not found. Pull it first:\n"
                    f"  ollama pull {self.model}"
                )
            raise ProviderError(f"Ollama API error: {e}")

        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Yield the content if present
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

            # Stop if done
            if chunk.get("done", False):
                return
