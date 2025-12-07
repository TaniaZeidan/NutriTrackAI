"""RAG pipeline helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

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


def _parse_recipe_text(doc: RecipeDocument) -> Tuple[str, str]:
    """Extract a best-effort ingredients and steps snippet from stored text."""
    parts = (doc.text or "").split("\n")
    ingredients = parts[1] if len(parts) > 1 else ""
    steps = parts[2] if len(parts) > 2 else parts[-1] if parts else ""
    return ingredients, steps


def summarize_recipes(query: str, servings: int = 2, k: int = 4) -> str:
    """Return a human-readable summary of top recipe matches and macros."""
    matches = search_recipes(query, k=k)
    if not matches:
        return (
            "I could not find recipes for that request. "
            "Try asking for a specific cuisine or ingredient."
        )

    lines: List[str] = [f"### Top recipe ideas for '{query}':"]
    for idx, result in enumerate(matches, start=1):
        doc = result.document
        scale = max(0.1, servings / max(1, doc.servings))
        calories = doc.calories * scale
        protein = doc.protein_g * scale
        carbs = doc.carb_g * scale
        fat = doc.fat_g * scale
        ingredients, steps = _parse_recipe_text(doc)

        short_steps = "; ".join(
            step.strip().capitalize()
            for step in steps.split(".")
            if step.strip()
        )
        if len(short_steps) > 220:
            short_steps = short_steps[:217].rsplit(";", 1)[0].strip() + "..."

        lines.append(
            f"- **{idx}. {doc.title}** for {servings} serving(s): "
            f"{calories:.0f} kcal | P {protein:.0f} g / C {carbs:.0f} g / F {fat:.0f} g"
        )
        if ingredients:
            lines.append(f"  - Key ingredients: {ingredients}")
        if short_steps:
            lines.append(f"  - Steps: {short_steps}")
        if doc.tags:
            lines.append(f"  - Tags: {', '.join(doc.tags)}")

    lines.append(
        "Ask for full instructions on any recipe above and I'll expand the steps."
    )
    return "\n".join(lines)


__all__ = ["build_index", "search_recipes", "summarize_recipes", "RetrievalResult"]
