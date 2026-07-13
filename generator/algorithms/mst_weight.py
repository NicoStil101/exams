"""Exercise: Minimum Spanning Tree total weight, via Prim's and Kruskal's.

A random connected weighted graph can have *multiple* minimum spanning
trees when edge weights tie (Kruskal's and Prim's may even pick a
different one of them) -- but the total weight of any MST of a given graph
is always unique. So instead of asking the student to reproduce one exact
tree, this exercise asks for that single number, and checks it instantly.
The full step-by-step Prim's and Kruskal's traces are still shown as the
worked solution, both independently converging on the same total weight.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "algo-mst-weight"
TITLE = "Minimum Spanning Tree: Prim's and Kruskal's"


class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.parent[ra] = rb
        return True


def _generate_graph(rng: random.Random) -> tuple[list[str], list[tuple[str, str, int]]]:
    n = rng.randint(5, 7)
    vertices = [chr(ord("A") + i) for i in range(n)]

    edges: list[tuple[str, str, int]] = []
    seen: set[frozenset[str]] = set()

    # random spanning tree first, to guarantee connectivity
    shuffled = vertices[:]
    rng.shuffle(shuffled)
    for i in range(1, n):
        u = shuffled[i]
        v = shuffled[rng.randint(0, i - 1)]
        w = rng.randint(1, 20)
        edges.append((u, v, w))
        seen.add(frozenset((u, v)))

    extra = rng.randint(1, n)
    attempts = 0
    while extra > 0 and attempts < 50:
        attempts += 1
        u, v = rng.sample(vertices, 2)
        key = frozenset((u, v))
        if key in seen:
            continue
        seen.add(key)
        w = rng.randint(1, 20)
        edges.append((u, v, w))
        extra -= 1

    return vertices, edges


def _adjacency(vertices: list[str], edges: list[tuple[str, str, int]]) -> dict[str, list[tuple[str, int]]]:
    adj: dict[str, list[tuple[str, int]]] = {v: [] for v in vertices}
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    return adj


def _prims_trace(
    vertices: list[str], adj: dict[str, list[tuple[str, int]]], start: str
) -> list[tuple[list[tuple[str, str, int]], set[str]]]:
    in_tree = {start}
    tree_edges: list[tuple[str, str, int]] = []
    snapshots = []
    while len(in_tree) < len(vertices):
        candidates = []
        for u in sorted(in_tree):
            for v, w in adj[u]:
                if v not in in_tree:
                    candidates.append((w, u, v))
        candidates.sort()
        w, u, v = candidates[0]
        tree_edges.append((u, v, w))
        in_tree.add(v)
        snapshots.append((list(tree_edges), set(in_tree)))
    return snapshots


def _kruskals_trace(
    vertices: list[str], edges: list[tuple[str, str, int]]
) -> list[list[tuple[str, str, int]]]:
    sorted_edges = sorted(edges, key=lambda e: (e[2], e[0], e[1]))
    uf = _UnionFind(vertices)
    tree_edges: list[tuple[str, str, int]] = []
    snapshots = []
    for u, v, w in sorted_edges:
        if uf.union(u, v):
            tree_edges.append((u, v, w))
            snapshots.append(list(tree_edges))
            if len(tree_edges) == len(vertices) - 1:
                break
    return snapshots


def _circle_positions(vertices: list[str], radius: float = 120, cx: float = 150, cy: float = 150):
    n = len(vertices)
    positions = {}
    for i, v in enumerate(vertices):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions[v] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
    return positions


def _graph_svg(
    vertices: list[str],
    positions: dict[str, tuple[float, float]],
    all_edges: list[tuple[str, str, int]],
    selected: set[frozenset[str]],
    highlight_vertices: set[str] = frozenset(),
) -> str:
    width, height, r = 320, 320, 16
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" class="graph-diagram">',
        "<style>.graph-diagram text { font-family: Georgia, 'Times New Roman', serif; font-size: 12px; "
        "fill: var(--diagram-ink, #111); } .graph-diagram .vlabel { font-size: 13px; }</style>",
    ]
    for u, v, w in all_edges:
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        is_sel = frozenset((u, v)) in selected
        stroke = "var(--diagram-ink, #111)" if is_sel else "var(--diagram-line-muted, #ccc)"
        sw = 2.6 if is_sel else 1.2
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" />')
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        label_color = "var(--diagram-ink, #111)" if is_sel else "var(--diagram-muted, #888)"
        parts.append(
            f'<rect x="{mx - 9}" y="{my - 9}" width="18" height="16" fill="var(--bg, #fdfdfb)" opacity="0.9" />'
        )
        parts.append(f'<text x="{mx}" y="{my + 4}" text-anchor="middle" fill="{label_color}">{w}</text>')
    for v in vertices:
        x, y = positions[v]
        fill = "var(--diagram-highlight, #ffe9a8)" if v in highlight_vertices else "var(--diagram-surface, #fff)"
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="var(--diagram-ink, #111)" stroke-width="1.6" />'
        )
        parts.append(f'<text x="{x}" y="{y + 5}" text-anchor="middle" class="vlabel">{v}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _edges_latex(edges: list[tuple[str, str, int]]) -> str:
    return ", ".join(f"({u}\\text{{-}}{v}: {w})" for u, v, w in edges)


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    vertices, edges = _generate_graph(rng)
    adj = _adjacency(vertices, edges)
    positions = _circle_positions(vertices)
    start = vertices[0]

    prim_snapshots = _prims_trace(vertices, adj, start)
    kruskal_snapshots = _kruskals_trace(vertices, edges)

    prim_weight = sum(w for _, _, w in prim_snapshots[-1][0]) if prim_snapshots else 0
    kruskal_weight = sum(w for _, _, w in kruskal_snapshots[-1]) if kruskal_snapshots else 0
    assert prim_weight == kruskal_weight, "Prim's and Kruskal's disagree on MST weight"
    mst_weight = kruskal_weight

    base_diagram = _graph_svg(vertices, positions, edges, selected=set())

    prompt = (
        f"Consider the weighted graph below (vertices ${', '.join(vertices)}$, edge weights as "
        f"labeled).\n\nFind the total weight of a **Minimum Spanning Tree** of this graph. "
        f"(Note: the graph may admit more than one MST if weights tie, but every MST of a "
        f"given graph has the same total weight -- that unique number is what you should enter.)"
    )

    steps = [
        Step(
            "Both **Prim's** and **Kruskal's** algorithms compute *a* minimum spanning tree; "
            "if edge weights tie, they can pick a different tree, but the total weight is "
            "always the unique minimum, so both traces below arrive at the same number."
        ),
        Step(f"**Prim's algorithm**, starting from vertex ${start}$."),
    ]

    for tree_edges, in_tree in prim_snapshots:
        u, v, w = tree_edges[-1]
        selected = {frozenset((a, b)) for a, b, _ in tree_edges}
        diagram = _graph_svg(vertices, positions, edges, selected, highlight_vertices=in_tree)
        steps.append(
            Step(
                text=f"Add cheapest edge leaving the tree: `{u}-{v}` (weight {w}).",
                diagram=diagram,
            )
        )

    steps.append(
        Step(
            f"Prim's total weight: ${' + '.join(str(w) for _, _, w in prim_snapshots[-1][0])} "
            f"= {prim_weight}$."
        )
    )

    steps.append(
        Step(
            "**Kruskal's algorithm**: process edges in increasing weight order, accepting an "
            "edge whenever its endpoints are in different components (union-find), skipping it "
            f"otherwise. Sorted edges: ${_edges_latex(sorted(edges, key=lambda e: (e[2], e[0], e[1])))}$."
        )
    )

    for tree_edges in kruskal_snapshots:
        u, v, w = tree_edges[-1]
        selected = {frozenset((a, b)) for a, b, _ in tree_edges}
        diagram = _graph_svg(vertices, positions, edges, selected)
        steps.append(Step(text=f"Accept edge `{u}-{v}` (weight {w}) -- it joins two components.", diagram=diagram))

    steps.append(
        Step(
            f"Kruskal's total weight: ${' + '.join(str(w) for _, _, w in kruskal_snapshots[-1])} "
            f"= {kruskal_weight}$."
        )
    )

    final_answer = f"Total MST weight: **{mst_weight}**"

    answers = {
        "vertices": vertices,
        "edges": [list(e) for e in edges],
        "mst_weight": mst_weight,
        "prim_tree": [list(e) for e in prim_snapshots[-1][0]] if prim_snapshots else [],
        "kruskal_tree": [list(e) for e in kruskal_snapshots[-1]] if kruskal_snapshots else [],
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        diagram=base_diagram,
        final_answer=final_answer,
        check_answers=[
            {"label": "Total weight of a Minimum Spanning Tree", "value": mst_weight, "type": "number"}
        ],
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate an MST-weight exercise.")
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
        print("Check answers:", ex.check_answers)
        print("Answers:", ex.answers)
