"""Exercise: Bellman-Ford algorithm for single-source shortest paths.

Standard edge-relaxation Bellman-Ford: relax every edge, in a fixed
order, for up to |V|-1 rounds, stopping early the first round that makes
no change (a further round would be identical). Every intermediate
distance table and diagram shown is the direct, deterministic output of
running the real algorithm on the generated graph -- there is no
hand-authored trace. (Edge weights here are non-negative too, purely so
this exercise's graph is directly comparable to the Dijkstra exercise's
-- Bellman-Ford itself doesn't require that.)
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from core import Exercise, Step, new_seed  # noqa: E402
from graph_utils import circle_positions, compute_offsets, directed_graph_svg, generate_graph, path_to  # noqa: E402

EXERCISE_ID = "algo-bellman-ford"
TITLE = "Bellman-Ford Algorithm: Single-Source Shortest Paths"

INF = float("inf")


def _dist_label(d) -> str:
    if d == 0:
        return "0"
    if d == INF:
        return "∞"
    return str(d)


def _bellman_ford(n: int, edges: list[tuple[int, int, int]], source: int):
    dist: list[float] = [INF] * n
    dist[source] = 0
    prev: list[int | None] = [None] * n
    trace = []

    for round_idx in range(1, n):
        changed = []
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                changed.append((u, v, dist[v]))
        trace.append({"round": round_idx, "changed": changed, "dist": dist[:], "prev": prev[:]})
        if not changed:
            break
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

    source = 0
    dist, prev, trace = _bellman_ford(n, edges, source)

    base_diagram = directed_graph_svg(vertices, positions, edges, offsets)
    edge_list_latex = ", ".join(f"{vertices[u]} \\to {vertices[v]}: {w}" for u, v, w in edges)

    prompt = (
        f"Consider the directed weighted graph below (edges ${edge_list_latex}$).\n\n"
        f"Apply the **Bellman-Ford algorithm** with ${vertices[source]}$ as the source "
        "vertex, relaxing edges in the order given above on every round. For each other "
        "vertex, report the shortest path length and the sequence of vertices on that path."
    )

    steps = [
        Step(
            "Bellman-Ford relaxes **every edge**, in a fixed order, for up to $|V|-1$ "
            "rounds: for each edge $(u,v)$ with weight $w$, if $dist(u) + w < dist(v)$, it "
            "updates $dist(v)$ and remembers $u$ as $v$'s predecessor. Unlike Dijkstra it "
            "never has to pick a specific vertex first, so it also works with negative edge "
            "weights (as long as there's no negative cycle). If a full round makes no "
            "change, every later round would be identical, so we can stop early."
        )
    ]

    for snap in trace:
        changed = snap["changed"]
        if changed:
            change_text = "; ".join(
                f"${vertices[u]} \\to {vertices[v]}$: $dist({vertices[v]}) \\to {d}$" for u, v, d in changed
            )
        else:
            change_text = "no changes -- a further round would be identical, so we stop here"
        dist_labels = {i: _dist_label(d) for i, d in enumerate(snap["dist"])}
        tree_edges = {(snap["prev"][v], v) for v in range(n) if snap["prev"][v] is not None}
        diagram = directed_graph_svg(
            vertices,
            positions,
            edges,
            offsets,
            tree_edges=tree_edges,
            settled={v for v in range(n) if snap["dist"][v] < INF},
            dist_labels=dist_labels,
        )
        steps.append(Step(text=f"**Round {snap['round']}**: {change_text}.", diagram=diagram))

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

    parser = argparse.ArgumentParser(description="Generate a Bellman-Ford-algorithm exercise.")
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
