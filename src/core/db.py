"""Database access layer for NutriTrackAI."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DEFAULT_DB_PATH
from .schemas import Meal, MealItem
from .utils import macro_totals


class DatabaseError(RuntimeError):
    """Raised when the database is unavailable."""


class Database:
    """Simple SQLite-backed persistence."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self.ensure_storage()

    def ensure_storage(self) -> None:
        """Prepare the persistence layer."""
        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._initialize()
        except sqlite3.Error as exc:  # pragma: no cover - rarely triggered
            self._conn = None
            raise DatabaseError(f"SQLite unavailable: {exc}") from exc

    def _initialize(self) -> None:
        assert self._conn is not None
        cursor = self._conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                height_cm REAL,
                weight_kg REAL,
                goal TEXT,
                diet_tags TEXT,
                exclusions TEXT,
                meals_per_day INTEGER DEFAULT 3,
                calorie_target INTEGER,
                protein_target INTEGER,
                carb_target INTEGER,
                fat_target INTEGER
            );

            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dt TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                total_cal REAL,
                protein_g REAL,
                carb_g REAL,
                fat_g REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS meal_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                qty REAL,
                unit TEXT,
                cal REAL,
                protein_g REAL,
                carb_g REAL,
                fat_g REAL,
                estimated INTEGER DEFAULT 0,
                FOREIGN KEY(meal_id) REFERENCES meals(id)
            );
            """
        )
        self._conn.commit()

    @contextmanager
    def cursor(self):
        if not self._conn:
            raise DatabaseError("Database connection not available")
        cursor = self._conn.cursor()
        try:
            yield cursor
            self._conn.commit()
        finally:
            cursor.close()

    def log_meal(self, meal: Meal, user_id: int = 1) -> int:
        """Persist a meal and associated items."""
        totals = meal.totals
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO meals(user_id, dt, meal_type, total_cal, protein_g, carb_g, fat_g)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    meal.meal_date.isoformat(),
                    meal.meal_type,
                    totals["calories"],
                    totals["protein_g"],
                    totals["carb_g"],
                    totals["fat_g"],
                ),
            )
            meal_id = cur.lastrowid
            for item in meal.items:
                cur.execute(
                    """INSERT INTO meal_items(meal_id, name, qty, unit, cal, protein_g, carb_g, fat_g, estimated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        meal_id,
                        item.name,
                        item.quantity,
                        item.unit,
                        item.calories,
                        item.protein_g,
                        item.carb_g,
                        item.fat_g,
                        int(item.estimated),
                    ),
                )
        return int(meal_id)

    def meals_for_date(self, day: date, user_id: int = 1) -> List[Dict[str, float]]:
        """Fetch meals for a given day."""
        with self.cursor() as cur:
            cur.execute(
                "SELECT * FROM meals WHERE user_id=? AND dt=? ORDER BY dt",
                (user_id, day.isoformat()),
            )
            rows = cur.fetchall()
        return [dict(row) for row in rows]

    def meal_items(self, meal_id: int) -> List[MealItem]:
        with self.cursor() as cur:
            cur.execute("SELECT * FROM meal_items WHERE meal_id=?", (meal_id,))
            rows = cur.fetchall()
        return [
            MealItem(
                name=row["name"],
                quantity=row["qty"],
                unit=row["unit"],
                calories=row["cal"],
                protein_g=row["protein_g"],
                carb_g=row["carb_g"],
                fat_g=row["fat_g"],
                estimated=bool(row["estimated"]),
            )
            for row in rows
        ]

    def daily_totals(self, day: date, user_id: int = 1) -> Dict[str, float]:
        meals = self.meals_for_date(day, user_id)
        return macro_totals(meals)

    def weekly_summary(self, ending: date, user_id: int = 1) -> Dict[str, float]:
        start = ending - timedelta(days=6)
        with self.cursor() as cur:
            cur.execute(
                "SELECT total_cal as calories, protein_g, carb_g, fat_g FROM meals "
                "WHERE user_id=? AND dt BETWEEN ? AND ?",
                (user_id, start.isoformat(), ending.isoformat()),
            )
            rows = cur.fetchall()
        return macro_totals(rows)

    def planned_meals(self, start: date, end: date, user_id: int = 1) -> List[Dict[str, str]]:
        with self.cursor() as cur:
            cur.execute(
                "SELECT * FROM meals WHERE user_id=? AND dt BETWEEN ? AND ? ORDER BY dt",
                (user_id, start.isoformat(), end.isoformat()),
            )
            rows = cur.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


__all__ = ["Database", "DatabaseError"]
