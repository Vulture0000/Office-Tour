"""Heading-aware document chunking.

Chunks keep their nearest Markdown heading so retrieved passages can be cited
precisely ("Atlas System Architecture → Why relational"). Chunking is
deterministic, which keeps the demo reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from .loader import CompanyDocument

DEFAULT_MAX_CHARS = 900
DEFAULT_MIN_CHARS = 120
OVERLAP_PARAGRAPHS = 1


@dataclass
class Chunk:
    """A retrievable passage of a company document."""

    id: str
    document_id: str
    text: str
    index: int
    heading: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "index": self.index,
            "heading": self.heading,
        }


def _split_heading(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("#"):
        return stripped.lstrip("#").strip()
    return None


def chunk_document(
    document: CompanyDocument,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> list[Chunk]:
    """Split a document into heading-aware chunks."""

    blocks: list[tuple[str, str]] = []
    heading = document.title
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            text = "\n".join(paragraph).strip()
            if text:
                blocks.append((heading, text))
            paragraph.clear()

    for line in document.body.splitlines():
        new_heading = _split_heading(line)
        if new_heading:
            flush()
            heading = new_heading
            continue
        if not line.strip():
            flush()
            continue
        paragraph.append(line)
    flush()

    # Merge small consecutive blocks that share a heading.
    merged: list[tuple[str, str]] = []
    for block_heading, text in blocks:
        if (
            merged
            and merged[-1][0] == block_heading
            and len(merged[-1][1]) + len(text) < max_chars
        ):
            merged[-1] = (block_heading, merged[-1][1] + "\n\n" + text)
        else:
            merged.append((block_heading, text))

    chunks: list[Chunk] = []
    for index, (block_heading, text) in enumerate(merged):
        if len(text) < min_chars and index < len(merged) - 1:
            # Fold tiny fragments forward so retrieval is not diluted.
            next_heading, next_text = merged[index + 1]
            merged[index + 1] = (next_heading, text + "\n\n" + next_text)
            continue
        chunks.append(
            Chunk(
                id=f"{document.id}::{index}",
                document_id=document.id,
                text=text,
                index=index,
                heading=block_heading,
            )
        )
    return chunks


def chunk_documents(documents: list[CompanyDocument]) -> list[Chunk]:
    """Chunk a list of documents."""

    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document))
    return chunks
