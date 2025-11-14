"""Conversation and preference memory utilities."""
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Tuple

from core.schemas import MacroTargets


class ConversationMemory:
    """Lightweight in-memory chat buffer with capacity."""

    def __init__(self, max_turns: int = 8) -> None:
        self.max_turns = max_turns
        self.buffer: Deque[Tuple[str, str]] = deque(maxlen=max_turns)

    def add_turn(self, user: str, assistant: str) -> None:
        self.buffer.append((user, assistant))

    def summary(self) -> str:
        return "\n".join(f"User: {u}\nAssistant: {a}" for u, a in self.buffer)


class PreferenceMemory:
    """Stores persistent nutrition targets and preferences."""

    def __init__(self) -> None:
        self.profile: Dict[str, str | int | List[str]] = {
            "updated_at": datetime.utcnow().isoformat(),
            "diet_tags": [],
            "exclusions": [],
        }

    def update_targets(self, targets: MacroTargets) -> None:
        self.profile.update(
            {
                "calorie_target": targets.calories,
                "protein_target": targets.protein,
                "carb_target": targets.carbs,
                "fat_target": targets.fat,
                "diet_tags": targets.diet_tags,
                "exclusions": targets.exclusions,
                "meals_per_day": targets.meals_per_day,
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

    def get_targets(self) -> Dict[str, str | int | List[str]]:
        return self.profile


__all__ = ["ConversationMemory", "PreferenceMemory"]
