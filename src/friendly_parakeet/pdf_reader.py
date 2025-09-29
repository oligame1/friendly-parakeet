"""Utilities for loading and pre-processing PDF documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from pypdf import PdfReader


@dataclass
class Page:
    """Represents a single PDF page and its extracted text."""

    number: int
    text: str

    def contains_section(self, section: str) -> bool:
        pattern = re.compile(rf"(?i)\bsection\s*{re.escape(section)}\b")
        alt_pattern = re.compile(rf"(?i)\bsection\s*{re.escape(section.replace('.', ''))}\b")
        return bool(pattern.search(self.text) or alt_pattern.search(self.text))


def load_pdf(path: str | Path) -> List[Page]:
    """Load a PDF file and return the extracted pages.

    The text of each page is normalised by stripping blank lines and trimming
    whitespace to make downstream processing more predictable.
    """

    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages: List[Page] = []
    for index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        normalised = "\n".join(cleaned_lines)
        pages.append(Page(number=index, text=normalised))
    return pages


def filter_pages_by_section(pages: Sequence[Page], section: str | None) -> List[Page]:
    """Filter the provided pages by a textual section reference.

    The function performs a fuzzy match that looks for occurrences of
    "Section <section>" or "Section<section>" inside the page content. When
    ``section`` is ``None`` all pages are returned unchanged.
    """

    if section is None:
        return list(pages)
    return [page for page in pages if page.contains_section(section)]


def group_pages_by_project(
    pages: Sequence[Page],
    *,
    project_pattern: str = r"(?im)^(projet|project)\s*[:\-]\s*(.+)$",
    default_project: str = "Général",
) -> Dict[str, List[Page]]:
    """Group pages by project name using a regular expression.

    Args:
        pages: The ordered sequence of PDF pages.
        project_pattern: A regex with two capturing groups: the keyword and the
            project label. It is executed with ``re.finditer`` on each page.
        default_project: Name used when no project heading is found.

    Returns:
        A mapping of project name to the pages that belong to it.

    Notes:
        The algorithm assigns pages to the most recent project heading found. If
        no heading is encountered the pages are assigned to ``default_project``.
    """

    compiled = re.compile(project_pattern)
    projects: Dict[str, List[Page]] = {default_project: []}
    current_project = default_project

    for page in pages:
        matches = list(compiled.finditer(page.text))
        if matches:
            # Use the last heading on the page so that appendices or footers do
            # not override the actual project name if multiple appear.
            last_match = matches[-1]
            label = last_match.group(2).strip()
            if label:
                current_project = label
                projects.setdefault(current_project, [])
        projects.setdefault(current_project, []).append(page)
    return projects


def iter_project_pages(projects: Dict[str, Sequence[Page]]) -> Iterable[tuple[str, Page]]:
    """Yield (project, page) pairs for downstream processing."""

    for project, pages in projects.items():
        for page in pages:
            yield project, page
