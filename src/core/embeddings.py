"""Embedding utilities using Google Generative AI and FAISS."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import faiss
except Exception:  # pragma: no cover
    faiss = None  # type: ignore

try:  # pragma: no cover - optional embedding dependency
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore

from config import (
    EMBEDDING_MODEL,
    FAISS_INDEX_DIR,
    RAW_DATA_DIR,
    get_google_api_key,
)
from .schemas import RecipeDocument


EMBED_DIM = 128
INDEX_FILE = FAISS_INDEX_DIR / "recipes.index"
META_FILE = FAISS_INDEX_DIR / "recipes_meta.json"
VECTORS_FILE = FAISS_INDEX_DIR / "recipes_vectors.json"
BACKEND_HASH = "hash"
BACKEND_GEMINI = "gemini"


def _latest_mtime(paths: List[Path]) -> float:
    """Return the latest modification time among existing paths."""
    mtimes = [p.stat().st_mtime for p in paths if p.exists()]
    return max(mtimes) if mtimes else 0.0


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

def _pad_or_trim(vec: List[float], target_dim: int) -> List[float]:
    """Pad or trim a vector to a target dimension for compatibility."""
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0] * (target_dim - len(vec))


def _safe_api_key() -> str | None:
    try:
        return get_google_api_key()
    except Exception:
        return None


def _parse_json_field(value: str | None, default):
    """Safely parse a JSON field from CSV."""
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _get_embeddings(texts: List[str]) -> tuple[List[List[float]], str]:
    """Return embeddings for a list of texts.

    If GOOGLE_API_KEY is configured and the Google Generative AI client is
    available, this uses the Gemini text-embedding-004 model. Otherwise it
    falls back to a deterministic hash-based embedding so the app can still
    run fully offline.
    """
    # Try real Gemini embeddings first
    if genai is not None:
        try:
            api_key = _safe_api_key()
            if api_key:
                genai.configure(api_key=api_key)
            else:
                raise RuntimeError("GOOGLE_API_KEY not configured")

            # Process texts one by one with progress indicator
            # Note: Gemini batch API has inconsistent response formats, so we process individually
            vectors: List[List[float]] = []
            total = len(texts)

            print(f"Processing {total} texts with Gemini embeddings...")
            for idx, text in enumerate(texts, 1):
                if idx % 100 == 0 or idx == 1:
                    print(f"  Progress: {idx}/{total} ({100*idx//total}%)...")

                resp = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                )

                # Extract embedding from response
                if isinstance(resp, dict) and "embedding" in resp:
                    vec = resp["embedding"]
                else:
                    # Try alternative response format
                    vec = resp.get("embedding") if hasattr(resp, 'get') else resp.embedding

                vectors.append(_normalize(vec))

            print(f"Completed {len(vectors)} embeddings")
            return vectors, BACKEND_GEMINI

        except Exception as exc:  # pragma: no cover - network / quota issues
            print(f"Embedding API error, falling back to hash embeddings: {exc}")

    # Offline / fallback path
    return [_normalize(_hash_embed(text)) for text in texts], BACKEND_HASH


def _embed_query(text: str, backend: str, target_dim: int) -> List[float]:
    """Embed a single query with the backend used for the index."""
    if backend == BACKEND_GEMINI and genai is not None:
        try:
            api_key = _safe_api_key()
            if api_key:
                genai.configure(api_key=api_key)
            else:
                raise RuntimeError("GOOGLE_API_KEY not configured")
            resp = genai.embed_content(model=EMBEDDING_MODEL, content=text)
            vec = resp.get("embedding")  # type: ignore[assignment]
            if vec is None:
                vec = resp["data"][0]["embedding"]  # type: ignore[index]
            return _normalize(vec)
        except Exception as exc:
            print(f"Query embedding fallback to hash: {exc}")

    # Fallback: deterministic hash embedding, padded to target dimension if needed
    hashed = _normalize(_hash_embed(text, dim=target_dim))
    return _pad_or_trim(hashed, target_dim)


def _load_recipe_sample_documents() -> List[RecipeDocument]:
    path = RAW_DATA_DIR / "recipes_sample.csv"
    documents: List[RecipeDocument] = []
    if not path.exists():
        return documents
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
                    recipe_id=f"classic-recipe-{idx}",
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


def _load_nutrition_recipes(start_idx: int = 0) -> List[RecipeDocument]:
    """Load recipes with full nutrient/ingredient detail."""
    path = RAW_DATA_DIR / "recipes-with-nutrition.csv"
    documents: List[RecipeDocument] = []
    if not path.exists():
        return documents

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for offset, row in enumerate(reader):
            title = (row.get("recipe_name") or "").strip()
            if not title:
                continue
            servings = max(1, int(float(row.get("servings") or 1)))
            calories_total = float(row.get("calories") or 0.0)

            nutrients = _parse_json_field(row.get("total_nutrients"), {})
            protein_total = float(nutrients.get("PROCNT", {}).get("quantity", 0.0))
            carbs_total = float(nutrients.get("CHOCDF", {}).get("quantity", 0.0))
            fat_total = float(nutrients.get("FAT", {}).get("quantity", 0.0))

            calories = calories_total / servings if servings else calories_total
            protein = protein_total / servings if servings else protein_total
            carbs = carbs_total / servings if servings else carbs_total
            fat = fat_total / servings if servings else fat_total

            ingredient_lines = _parse_json_field(row.get("ingredient_lines"), [])
            ingredients_items = _parse_json_field(row.get("ingredients"), [])
            if not ingredient_lines and isinstance(ingredients_items, list):
                ingredient_lines = [str(item.get("text", "")).strip() for item in ingredients_items if item.get("text")]
            ingredient_text = ", ".join([ln for ln in ingredient_lines if ln]) or ""

            tags: List[str] = []
            for field in ("diet_labels", "health_labels", "cuisine_type", "meal_type", "dish_type"):
                parsed = _parse_json_field(row.get(field), [])
                if isinstance(parsed, list):
                    tags.extend([str(x).strip() for x in parsed if str(x).strip()])
            tags = [t for t in tags if t]

            description_parts = [
                title,
                f"Servings: {servings}",
                f"Ingredients: {ingredient_text}",
                f"Tags: {', '.join(tags)}" if tags else "",
            ]
            text = "\n".join(part for part in description_parts if part)

            documents.append(
                RecipeDocument(
                    recipe_id=f"nutrition-recipe-{start_idx + offset}",
                    title=title,
                    text=text,
                    tags=tags,
                    servings=servings,
                    calories=calories,
                    protein_g=protein,
                    carb_g=carbs,
                    fat_g=fat,
                )
            )

    return documents


def _bool_flag(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _load_meal_plan_documents(start_idx: int = 0) -> List[RecipeDocument]:
    path = RAW_DATA_DIR / "healthy_meal_plans.csv"
    documents: List[RecipeDocument] = []
    if not path.exists():
        return documents
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for offset, row in enumerate(reader):
            name = (row.get("meal_name") or "Healthy Meal").strip()
            if not name:
                continue
            ingredient_score = float(row.get("num_ingredients", 0.0) or 0.0)
            approx_ingredients = max(1, round(ingredient_score * 10))
            prep_minutes = max(5, round(float(row.get("prep_time", 0.0) or 0.0) * 60))
            calories = round(float(row.get("calories", 0.0) or 0.0) * 900, 2)
            protein = round(float(row.get("protein", 0.0) or 0.0) * 100, 2)
            fat = round(float(row.get("fat", 0.0) or 0.0) * 100, 2)
            carbs = round(float(row.get("carbs", 0.0) or 0.0) * 100, 2)
            diet_tags = []
            for field in [
                ("vegan", "vegan"),
                ("vegetarian", "vegetarian"),
                ("keto", "keto"),
                ("paleo", "paleo"),
                ("gluten_free", "gluten-free"),
                ("mediterranean", "mediterranean"),
            ]:
                if _bool_flag(row.get(field[0])):
                    diet_tags.append(field[1])
            if _bool_flag(row.get("is_healthy")):
                diet_tags.append("healthy")
            description = (
                f"{name} is a meal suggestion with about {calories:.0f} calories per serving, "
                f"{protein:.1f} g protein, {carbs:.1f} g carbs, and {fat:.1f} g fat. "
                f"It typically uses ~{approx_ingredients} ingredients and takes around {prep_minutes} minutes to prepare. "
                f"Diet suitability: {', '.join(diet_tags) if diet_tags else 'general audience'}."
            )
            documents.append(
                RecipeDocument(
                    recipe_id=f"meal-plan-{start_idx + offset}",
                    title=name,
                    text=description,
                    tags=diet_tags,
                    servings=1,
                    calories=calories,
                    protein_g=protein,
                    carb_g=carbs,
                    fat_g=fat,
                )
            )
    return documents


def _load_raw_documents() -> List[RecipeDocument]:
    recipes = _load_recipe_sample_documents()
    meal_plans = _load_meal_plan_documents(start_idx=len(recipes))
    nutrition_recipes = _load_nutrition_recipes(start_idx=len(recipes) + len(meal_plans))
    return recipes + meal_plans + nutrition_recipes


def build_index(force: bool = False) -> None:
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    data_sources = [
        RAW_DATA_DIR / "recipes_sample.csv",
        RAW_DATA_DIR / "healthy_meal_plans.csv",
        RAW_DATA_DIR / "recipes-with-nutrition.csv",
    ]
    index_files = [INDEX_FILE, META_FILE, VECTORS_FILE]
    if INDEX_FILE.exists() and META_FILE.exists() and VECTORS_FILE.exists() and not force:
        data_mtime = _latest_mtime(data_sources)
        index_mtime = _latest_mtime(index_files)
        if data_mtime <= index_mtime:
            return
    documents = _load_raw_documents()
    vectors, backend = _get_embeddings([doc.text for doc in documents])
    if faiss and np is not None:
        array = np.array(vectors, dtype="float32")
        index = faiss.IndexFlatIP(array.shape[1])
        faiss.normalize_L2(array)
        index.add(array)
        faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump([doc.model_dump() for doc in documents], f)
    with open(VECTORS_FILE, "w", encoding="utf-8") as f:
        json.dump({"backend": backend, "vectors": vectors}, f)


def _load_index() -> Tuple[List[List[float]], List[RecipeDocument], str]:
    if not META_FILE.exists() or not VECTORS_FILE.exists():
        build_index()
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta_raw = json.load(f)
        if isinstance(meta_raw, dict) and "documents" in meta_raw:
            meta_list = meta_raw["documents"]
        else:
            meta_list = meta_raw
        meta = [RecipeDocument(**item) for item in meta_list]
    with open(VECTORS_FILE, "r", encoding="utf-8") as f:
        payload: Dict[str, object] | List[List[float]] = json.load(f)
    backend = BACKEND_HASH
    vectors: List[List[float]]
    if isinstance(payload, dict) and "vectors" in payload:
        vectors = payload["vectors"]  # type: ignore[assignment]
        backend = str(payload.get("backend", BACKEND_HASH))
    else:
        vectors = payload  # type: ignore[assignment]
        # Heuristic: assume Gemini backend when embedding dim is larger than hash dim
        backend = BACKEND_GEMINI if vectors and len(vectors[0]) > EMBED_DIM else BACKEND_HASH
    return vectors, meta, backend


def retrieve(query: str, k: int = 6) -> List[Tuple[RecipeDocument, float]]:
    vectors, meta, backend = _load_index()
    if not vectors:
        return []
    target_dim = len(vectors[0]) if vectors else EMBED_DIM
    query_vec = _embed_query(query, backend=backend, target_dim=target_dim)
    scored = []
    for vec, doc in zip(vectors, meta):
        score = _dot(vec, query_vec)
        scored.append((doc, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


__all__ = ["build_index", "retrieve"]
