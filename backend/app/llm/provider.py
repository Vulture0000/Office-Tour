"""LLM provider abstraction.

The application never imports a vendor SDK directly. Providers implement a tiny
``complete`` method, and when no provider is configured (or a call fails) the
agents fall back to deterministic, graph-derived answer composition. That keeps
the demo reproducible and outage-proof.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Minimal text completion interface."""

    name: str
    available: bool

    def complete(self, system: str, user: str, temperature: float = 0.0) -> str: ...


class MockProvider:
    """Used when no provider is configured; callers use deterministic output."""

    name = "demo"
    available = False

    def complete(self, system: str, user: str, temperature: float = 0.0) -> str:
        return ""


class GoogleProvider:
    """Google Gemini via the REST API."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.name = f"google:{model}"
        self.available = True

    def complete(self, system: str, user: str, temperature: float = 0.0) -> str:
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": temperature},
            },
            timeout=45.0,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts).strip()


class OpenAIProvider:
    """OpenAI chat completions."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.name = f"openai:{model}"
        self.available = True

    def complete(self, system: str, user: str, temperature: float = 0.0) -> str:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        choices = response.json().get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message", {}).get("content") or "").strip()


def get_llm(settings: Settings | None = None) -> LLMProvider:
    """Return the configured LLM provider (never raises)."""

    settings = settings or get_settings()
    provider = settings.llm_provider
    try:
        if provider == "google" and settings.google_api_key:
            return GoogleProvider(settings.google_api_key, settings.llm_model)
        if provider == "openai" and settings.openai_api_key:
            model = settings.llm_model or "gpt-4o-mini"
            return OpenAIProvider(settings.openai_api_key, model)
    except Exception as exc:  # noqa: BLE001 - degrade to deterministic mode
        logger.warning("LLM provider unavailable (%s); using deterministic mode", exc)
    return MockProvider()


def safe_complete(
    llm: LLMProvider, system: str, user: str, temperature: float = 0.0
) -> str | None:
    """Call the provider, returning ``None`` on any failure."""

    if not getattr(llm, "available", False):
        return None
    try:
        text = llm.complete(system, user, temperature)
        return text or None
    except Exception as exc:  # noqa: BLE001 - providers are best effort
        logger.warning("LLM completion failed (%s); falling back", exc)
        return None
