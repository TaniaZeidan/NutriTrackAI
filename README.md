# NutriTrackAI

NutriTrackAI is a multi-page Streamlit application for logging meals, tracking macros, planning weekly menus, exporting grocery lists, and getting guided cooking help. The project pairs local tooling (SQLite, FAISS, nutrition reference data) with LangChain/Gemini integrations so it runs offline by default but can call Gemini when a Google API key is available.

## Feature Highlights
- **Food logging & macro tracking** - Log gram-based foods from a curated reference, extend the dataset when items are missing, and view totals and trends backed by SQLite (`data/processed/nutritrackai.db`).
- **Weekly planning & grocery export** - Generate macro-aware plans with `tools.meal_planner`, summarize them in the UI, and turn them into categorized grocery CSVs.
- **Cooking assistant** - Retrieve recipes with the FAISS-backed RAG pipeline and display scaled, tip-rich cooking steps.
- **Conversation & agent layer** - `src/agent` wires LangChain tools and optional Gemini models so you can orchestrate the calorie tracker, planner, grocery list, and cooking helpers through a single agent facade.
- **All-local datasets** - Recipes and nutrition references live under `data/raw`, while FAISS artifacts and the SQLite database remain in `data/processed`.

## Repository Layout

```
NutriTrackAI/
|-- data/
|   |-- raw/               # recipes_sample.csv, nutrition_reference.json
|   `-- processed/         # nutritrackai.db, faiss_index/*
|-- src/
|   |-- app.py             # Streamlit entrypoint + page routing
|   |-- pages/             # Daily Log, Plan My Week, Grocery List, Cooking, Progress
|   |-- core/              # config, schemas, db, utils, prompts, embeddings, llm
|   |-- tools/             # calorie tracker, planner, grocery, cooking helpers
|   |-- agent/             # LangChain/Gemini orchestration
|   `-- ui/                # shared Streamlit components
|-- tests/                 # pytest coverage for macros, RAG, and tools
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

echo GOOGLE_API_KEY=your_key_here > .env  # required for Gemini features
```

The app loads `.env` via `src/config.py`. If `GOOGLE_API_KEY` is absent, the Gemini client falls back to deterministic offline responses so you can still exercise the UI and tools.

## Running the App

```bash
streamlit run src/app.py
```

What to expect:

- On first launch a FAISS index is created from `data/raw/recipes_sample.csv` (handled by `core.embeddings.build_index`). You can force a rebuild later with:

  ```bash
  python -c "from src.core.embeddings import build_index; build_index(force=True)"
  ```

- Streamlit pages live in `src/pages` and show up in the left sidebar:
  - **Daily Meal Log** - Log foods by grams, calculate macros with the nutrition reference, and view per-meal breakdowns with delete actions.
  - **Plan My Week** - Adjust macro targets in the sidebar, call `generate_plan`, and persist the result in `st.session_state`.
  - **Grocery List** - Build categorized items from the current plan and download a CSV via `tools.grocery_list.export_csv`.
  - **Cooking Assistant** - Search recipes, scale ingredients, and display structured tips from `tools.cooking_assistant.recipe_steps`.
  - **Progress Dashboard** - Summarize the last seven days with SQLite rollups and visualize macros using Streamlit charts.

## Data, Storage & Privacy

- **Nutrition reference** (`data/raw/nutrition_reference.json`) powers gram-based logging; you can append to it in the UI or edit the JSON directly.
- **Recipe dataset** (`data/raw/recipes_sample.csv`) feeds both planning and the FAISS retrieval pipeline. Replace it with your own CSV to customize suggestions.
- **Local persistence** - Logged meals live in `data/processed/nutritrackai.db` and never leave your machine. FAISS metadata/vectors are stored under `data/processed/faiss_index`.
- Keep `.env` and any exported data files (e.g., grocery CSVs) out of version control to avoid leaking personal information or API keys.

## Testing

Run the automated suite anytime you touch the core logic:

```bash
pytest -q
```

The tests cover macro utilities, the FAISS retrieval helpers, and high-level tool behavior so regressions are caught early.

## Troubleshooting

- **Missing nutrition reference** - Ensure `data/raw/nutrition_reference.json` exists; the Daily Log page relies on it for lookups.
- **FAISS complaints** - `faiss-cpu` and `numpy` are optional; the app falls back to pure-Python similarity scoring but you may reinstall FAISS if you need the native index.
- **Gemini errors** - Verify `GOOGLE_API_KEY` is set and that the Generative AI API is enabled for your project.

With the README in sync, you can confidently develop new Streamlit pages, extend LangChain tooling, or swap in production-ready datasets without guessing how the current system hangs together.
