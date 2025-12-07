"""Cooking assistant tool that wraps recipe RAG retrieval."""
from __future__ import annotations

import csv
import json
import re
from typing import Dict, List

from config import RAW_DATA_DIR
from core.llm import GeminiClient
from core.rag import search_recipes, summarize_recipes


def _load_recipes() -> List[Dict[str, str]]:
    """Load recipes from the sample CSV file."""
    csv_path = RAW_DATA_DIR / "recipes_sample.csv"
    if not csv_path.exists():
        print(f"Warning: Recipe file not found at {csv_path}")
        return []

    try:
        with csv_path.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception as exc:  # pragma: no cover - file issues
        print(f"Error loading recipes: {exc}")
        return []


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _find_recipe(query: str) -> Dict[str, str] | None:
    """Find a recipe whose title matches the query."""
    query_norm = _normalize(query)
    recipes = _load_recipes()

    for recipe in recipes:
        title_norm = _normalize(recipe.get("title", ""))
        if title_norm and title_norm == query_norm:
            return recipe

    for recipe in recipes:
        title_norm = _normalize(recipe.get("title", ""))
        if title_norm and title_norm in query_norm:
            return recipe

    return None


def _guess_base_amount(ingredient: str) -> float:
    """Heuristic base grams per ingredient when structured data is missing."""
    name = ingredient.lower()
    if any(k in name for k in ["salt", "pepper", "spice", "season", "garlic", "ginger", "herb"]):
        return 5
    if any(k in name for k in ["oil", "sauce", "broth", "stock", "milk", "water"]):
        return 120
    if any(k in name for k in ["seed", "chia", "flax"]):
        return 12
    if any(k in name for k in ["butter", "nut", "almond", "peanut"]):
        return 20
    if any(k in name for k in ["bread", "rice", "pasta", "noodle", "grain", "oat"]):
        return 70
    if any(k in name for k in ["banana", "apple", "fruit", "berry"]):
        return 100
    if any(k in name for k in ["chicken", "beef", "turkey", "pork", "fish", "salmon", "shrimp", "tofu", "tempeh"]):
        return 120
    return 80


def _estimate_ingredient_grams(
    ingredients: List[str],
    base_servings: int,
    target_servings: int,
    llm: GeminiClient | None,
) -> Dict[str, float]:
    """Estimate grams for each ingredient, using LLM when available."""
    scale = target_servings / max(1, base_servings)
    estimates = {ing.lower(): _guess_base_amount(ing) * scale for ing in ingredients}

    if llm:
        prompt = (
            "You are a recipe scaler. Given an ingredient list and servings, return ONLY JSON "
            "with grams per ingredient for the target servings. Round grams to whole numbers.\n"
            f"Base servings: {base_servings}\n"
            f"Target servings: {target_servings}\n"
            f"Ingredients: {', '.join(ingredients)}\n\n"
            'Respond as: {"ingredients": [{"name": "ingredient", "grams": 120}]}'
        )
        try:
            llm_response = llm.generate_text(prompt)
            parsed = json.loads(llm_response)
            items = parsed.get("ingredients", []) if isinstance(parsed, dict) else []
            for item in items:
                name = str(item.get("name", "")).lower().strip()
                grams = float(item.get("grams", 0))
                if name and grams > 0:
                    estimates[name] = grams
        except Exception:
            pass

    return {k: round(v, 0) for k, v in estimates.items()}


def _parse_steps(steps_raw: str) -> List[str]:
    """Convert raw steps text into a clean, ordered list."""
    steps = [s.strip() for s in re.split(r"[.\n]", steps_raw) if s.strip()]
    return steps or ["Combine the ingredients and cook until done."]


