"""Core orchestration logic for the Friendly Parakeet agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .chunker import Chunk, iter_chunks_by_project
from .gemini_client import GeminiClient
from .index import DocumentIndex, SearchResult, build_documents
from .pdf_reader import Page, filter_pages_by_section, group_pages_by_project, iter_project_pages, load_pdf


@dataclass
class SourceAttribution:
    """Captures the origin of a piece of evidence."""

    page_number: int
    score: float
    excerpt: str


@dataclass
class AgentAnswer:
    """Encapsulates an answer generated for a single project."""

    project: str
    answer: str
    confidence: float
    sources: List[SourceAttribution]


class Agent:
    """Gemini-backed retrieval augmented generation agent."""

    def __init__(
        self,
        *,
        project_indexes: Dict[str, DocumentIndex],
        gemini: Optional[GeminiClient] = None,
    ) -> None:
        self.project_indexes = project_indexes
        self.gemini = gemini or GeminiClient()

    @classmethod
    def from_pdf(
        cls,
        path: str,
        *,
        section: Optional[str] = None,
        chunk_size: int = 1100,
        overlap: int = 200,
        gemini: Optional[GeminiClient] = None,
    ) -> "Agent":
        pages = load_pdf(path)
        pages = filter_pages_by_section(pages, section)
        projects = group_pages_by_project(pages)
        chunks: List[tuple[str, Chunk]] = list(
            iter_chunks_by_project(iter_project_pages(projects), max_characters=chunk_size, overlap=overlap)
        )
        documents = build_documents(
            (
                chunk.content,
                project,
                {"page_number": chunk.page_number, "chunk_index": chunk.index},
            )
            for project, chunk in chunks
        )
        project_documents: Dict[str, List] = {}
        for document in documents:
            project_documents.setdefault(document.metadata["project"], []).append(document)
        project_indexes = {
            project: DocumentIndex(docs)
            for project, docs in project_documents.items()
            if docs
        }
        return cls(project_indexes=project_indexes, gemini=gemini)

    @classmethod
    def from_pages(
        cls,
        pages_by_project: Dict[str, Sequence[Page]],
        *,
        chunk_size: int = 1100,
        overlap: int = 200,
        gemini: Optional[GeminiClient] = None,
    ) -> "Agent":
        chunks: List[tuple[str, Chunk]] = list(
            iter_chunks_by_project(
                iter_project_pages(pages_by_project),
                max_characters=chunk_size,
                overlap=overlap,
            )
        )
        documents = build_documents(
            (
                chunk.content,
                project,
                {"page_number": chunk.page_number, "chunk_index": chunk.index},
            )
            for project, chunk in chunks
        )
        project_documents: Dict[str, List] = {}
        for document in documents:
            project_documents.setdefault(document.metadata["project"], []).append(document)
        project_indexes = {
            project: DocumentIndex(docs)
            for project, docs in project_documents.items()
            if docs
        }
        return cls(project_indexes=project_indexes, gemini=gemini)

    def answer(
        self,
        question: str,
        *,
        top_k: int = 4,
        instructions: Optional[str] = None,
    ) -> List[AgentAnswer]:
        """Answer a user question for each project."""

        responses: List[AgentAnswer] = []
        for project, index in self.project_indexes.items():
            search_results = index.search(question, top_k=top_k)
            if not search_results:
                responses.append(
                    AgentAnswer(
                        project=project,
                        answer="Aucune information pertinente trouvée dans ce projet.",
                        confidence=0.0,
                        sources=[],
                    )
                )
                continue

            context = self._build_context(search_results)
            prompt = self.gemini.build_prompt(question=question, context=context, instructions=instructions)
            raw_response = self.gemini.generate(prompt)
            confidence = max(index.score_to_confidence(result.score) for result in search_results)
            sources = [
                SourceAttribution(
                    page_number=result.document.metadata.get("page_number", -1),
                    score=result.score,
                    excerpt=result.document.content[:300].strip(),
                )
                for result in search_results
            ]
            responses.append(
                AgentAnswer(
                    project=project,
                    answer=raw_response.text.strip(),
                    confidence=confidence,
                    sources=sources,
                )
            )
        return responses

    @staticmethod
    def _build_context(results: Sequence[SearchResult]) -> str:
        sections: List[str] = []
        for result in results:
            meta = result.document.metadata
            page_number = meta.get("page_number", "?")
            excerpt = result.document.content.strip()
            sections.append(
                f"[Page {page_number} | Score {result.score:.2f}]\n{excerpt}"
            )
        return "\n\n".join(sections)
