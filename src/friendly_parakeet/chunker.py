"""Chunking utilities for preparing documents for retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .pdf_reader import Page


@dataclass
class Chunk:
    """Represents a chunk of text tied to a PDF page."""

    content: str
    page_number: int
    index: int


def split_page_into_chunks(
    page: Page,
    *,
    max_characters: int = 1100,
    overlap: int = 200,
) -> List[Chunk]:
    """Split a page into overlapping chunks for retrieval.

    Args:
        page: The :class:`~friendly_parakeet.pdf_reader.Page` instance.
        max_characters: Maximum length of each chunk. Defaults to 1,100 which
            aligns with the context window of Gemini when multiple chunks are
            concatenated.
        overlap: Number of characters that overlap between consecutive chunks to
            preserve context continuity.
    """

    if max_characters <= 0:
        raise ValueError("max_characters must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")

    text = page.text
    if not text:
        return []

    chunks: List[Chunk] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(len(text), start + max_characters)
        content = text[start:end]
        chunks.append(Chunk(content=content, page_number=page.number, index=idx))
        idx += 1
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_pages(pages: Sequence[Page], **kwargs) -> List[Chunk]:
    """Chunk multiple pages using :func:`split_page_into_chunks`."""

    output: List[Chunk] = []
    for page in pages:
        output.extend(split_page_into_chunks(page, **kwargs))
    return output


def iter_chunks_by_project(
    project_pages: Iterable[tuple[str, Page]],
    *,
    max_characters: int = 1100,
    overlap: int = 200,
) -> Iterable[tuple[str, Chunk]]:
    """Yield chunks annotated with their originating project."""

    for project, page in project_pages:
        for chunk in split_page_into_chunks(page, max_characters=max_characters, overlap=overlap):
            yield project, chunk