def _format_instructions(recipe: Dict[str, str], servings: int, llm: GeminiClient | None = None) -> str:
    """Format recipe with steps, scaled ingredients, and macros."""
    title = recipe.get("title", "Recipe")
    description = recipe.get("description") or recipe.get("summary") or ""
    if not description:
        tag_phrase = recipe.get("tags") or "balanced"
        description = f"A {tag_phrase.lower()} take on {title}."
    base_servings = max(1, int(float(recipe.get("servings", 1))))

    cals_per_serving = float(recipe.get("per_serving_calories", 0))
    protein_per_serving = float(recipe.get("protein_g", 0))
    carbs_per_serving = float(recipe.get("carb_g", 0))
    fat_per_serving = float(recipe.get("fat_g", 0))

    total_cals = cals_per_serving * servings
    total_protein = protein_per_serving * servings
    total_carbs = carbs_per_serving * servings
    total_fat = fat_per_serving * servings

    ingredients_raw = recipe.get("ingredients", "")
    ingredients = [i.strip().title() for i in ingredients_raw.split("|") if i.strip()]
    ingredient_grams = _estimate_ingredient_grams(ingredients, base_servings, servings, llm)

    steps_raw = recipe.get("steps", "")
    steps = _parse_steps(steps_raw)

    tags = recipe.get("tags", "")

    lines = [
        f"## {title}",
        description,
        f"*{tags}*" if tags else "",
        f"Servings: {servings}",
        f"### Ingredients for {servings} serving(s)",
    ]

    for ingredient in ingredients:
        grams = ingredient_grams.get(ingredient.lower())
        if grams:
            lines.append(f"- {ingredient}: ~{grams:.0f} g")
        else:
            lines.append(f"- {ingredient}")

    lines.append("### Instructions")
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")

    lines.append("### Nutrition Per Serving")
    lines.append(f"- Calories: {cals_per_serving:.0f} kcal")
    lines.append(f"- Protein: {protein_per_serving:.0f} g")
    lines.append(f"- Carbs: {carbs_per_serving:.0f} g")
    lines.append(f"- Fat: {fat_per_serving:.0f} g")

    lines.append(f"\nTotals for {servings} serving(s):")
    lines.append(f"- Calories: {total_cals:.0f} kcal")
    lines.append(f"- Protein: {total_protein:.0f} g")
    lines.append(f"- Carbs: {total_carbs:.0f} g")
    lines.append(f"- Fat: {total_fat:.0f} g")

    return "\n".join(line for line in lines if line)


def _fallback_recipe_from_doc(doc, servings: int) -> str:
    """Best-effort Markdown recipe when LLM generation is unavailable."""
    tags = doc.tags or []
    parts = (doc.text or "").split("\n")
    description = parts[0].strip() if parts else ""
    if not description:
        tag_phrase = ", ".join(tags) if tags else "healthy"
        description = f"A {tag_phrase} friendly recipe."

    ingredients_text = parts[1] if len(parts) > 1 else ""
    steps_text = parts[2] if len(parts) > 2 else (parts[-1] if parts else "")

    ingredients = [
        segment.strip(" -*")
        for segment in re.split(r"[;|,]", ingredients_text)
        if segment.strip()
    ]
    if not ingredients and ingredients_text:
        ingredients = [ingredients_text.strip(" -*")]
    if not ingredients:
        ingredients = ["Protein of choice", "Vegetables", "Healthy fat or sauce", "Seasonings"]

    base_servings = max(1, getattr(doc, "servings", 1) or 1)
    grams_lookup = _estimate_ingredient_grams(ingredients, base_servings, servings, llm=None)
    steps = _parse_steps(steps_text or description)

    lines = [
        f"## {doc.title}",
        description,
        f"### Ingredients for {servings} serving(s)",
    ]
    for ingredient in ingredients:
        grams = grams_lookup.get(ingredient.lower())
        if grams:
            lines.append(f"- {ingredient}: ~{grams:.0f} g")
        else:
            lines.append(f"- {ingredient}")

    lines.append("### Steps")
    for idx, step in enumerate(steps, 1):
        lines.append(f"{idx}. {step}")

    lines.append("### Estimated macros per serving")
    lines.append(f"- Calories: {doc.calories:.0f} kcal")
    lines.append(f"- Protein: {doc.protein_g:.0f} g")
    lines.append(f"- Carbs: {doc.carb_g:.0f} g")
    lines.append(f"- Fat: {doc.fat_g:.0f} g")

    return "\n".join(line for line in lines if line)


