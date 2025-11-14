"""Configuration helpers for NutriTrackAI."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FAISS_INDEX_DIR = PROCESSED_DATA_DIR / "faiss_index"
DEFAULT_DB_PATH = PROCESSED_DATA_DIR / "nutritrackai.db"
ENV_FILE = ROOT_DIR / ".env"

EMBEDDING_MODEL = "text-embedding-004"
CHAT_MODEL = "gemini-2.5-pro"


def get_google_api_key() -> str:
    """Return the Google API key or raise a helpful error."""
    print("Attempting to get API KEY")
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY environment variable. "
            "Set it in a .env file or the environment."
        )
    print("API Key successfully retrieved")
    return key


def get_env(name: str, default: Optional[str] = None) -> str:
    """Fetch an environment variable with an optional default."""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required but missing.")
    return value


GOOGLE_API_KEY = get_google_api_key()


__all__ = [
    "ROOT_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "FAISS_INDEX_DIR",
    "DEFAULT_DB_PATH",
    "EMBEDDING_MODEL",
    "CHAT_MODEL",
    "GOOGLE_API_KEY",
    "get_google_api_key",
    "get_env",
]
