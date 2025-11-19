"""Cooking assistant tool - simplified and functional."""
from __future__ import annotations

import csv
import re
from typing import Dict, List

from config import RAW_DATA_DIR
from core.llm import GeminiClient
from core.rag import search_recipes


def _load_recipes() -> List[Dict[str, str]]:
    """Load recipes from CSV."""
    csv_path = RAW_DATA_DIR / "recipes_sample.csv"
    if not csv_path.exists():
        print(f"Warning: Recipe file not found at {csv_path}")
        return []
    
    try:
        with csv_path.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _find_recipe(query: str) -> Dict[str, str] | None:
    """Find recipe by title match in query."""
    query_norm = _normalize(query)
    recipes = _load_recipes()
    
    # Try exact title match first
    for recipe in recipes:
        title_norm = _normalize(recipe.get("title", ""))
        if title_norm and title_norm == query_norm:
            return recipe
    
    # Try contains match
    for recipe in recipes:
        title_norm = _normalize(recipe.get("title", ""))
        if title_norm and title_norm in query_norm:
            return recipe
    
    return None


def _format_instructions(recipe: Dict[str, str], servings: int) -> str:
    """Format recipe with full instructions and nutrition info."""
    title = recipe.get("title", "Recipe")
    base_servings = max(1, int(float(recipe.get("servings", 1))))
    scale = servings / base_servings
    
    # Get macros per serving
    cals_per_serving = float(recipe.get("per_serving_calories", 0))
    protein_per_serving = float(recipe.get("protein_g", 0))
    carbs_per_serving = float(recipe.get("carb_g", 0))
    fat_per_serving = float(recipe.get("fat_g", 0))
    
    # Calculate totals
    total_cals = cals_per_serving * servings
    total_protein = protein_per_serving * servings
    total_carbs = carbs_per_serving * servings
    total_fat = fat_per_serving * servings
    
    # Parse ingredients and steps
    ingredients_raw = recipe.get("ingredients", "")
    ingredients = [i.strip().title() for i in ingredients_raw.split("|") if i.strip()]
    
    steps_raw = recipe.get("steps", "")
    steps = [s.strip() for s in steps_raw.split(".") if s.strip()]
    
    # Get tags
    tags = recipe.get("tags", "")
    
    # Build response
    lines = [
        f"# {title}",
        f"*{tags}*\n" if tags else "",
        f"**Servings:** {servings}\n",
        "## Ingredients\n"
    ]
    
    for ingredient in ingredients:
        lines.append(f"- {ingredient}")
    
    lines.append("\n## Instructions\n")
    
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")
    
    lines.append("\n## Nutrition Information\n")
    
    lines.append("**Per Serving:**")
    lines.append(f"- Calories: {cals_per_serving:.0f} kcal")
    lines.append(f"- Protein: {protein_per_serving:.0f}g")
    lines.append(f"- Carbs: {carbs_per_serving:.0f}g")
    lines.append(f"- Fat: {fat_per_serving:.0f}g")
    
    lines.append(f"\n**Total for {servings} serving(s):**")
    lines.append(f"- Calories: {total_cals:.0f} kcal")
    lines.append(f"- Protein: {total_protein:.0f}g")
    lines.append(f"- Carbs: {total_carbs:.0f}g")
    lines.append(f"- Fat: {total_fat:.0f}g")
    
    return "\n".join(lines)


def grounded_cooking_response(
    query: str,
    servings: int = 2,
    top_k: int = 5,
    llm: GeminiClient | None = None
) -> Dict[str, object]:
    """Main cooking response function using RAG.
    
    This function provides two types of responses:
    1. If asking for specific recipe instructions: Returns formatted recipe with steps
    2. If searching for recipes: Returns list of matching recipes from RAG
    
    Args:
        query: User's cooking question
        servings: Number of servings to prepare
        top_k: Number of recipes to retrieve from RAG
        llm: LLM client (optional, not used in current implementation)
    
    Returns:
        Dictionary with:
        - answer: Formatted response string
        - sources: List of source recipes used
    """
    servings = max(1, int(servings))
    
    # Check if user is asking for specific cooking instructions
    instruction_keywords = [
        "how", "make", "cook", "prepare", "instructions", 
        "steps", "recipe for", "guide", "directions"
    ]
    
    is_instruction_request = any(kw in query.lower() for kw in instruction_keywords)
    
    if is_instruction_request:
        # Try to find exact recipe match
        recipe = _find_recipe(query)
        if recipe:
            answer = _format_instructions(recipe, servings)
            return {
                "answer": answer,
                "sources": [{"title": recipe.get("title", "Recipe")}]
            }
    
    # Use RAG to search for recipes
    try:
        results = search_recipes(query, k=top_k)
    except Exception as e:
        print(f"Error in RAG search: {e}")
        return {
            "answer": (
                f"I encountered an error searching recipes: {str(e)}\n\n"
                "Please try:\n"
                "- Simplifying your query\n"
                "- Asking about specific recipe names\n"
                "- Checking that recipe data files exist"
            ),
            "sources": []
        }
    
    if not results:
        return {
            "answer": (
                "I couldn't find any recipes matching your query.\n\n"
                "**Try asking:**\n"
                "- 'Show me high protein recipes'\n"
                "- 'How do I make Grilled Chicken Bowl?'\n"
                "- 'Give me vegetarian recipes'\n"
                "- 'What are some healthy breakfast ideas?'"
            ),
            "sources": []
        }
    
    # Format search results
    lines = ["**I found these recipes for you:**\n"]
    sources = []
    
    for i, result in enumerate(results, 1):
        doc = result.document
        
        # Scale macros for requested servings
        scale = servings / max(1, doc.servings)
        scaled_cals = doc.calories * scale
        scaled_protein = doc.protein_g * scale
        scaled_carbs = doc.carb_g * scale
        scaled_fat = doc.fat_g * scale
        
        # Format recipe entry
        lines.append(f"**{i}. {doc.title}**")
        
        if doc.tags:
            lines.append(f"   *Tags: {', '.join(doc.tags)}*")
        
        lines.append(
            f"   **For {servings} serving(s):** "
            f"{scaled_cals:.0f} kcal | "
            f"P: {scaled_protein:.0f}g | "
            f"C: {scaled_carbs:.0f}g | "
            f"F: {scaled_fat:.0f}g\n"
        )
        
        sources.append({
            "title": doc.title,
            "tags": doc.tags,
            "servings": doc.servings,
            "calories": doc.calories,
            "protein_g": doc.protein_g,
            "carb_g": doc.carb_g,
            "fat_g": doc.fat_g
        })
    
    lines.append(
        "\n💡 **Tip:** To get detailed cooking instructions, ask: "
        "*'How do I make [recipe name]?'*"
    )
    
    return {
        "answer": "\n".join(lines),
        "sources": sources
    }


def recipe_steps(query: str, servings: int = 1) -> Dict[str, object]:
    """Legacy function for backward compatibility.
    
    This function is kept for any old code that might reference it.
    It simply redirects to grounded_cooking_response.
    
    Args:
        query: Recipe query
        servings: Number of servings
    
    Returns:
        Same as grounded_cooking_response
    """
    return grounded_cooking_response(query, servings)


__all__ = ["grounded_cooking_response", "recipe_steps"]