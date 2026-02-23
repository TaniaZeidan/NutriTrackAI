# NutriTrackAI

NutriTrackAI is a multi-page Streamlit application for logging meals, planning weekly menus, and getting grounded cooking help. The app pairs local datasets (SQLite, FAISS, nutrition reference JSON/CSVs) with a **multi-agent LangGraph system** powered by Google Gemini so you can run offline by default and switch to live LLM responses when an API key is available.

## Multi-Agent LangGraph Architecture

The core of the application is a **3-agent LangGraph StateGraph** that routes user queries to the right specialist:

```
START -> Router -> [route_by_type] -> CookingAgent  <-> CookingTools  -> END
                                   -> NutritionAgent <-> NutritionTools -> END
```

### Agent Roles

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| **Router** | Classifies queries using Structured Output Mode (Pydantic `RouterDecision`) | None (SOM only) |
| **Cooking Agent** | Recipes, cooking instructions, ingredient scaling | `cooking_rag`, `ingredient_weights` |
| **Nutrition Agent** | Calorie targets, BMR/TDEE, meal planning | `macro_targets`, `meal_planner` |

### State Schema (Pydantic)

```python
class NutriTrackState(BaseModel):
    messages: Annotated[list, add_messages]   # conversation history
    current_agent: Optional[str] = None       # which agent is handling the query
    query_type: Optional[str] = None          # cooking / nutrition / general
    confidence: float = 0.0                   # router classification confidence
    tool_calls_count: int = 0                 # number of tool invocations
    needs_review: bool = False                # flagged when confidence is low
```

### Key Design Decisions

- **Structured Output Mode**: The Router agent uses `.with_structured_output(RouterDecision)` to produce a validated Pydantic classification, ensuring type-safe routing.
- **Conditional Edges**: `route_by_type()` reads `query_type` and `confidence` from state. Low-confidence queries fall back to the Cooking Agent. Each specialist agent also has a `tools_condition` edge for tool call loops.
- **MemorySaver Checkpointer**: Thread-based conversation memory so multi-turn interactions accumulate context.
- **Different Toolsets**: Each specialist agent has its own distinct toolset, not shared.

## Feature Highlights

- **Daily Log (deterministic)** -- Gram-based logging backed by SQLite and a nutrition reference JSON. No LLM involvement.
- **Plan My Week (deterministic + narrated)** -- Calculates BMR/TDEE/macros with pure Python, builds a weekly plan, then optionally asks the NutriTrack agent to rewrite the summary.
- **Cooking Assistant (multi-agent LLM)** -- Conversational assistant backed by the LangGraph multi-agent system. Includes an "Agent State" panel that shows routing decisions, confidence scores, and tool usage.
- **RAG pipeline** -- FAISS index over recipe datasets. Uses Gemini embeddings when an API key is present, with a deterministic hash embedding fallback when offline.

## Repository Layout

```
NutriTrackAI/
|-- data/
|   |-- raw/               # recipes_sample.csv, healthy_meal_plans.csv, nutrition_reference.json
|   `-- processed/         # nutritrackai.db, faiss_index/*
|-- src/
|   |-- app.py             # Streamlit entrypoint + page routing
|   |-- config.py          # Environment and model configuration
|   |-- pages/             # Daily Log, Plan My Week, Cooking Assistant
|   |-- core/              # schemas, prompts, db, embeddings, llm, rag, memory
|   |-- tools/             # calorie calculator, meal planner, cooking helpers, tool registry
|   |-- agent/             # orchestrator (LangGraph), cooking_agent, planning_agent
|   `-- ui/                # shared Streamlit components
|-- demo.py                # CLI demo exercising all 3 agent roles
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.11+
- pip
- (Optional) Google Generative AI API key for live Gemini responses

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # or: source venv/bin/activate
pip install -r requirements.txt

echo GOOGLE_API_KEY=your_key_here > .env  # optional; enables live Gemini + embeddings
```

`src/config.py` loads `.env`. If `GOOGLE_API_KEY` is absent, Gemini calls fall back to deterministic offline responses and hash-based embeddings.

## Running the App

```bash
streamlit run src/app.py
```

On first launch a FAISS index is created from the files in `data/raw/`.

### CLI Demo

To exercise all three agent roles from the command line:

```bash
python demo.py
```

This sends a cooking query, a nutrition query, and a general query through the graph and prints the state evolution after each.

## Course Requirement Mapping

| Requirement | Implementation |
|-------------|---------------|
| A) 3+ Agent Roles | Router, Cooking Agent, Nutrition Agent |
| B) Different Toolsets | Cooking = {cooking_rag, ingredient_weights}, Nutrition = {macro_targets, meal_planner} |
| C) Pydantic State + MemorySaver | `NutriTrackState(BaseModel)` with `MemorySaver()` checkpointer |
| D) Structured Output Mode | Router uses `.with_structured_output(RouterDecision)` |
| E) Non-String + Optional Fields | `float`, `int`, `bool`, `Optional[str]` fields that evolve during execution |
| F) Conditional Edge | `route_by_type()` checks query_type and confidence; `tools_condition` for tool loops |
| G) Demo | Streamlit UI + CLI demo script |

## Data, Storage & Privacy

- **Nutrition reference** (`data/raw/nutrition_reference.json`) powers gram-based logging.
- **Recipe datasets** (`data/raw/recipes_sample.csv` and `data/raw/healthy_meal_plans.csv`) feed planning and FAISS retrieval.
- **Local persistence** -- Logged meals live in `data/processed/nutritrackai.db` and never leave your machine.
- Keep `.env` and any exported data files out of version control to avoid leaking API keys.

## Troubleshooting

- **Rate limits** -- The free tier for `gemini-2.5-flash` allows ~20 requests/day. Each query uses 2-3 API calls through the multi-agent graph. The app shows a clear message when limits are hit.
- **Missing nutrition reference** -- Ensure `data/raw/nutrition_reference.json` exists.
- **FAISS complaints** -- `faiss-cpu` and `numpy` are optional; the app falls back to pure-Python similarity scoring.
- **Gemini errors** -- Verify `GOOGLE_API_KEY` is set in `.env`. Without a key, the app switches to offline fallbacks.
