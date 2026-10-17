"""Document loading and parsing.

Company documents live in ``data/documents`` as Markdown files with a small
YAML-like front matter block. The loader is intentionally dependency free: the
front matter is simple ``key: value`` pairs, so a tiny parser keeps the RAG
pipeline portable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..config import get_settings


@dataclass
class CompanyDocument:
    """A parsed company document."""

    id: str
    title: str
    type: str
    author_id: str
    created_at: str
    updated_at: str
    project_id: str
    team_id: str
    source_path: str
    content: str
    body: str = ""
    references: list[str] = field(default_factory=list)

    def as_node_props(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "author_id": self.author_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_id": self.project_id,
            "team_id": self.team_id,
            "source_path": self.source_path,
            "content": self.body,
        }


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a Markdown document into front matter and body."""

    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_meta = parts[1]
    body = parts[2].lstrip("\n")
    meta: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def load_document_file(path: Path) -> CompanyDocument:
    """Load a single Markdown document from disk."""

    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    doc_id = meta.get("id") or path.stem
    title = meta.get("title") or doc_id.replace("_", " ").title()
    return CompanyDocument(
        id=doc_id,
        title=title,
        type=meta.get("type", "Document"),
        author_id=meta.get("author_id", ""),
        created_at=meta.get("created_at", ""),
        updated_at=meta.get("updated_at", ""),
        project_id=meta.get("project_id", ""),
        team_id=meta.get("team_id", ""),
        source_path=meta.get("source_path", str(path)),
        content=body.strip(),
        body=body.strip(),
    )


def load_documents(documents_dir: Path | None = None) -> list[CompanyDocument]:
    """Load every Markdown document from the dataset."""

    directory = documents_dir or (get_settings().data_dir / "documents")
    if not directory.exists():
        return []
    documents = [load_document_file(path) for path in sorted(directory.glob("*.md"))]
    return [doc for doc in documents if doc.content]
