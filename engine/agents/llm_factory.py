"""Tworzenie agentów LLM po nazwie dostawcy — wspólne dla web i eksperymentów.

    make_llm_agent("anthropic", mode="guided")
    make_llm_agent("ollama", model="qwen2.5")

`provider_available()` pozwala pominąć dostawcę bez klucza / serwera
zamiast wywracać cały przebieg eksperymentów.
"""
from __future__ import annotations

import os
import urllib.request

from ..rng import Rng
from .llm_agent import (
    AnthropicLLMAgent,
    BaseLLMAgent,
    GeminiLLMAgent,
    LLMMode,
    OllamaLLMAgent,
    OpenAILLMAgent,
)

# dostawca -> (domyślny model, zmienna z kluczem albo None, moduł SDK, pakiet pip)
PROVIDERS: dict[str, tuple[str, str | None, str, str]] = {
    "anthropic": ("claude-haiku-4-5", "ANTHROPIC_API_KEY", "anthropic",           "anthropic"),
    "openai":    ("gpt-4o-mini",      "OPENAI_API_KEY",    "openai",              "openai"),
    "gemini":    ("gemini-2.0-flash", "GOOGLE_API_KEY",    "google.generativeai", "google-generativeai"),
    "ollama":    ("llama3.2",         None,                "openai",              "openai"),
}


def ollama_host() -> str:
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def provider_available(provider: str) -> tuple[bool, str]:
    """(czy_da_się_użyć, powód_jeśli_nie) — bez wykonywania płatnych wywołań."""
    if provider not in PROVIDERS:
        return False, f"nieznany dostawca: {provider}"
    _, env_key, module, pip_name = PROVIDERS[provider]
    try:
        __import__(module)
    except ImportError:
        return False, f"brak pakietu: pip install {pip_name}"
    if env_key and not os.environ.get(env_key):
        return False, f"brak {env_key} w .env"
    if provider == "ollama":
        try:
            urllib.request.urlopen(f"{ollama_host()}/api/tags", timeout=1)
        except OSError:
            return False, f"serwer Ollama nie odpowiada ({ollama_host()})"
    return True, ""


def make_llm_agent(
    provider: str,
    model: str | None = None,
    mode: str | LLMMode = LLMMode.GUIDED,
    fallback_rng: Rng | None = None,
    verbose: bool = False,
) -> BaseLLMAgent:
    if provider not in PROVIDERS:
        raise ValueError(f"nieznany dostawca LLM: {provider}")
    mode = LLMMode(mode) if isinstance(mode, str) else mode
    model = model or PROVIDERS[provider][0]
    common = {"mode": mode, "fallback_rng": fallback_rng, "verbose": verbose}
    if provider == "anthropic":
        return AnthropicLLMAgent(model=model, **common)
    if provider == "openai":
        return OpenAILLMAgent(model=model, **common)
    if provider == "gemini":
        return GeminiLLMAgent(model=model, **common)
    return OllamaLLMAgent(model=model, host=ollama_host(), **common)
