"""Exercise: Dijkstra's algorithm for single-source shortest paths.

Standard array-based Dijkstra: repeatedly extract the unvisited vertex
with the smallest tentative distance, mark it settled, then relax its
outgoing edges. Every intermediate distance table and diagram shown is
the direct, deterministic output of running the real algorithm on the
generated graph -- there is no hand-authored trace. Edge weights are
always non-negative (Dijkstra's correctness requirement).
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from core import Exercise, Step, new_seed  # noqa: E402
from graph_utils import circle_positions, compute_offsets, directed_graph_svg, generate_graph, path_to  # noqa: E402

EXERCISE_ID = "algo-dijkstra"
TITLE = "Dijkstra's Algorithm: Single-Source Shortest Paths"

INF = float("inf")


def _dist_label(d) -> str:
    if d == 0:
        return "0"
    if d == INF:
        return "∞"
    return str(d)


def _dijkstra(n: int, adj: list[list[tuple[int, int]]], source: int):
    dist: list[float] = [INF] * n
    dist[source] = 0
    prev: list[int | None] = [None] * n
    settled: set[int] = set()
    tree_edges: set[tuple[int, int]] = set()
    trace = []

    for _ in range(n):
        candidates = [v for v in range(n) if v not in settled and dist[v] < INF]
        if not candidates:
            break
        u = min(candidates, key=lambda v: (dist[v], v))
        settled.add(u)
        if prev[u] is not None:
            tree_edges.add((prev[u], u))
        relaxed = []
        for v, w in adj[u]:
            if v in settled:
                continue
            new_d = dist[u] + w
            if new_d < dist[v]:
                dist[v] = new_d
                prev[v] = u
                relaxed.append((v, new_d))
        trace.append(
            {
                "current": u,
                "relaxed": relaxed,
                "dist": dist[:],
                "tree_edges": set(tree_edges),
                "settled": set(settled),
            }
        )
    return dist, prev, trace


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    n = rng.choice([5, 6])
    vertices, edges = generate_graph(rng, n)
    positions = circle_positions(n)
    offsets = compute_offsets(edges)

    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))

    source = 0
    dist, prev, trace = _dijkstra(n, adj, source)

    base_diagram = directed_graph_svg(vertices, positions, edges, offsets)
    edge_list_latex = ", ".join(f"{vertices[u]} \\to {vertices[v]}: {w}" for u, v, w in edges)

    prompt = (
        f"Consider the directed weighted graph below (edges ${edge_list_latex}$).\n\n"
        f"Apply **Dijkstra's algorithm** with ${vertices[source]}$ as the source vertex. "
        "For each other vertex, report the shortest path length and the sequence of "
        "vertices on that path."
    )

    steps = [
        Step(
            "Dijkstra repeatedly picks the **unvisited vertex with the smallest tentative "
            "distance**, marks it settled, and *relaxes* every outgoing edge from it -- if "
            "$dist(u) + w(u,v) < dist(v)$, it updates $dist(v)$ and remembers $u$ as $v$'s "
            "predecessor. Once a vertex is settled its distance is final; this only works "
            "because every edge weight is non-negative."
        )
    ]

    for snap in trace:
        u = snap["current"]
        if snap["relaxed"]:
            relax_text = "; ".join(
                f"${vertices[u]} \\to {vertices[v]}$: $dist({vertices[v]}) \\to {new_d}$"
                for v, new_d in snap["relaxed"]
            )
        else:
            relax_text = "no improvements"
        dist_labels = {i: _dist_label(d) for i, d in enumerate(snap["dist"])}
        diagram = directed_graph_svg(
            vertices,
            positions,
            edges,
            offsets,
            tree_edges=snap["tree_edges"],
            settled=snap["settled"],
            current=u,
            dist_labels=dist_labels,
        )
        steps.append(
            Step(
                text=(
                    f"Settle ${vertices[u]}$ (smallest tentative distance "
                    f"$= {_dist_label(snap['dist'][u])}$). Relax its outgoing edges: {relax_text}."
                ),
                diagram=diagram,
            )
        )

    final_dist_labels = {i: _dist_label(d) for i, d in enumerate(dist)}
    final_diagram = directed_graph_svg(
        vertices,
        positions,
        edges,
        offsets,
        tree_edges={(prev[v], v) for v in range(n) if prev[v] is not None},
        settled=set(range(n)),
        dist_labels=final_dist_labels,
    )

    path_lines = []
    for v in range(n):
        if v == source:
            continue
        if dist[v] == INF:
            path_lines.append(f"${vertices[v]}$: unreachable")
        else:
            path_lines.append(f"${vertices[v]}$: dist $= {dist[v]}$, path ${path_to(prev, vertices, v)}$")
    steps.append(Step(text="Final shortest-path tree:\n\n" + "\n".join(path_lines), diagram=final_diagram))

    final_answer = "\n".join(path_lines)

    answers = {
        "vertices": vertices,
        "edges": [list(e) for e in edges],
        "source": source,
        "dist": dist,
        "prev": prev,
    }

    check_answers = [
        {"label": f"Shortest distance from {vertices[source]} to {vertices[v]}", "value": dist[v], "type": "number"}
        for v in range(n)
        if v != source and dist[v] != INF
    ]

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        diagram=base_diagram,
        final_answer=final_answer,
        check_answers=check_answers,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Dijkstra's-algorithm exercise.")
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
