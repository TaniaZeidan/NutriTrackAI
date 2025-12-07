# NutriTrackAI

NutriTrackAI is a multi-page Streamlit application for logging meals, planning weekly menus, and getting grounded cooking help. The app pairs local datasets (SQLite, FAISS, nutrition reference JSON/CSVs) with a LangChain agent that wraps Gemini Pro so you can run offline by default and switch to live LLM responses when a Google API key is available.

## Feature Highlights
- **Daily Log (deterministic)** – Gram-based logging backed by SQLite (`data/processed/nutritrackai.db`) and a nutrition reference JSON. No LLM involvement.
- **Plan My Week (deterministic + narrated)** – Calculates BMR/TDEE/macros with pure Python, builds a weekly plan, then optionally asks the NutriTrack agent to rewrite the summary in natural language.
- **Cooking Assistant (LLM agent)** – Conversational assistant backed by the NutriTrackAgent (LangChain + Gemini Pro) that can call tools for recipe RAG, macro targets, and ingredient weights.
- **RAG pipeline** – FAISS index over `data/raw/recipes_sample.csv` and `data/raw/healthy_meal_plans.csv`. Uses Gemini `text-embedding-004` when an API key is present, with a deterministic hash embedding fallback when offline.
- **Tooling surface** – The agent exposes at least three tools: `cooking_rag` (recipe search + macros), `macro_targets` (BMR/TDEE/macro calculator), and `ingredient_weights` (gram estimates from the nutrition reference).

## Repository Layout

```
NutriTrackAI/
|-- data/
|   |-- raw/               # recipes_sample.csv, healthy_meal_plans.csv, nutrition_reference.json
|   `-- processed/         # nutritrackai.db, faiss_index/*
|-- src/
|   |-- app.py             # Streamlit entrypoint + page routing
|   |-- pages/             # Daily Log, Plan My Week, Cooking Assistant
|   |-- core/              # config, schemas, db, utils, prompts, embeddings, llm, rag
|   |-- tools/             # calorie tracker, planner, cooking helpers, LangChain tool registry
|   |-- agent/             # NutriTrackAgent orchestration and helpers
|   `-- ui/                # shared Streamlit components
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.11+
- pip
- (Optional) Google Generative AI API access for live Gemini responses

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # or: source venv/bin/activate
pip install -r requirements.txt

echo GOOGLE_API_KEY=your_key_here > .env  # optional; enables live Gemini + embeddings
```

`src/config.py` loads `.env`. If `GOOGLE_API_KEY` is absent, Gemini calls fall back to deterministic offline responses and hash-based embeddings so you can still exercise the UI and tools.

## Running the App

```bash
streamlit run src/app.py
```

On first launch a FAISS index is created from the files in `data/raw/`. You can rebuild later from the sidebar button or via:

```bash
python - <<'PY'
import sys
sys.path.append("src")
from core.embeddings import build_index
build_index(force=True)
PY
```

### Pages and Agent Mapping
- **📋 Daily Log** – Purely local logging; SQLite-backed; unchanged by the agent.
- **📅 Plan My Week** – Deterministic macro math + plan generator; summary text may be rewritten by the NutriTrack agent (LangChain + Gemini Pro) while tables and totals remain deterministic.
- **👩‍🍳 Cooking Assistant** – Fully LLM-powered chat. The agent uses ConversationBufferMemory, Gemini Pro chat, and tools (`cooking_rag`, `macro_targets`, `ingredient_weights`) to fetch recipes, scale ingredients, and present macros in natural language.

## Data, Storage & Privacy

- **Nutrition reference** (`data/raw/nutrition_reference.json`) powers gram-based logging; you can append via the UI or edit JSON directly.
- **Recipe datasets** (`data/raw/recipes_sample.csv` and `data/raw/healthy_meal_plans.csv`) feed both planning and the FAISS retrieval pipeline. Replace or extend them with your own CSV files to customize suggestions.
- **Local persistence** – Logged meals live in `data/processed/nutritrackai.db` and never leave your machine. FAISS metadata/vectors are stored under `data/processed/faiss_index`.
- Keep `.env` and any exported data files (e.g., plan summaries) out of version control to avoid leaking personal information or API keys.

## Testing

```bash
pytest -q
```

The tests cover macro utilities, retrieval helpers, and tool behavior so regressions are caught early.

## Troubleshooting

- **Missing nutrition reference** – Ensure `data/raw/nutrition_reference.json` exists; the Daily Log page relies on it.
- **FAISS complaints** – `faiss-cpu` and `numpy` are optional; the app falls back to pure-Python similarity scoring but you may reinstall FAISS if you need the native index.
- **Gemini errors** – Verify `GOOGLE_API_KEY` is set and that the Generative AI API is enabled for your project. Without a key, the app automatically switches to offline fallbacks (hash embeddings + deterministic text).

With this setup, you can confidently develop new Streamlit pages, extend LangChain tooling, or swap in production-ready datasets without guessing how the system hangs together.
