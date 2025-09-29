"""Lightweight vector index built with TF-IDF for semantic retrieval."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Document:
    """A document ready to be indexed."""

    content: str
    metadata: dict


@dataclass
class SearchResult:
    """Represents a search hit with relevance score."""

    document: Document
    score: float


class DocumentIndex:
    """Simple TF-IDF index for retrieving relevant chunks."""

    def __init__(self, documents: Sequence[Document]):
        if not documents:
            raise ValueError("DocumentIndex requires at least one document")
        self.documents: List[Document] = list(documents)
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(doc.content for doc in self.documents)

    def search(self, query: str, *, top_k: int = 5) -> List[SearchResult]:
        if not query.strip():
            return []
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [
            SearchResult(document=self.documents[idx], score=float(similarities[idx]))
            for idx in top_indices
            if similarities[idx] > 0
        ]
        return results

    @staticmethod
    def score_to_confidence(score: float) -> float:
        """Convert cosine similarity into a 0-1 confidence score."""

        if score <= 0:
            return 0.0
        # Cosine scores rarely exceed 0.6 for long documents. Use a logistic
        # mapping centred around 0.25 to provide interpretable confidences.
        return 1.0 / (1.0 + math.exp(-6.0 * (score - 0.25)))


def build_documents(chunks: Iterable[tuple[str, str, dict]]) -> List[Document]:
    """Create :class:`Document` instances from an iterable of tuples."""

    documents: List[Document] = []
    for content, project, metadata in chunks:
        doc_meta = {"project": project, **metadata}
        documents.append(Document(content=content, metadata=doc_meta))
    return documents
