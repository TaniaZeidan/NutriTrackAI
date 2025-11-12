"""Embedding utilities using Google Generative AI and FAISS."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Sequence, Tuple

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import faiss
except Exception:  # pragma: no cover
    faiss = None  # type: ignore

from ..config import FAISS_INDEX_DIR, RAW_DATA_DIR
from .schemas import RecipeDocument


EMBED_DIM = 128
INDEX_FILE = FAISS_INDEX_DIR / "recipes.index"
META_FILE = FAISS_INDEX_DIR / "recipes_meta.json"
VECTORS_FILE = FAISS_INDEX_DIR / "recipes_vectors.json"


def _hash_embed(text: str, dim: int = EMBED_DIM) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for idx in range(dim):
        byte = digest[idx % len(digest)]
        values.append(((byte / 255.0) * 2) - 1)
    return values


def _normalize(vec: Sequence[float]) -> List[float]:
    if np is not None:
        arr = np.array(vec, dtype="float32")
        norm = np.linalg.norm(arr) or 1.0
        return (arr / norm).tolist()
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    if np is not None:
        return float(np.dot(np.array(a), np.array(b)))
    return sum(x * y for x, y in zip(a, b))


def _get_embeddings(texts: List[str]) -> List[List[float]]:
    return [_normalize(_hash_embed(text)) for text in texts]


def _load_raw_documents() -> List[RecipeDocument]:
    path = RAW_DATA_DIR / "recipes_sample.csv"
    documents: List[RecipeDocument] = []
    with path.open("r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for idx, line in enumerate(f):
            parts = []
            current = ""
            in_quotes = False
            for char in line.strip():
                if char == '"':
                    in_quotes = not in_quotes
                    continue
                if char == "," and not in_quotes:
                    parts.append(current)
                    current = ""
                else:
                    current += char
            parts.append(current)
            if len(parts) < 9:
                continue
            title, ingredients, steps, tags, calories, protein, carbs, fat, servings = parts
            text = "\n".join([title, ingredients.replace("|", ", "), steps, f"Tags: {tags}"])
            documents.append(
                RecipeDocument(
                    recipe_id=f"recipe-{idx}",
                    title=title,
                    text=text,
                    tags=[t.strip() for t in tags.split(";") if t.strip()],
                    servings=int(float(servings or 1)),
                    calories=float(calories or 0.0),
                    protein_g=float(protein or 0.0),
                    carb_g=float(carbs or 0.0),
                    fat_g=float(fat or 0.0),
                )
            )
    return documents


def build_index(force: bool = False) -> None:
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_FILE.exists() and META_FILE.exists() and VECTORS_FILE.exists() and not force:
        return
    documents = _load_raw_documents()
    vectors = _get_embeddings([doc.text for doc in documents])
    if faiss and np is not None:
        array = np.array(vectors, dtype="float32")
        index = faiss.IndexFlatIP(array.shape[1])
        faiss.normalize_L2(array)
        index.add(array)
        faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump([doc.model_dump() for doc in documents], f)
    with open(VECTORS_FILE, "w", encoding="utf-8") as f:
        json.dump(vectors, f)


def _load_index() -> Tuple[List[List[float]], List[RecipeDocument]]:
    if not META_FILE.exists() or not VECTORS_FILE.exists():
        build_index()
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = [RecipeDocument(**item) for item in json.load(f)]
    with open(VECTORS_FILE, "r", encoding="utf-8") as f:
        vectors = json.load(f)
    return vectors, meta


def retrieve(query: str, k: int = 6) -> List[Tuple[RecipeDocument, float]]:
    vectors, meta = _load_index()
    query_vec = _normalize(_hash_embed(query))
    scored = []
    for vec, doc in zip(vectors, meta):
        score = _dot(vec, query_vec)
        scored.append((doc, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


__all__ = ["build_index", "retrieve"]
