from __future__ import annotations

from src.core.embeddings import build_index, retrieve


def test_build_index_and_retrieve():
    build_index(force=True)
    results = retrieve("high protein salmon", k=3)
    assert results
    titles = [doc.title for doc, _ in results]
    assert any("Salmon" in title for title in titles)
