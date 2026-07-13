"""Tiny SQLite-backed store for exercise-check submissions (right/wrong,
with a timestamp), used to power the /progress dashboard."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "progress.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            seed INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def record_attempt(exercise_id: str, correct: bool, seed: int | None = None) -> None:
    conn = _get_conn()
    with conn:
        conn.execute(
            "INSERT INTO attempts (exercise_id, correct, seed, created_at) VALUES (?, ?, ?, ?)",
            (exercise_id, 1 if correct else 0, seed, datetime.now(timezone.utc).isoformat()),
        )
    conn.close()


def get_stats() -> dict[str, dict]:
    """exercise_id -> {total, correct, last_attempt (ISO str or None)}"""
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT exercise_id, COUNT(*), SUM(correct), MAX(created_at)
        FROM attempts
        GROUP BY exercise_id
        """
    ).fetchall()
    conn.close()
    return {
        exercise_id: {"total": total, "correct": correct or 0, "last_attempt": last}
        for exercise_id, total, correct, last in rows
    }
