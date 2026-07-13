"""SQLite-backed store for the manual "retrospective revision timetable"
study log: freeform entries of what subject/topic you studied on a given
day, filled in after the fact rather than planned in advance -- see
https://aliabdaal.com/studying/how-to-study-the-power-of-retrospective-revision-timetables/

Deliberately separate from progress_db.py, which auto-logs right/wrong
exercise-check submissions: this is a manual journal covering anything you
studied, not just this app's exercises."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "study_log.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS study_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_study_log_date ON study_log (log_date)")
    try:
        # Migration for DBs created before the retrospective red/yellow/green
        # confidence rating existed; existing rows default to 'yellow'.
        conn.execute("ALTER TABLE study_log ADD COLUMN assessment TEXT NOT NULL DEFAULT 'yellow'")
    except sqlite3.OperationalError:
        pass  # column already present

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS exam_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_date TEXT NOT NULL,
            subject TEXT,
            label TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_exam_dates_date ON exam_dates (exam_date)")
    return conn


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "date": row[1],
        "subject": row[2],
        "topic": row[3],
        "assessment": row[4],
        "notes": row[5],
        "created_at": row[6],
    }


def add_entry(log_date: str, subject: str, topic: str, assessment: str, notes: str = "") -> dict:
    conn = _get_conn()
    created_at = datetime.now(timezone.utc).isoformat()
    with conn:
        cur = conn.execute(
            "INSERT INTO study_log (log_date, subject, topic, assessment, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (log_date, subject, topic, assessment, notes, created_at),
        )
        entry_id = cur.lastrowid
    conn.close()
    return {
        "id": entry_id,
        "date": log_date,
        "subject": subject,
        "topic": topic,
        "assessment": assessment,
        "notes": notes,
        "created_at": created_at,
    }


def delete_entry(entry_id: int) -> bool:
    conn = _get_conn()
    with conn:
        cur = conn.execute("DELETE FROM study_log WHERE id = ?", (entry_id,))
        deleted = cur.rowcount > 0
    conn.close()
    return deleted


def get_entries_in_range(start_date: str, end_date: str) -> list[dict]:
    """Inclusive [start_date, end_date] range, both 'YYYY-MM-DD' strings."""
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT id, log_date, subject, topic, assessment, notes, created_at
        FROM study_log
        WHERE log_date BETWEEN ? AND ?
        ORDER BY log_date, id
        """,
        (start_date, end_date),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_distinct_subjects() -> list[str]:
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT subject FROM study_log ORDER BY subject").fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_exam(exam_date: str, subject: str = "", label: str = "") -> dict:
    conn = _get_conn()
    created_at = datetime.now(timezone.utc).isoformat()
    with conn:
        cur = conn.execute(
            "INSERT INTO exam_dates (exam_date, subject, label, created_at) VALUES (?, ?, ?, ?)",
            (exam_date, subject, label, created_at),
        )
        exam_id = cur.lastrowid
    conn.close()
    return {"id": exam_id, "date": exam_date, "subject": subject, "label": label, "created_at": created_at}


def delete_exam(exam_id: int) -> bool:
    conn = _get_conn()
    with conn:
        cur = conn.execute("DELETE FROM exam_dates WHERE id = ?", (exam_id,))
        deleted = cur.rowcount > 0
    conn.close()
    return deleted


def get_exams_in_range(start_date: str, end_date: str) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT id, exam_date, subject, label, created_at
        FROM exam_dates
        WHERE exam_date BETWEEN ? AND ?
        ORDER BY exam_date, id
        """,
        (start_date, end_date),
    ).fetchall()
    conn.close()
    return [{"id": r[0], "date": r[1], "subject": r[2], "label": r[3], "created_at": r[4]} for r in rows]
