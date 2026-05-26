"""Ollama API client with streaming support."""

import requests
import json
from typing import Generator
from heywtf.providers import Provider, ProviderError

OllamaError = ProviderError


class OllamaProvider(Provider):
    def __init__(self, model: str, ollama_url: str = "http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url

    def chat_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        url = f"{self.ollama_url.rstrip('/')}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": True}

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            response.raise_for_status()
        except requests.ConnectionError:
            import shutil
            if shutil.which("ollama") is None:
                raise ProviderError(
                    "Ollama is not installed.\n"
                    "  Install: https://ollama.com  or  brew install ollama\n"
                    "  Or switch backends: hey config"
                )
            raise ProviderError(
                f"Ollama is not running.\n"
                "  Start it: ollama serve\n"
                "  Or switch backends: hey config"
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

            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

            if chunk.get("done", False):
                return
