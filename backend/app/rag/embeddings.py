"""Embedding providers.

The default is a deterministic hashing embedder that needs no API key: it maps
word unigrams and bigrams into a fixed dimensional vector using stable hashes.
It is not as semantically rich as a hosted model, but it is reproducible,
instant, and sufficient for passage ranking inside a graph-filtered candidate
set. Hosted providers can be enabled through configuration.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

import httpx

from ..config import Settings, get_settings

DIMENSION = 256
WORD_RE = re.compile(r"[a-z0-9_]+")

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is",
    "are", "was", "were", "be", "been", "it", "this", "that", "as", "at", "by",
    "from", "we", "our", "their", "they", "he", "she", "his", "her", "what",
    "which", "who", "whom", "how", "why", "when", "where", "do", "does", "did",
    "can", "could", "should", "would", "will", "not", "no", "yes", "but", "if",
    "then", "than", "so", "such", "into", "about", "over", "under", "after",
}


class Embedder(Protocol):
    """Minimal embedding provider interface."""

    name: str
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _tokenize(text: str) -> list[str]:
    tokens = [t for t in WORD_RE.findall(text.lower()) if t not in STOPWORDS]
    bigrams = [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    return tokens + bigrams


def _hash_index(token: str) -> int:
    digest = hashlib.md5(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % DIMENSION


class HashingEmbedder:
    """Deterministic, dependency-free bag-of-ngrams embedding."""

    name = "hashing-256"
    dimension = DIMENSION

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSION
        tokens = _tokenize(text or "")
        if not tokens:
            return vector
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        for token, count in counts.items():
            index = _hash_index(token)
            weight = 1.0 + math.log(count)
            vector[index] += weight
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class RemoteEmbedder:
    """Embeddings from a hosted provider (OpenAI or Google)."""

    def __init__(self, provider: str, api_key: str, model: str | None = None) -> None:
        if not api_key:
            raise ValueError(f"{provider} embeddings require an API key")
        self.provider = provider
        self.api_key = api_key
        self.model = model or (
            "text-embedding-3-small" if provider == "openai" else "text-embedding-004"
        )
        self.name = f"{provider}:{self.model}"
        self.dimension = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "openai":
            vectors = self._openai(texts)
        else:
            vectors = self._google(texts)
        if vectors and not self.dimension:
            self.dimension = len(vectors[0])
        return vectors

    def _openai(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=30.0,
        )
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]

    def _google(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:batchEmbedContents",
            params={"key": self.api_key},
            json={
                "requests": [
                    {"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}}
                    for t in texts
                ]
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return [item["values"] for item in response.json()["embeddings"]]


def get_embedder(settings: Settings | None = None) -> Embedder:
    """Return the configured embedder, falling back to hashing on error."""

    settings = settings or get_settings()
    provider = settings.embedding_provider
    try:
        if provider == "openai" and settings.openai_api_key:
            return RemoteEmbedder("openai", settings.openai_api_key)
        if provider == "google" and settings.google_api_key:
            return RemoteEmbedder("google", settings.google_api_key)
    except Exception:  # noqa: BLE001 - fall back to the deterministic embedder
        pass
    return HashingEmbedder()
