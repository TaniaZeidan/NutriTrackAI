"""Embedding utilities using Google Generative AI and FAISS."""
from __future__ import annotations

import csv
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

from config import FAISS_INDEX_DIR, RAW_DATA_DIR
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


def _bool_flag(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _load_meal_plan_documents(start_idx: int = 0) -> List[RecipeDocument]:
    """
    Load meal plan documents from healthy_meal_plans.csv.
    UPDATED: Creates better search text that includes actual recipe name words.
    """
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
            
            # Denormalize values (CSV has 0-1 range)
            ingredient_score = float(row.get("num_ingredients", 0.0) or 0.0)
            approx_ingredients = max(1, round(ingredient_score * 10))
            prep_minutes = max(5, round(float(row.get("prep_time", 0.0) or 0.0) * 60))
            calories = round(float(row.get("calories", 0.0) or 0.0) * 900, 2)
            protein = round(float(row.get("protein", 0.0) or 0.0) * 100, 2)
            fat = round(float(row.get("fat", 0.0) or 0.0) * 100, 2)
            carbs = round(float(row.get("carbs", 0.0) or 0.0) * 100, 2)
            
            # Extract diet tags
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
            
            # Add macro-based tags for better search
            if protein > 25:
                diet_tags.append("high-protein")
            if calories < 300:
                diet_tags.append("low-calorie")
            if carbs < 20:
                diet_tags.append("low-carb")
            
            # IMPROVED: Create search text that emphasizes recipe name and key ingredients
            # This makes "beef" queries match "Beef Stew", "chicken" match "Grilled Chicken", etc.
            name_words = name.lower().split()
            
            # Extract ALL meaningful words from name (not just protein keywords)
            # This ensures "Gluten-Free Pasta" matches "gluten" and "pasta" queries
            stop_words = {'a', 'an', 'the', 'with', 'and', 'or', 'for', 'in', 'on'}
            meaningful_words = [w for w in name_words if w not in stop_words and len(w) > 2]
            
            # Extract key ingredient/dish type words
            protein_keywords = ['beef', 'chicken', 'salmon', 'tuna', 'shrimp', 'turkey', 
                               'pork', 'lamb', 'tofu', 'tempeh', 'lentil', 'bean', 'chickpea']
            dish_keywords = ['pasta', 'pizza', 'bowl', 'wrap', 'salad', 'soup', 'stew', 
                           'tacos', 'burger', 'sandwich', 'noodles', 'rice', 'curry']
            
            main_ingredients = [word for word in name_words if word in protein_keywords]
            dish_types = [word for word in name_words if word in dish_keywords]
            
            # Build search-optimized text with heavy repetition of key terms
            search_parts = [
                name,  # Full name (most important)
                name,  # Repeat for emphasis
                name,  # Triple repetition for hash embedding
                ' '.join(meaningful_words),  # All meaningful words from name
                ' '.join(meaningful_words),  # Repeat meaningful words
                ' '.join(main_ingredients * 2) if main_ingredients else '',  # Protein keywords x2
                ' '.join(dish_types * 2) if dish_types else '',  # Dish types x2
                ' '.join(diet_tags),  # Diet tags
            ]
            
            # Add descriptive terms based on macros
            if protein > 30:
                search_parts.append('high protein protein-rich')
            if protein > 20:
                search_parts.append('protein')
            if calories < 350:
                search_parts.append('light low-calorie healthy')
            if carbs < 20:
                search_parts.append('low-carb keto-friendly')
            
            # Create full description for the text field
            description = (
                f"{name}. "
                f"A {', '.join(diet_tags) if diet_tags else 'balanced'} meal with "
                f"{calories:.0f} calories, {protein:.1f}g protein, {carbs:.1f}g carbs, {fat:.1f}g fat. "
                f"Uses ~{approx_ingredients} ingredients, prep time ~{prep_minutes} min."
            )
            
            # The search text is what gets embedded - this is critical for matching
            search_text = ' '.join(filter(None, search_parts))
            
            documents.append(
                RecipeDocument(
                    recipe_id=f"meal-plan-{start_idx + offset}",
                    title=name,
                    text=search_text,  # USE SEARCH TEXT for embedding
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
    return recipes + meal_plans


def build_index(force: bool = False) -> None:
    """Build the FAISS index from recipe data."""
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_FILE.exists() and META_FILE.exists() and VECTORS_FILE.exists() and not force:
        return
    
    print("Building index from recipe data...")
    documents = _load_raw_documents()
    print(f"Loaded {len(documents)} recipes")
    
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
    
    print(f"✅ Index built with {len(documents)} recipes")


def _load_index() -> Tuple[List[List[float]], List[RecipeDocument]]:
    if not META_FILE.exists() or not VECTORS_FILE.exists():
        build_index()
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = [RecipeDocument(**item) for item in json.load(f)]
    with open(VECTORS_FILE, "r", encoding="utf-8") as f:
        vectors = json.load(f)
    return vectors, meta


def retrieve(query: str, k: int = 6) -> List[Tuple[RecipeDocument, float]]:
    """
    Retrieve top-k recipes matching the query.
    Uses hybrid approach: text matching + embedding similarity.
    """
    vectors, meta = _load_index()
    query_lower = query.lower().strip()
    
    # Step 1: Try exact/substring text matching first (most reliable)
    text_matches = []
    for doc in meta:
        title_lower = doc.title.lower()
        
        # Exact match - highest score
        if query_lower == title_lower:
            text_matches.append((doc, 1.0))
        # Contains query - high score
        elif query_lower in title_lower:
            text_matches.append((doc, 0.9))
        # Query words in title - medium score  
        else:
            query_words = query_lower.split()
            title_words = title_lower.split()
            matches = sum(1 for qw in query_words if any(qw in tw for tw in title_words))
            if matches > 0:
                score = 0.7 + (matches / len(query_words)) * 0.2
                text_matches.append((doc, score))
    
    # Step 2: If we have good text matches, use those
    if text_matches:
        text_matches.sort(key=lambda x: x[1], reverse=True)
        if text_matches[0][1] > 0.85:  # Strong text match
            return text_matches[:k]
    
    # Step 3: Enhance query for embedding search
    query_enhanced = query_lower
    if 'beef' in query_lower:
        query_enhanced += ' beef meat protein'
    elif 'chicken' in query_lower:
        query_enhanced += ' chicken poultry protein'
    elif 'salmon' in query_lower or 'fish' in query_lower:
        query_enhanced += ' salmon fish seafood protein'
    elif 'pasta' in query_lower:
        query_enhanced += ' pasta noodles italian'
    elif 'gluten' in query_lower:
        query_enhanced += ' gluten-free gluten free'
    
    query_vec = _normalize(_hash_embed(query_enhanced))
    
    # Step 4: Combine text matching scores with embedding scores
    scored = []
    text_match_dict = {doc.recipe_id: score for doc, score in text_matches}
    
    for vec, doc in zip(vectors, meta):
        embed_score = _dot(vec, query_vec)
        text_score = text_match_dict.get(doc.recipe_id, 0.0)
        
        # Weighted combination: 70% text matching, 30% embedding
        final_score = (text_score * 0.7) + (embed_score * 0.3)
        scored.append((doc, final_score))
    
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


__all__ = ["build_index", "retrieve"]