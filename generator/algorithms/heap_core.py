"""Binary max-heap (array-based), matching the max-heap convention
already used by the heapsort exercise (generator/algorithms/heapsort.py).
Supports insert (append + sift-up) and delete-by-key (swap in the last
element + sift-up-or-down), both instrumented with the same fine-grained
step tracing used by the Red-Black tree / BST visualizers: every
individual swap is its own frame, not just the final heap.

Unlike the tree visualizers, there's no pointer structure here at all --
a heap's "tree" is purely the array's implicit index arithmetic
(children of i are at 2i+1, 2i+2), which is also what gets rendered via
tree_utils.render_tree_svg.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from tree_utils import TNode, render_tree_svg  # noqa: E402


class BinaryHeap:
    def __init__(self):
        self.array: list[int] = []
        self.trace: list[dict] = []

    # -- basic helpers ----------------------------------------------------

    @staticmethod
    def _parent(i: int) -> int:
        return (i - 1) // 2

    @staticmethod
    def _left(i: int) -> int:
        return 2 * i + 1

    @staticmethod
    def _right(i: int) -> int:
        return 2 * i + 2

    def keys(self) -> list[int]:
        return list(self.array)

    def _swap(self, i: int, j: int) -> None:
        self.array[i], self.array[j] = self.array[j], self.array[i]

    # -- rendering ----------------------------------------------------------

    def _to_tnodes(self, highlight: set[int] = frozenset()):
        nodes: dict[str, TNode] = {}
        n = len(self.array)
        for i in range(n):
            left_id = str(self._left(i)) if self._left(i) < n else None
            right_id = str(self._right(i)) if self._right(i) < n else None
            is_hl = i in highlight
            nodes[str(i)] = TNode(
                id=str(i),
                label=str(self.array[i]),
                left=left_id,
                right=right_id,
                fill="var(--diagram-highlight, #ffe9a8)" if is_hl else "var(--diagram-surface, #fff)",
                stroke="var(--diagram-ink, #111)",
                text_color="var(--diagram-ink, #111)",
                highlight=is_hl,
            )
        root_id = "0" if n > 0 else None
        return nodes, root_id

    def _snapshot(self, note: str, highlight: set[int] = frozenset()) -> None:
        nodes, root_id = self._to_tnodes(highlight=highlight)
        self.trace.append({"note": note, "diagram": render_tree_svg(nodes, root_id)})

    def diagram(self) -> str:
        nodes, root_id = self._to_tnodes()
        return render_tree_svg(nodes, root_id)

    # -- insert -------------------------------------------------------------

    def insert(self, key) -> None:
        self.trace = []
        self.array.append(key)
        i = len(self.array) - 1
        self._snapshot(f"Insert `{key}` at the end of the array (index {i}).", highlight={i})
        self._sift_up(i)

    def _sift_up(self, i: int) -> None:
        moved = False
        while i > 0:
            p = self._parent(i)
            if self.array[p] >= self.array[i]:
                break
            child_val, parent_val = self.array[i], self.array[p]
            self._swap(i, p)
            moved = True
            self._snapshot(f"`{child_val}` > parent `{parent_val}`: swap up.", highlight={p})
            i = p
        if not moved:
            self._snapshot("Already satisfies the max-heap property; no swap needed.", highlight={i})

    # -- delete ---------------------------------------------------------

    def delete(self, key) -> bool:
        try:
            i = self.array.index(key)
        except ValueError:
            return False
        self.trace = []

        last = len(self.array) - 1
        if i == last:
            self.array.pop()
            self._snapshot(f"Remove `{key}`: it was the last element in the array, so just drop it.")
            return True

        moved_val = self.array[last]
        self.array[i] = moved_val
        self.array.pop()
        self._snapshot(
            f"Remove `{key}` (index {i}): move the last element (`{moved_val}`) into its place, "
            f"then restore the heap property.",
            highlight={i},
        )

        p = self._parent(i)
        if i > 0 and self.array[p] < self.array[i]:
            self._sift_up(i)
        else:
            self._sift_down(i)
        return True

    def _sift_down(self, i: int) -> None:
        n = len(self.array)
        moved = False
        while True:
            left, right = self._left(i), self._right(i)
            largest = i
            if left < n and self.array[left] > self.array[largest]:
                largest = left
            if right < n and self.array[right] > self.array[largest]:
                largest = right
            if largest == i:
                break
            child_val, cur_val = self.array[largest], self.array[i]
            self._swap(i, largest)
            moved = True
            self._snapshot(f"`{child_val}` > `{cur_val}`: swap down.", highlight={largest})
            i = largest
        if not moved:
            self._snapshot("Already satisfies the max-heap property; no swap needed.", highlight={i})

    # -- validation (property-based testing) ------------------------------

    def validate(self) -> None:
        n = len(self.array)
        for i in range(n):
            for child in (self._left(i), self._right(i)):
                if child < n:
                    assert self.array[i] >= self.array[child], "max-heap property violated"
