"""Cooking assistant tool."""
from __future__ import annotations

import csv
import textwrap
import re
import re
from typing import Dict, List

from config import RAW_DATA_DIR
from core.llm import GeminiClient
from core.prompts import COOKING_PROMPT
from core.rag import search_recipes
from core.schemas import MealItem, PlanMeal, RecipeDocument, Step
from tools.ingredient_weights import estimate_ingredient_grams


def _load_dataset() -> List[Dict[str, str]]:
    with (RAW_DATA_DIR / "recipes_sample.csv").open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _find_recipe(query: str) -> Dict[str, str]:
    data = _load_dataset()
    query_lower = query.lower()
    for row in data:
        title_lower = row["title"].lower()
        if query_lower in title_lower or title_lower in query_lower:
            return row
    for row in data:
        if query_lower in row["ingredients"].lower():
            return row
    raise ValueError(f"Recipe not found for query: {query}")


def _normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(cleaned.split())


def _find_recipe_by_title(query: str) -> Dict[str, str]:
    """Return a recipe whose title appears verbatim in the query."""
    normalized_query = _normalize_text(query)
    data = _load_dataset()
    for row in data:
        title_norm = _normalize_text(row["title"])
        if title_norm and title_norm in normalized_query:
            return row
    raise ValueError(f"Recipe title not found for query: {query}")


def _suggest_recipes(query: str, limit: int = 3) -> List[Dict[str, str]]:
    """Return similar recipes even when the query isn't an exact match."""
    data = _load_dataset()
    terms = [token.lower() for token in query.split() if token.strip()]
    scored: List[tuple[int, Dict[str, str]]] = []
    for row in data:
        haystack = f"{row['title']} {row['ingredients']}".lower()
        score = sum(term in haystack for term in terms) or 0
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    filtered = [row for score, row in scored if score > 0][:limit]
    if filtered:
        return filtered
    return [row for _, row in scored[:limit]] if scored else []


def recipe_steps(query: str, servings: int = 1) -> Dict[str, List[Step]]:
    row = _find_recipe(query)
    steps_raw = row["steps"].split(".")
    parsed: List[Step] = []
    for idx, step in enumerate(filter(None, [s.strip() for s in steps_raw]), start=1):
        parsed.append(
            Step(
                idx=idx,
                instruction=step,
                estimated_minutes=5,
                tips=["Read the entire step before starting."],
                substitutions=["Swap similar vegetables if needed."],
            )
        )
    base_servings = int(float(row.get("servings", 1))) or 1
    scale = servings / base_servings
    ingredients = []
    for ingredient in row["ingredients"].split("|"):
        ingredients.append(
            MealItem(
                name=ingredient.title(),
                quantity=scale,
                unit="serving",
                calories=float(row["per_serving_calories"]) * scale,
                protein_g=float(row["protein_g"]) * scale,
                carb_g=float(row["carb_g"]) * scale,
                fat_g=float(row["fat_g"]) * scale,
                estimated=True,
            )
        )
    meal = PlanMeal(name=row["title"], meal_type="dinner", items=ingredients, notes=row.get("tags"))
    return {"steps": parsed, "meal": meal}


COOK_KEYWORDS = (
    "cook",
    "make",
    "prepare",
    "instructions",
    "how do i",
    "step",
    "recipe for",
    "guide",
)


def _is_instruction_request(query: str) -> bool:
    lowered = query.lower()
    return any(keyword in lowered for keyword in COOK_KEYWORDS)


def _local_instruction_response(query: str, servings: int) -> Dict[str, object] | None:
    try:
        row = _find_recipe_by_title(query)
    except ValueError:
        return None
    servings = max(1, int(servings))
    ingredients = [
        ingredient.strip().title()
        for ingredient in row["ingredients"].split("|")
        if ingredient.strip()
    ]
    steps_raw = [s.strip() for s in row["steps"].split(".") if s.strip()]
    per_serving_macros = {
        "calories": float(row["per_serving_calories"]),
        "protein_g": float(row["protein_g"]),
        "carb_g": float(row["carb_g"]),
        "fat_g": float(row["fat_g"]),
    }
    totals = {key: value * servings for key, value in per_serving_macros.items()}
    lines = [
        f"NutriTrack found **{row['title']}**. Here's how to cook it for {servings} serving(s).",
    ]
    try:
        estimates = estimate_ingredient_grams(ingredients, per_serving_macros["calories"], servings)
    except ValueError:
        estimates = []
    lines.append("")
    lines.append("### Ingredients (with estimated grams per serving)")
    if estimates:
        for entry in estimates:
            lines.append(
                f"- {entry['ingredient']} ({entry['grams_per_serving']:.0f} g per serving)"
            )
        missing = {ingredient.title() for ingredient in ingredients} - {
            entry["ingredient"] for entry in estimates
        }
        for ingredient in missing:
            lines.append(f"- {ingredient}")
    else:
        lines.extend(f"- {ingredient}" for ingredient in ingredients)
    lines.append("")
    lines.append("### Steps")
    for idx, instruction in enumerate(steps_raw, start=1):
        lines.append(f"{idx}. {instruction}")
    lines.append("")
    lines.append("### Macros")
    lines.append(
        f"- Per serving: {per_serving_macros['calories']:.0f} kcal, "
        f"{per_serving_macros['protein_g']:.1f}g protein, "
        f"{per_serving_macros['carb_g']:.1f}g carbs, "
        f"{per_serving_macros['fat_g']:.1f}g fat"
    )
    lines.append(
        f"- Total ({servings} servings): {totals['calories']:.0f} kcal, "
        f"{totals['protein_g']:.1f}g protein, "
        f"{totals['carb_g']:.1f}g carbs, "
        f"{totals['fat_g']:.1f}g fat"
    )
    base_servings = max(1, int(float(row.get("servings", 1)) or 1))
    scale = servings / base_servings
    sources = [
        {
            "title": row["title"],
            "tags": [tag for tag in row.get("tags", "").split(";") if tag.strip()],
            "servings": base_servings,
            "per_serving_macros": per_serving_macros,
            "scaled_macros": {
                "calories": round(per_serving_macros["calories"] * scale, 2),
                "protein_g": round(per_serving_macros["protein_g"] * scale, 2),
                "carb_g": round(per_serving_macros["carb_g"] * scale, 2),
                "fat_g": round(per_serving_macros["fat_g"] * scale, 2),
            },
        }
    ]
    return {"answer": "\n".join(lines), "sources": sources}


