"""In-memory state for the interactive max-heap visualizer -- same
pattern as rb_visualizer_state.py / bst_visualizer_state.py, applied to
an array-based binary max-heap. Single shared heap, no persistence,
resets whenever the Flask process restarts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generator" / "algorithms"))

from heap_core import BinaryHeap  # noqa: E402

_heap = BinaryHeap()


def _state_dict(trace: list[dict] | None = None) -> dict:
    return {
        "keys": _heap.keys(),
        "diagram": _heap.diagram(),
        "trace": trace or [],
    }


def get_state() -> dict:
    return _state_dict()


def insert(key: int) -> dict:
    _heap.insert(key)  # duplicates allowed
    return _state_dict(_heap.trace)


def delete(key: int) -> dict:
    ok = _heap.delete(key)
    if not ok:
        return {"error": f"{key} is not in the heap."}
    return _state_dict(_heap.trace)


def reset() -> dict:
    global _heap
    _heap = BinaryHeap()
    return _state_dict()
