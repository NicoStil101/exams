"""Exercise: reachability graph of a binary (1-safe) Petri net.

Every generated net has exactly one input place and one output place per
transition ("move the token from i to o"), and starts with exactly one
token total. Because firing a transition never changes the total token
count, every reachable marking has that single token sitting at exactly
one place -- so a marking is fully described by *which* place currently
holds it, a transition is enabled exactly when the token is at its input
place, and its output place is therefore always guaranteed to be empty
(capacity 1 can never be violated). This keeps the reachability graph
small and hand-checkable while still exercising the real skills the exam
question is after: spotting every enabled transition from a state,
computing the resulting marking, and recognizing when a transition leads
back to a marking that was already discovered.

Reproducing the full reachability graph as a fill-in-the-blank doesn't
map cleanly onto this app's answer-checking widgets, so -- mirroring
mst_weight.py, which reduces "find the MST" to its unique total weight --
this exercise reduces "construct the reachability graph" to two checkable
numbers (state count, edge count) while the full step-by-step BFS
construction with diagrams is still shown as the worked solution.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "os-petri-reachability"
TITLE = "Binary Petri Net: Reachability Graph"

_CIRCLE_CX = 160
_CIRCLE_CY = 160
_CIRCLE_RADIUS = 100
_PLACE_R = 20
_CANVAS = 320


def _generate_net(rng: random.Random):
    """Random binary Petri net: pick a random subset of directed
    place -> place edges (the transitions), drop any whose source is
    never reached from the start place P0 (they could never fire), and
    require at least one real choice point (a place with >=2 outgoing
    transitions) and one real merge point (a place with >=2 incoming
    transitions) so the exercise isn't a trivial straight line.
    """
    for _ in range(500):
        num_places = rng.choice([4, 4, 5])
        all_pairs = [(i, o) for i in range(num_places) for o in range(num_places) if i != o]
        rng.shuffle(all_pairs)
        num_candidates = rng.randint(num_places, min(len(all_pairs), num_places + 3))
        candidate_pairs = all_pairs[:num_candidates]

        adj_all: dict[int, list[int]] = {i: [] for i in range(num_places)}
        for i, o in candidate_pairs:
            adj_all[i].append(o)
        reachable = {0}
        frontier = [0]
        while frontier:
            cur = frontier.pop()
            for o in adj_all[cur]:
                if o not in reachable:
                    reachable.add(o)
                    frontier.append(o)

        kept_pairs = sorted(p for p in candidate_pairs if p[0] in reachable)
        if len(kept_pairs) < num_places or len(reachable) < 3:
            continue

        out_degree = {i: 0 for i in range(num_places)}
        in_degree = {i: 0 for i in range(num_places)}
        for i, o in kept_pairs:
            out_degree[i] += 1
            in_degree[o] += 1

        if max(out_degree.values()) < 2 or max(in_degree.values()) < 2:
            continue

        places = [f"P{i}" for i in range(num_places)]
        transitions = [(i, o, f"t{k}") for k, (i, o) in enumerate(kept_pairs)]
        return num_places, places, transitions

    raise RuntimeError("failed to generate a valid Petri net after many attempts")


def _bfs_reachability(num_places: int, transitions: list[tuple[int, int, str]]):
    adj: dict[int, list[tuple[int, str]]] = {i: [] for i in range(num_places)}
    for i, o, label in transitions:
        adj[i].append((o, label))

    order = [0]
    visited = {0}
    edges: list[tuple[int, str, int, bool]] = []
    queue = [0]
    while queue:
        cur = queue.pop(0)
        for o, label in adj[cur]:
            is_new = o not in visited
            edges.append((cur, label, o, is_new))
            if is_new:
                visited.add(o)
                order.append(o)
                queue.append(o)
    return order, edges


def _marking_latex(places: list[str], idx: int) -> str:
    vals = ["1" if i == idx else "0" for i in range(len(places))]
    return "\\langle " + ", ".join(vals) + " \\rangle"


def _circle_positions(n: int) -> dict[int, tuple[float, float]]:
    positions = {}
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions[i] = (
            _CIRCLE_CX + _CIRCLE_RADIUS * math.cos(angle),
            _CIRCLE_CY + _CIRCLE_RADIUS * math.sin(angle),
        )
    return positions


def _compute_edge_offsets(transitions: list[tuple[int, int, str]]) -> dict[str, float]:
    """Transitions between the same pair of places in both directions
    would otherwise draw on top of each other; nudge each one to its own
    side of the straight line so both remain visible."""
    pairs = {(i, o) for i, o, _ in transitions}
    offsets = {}
    for i, o, label in transitions:
        offsets[label] = 16 if (o, i) in pairs and i < o else (-16 if (o, i) in pairs else 0)
    return offsets


def _point_on_circle(cx: float, cy: float, r: float, tx: float, ty: float) -> tuple[float, float]:
    dx, dy = tx - cx, ty - cy
    d = math.hypot(dx, dy) or 1
    return cx + dx / d * r, cy + dy / d * r


def _pull_back(fx: float, fy: float, tx: float, ty: float, dist: float) -> tuple[float, float]:
    dx, dy = tx - fx, ty - fy
    d = math.hypot(dx, dy) or 1
    if d <= dist:
        return fx, fy
    return tx - dx / d * dist, ty - dy / d * dist


def _rect_boundary(cx: float, cy: float, w: float, h: float, tx: float, ty: float) -> tuple[float, float]:
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = w / 2, h / 2
    candidates = []
    if dx != 0:
        t = hw / abs(dx)
        if abs(dy * t) <= hh:
            candidates.append(t)
    if dy != 0:
        t = hh / abs(dy)
        if abs(dx * t) <= hw:
            candidates.append(t)
    t = min(candidates) if candidates else 0
    return cx + dx * t, cy + dy * t


def _petri_net_svg(
    places: list[str],
    positions: dict[int, tuple[float, float]],
    transitions: list[tuple[int, int, str]],
    offsets: dict[str, float],
    initial_place: int = 0,
) -> str:
    parts = [
        f'<svg viewBox="0 0 {_CANVAS} {_CANVAS}" width="{_CANVAS}" height="{_CANVAS}" '
        f'xmlns="http://www.w3.org/2000/svg" class="petri-diagram">',
        "<style>.petri-diagram text { font-family: Georgia, 'Times New Roman', serif; "
        "font-size: 12px; fill: var(--diagram-ink, #111); } "
        ".petri-diagram .plabel { font-size: 14px; }</style>",
        '<defs><marker id="petri-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--diagram-ink, #111)" /></marker></defs>',
    ]
    rect_half = 8
    for i, o, label in transitions:
        cx1, cy1 = positions[i]
        cx2, cy2 = positions[o]
        dx, dy = cx2 - cx1, cy2 - cy1
        d = math.hypot(dx, dy) or 1
        px, py = -dy / d, dx / d
        off = offsets.get(label, 0)
        mx, my = (cx1 + cx2) / 2 + px * off, (cy1 + cy2) / 2 + py * off

        start = _point_on_circle(cx1, cy1, _PLACE_R, mx, my)
        end = _point_on_circle(cx2, cy2, _PLACE_R, mx, my)
        seg1_end = _pull_back(start[0], start[1], mx, my, rect_half + 3)
        seg2_start = _pull_back(end[0], end[1], mx, my, rect_half + 3)

        parts.append(
            f'<line x1="{start[0]:.1f}" y1="{start[1]:.1f}" x2="{seg1_end[0]:.1f}" '
            f'y2="{seg1_end[1]:.1f}" stroke="var(--diagram-ink, #111)" stroke-width="1.4" '
            f'marker-end="url(#petri-arrow)" />'
        )
        parts.append(
            f'<line x1="{seg2_start[0]:.1f}" y1="{seg2_start[1]:.1f}" x2="{end[0]:.1f}" '
            f'y2="{end[1]:.1f}" stroke="var(--diagram-ink, #111)" stroke-width="1.4" '
            f'marker-end="url(#petri-arrow)" />'
        )
        parts.append(
            f'<rect x="{mx - rect_half:.1f}" y="{my - rect_half:.1f}" width="{2 * rect_half}" '
            f'height="{2 * rect_half}" fill="var(--diagram-surface, #fff)" '
            f'stroke="var(--diagram-ink, #111)" stroke-width="1.4" />'
        )
        parts.append(f'<text x="{mx:.1f}" y="{my - 14:.1f}" text-anchor="middle">{label}</text>')

    for i, p in enumerate(places):
        cx, cy = positions[i]
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{_PLACE_R}" fill="var(--diagram-surface, #fff)" '
            f'stroke="var(--diagram-ink, #111)" stroke-width="1.6" />'
        )
        parts.append(
            f'<text x="{cx:.1f}" y="{cy - _PLACE_R - 8:.1f}" text-anchor="middle" class="plabel">{p}</text>'
        )
        if i == initial_place:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="var(--diagram-ink, #111)" />')
    parts.append("</svg>")
    return "".join(parts)


def _reachability_svg(
    places: list[str],
    positions: dict[int, tuple[float, float]],
    offsets: dict[str, float],
    discovered_nodes: list[int],
    discovered_edges: list[tuple[int, str, int]],
    highlight: int | None = None,
) -> str:
    n = len(places)
    box_w, box_h = 74, 30
    parts = [
        f'<svg viewBox="0 0 {_CANVAS} {_CANVAS}" width="{_CANVAS}" height="{_CANVAS}" '
        f'xmlns="http://www.w3.org/2000/svg" class="reach-diagram">',
        "<style>.reach-diagram text { font-family: Georgia, 'Times New Roman', serif; "
        "font-size: 12px; fill: var(--diagram-ink, #111); }</style>",
        '<defs><marker id="reach-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--diagram-ink, #111)" /></marker></defs>',
    ]
    for i, label, o in discovered_edges:
        cx1, cy1 = positions[i]
        cx2, cy2 = positions[o]
        dx, dy = cx2 - cx1, cy2 - cy1
        d = math.hypot(dx, dy) or 1
        px, py = -dy / d, dx / d
        off = offsets.get(label, 0)
        mx, my = (cx1 + cx2) / 2 + px * off, (cy1 + cy2) / 2 + py * off

        start = _rect_boundary(cx1, cy1, box_w, box_h, mx, my)
        end = _rect_boundary(cx2, cy2, box_w, box_h, mx, my)
        parts.append(
            f'<path d="M{start[0]:.1f},{start[1]:.1f} Q{mx:.1f},{my:.1f} '
            f'{end[0]:.1f},{end[1]:.1f}" fill="none" stroke="var(--diagram-ink, #111)" '
            f'stroke-width="1.4" marker-end="url(#reach-arrow)" />'
        )
        parts.append(
            f'<rect x="{mx - 10:.1f}" y="{my - 9:.1f}" width="20" height="16" '
            f'fill="var(--bg, #fdfdfb)" opacity="0.9" />'
        )
        parts.append(f'<text x="{mx:.1f}" y="{my + 4:.1f}" text-anchor="middle">{label}</text>')

    for i in discovered_nodes:
        cx, cy = positions[i]
        fill = "var(--diagram-highlight, #ffe9a8)" if i == highlight else "var(--diagram-surface, #fff)"
        text = ", ".join("1" if j == i else "0" for j in range(n))
        parts.append(
            f'<rect x="{cx - box_w / 2:.1f}" y="{cy - box_h / 2:.1f}" width="{box_w}" height="{box_h}" '
            f'rx="8" ry="8" fill="{fill}" stroke="var(--diagram-ink, #111)" stroke-width="1.4" />'
        )
        parts.append(f'<text x="{cx:.1f}" y="{cy + 4:.1f}" text-anchor="middle">{text}</text>')
    parts.append("</svg>")
    return "".join(parts)


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    num_places, places, transitions = _generate_net(rng)
    positions = _circle_positions(num_places)
    offsets = _compute_edge_offsets(transitions)

    base_diagram = _petri_net_svg(places, positions, transitions, offsets)

    order, bfs_edges = _bfs_reachability(num_places, transitions)

    state_order_label = "\\langle " + ", ".join(places) + " \\rangle"
    prompt = (
        "The following is a binary Petri net (every place has capacity 1 -- at most "
        f"one token at a time). It starts in the marking shown (one token in "
        f"${places[0]}$, all other places empty).\n\n"
        "Construct the **reachability graph** of this net: starting from the initial "
        "marking, repeatedly determine which transitions are enabled and which "
        "marking firing each one leads to, until no new markings appear. Express a "
        f"state in the order ${state_order_label}$ and label every edge with the "
        "transition that produced it."
    )

    steps = [
        Step(
            "Every transition here has exactly one input place and one output place, "
            "and the net starts with exactly **one token total**. Firing a transition "
            "just moves that single token from its input place to its output place, "
            "so the token count never changes -- at every reachable marking exactly "
            "one place holds the token, and any transition's output place is "
            "therefore always guaranteed to be empty (capacity 1 can never be "
            "violated). So a transition $i \\to o$ is enabled exactly when the token "
            "currently sits at place $i$."
        ),
        Step(f"Start state: ${_marking_latex(places, 0)}$ (token at ${places[0]}$)."),
    ]

    discovered_nodes = [0]
    discovered_edges: list[tuple[int, str, int]] = []
    for cur, label, dst, is_new in bfs_edges:
        discovered_edges.append((cur, label, dst))
        if is_new:
            discovered_nodes.append(dst)
        diagram = _reachability_svg(places, positions, offsets, discovered_nodes, discovered_edges, highlight=dst)
        tail = "." if is_new else " -- a state we've already seen, so no new node is added."
        steps.append(
            Step(
                text=(
                    f"From ${_marking_latex(places, cur)}$, transition `{label}` "
                    f"(${places[cur]} \\to {places[dst]}$) is enabled and leads to "
                    f"${_marking_latex(places, dst)}${tail}"
                ),
                diagram=diagram,
            )
        )

    num_states = len(discovered_nodes)
    num_edges = len(discovered_edges)
    final_diagram = _reachability_svg(places, positions, offsets, discovered_nodes, discovered_edges)
    steps.append(
        Step(
            text=(
                "No new markings appear once every enabled transition from every "
                f"discovered state has been explored. Full reachability graph "
                f"(${num_states}$ states, ${num_edges}$ edges):"
            ),
            diagram=final_diagram,
        )
    )

    final_answer = f"Reachability graph: **{num_states} states**, **{num_edges} edges**."

    answers = {
        "places": places,
        "transitions": [[i, o, label] for i, o, label in transitions],
        "reachable_order": order,
        "edges": [[i, label, o] for i, label, o, _ in bfs_edges],
        "num_states": num_states,
        "num_edges": num_edges,
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
            {
                "label": "Number of distinct reachable states (nodes in the reachability graph)",
                "value": num_states,
                "type": "number",
            },
            {
                "label": "Number of edges in the reachability graph",
                "value": num_edges,
                "type": "number",
            },
        ],
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Petri net reachability-graph exercise.")
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
