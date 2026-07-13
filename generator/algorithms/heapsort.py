"""Exercise: Heapsort, drawing the array/heap tree after every change.

(a) BuildHeap (bottom-up MAX-HEAPIFY) -- one snapshot per individual swap,
    matching the classic exam phrasing "one change at a time".
(b) The main HeapSort for-loop -- one snapshot per loop iteration (swap
    root with the last element of the heap, shrink the heap, sift down).

Everything shown is the direct, deterministic output of running the real
algorithm on the generated array -- there is no hand-authored trace.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from core import Exercise, Step, new_seed  # noqa: E402
from tree_utils import TNode, render_tree_svg  # noqa: E402

EXERCISE_ID = "algo-heapsort"
TITLE = "Heapsort: BuildHeap and the Sorting Loop"


def _array_latex(arr: list[int]) -> str:
    if not arr:
        return "(\\text{empty})"
    cols = "|" + "c|" * len(arr)
    row = " & ".join(str(x) for x in arr)
    return f"\\begin{{array}}{{{cols}}}\\hline {row} \\\\ \\hline\\end{{array}}"


def _heap_nodes(array: list[int], heap_size: int, highlight: frozenset[int]) -> tuple[dict[str, TNode], str | None]:
    nodes: dict[str, TNode] = {}
    for i in range(heap_size):
        left = str(2 * i + 1) if 2 * i + 1 < heap_size else None
        right = str(2 * i + 2) if 2 * i + 2 < heap_size else None
        nodes[str(i)] = TNode(
            id=str(i),
            label=str(array[i]),
            left=left,
            right=right,
            fill="var(--diagram-highlight, #ffe9a8)" if i in highlight else "var(--diagram-surface, #fff)",
            highlight=i in highlight,
        )
    root_id = "0" if heap_size > 0 else None
    return nodes, root_id


def _sift_down_steps(working: list[int], start: int, heap_size: int) -> list[Step]:
    """Iterative MAX-HEAPIFY from `start`, one Step per swap performed."""
    steps: list[Step] = []
    i = start
    while True:
        left, right = 2 * i + 1, 2 * i + 2
        largest = i
        if left < heap_size and working[left] > working[largest]:
            largest = left
        if right < heap_size and working[right] > working[largest]:
            largest = right
        if largest == i:
            break
        working[i], working[largest] = working[largest], working[i]
        nodes, root = _heap_nodes(working, heap_size, frozenset({i, largest}))
        steps.append(
            Step(
                text=f"Swap `A[{i}]` and `A[{largest}]`: $${_array_latex(working[:heap_size])}$$",
                diagram=render_tree_svg(nodes, root),
            )
        )
        i = largest
    return steps


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    n = rng.randint(7, 9)
    array = rng.sample(range(1, 60), n)
    working = array[:]

    prompt = (
        f"Show the contents of the array below\n\n$${_array_latex(array)}$$\n\n"
        f"**(a)** after `BuildHeap` is called (one change at a time)\n\n"
        f"**(b)** after each iteration of the `for`-loop of `HeapSort`."
    )

    steps = [
        Step(
            "`BuildHeap` calls `MAX-HEAPIFY(A, i)` for $i = \\lfloor n/2 \\rfloor - 1$ down to "
            "$0$; each call sifts $A[i]$ down by repeatedly swapping it with its larger child "
            "until the max-heap property holds locally. `HeapSort` then repeatedly swaps the "
            "root (the max) with the last element of the current heap, shrinks the heap by one, "
            "and sifts the new root down."
        )
    ]

    steps.append(Step("**(a) BuildHeap.**"))
    for i in range(n // 2 - 1, -1, -1):
        steps.extend(_sift_down_steps(working, i, n))

    after_buildheap = working[:]

    steps.append(Step("**(b) HeapSort for-loop.**"))
    heap_size = n
    for i in range(n - 1, 0, -1):
        working[0], working[i] = working[i], working[0]
        heap_size -= 1
        idx = 0
        while True:
            left, right = 2 * idx + 1, 2 * idx + 2
            largest = idx
            if left < heap_size and working[left] > working[largest]:
                largest = left
            if right < heap_size and working[right] > working[largest]:
                largest = right
            if largest == idx:
                break
            working[idx], working[largest] = working[largest], working[idx]
            idx = largest
        nodes, root = _heap_nodes(working, heap_size, frozenset())
        sorted_tail = working[heap_size:]
        tail_text = f", sorted suffix `{sorted_tail}`" if sorted_tail else ""
        steps.append(
            Step(
                text=(
                    f"Swap `A[0]` and `A[{i}]`, shrink heap to size {heap_size}, sift down: "
                    f"$${_array_latex(working[:heap_size])}$${tail_text}"
                ),
                diagram=render_tree_svg(nodes, root),
            )
        )

    final_answer = f"$${_array_latex(working)}$$"

    answers = {
        "initial_array": array,
        "after_buildheap": after_buildheap,
        "sorted_array": working,
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        final_answer=final_answer,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a heapsort exercise.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    ex = generate(args.seed)
    if args.json:
        print(ex.to_json(indent=2))
    else:
        print(f"[seed={ex.seed}] {ex.title}\n")
        print(ex.prompt)
        print("\n--- Solution ---")
        for i, step in enumerate(ex.steps, 1):
            print(f"{i}. {step.text}")
        print("\nFinal answer:", ex.final_answer)
        print("Answers:", ex.answers)