def _format_recipe_context(doc: RecipeDocument) -> str:
    section = textwrap.dedent(
        f"""
        Recipe: {doc.title}
        Tags: {', '.join(doc.tags) or 'none'}
        Servings: {doc.servings}
        Calories per serving: {doc.calories}
        Protein per serving: {doc.protein_g}
        Carbs per serving: {doc.carb_g}
        Fat per serving: {doc.fat_g}
        Content:
        {doc.text}
        """
    )
    return section.strip()


def grounded_cooking_response(
    query: str,
    servings: int = 1,
    top_k: int = 4,
    llm: GeminiClient | None = None,
) -> Dict[str, object]:
    """Return a grounded NutriTrack response using RAG over recipes."""
    servings = max(1, int(servings))
    if _is_instruction_request(query):
        direct = _local_instruction_response(query, servings)
        if direct:
            return direct

    results = search_recipes(query, k=top_k)
    if not results:
        suggestions = _suggest_recipes(query)
        if not suggestions:
            return {
                "answer": (
                    "NutriTrack doesn't recognize that recipe yet and couldn't find "
                    "any close matches. Try describing it differently or specify an ingredient."
                ),
                "sources": [],
            }
        lines = [
            "NutriTrack couldn't find that exact dish, but these recipes are close matches:"
        ]
        sources: List[Dict[str, object]] = []
        for row in suggestions:
            base_servings = max(1, int(float(row.get("servings", 1)) or 1))
            scale = servings / base_servings
            scaled_macros = {
                "calories": round(float(row["per_serving_calories"]) * scale, 2),
                "protein_g": round(float(row["protein_g"]) * scale, 2),
                "carb_g": round(float(row["carb_g"]) * scale, 2),
                "fat_g": round(float(row["fat_g"]) * scale, 2),
            }
            lines.append(
                f"- **{row['title']}** ({scaled_macros['calories']:.0f} kcal total, "
                f"{scaled_macros['protein_g']:.0f}g protein for {servings} servings)"
            )
            sources.append(
                {
                    "title": row["title"],
                    "tags": row.get("tags", "").split(";"),
                    "servings": base_servings,
                    "per_serving_macros": {
                        "calories": float(row["per_serving_calories"]),
                        "protein_g": float(row["protein_g"]),
                        "carb_g": float(row["carb_g"]),
                        "fat_g": float(row["fat_g"]),
                    },
                    "scaled_macros": scaled_macros,
                }
            )
        return {"answer": "\n".join(lines), "sources": sources}

    llm = llm or GeminiClient()
    context_blocks: List[str] = []
    sources: List[Dict[str, object]] = []
    for result in results:
        doc = result.document
        context_blocks.append(_format_recipe_context(doc))
        scale = servings / max(1, doc.servings)
        scaled_macros = {
            "calories": round(doc.calories * scale, 2),
            "protein_g": round(doc.protein_g * scale, 2),
            "carb_g": round(doc.carb_g * scale, 2),
            "fat_g": round(doc.fat_g * scale, 2),
        }
        sources.append(
            {
                "title": doc.title,
                "tags": doc.tags,
                "servings": doc.servings,
                "per_serving_macros": {
                    "calories": doc.calories,
                    "protein_g": doc.protein_g,
                    "carb_g": doc.carb_g,
                    "fat_g": doc.fat_g,
                },
                "scaled_macros": scaled_macros,
            }
        )
    context = "\n\n".join(context_blocks)
    prompt = textwrap.dedent(
        f"""
        {COOKING_PROMPT}

        You are NutriTrack, a culinary agent that always grounds answers in the recipes provided.
        Decide what the user needs:
        - If they explicitly ask to cook, prepare, or get instructions for a meal, pick the single best recipe.
          Respond with sections:
            * Overview explaining why the recipe fits.
            * Ingredients list with quantities from the context.
            * Macros per serving and for {servings} servings (calories, protein, carbs, fat).
            * Numbered step-by-step instructions pulled from the context.
        - If they ask for ideas or recipes containing an ingredient (e.g., "give me recipes with chicken"),
          list up to three relevant recipes. For each recipe include calories/protein/carbs/fat per serving,
          total macros for {servings} servings, and a short summary. No steps unless explicitly requested.
        - Never invent data not in the context.

        User request: {query}
        Requested servings: {servings}

        Retrieved recipes:
        {context}
        """
    ).strip()
    try:
        answer = llm.generate_text(prompt)
    except Exception:
        top = sources[0]
        fallback_lines = [
            "NutriTrack can't reach the recipe brain right now, so here's a quick suggestion."
        ]
        fallback_lines.append(
            f"Try **{top['title']}** "
            f"({top['scaled_macros']['calories']:.0f} kcal total for {servings} servings, "
            f"{top['scaled_macros']['protein_g']:.0f}g protein)."
        )
        fallback_lines.append("Please try again in a moment for full instructions.")
        answer = "\n\n".join(fallback_lines)
    return {"answer": answer, "sources": sources}


__all__ = ["recipe_steps", "grounded_cooking_response"]
