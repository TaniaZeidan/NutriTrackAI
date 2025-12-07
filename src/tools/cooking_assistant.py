from __future__ import annotations
from typing import Dict, List
from config import RAW_DATA_DIR
from core.llm import GeminiClient
from core.rag import search_recipes
import time
import csv
import re

# Cache and rate limiting
_response_cache = {}
_last_llm_call = 0
_min_call_interval = 2


def _load_recipes() -> List[Dict[str, str]]:
    """Load recipes from CSV - handles both 'title' and 'meal_name' columns."""
    csv_path = RAW_DATA_DIR / "healthy_meal_plans.csv"
    if not csv_path.exists():
        print(f"Warning: Recipe file not found at {csv_path}")
        return []
    
    try:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            recipes = []
            for row in reader:
                # Map meal_name -> title if needed
                if 'meal_name' in row and 'title' not in row:
                    row['title'] = row['meal_name']
                recipes.append(row)
            return recipes
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _find_recipe(query: str) -> Dict[str, str] | None:
    """Find recipe by title match."""
    query_norm = _normalize(query)
    recipes = _load_recipes()
    
    # Try exact match
    for recipe in recipes:
        title = recipe.get("title") or recipe.get("meal_name", "")
        if _normalize(title) == query_norm:
            return recipe
    
    # Try contains match
    for recipe in recipes:
        title = recipe.get("title") or recipe.get("meal_name", "")
        if query_norm in _normalize(title):
            return recipe
    
    return None


def _format_instructions(recipe: Dict[str, str], servings: int) -> str:
    """Format recipe with available information."""
    title = recipe.get("title") or recipe.get("meal_name", "Recipe")
    base_servings = 1
    scale = servings
    
    # Get macros - handle normalized values (0-1) from CSV
    cals = float(recipe.get("calories", 0))
    protein = float(recipe.get("protein", 0))
    carbs = float(recipe.get("carbs", 0))
    fat = float(recipe.get("fat", 0))
    
    # Denormalize if values are 0-1 range
    if cals < 2:
        cals = cals * 600 + 200
    if protein < 2:
        protein = protein * 50
    if carbs < 2:
        carbs = carbs * 80
    if fat < 2:
        fat = fat * 30
    
    # Get dietary tags
    tags = []
    for tag, col in [("vegan", "vegan"), ("vegetarian", "vegetarian"), 
                     ("keto", "keto"), ("paleo", "paleo"),
                     ("gluten-free", "gluten_free"), ("mediterranean", "mediterranean"),
                     ("healthy", "is_healthy")]:
        if str(recipe.get(col, "0")) in ["1", "True", "true"]:
            tags.append(tag)
    
    # Build response
    lines = [
        f"# {title}",
        f"*{', '.join(tags)}*\n" if tags else "",
        f"**Servings:** {servings}\n",
        "## Ingredients\n",
        "*Ingredient details not available in this dataset*\n",
        "## Instructions\n",
        "*Detailed cooking instructions not available in this dataset*\n",
        "## Nutrition Information\n",
        "**Per Serving:**",
        f"- Calories: {cals:.0f} kcal",
        f"- Protein: {protein:.0f}g",
        f"- Carbs: {carbs:.0f}g",
        f"- Fat: {fat:.0f}g",
        f"\n**Total for {servings} serving(s):**",
        f"- Calories: {cals * servings:.0f} kcal",
        f"- Protein: {protein * servings:.0f}g",
        f"- Carbs: {carbs * servings:.0f}g",
        f"- Fat: {fat * servings:.0f}g"
    ]
    
    return "\n".join(lines)


def _build_recipe_context(results: List, servings: int) -> str:
    """Build context from RAG results."""
    context_parts = []
    
    for i, result in enumerate(results, 1):
        doc = result.document
        scale = servings / max(1, doc.servings)
        
        recipe_info = (
            f"Recipe {i}: {doc.title}\n"
            f"Tags: {', '.join(doc.tags) if doc.tags else 'None'}\n"
            f"For {servings} serving(s): {doc.calories * scale:.0f} kcal, "
            f"Protein: {doc.protein_g * scale:.0f}g, Carbs: {doc.carb_g * scale:.0f}g, Fat: {doc.fat_g * scale:.0f}g\n"
        )
        context_parts.append(recipe_info)
    
    return "\n".join(context_parts)