def grounded_cooking_response(
    query: str,
    servings: int = 2,
    top_k: int = 5,
    llm: GeminiClient | None = None,
) -> Dict[str, object]:
    """Generate a grounded answer using direct recipe lookups or RAG summaries."""
    servings = max(1, int(servings))

    instruction_keywords = [
        "how to",
        "how do i",
        "make",
        "cook",
        "prepare",
        "instructions",
        "steps",
        "recipe",
        "recipe for",
        "guide",
        "directions",
    ]
    query_lower = query.lower()
    is_instruction_request = any(kw in query_lower for kw in instruction_keywords) or bool(
        re.search(r"\b(how to|recipe for|how do i (cook|make))\b", query_lower)
    )

    try:
        results = search_recipes(query, k=top_k)
    except Exception as exc:  # pragma: no cover - integration error
        print(f"Error in RAG search: {exc}")
        return {
            "answer": (
                f"I encountered an error searching recipes: {exc}\n\n"
                "Please try simplifying your query or check that recipe data files exist."
            ),
            "sources": [],
        }

    sources = [
        {
            "title": res.document.title,
            "tags": res.document.tags,
            "servings": res.document.servings,
            "calories": res.document.calories,
            "protein_g": res.document.protein_g,
            "carb_g": res.document.carb_g,
            "fat_g": res.document.fat_g,
        }
        for res in results
    ]

    best_doc = results[0].document if results else None

    if is_instruction_request:
        recipe = _find_recipe(query)
        if recipe:
            active_llm = llm or GeminiClient()
            answer = _format_instructions(recipe, servings, llm=active_llm)
            recipe_sources = sources or [
                {
                    "title": recipe.get("title", "Recipe"),
                    "servings": servings,
                    "calories": float(recipe.get("per_serving_calories", 0)),
                    "protein_g": float(recipe.get("protein_g", 0)),
                    "carb_g": float(recipe.get("carb_g", 0)),
                    "fat_g": float(recipe.get("fat_g", 0)),
                }
            ]
            return {"answer": answer, "sources": recipe_sources}

        if best_doc:
            active_llm = llm or GeminiClient()
            doc_tags = best_doc.tags or []
            if isinstance(doc_tags, str):
                doc_tags = [doc_tags]
            tags_text = ", ".join(doc_tags) or "general"

            # Extract actual recipe data from the document text
            # Document text format: "Title\nIngredients\nSteps\nTags"
            parts = (best_doc.text or "").split("\n")
            ingredients_raw = parts[1] if len(parts) > 1 else "Not available in database"
            steps_raw = parts[2] if len(parts) > 2 else "Not available in database"

            prompt = f"""
You are a professional recipe formatter for a nutrition tracking app.

IMPORTANT: You must use ONLY the information provided below. Do not add, remove, or modify ingredients or steps.

Recipe Title: "{best_doc.title}"

Ingredients (from database): {ingredients_raw}

Cooking Steps (from database): {steps_raw}

Per-serving macros (verified from database):
- Calories: {best_doc.calories:.0f} kcal
- Protein: {best_doc.protein_g:.0f} g
- Carbohydrates: {best_doc.carb_g:.0f} g
- Fats: {best_doc.fat_g:.0f} g

Dietary tags: {tags_text}
Number of servings to scale to: {servings} (original recipe is for {best_doc.servings} servings)

Your task:
1. Format the recipe clearly in Markdown
2. Scale ingredient quantities to {servings} serving(s) if needed
3. Use the EXACT ingredients and steps provided above - do not invent new ones
4. Add gram measurements where reasonable based on the scaled servings
5. Include all macro information per serving

Output format:
1. A one-sentence description based on the tags
2. "Ingredients for {servings} serving(s)" - list with gram amounts
3. "Steps" - numbered list of the provided cooking steps
4. "Nutrition per serving" - the exact macros provided above

CRITICAL: Use only the ingredients and steps given above. Do not hallucinate or add creative details.
"""
            try:
                llm_answer = active_llm.generate_text(prompt) if active_llm else ""
            except Exception as exc:  # pragma: no cover - llm error
                print(f"LLM generation error: {exc}")
                llm_answer = ""

            llm_answer = (llm_answer or "").strip()
            needs_fallback = (not llm_answer) or ("offline mode" in llm_answer.lower())
            final_answer = llm_answer if not needs_fallback else _fallback_recipe_from_doc(best_doc, servings)

            primary_source = {
                "title": best_doc.title,
                "tags": best_doc.tags,
                "servings": best_doc.servings,
                "calories": best_doc.calories,
                "protein_g": best_doc.protein_g,
                "carb_g": best_doc.carb_g,
                "fat_g": best_doc.fat_g,
            }
            source_list = sources or [primary_source]
            return {"answer": final_answer, "sources": source_list}

        return {
            "answer": (
                "I could not find recipe matches for that request. "
                "Try a different main ingredient or cuisine."
            ),
            "sources": sources,
        }

    summary = summarize_recipes(query, servings=servings, k=top_k)
    return {"answer": summary, "sources": sources}


def recipe_steps(query: str, servings: int = 1) -> Dict[str, object]:
    """Legacy alias for grounded_cooking_response."""
    return grounded_cooking_response(query, servings)


__all__ = ["grounded_cooking_response", "recipe_steps"]
