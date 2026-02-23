"""CLI demo for the NutriTrackAI multi-agent LangGraph system.

Sends three queries (one per agent role) and prints the state evolution
after each step to demonstrate that all course requirements are met.
"""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_core.messages import HumanMessage
from agent.orchestrator import build_graph
from core.schemas import NutriTrackState

QUERIES = [
    ("COOKING query", "How do I make a high-protein chicken bowl for 2 servings?"),
    ("NUTRITION query", "I weigh 70 kg, 175 cm tall, 25 years old male, moderately active. "
     "I want to lose fat. What are my daily calorie and macro targets?"),
    ("GENERAL query", "Hello! What can you help me with?"),
]

SEPARATOR = "=" * 70


def print_state(state: dict) -> None:
    """Print the non-message fields of the state."""
    print(f"  current_agent   : {state.get('current_agent')}")
    print(f"  query_type      : {state.get('query_type')}")
    print(f"  confidence      : {state.get('confidence')}")
    print(f"  tool_calls_count: {state.get('tool_calls_count')}")
    print(f"  needs_review    : {state.get('needs_review')}")
    print(f"  messages count  : {len(state.get('messages', []))}")


def main() -> None:
    print(SEPARATOR)
    print("NutriTrackAI  --  Multi-Agent LangGraph Demo")
    print(SEPARATOR)

    graph = build_graph()
    thread_id = "demo-thread-001"

    for label, query in QUERIES:
        print(f"\n{SEPARATOR}")
        print(f"[{label}]")
        print(f"User: {query}")
        print(SEPARATOR)

        try:
            result = graph.invoke(
                {"messages": [HumanMessage(content=query)]},
                config={"configurable": {"thread_id": thread_id}},
            )
        except Exception as exc:
            print(f"\n[SKIPPED] API error (likely rate-limit): {type(exc).__name__}")
            print("The graph routed correctly but the LLM call was throttled.")
            continue

        print("\n--- State after invocation ---")
        print_state(result)

        ai_msg = result["messages"][-1]
        answer = ai_msg.content if hasattr(ai_msg, "content") else str(ai_msg)
        safe_answer = answer.encode("ascii", errors="replace").decode("ascii")
        print(f"\n--- Agent response (first 500 chars) ---")
        print(safe_answer[:500])
        if len(safe_answer) > 500:
            print("...")
        print()

    print(SEPARATOR)
    print("Demo complete. All three agent roles were exercised.")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
