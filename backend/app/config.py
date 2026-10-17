"""Application configuration.

All configuration is environment driven. Secrets are never hard-coded; see
`.env.example` for the full list of supported variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Runtime settings resolved from the environment."""

    # LLM
    llm_provider: str = "demo"
    google_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.0

    # Embeddings
    embedding_provider: str = "hashing"

    # FalkorDB
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    falkordb_username: str = ""
    falkordb_password: str = ""
    falkordb_graph: str = "novatech"
    graph_backend: str = "auto"

    # Runtime
    demo_mode: bool = True
    vector_store_path: str = "./var/vector_store.json"
    actions_store_path: str = "./var/actions.json"
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    log_level: str = "INFO"

    @property
    def llm_available(self) -> bool:
        if self.llm_provider == "google":
            return bool(self.google_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return False

    @property
    def workspace_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    def resolved_vector_store_path(self) -> Path:
        path = Path(self.vector_store_path)
        return path if path.is_absolute() else (BACKEND_ROOT / path).resolve()

    def resolved_actions_store_path(self) -> Path:
        path = Path(self.actions_store_path)
        return path if path.is_absolute() else (BACKEND_ROOT / path).resolve()


def load_settings() -> Settings:
    """Build a :class:`Settings` instance from the current environment."""

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "demo").strip().lower() or "demo",
        google_api_key=os.getenv("GOOGLE_API_KEY", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        llm_model=os.getenv("LLM_MODEL", "gemini-2.0-flash").strip(),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0") or 0),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "hashing").strip().lower(),
        falkordb_host=os.getenv("FALKORDB_HOST", "localhost").strip(),
        falkordb_port=int(os.getenv("FALKORDB_PORT", "6379") or 6379),
        falkordb_username=os.getenv("FALKORDB_USERNAME", "").strip(),
        falkordb_password=os.getenv("FALKORDB_PASSWORD", "").strip(),
        falkordb_graph=os.getenv("FALKORDB_GRAPH", "novatech").strip() or "novatech",
        graph_backend=os.getenv("GRAPH_BACKEND", "auto").strip().lower() or "auto",
        demo_mode=_get_bool("DEMO_MODE", True),
        vector_store_path=os.getenv("VECTOR_STORE_PATH", "./var/vector_store.json"),
        actions_store_path=os.getenv("ACTIONS_STORE_PATH", "./var/actions.json"),
        cors_origins=_get_list(
            "CORS_ORIGINS", ["http://localhost:5173", "http://localhost:3000"]
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""

    return load_settings()
