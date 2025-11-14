"""RAG pipeline helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from core.embeddings import build_index, retrieve
from core.schemas import RecipeDocument


@dataclass
class RetrievalResult:
    document: RecipeDocument
    score: float


def search_recipes(query: str, k: int = 6) -> List[RetrievalResult]:
    """Retrieve recipe documents for a query."""
    results = retrieve(query, k=k)
    return [RetrievalResult(document=doc, score=score) for doc, score in results]


__all__ = ["build_index", "search_recipes", "RetrievalResult"]
