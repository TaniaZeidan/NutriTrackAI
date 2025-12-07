from __future__ import annotations
from typing import Dict
from core.llm import GeminiClient
from core.rag import search_recipes
from tools.cooking_assistant import grounded_cooking_response


class CookingAgent:    
    def __init__(self, llm: GeminiClient = None):
        self.llm = llm or GeminiClient()
    
    def chat(self, user_input: str, servings: int = 2) -> str:
        """Process user input and return cooking guidance.
        
        Args:
            user_input: User's cooking-related question
            servings: Number of servings to prepare
        
        Returns:
            Cooking guidance with recipes, instructions, and macros
        """
        try:
            # Use the grounded cooking response tool directly
            result = grounded_cooking_response(
                query=user_input,
                servings=servings,
                llm=self.llm
            )
            
            return result["answer"]
            
        except Exception as e:
            # Fallback error handling
            error_msg = (
                f"I encountered an error: {str(e)}\n\n"
                "Please try:\n"
                "- Asking about a specific recipe name from our database\n"
                "- Examples: 'How do I make Grilled Chicken Bowl?' or 'Show me vegetarian recipes'\n"
                "- Make sure your Google API key is set correctly in .env"
            )
            print(f"DEBUG - Cooking Agent Error: {e}")
            import traceback
            traceback.print_exc()
            return error_msg


__all__ = ["CookingAgent"]