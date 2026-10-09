"""In-memory state for the interactive Red-Black tree visualizer: a
single shared tree (this is a local, single-user app, so no per-session
isolation is needed -- same simplicity as the rest of the app's storage).
Resets to empty whenever the Flask process restarts; nothing here is
persisted to disk, unlike progress.db / study_log.db."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generator" / "algorithms"))

from rb_tree_core import RedBlackTree  # noqa: E402

_tree = RedBlackTree()

MAX_BULK_KEYS = 200


def parse_int_list(text: str) -> list[int]:
    """Accepts real Python list/tuple syntax ("[10, 5, 15]", "(10, 5)"),
    bare comma-separated values ("10, 5, 15" -- itself valid Python tuple
    syntax), and as a fallback, plain whitespace/comma-separated numbers
    with no brackets at all ("10 5 15")."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("Paste an array of integers first.")

    wrapped = stripped if stripped.startswith(("[", "(")) else f"[{stripped}]"
    try:
        parsed = ast.literal_eval(wrapped)
    except (ValueError, SyntaxError):
        tokens = [t for t in re.split(r"[,\s]+", stripped.strip("[]() ")) if t]
        try:
            return [int(t) for t in tokens]
        except ValueError:
            raise ValueError("Could not parse that as a list of integers.")

    if not isinstance(parsed, (list, tuple)):
        parsed = [parsed]
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in parsed):
        raise ValueError("All elements must be plain integers.")
    return list(parsed)


def _state_dict(trace: list[dict] | None = None) -> dict:
    return {
        "keys": _tree.keys_inorder(),
        "diagram": _tree.diagram(),
        "trace": trace or [],
    }


def get_state() -> dict:
    return _state_dict()


def insert(key: int) -> dict:
    _tree.insert(key)  # duplicates allowed -- ties descend right
    return _state_dict(_tree.trace)


def delete(key: int) -> dict:
    ok = _tree.delete(key)
    if not ok:
        return {"error": f"{key} is not in the tree."}
    return _state_dict(_tree.trace)


def reset() -> dict:
    global _tree
    _tree = RedBlackTree()
    return _state_dict()


def bulk_load(text: str) -> dict:
    """Parses `text` as an array of integers, replaces the current tree
    with a fresh one, and inserts every key in order. Only the final tree
    is shown (no per-key step trace) -- this is meant for quickly seeing
    the end result of a specific sequence, not walking through it."""
    try:
        keys = parse_int_list(text)
    except ValueError as e:
        return {"error": str(e)}
    if len(keys) > MAX_BULK_KEYS:
        return {"error": f"That's {len(keys)} keys; please paste at most {MAX_BULK_KEYS}."}

    global _tree
    _tree = RedBlackTree()
    for k in keys:
        _tree.insert(k)
    return _state_dict()
