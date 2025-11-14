from __future__ import annotations

import textwrap
from typing import List

import streamlit as st

from agent.orchestrator import NutriTrackAgent
from core.schemas import MacroTargets, PlanDay
from tools.grocery_list import build_list_from_plan
from tools.meal_planner import generate_plan
from tools.tool_registry import get_tools
from ui.components import plan_table, targets_sidebar


def _ensure_agent() -> None:
    if "planner_agent" not in st.session_state:
        st.session_state["planner_agent"] = NutriTrackAgent(get_tools())
    if "planner_chat" not in st.session_state:
        st.session_state["planner_chat"] = []


def _normalize_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _plan_from_agent(
    agent: NutriTrackAgent, prompt: str, defaults: MacroTargets
) -> tuple[List[PlanDay], MacroTargets]:
    base = defaults.model_dump()
    guide = textwrap.dedent(
        """
        Translate the user's request into concrete macro targets. Respond with strict JSON using
        the following keys (all required):
        {
            "calories": int,
            "protein": int,
            "carbs": int,
            "fat": int,
            "diet_tags": [str],
            "exclusions": [str],
            "meals_per_day": int,
            "days": int
        }
        Rules:
        - calories must stay between 1200 and 3500.
        - protein should be at least 0 and not exceed 300.
        - carbs and fat should be non-negative integers.
        - meals_per_day may be 3 or 4. If absent, keep the default.
        - days should be between 1 and 7.
        - diet_tags and exclusions must be short lowercase phrases without explanations.
        Use these defaults when the user does not specify a field:
        """
    )
    payload = agent.gemini.structured_json(f"{guide}\n{base}\n\nUser request: {prompt}")
    if not isinstance(payload, dict) or payload.get("error"):
        raise RuntimeError("Agent response was not valid JSON.")

    def _as_int(key: str, fallback: int) -> int:
        value = payload.get(key, fallback)
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    calories = _clamp(_as_int("calories", base["calories"]), 1200, 3500)
    protein = _clamp(_as_int("protein", base["protein"]), 0, 300)
    carbs = max(0, _as_int("carbs", base["carbs"]))
    fat = max(0, _as_int("fat", base["fat"]))
    meals_per_day = _as_int("meals_per_day", base.get("meals_per_day", 3))
    if meals_per_day not in (3, 4):
        meals_per_day = base.get("meals_per_day", 3)
    days = _clamp(_as_int("days", 7), 1, 7)
    diet_tags = _normalize_list(payload.get("diet_tags")) or base.get("diet_tags", [])
    exclusions = _normalize_list(payload.get("exclusions")) or base.get("exclusions", [])

    targets = MacroTargets(
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        diet_tags=diet_tags,
        exclusions=exclusions,
        meals_per_day=meals_per_day,
    )
    plan = generate_plan(targets, days=days)
    return plan, targets


def _summarize_plan(plan: List[PlanDay]) -> str:
    lines = []
    preview = plan[: min(2, len(plan))]
    for day in preview:
        day_totals = day.totals()
        lines.append(
            f"{day.date:%A}: {int(day_totals['calories'])} kcal, "
            f"{int(day_totals['protein_g'])}g protein ({len(day.meals)} meals)"
        )
        for meal in day.meals[:2]:
            totals = meal.totals
            lines.append(
                f"- {meal.meal_type.title()}: {meal.name} "
                f"({int(totals['calories'])} kcal, {int(totals['protein_g'])}g protein)"
            )
    return "\n".join(lines)


def main() -> None:
    st.title("Plan My Week")
    _ensure_agent()

    sidebar_defaults = MacroTargets(calories=2000, protein=140, carbs=220, fat=60)
    manual_targets = targets_sidebar(sidebar_defaults)
    if st.button("Generate Plan", use_container_width=True):
        plan = generate_plan(manual_targets, days=7)
        st.session_state["weekly_plan"] = plan
        st.session_state["planner_targets"] = manual_targets
        st.success("Plan generated from sidebar targets.")

    st.divider()
    st.subheader("Chat with NutriTrackAI")
    agent = st.session_state["planner_agent"]
    history = st.session_state["planner_chat"]
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Describe the weekly plan you'd like."):
        with st.chat_message("user"):
            st.markdown(prompt)
        history.append({"role": "user", "content": prompt})
        try:
            defaults = st.session_state.get("planner_targets", manual_targets)
            plan, targets = _plan_from_agent(agent, prompt, defaults)
        except RuntimeError as exc:
            reply = {"role": "assistant", "content": f"Warning: {exc}"}
        else:
            st.session_state["weekly_plan"] = plan
            st.session_state["planner_targets"] = targets
            summary = _summarize_plan(plan)
            assistant_prompt = (
                f"{prompt}\n\nContext: A meal plan was created with targets "
                f"{targets.model_dump()}.\nPreview:\n{summary}\n"
                "Explain how this plan helps the user and invite follow-up questions."
            )
            response_text = agent.run(assistant_prompt)
            reply = {"role": "assistant", "content": response_text}
        history.append(reply)
        with st.chat_message("assistant"):
            st.markdown(reply["content"])

    plan = st.session_state.get("weekly_plan")
    if plan:
        plan_table(plan)
        if st.button("Build Grocery List"):
            groceries = build_list_from_plan(plan)
            st.session_state["groceries"] = groceries
            st.success("Grocery list ready. Switch to the Grocery List page.")


if __name__ == "__main__":
    main()
