"""In-memory state for the interactive plain-BST visualizer -- same
pattern as rb_visualizer_state.py, applied to an unbalanced binary
search tree instead of a red-black tree. Single shared tree, no
persistence, resets whenever the Flask process restarts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generator" / "algorithms"))

from bst_core import BinarySearchTree  # noqa: E402

_tree = BinarySearchTree()


def _state_dict(trace: list[dict] | None = None) -> dict:
    return {
        "keys": _tree.keys_inorder(),
        "diagram": _tree.diagram(),
        "trace": trace or [],
    }


def get_state() -> dict:
    return _state_dict()


def insert(key: int) -> dict:
    ok = _tree.insert(key)
    if not ok:
        return {"error": f"{key} is already in the tree (duplicates aren't allowed here)."}
    return _state_dict(_tree.trace)


def delete(key: int) -> dict:
    ok = _tree.delete(key)
    if not ok:
        return {"error": f"{key} is not in the tree."}
    return _state_dict(_tree.trace)


def reset() -> dict:
    global _tree
    _tree = BinarySearchTree()
    return _state_dict()
