"""Ollama API client with streaming support."""

import requests
import json
from typing import Generator


class OllamaError(Exception):
    """Raised when Ollama API communication fails."""
    pass


def chat_stream(
    messages: list[dict],
    model: str,
    ollama_url: str,
) -> Generator[str, None, None]:
    """Stream chat response from Ollama, yielding content chunks.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        model: Ollama model name (e.g. 'qwen3-coder:1.5b').
        ollama_url: Base URL for Ollama (e.g. 'http://localhost:11434').

    Yields:
        Content string chunks as they arrive.

    Raises:
        OllamaError: If the request fails or Ollama is unreachable.
    """
    url = f"{ollama_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        response.raise_for_status()
    except requests.ConnectionError:
        raise OllamaError(
            f"Cannot connect to Ollama at {ollama_url}.\n"
            "Make sure Ollama is running: ollama serve"
        )
    except requests.Timeout:
        raise OllamaError("Ollama request timed out after 30s.")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            raise OllamaError(
                f"Model '{model}' not found. Pull it first:\n"
                f"  ollama pull {model}"
            )
        raise OllamaError(f"Ollama API error: {e}")

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


def chat(
    messages: list[dict],
    model: str,
    ollama_url: str,
) -> str:
    """Non-streaming chat — collects full response as a string."""
    chunks = []
    for chunk in chat_stream(messages, model, ollama_url):
        chunks.append(chunk)
    return "".join(chunks)