def grounded_cooking_response(
    query: str,
    servings: int = 2,
    top_k: int = 3,
    llm: GeminiClient | None = None
) -> Dict[str, object]:
    """Main cooking response using RAG + LLM."""
    servings = max(1, int(servings))
    llm = llm or GeminiClient()
    
    instruction_keywords = ["how", "how to", "how do i", "make", "cook", "prepare", "instructions", "steps"]
    is_instruction_request = any(kw in query.lower() for kw in instruction_keywords)
    
    # Try exact recipe match for instructions
    if is_instruction_request:
        recipe = _find_recipe(query)
        if recipe:
            return {
                "answer": _format_instructions(recipe, servings),
                "sources": [{"title": recipe.get("title") or recipe.get("meal_name")}]
            }
        else:
            # Clean query for RAG
            for kw in instruction_keywords:
                query = query.lower().replace(kw, "").strip()
            query = query.replace("?", "").strip()
    
    # RAG search
    try:
        results = search_recipes(query, k=top_k)
    except Exception as e:
        return {
            "answer": f"Error searching recipes: {e}\nTry a simpler query.",
            "sources": []
        }
    
    if not results:
        return {
            "answer": "No recipes found. Try: 'chicken recipes', 'vegetarian meals', 'high protein'",
            "sources": []
        }
    
    # Check cache
    cache_key = f"{_normalize(query)}:{servings}"
    if cache_key in _response_cache:
        return _response_cache[cache_key]
    
    # Build LLM prompt
    context = _build_recipe_context(results, servings)
    prompt = f"""User: "{query}"

{context}

{"Say you don't have that exact recipe but suggest alternatives." if is_instruction_request else ""}

Brief response (100 words):
- Best 1-2 options
- Calories & protein
- Dietary tags
End: "Ask 'How do I make [recipe]?' for details"

Only use data above."""

    try:
        # Rate limiting
        global _last_llm_call
        wait = _min_call_interval - (time.time() - _last_llm_call)
        if wait > 0:
            time.sleep(wait)
        
        _last_llm_call = time.time()
        llm_response = llm.generate_text(prompt)
        
        sources = [{"title": r.document.title, "tags": r.document.tags} for r in results]
        result_dict = {"answer": llm_response, "sources": sources}
        
        # Cache (max 50)
        if len(_response_cache) >= 50:
            _response_cache.pop(next(iter(_response_cache)))
        _response_cache[cache_key] = result_dict
        
        return result_dict
    
    except Exception as e:
        # Rate limit or other error
        if any(x in str(e).lower() for x in ["rate limit", "quota", "429"]):
            return {
                "answer": (
                    "⏱️ **Rate limit**\n\n" +
                    "\n".join([f"**{i+1}. {r.document.title}** - {r.document.calories * servings / max(1, r.document.servings):.0f} kcal"
                              for i, r in enumerate(results)]) +
                    "\n\n💡 Ask 'How do I make [name]?' for details"
                ),
                "sources": [{"title": r.document.title} for r in results]
            }
        
        # Generic fallback
        return {
            "answer": "\n".join([
                "**Recipes:**\n",
                *[f"{i+1}. **{r.document.title}** ({r.document.calories * servings / max(1, r.document.servings):.0f} kcal, {r.document.protein_g * servings / max(1, r.document.servings):.0f}g protein)"
                  for i, r in enumerate(results)]
            ]),
            "sources": [{"title": r.document.title} for r in results]
        }


def recipe_steps(query: str, servings: int = 1) -> Dict[str, object]:
    """Legacy compatibility."""
    return grounded_cooking_response(query, servings)


__all__ = ["grounded_cooking_response", "recipe_steps"]