from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generator"))

from flask import Flask, abort, jsonify, render_template, request  # noqa: E402

import progress_db  # noqa: E402
import registry  # noqa: E402
import study_log_db  # noqa: E402

app = Flask(__name__)

_VALID_ASSESSMENTS = {"red", "yellow", "green"}


def _exercise_to_dict(ex) -> dict:
    return {
        "id": ex.id,
        "seed": ex.seed,
        "title": ex.title,
        "prompt": ex.prompt,
        "steps": [{"text": s.text, "diagram": s.diagram} for s in ex.steps],
        "answers": ex.answers,
        "diagram": ex.diagram,
        "final_answer": ex.final_answer,
        "check_answers": ex.check_answers,
        "check_table": ex.check_table,
    }


@app.route("/")
def index():
    return render_template("index.html", categories=registry.CATEGORIES)


@app.route("/exercise/<exercise_id>")
def exercise_page(exercise_id):
    try:
        module = registry.get_module(exercise_id)
    except KeyError:
        abort(404)
    return render_template("exercise.html", exercise_id=exercise_id, title=module.TITLE)


@app.route("/api/exercise/<exercise_id>/new")
def api_new_exercise(exercise_id):
    try:
        module = registry.get_module(exercise_id)
    except KeyError:
        abort(404)
    return jsonify(_exercise_to_dict(module.generate(None)))


@app.route("/api/exercise/<exercise_id>/seed/<int:seed>")
def api_exercise_by_seed(exercise_id, seed):
    try:
        module = registry.get_module(exercise_id)
    except KeyError:
        abort(404)
    return jsonify(_exercise_to_dict(module.generate(seed)))


@app.route("/progress")
def progress_page():
    return render_template("progress.html")


@app.route("/api/progress", methods=["GET"])
def api_progress_get():
    stats = progress_db.get_stats()
    result = []
    for category in registry.CATEGORIES.values():
        for exercise_id, info in category["exercises"].items():
            s = stats.get(exercise_id, {"total": 0, "correct": 0, "last_attempt": None})
            total = s["total"]
            correct = s["correct"]
            result.append(
                {
                    "id": exercise_id,
                    "title": info["label"],
                    "category": category["label"],
                    "total": total,
                    "correct": correct,
                    "wrong": total - correct,
                    "last_attempt": s["last_attempt"],
                }
            )
    return jsonify(result)


@app.route("/api/progress", methods=["POST"])
def api_progress_post():
    data = request.get_json(force=True, silent=True) or {}
    exercise_id = data.get("exercise_id")
    if not exercise_id or exercise_id not in _all_exercise_ids():
        abort(400)
    progress_db.record_attempt(exercise_id, bool(data.get("correct")), data.get("seed"))
    return jsonify({"status": "ok"})


def _all_exercise_ids() -> set[str]:
    return {
        exercise_id
        for category in registry.CATEGORIES.values()
        for exercise_id in category["exercises"]
    }


def _is_valid_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


@app.route("/log")
def study_log_page():
    return render_template("study_log.html")


@app.route("/api/log", methods=["GET"])
def api_log_get():
    start = request.args.get("start")
    end = request.args.get("end")
    if not _is_valid_date(start) or not _is_valid_date(end):
        abort(400)
    return jsonify(study_log_db.get_entries_in_range(start, end))


@app.route("/api/log", methods=["POST"])
def api_log_post():
    data = request.get_json(force=True, silent=True) or {}
    log_date = (data.get("date") or "").strip()
    subject = (data.get("subject") or "").strip()
    topic = (data.get("topic") or "").strip()
    assessment = (data.get("assessment") or "").strip().lower()
    notes = (data.get("notes") or "").strip()
    if not _is_valid_date(log_date) or not subject or not topic or assessment not in _VALID_ASSESSMENTS:
        abort(400)
    entry = study_log_db.add_entry(log_date, subject, topic, assessment, notes)
    return jsonify(entry), 201


@app.route("/api/log/<int:entry_id>", methods=["DELETE"])
def api_log_delete(entry_id):
    if not study_log_db.delete_entry(entry_id):
        abort(404)
    return jsonify({"status": "ok"})


@app.route("/api/log/subjects")
def api_log_subjects():
    known = [cat["label"] for cat in registry.CATEGORIES.values()]
    logged = study_log_db.get_distinct_subjects()
    return jsonify(sorted(set(known) | set(logged)))


@app.route("/api/exams", methods=["GET"])
def api_exams_get():
    start = request.args.get("start")
    end = request.args.get("end")
    if not _is_valid_date(start) or not _is_valid_date(end):
        abort(400)
    return jsonify(study_log_db.get_exams_in_range(start, end))


@app.route("/api/exams", methods=["POST"])
def api_exams_post():
    data = request.get_json(force=True, silent=True) or {}
    exam_date = (data.get("date") or "").strip()
    subject = (data.get("subject") or "").strip()
    label = (data.get("label") or "").strip()
    if not _is_valid_date(exam_date):
        abort(400)
    entry = study_log_db.add_exam(exam_date, subject, label)
    return jsonify(entry), 201


@app.route("/api/exams/<int:exam_id>", methods=["DELETE"])
def api_exams_delete(exam_id):
    if not study_log_db.delete_exam(exam_id):
        abort(404)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
