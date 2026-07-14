"""Shared helpers for directed weighted graph exercises (Dijkstra,
Bellman-Ford): random graph generation guaranteeing every vertex is
reachable from the source, plus an SVG renderer for directed graphs that
can highlight an algorithm's current state (settled/reached vertices,
shortest-path-tree edges so far, tentative distances)."""

from __future__ import annotations

import math
import random

CIRCLE_CX = 160
CIRCLE_CY = 160
CIRCLE_RADIUS = 105
NODE_R = 19
CANVAS = 320


def circle_positions(n: int) -> dict[int, tuple[float, float]]:
    positions = {}
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions[i] = (
            CIRCLE_CX + CIRCLE_RADIUS * math.cos(angle),
            CIRCLE_CY + CIRCLE_RADIUS * math.sin(angle),
        )
    return positions


def generate_graph(rng: random.Random, n: int) -> tuple[list[str], list[tuple[int, int, int]]]:
    """Random directed weighted graph on `n` vertices (0 = source) where
    every vertex is guaranteed reachable from vertex 0: a random
    out-arborescence rooted at 0 first (so every vertex has *some* path
    from the source), then extra random edges (any direction, any pair)
    layered on top so there are alternative/longer routes worth relaxing."""
    vertices = [chr(ord("a") + i) for i in range(n)]
    edges: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int]] = set()

    reached = [0]
    remaining = list(range(1, n))
    rng.shuffle(remaining)
    for v in remaining:
        parent = rng.choice(reached)
        w = rng.randint(1, 9)
        edges.append((parent, v, w))
        seen.add((parent, v))
        reached.append(v)

    all_pairs = [(i, j) for i in range(n) for j in range(n) if i != j and (i, j) not in seen]
    rng.shuffle(all_pairs)
    extra = rng.randint(n - 1, min(len(all_pairs), 2 * n))
    for i, j in all_pairs[:extra]:
        w = rng.randint(1, 9)
        edges.append((i, j, w))
        seen.add((i, j))

    return vertices, edges


def compute_offsets(edges: list[tuple[int, int, int]]) -> list[float]:
    """A u->v edge and a v->u edge (if both exist) would otherwise draw
    on top of each other; nudge each to its own side of the straight line."""
    pairs = [(u, v) for u, v, _ in edges]
    pairset = set(pairs)
    offsets = []
    for u, v in pairs:
        if (v, u) in pairset:
            offsets.append(15.0 if u < v else -15.0)
        else:
            offsets.append(0.0)
    return offsets


def path_to(prev: list[int | None], vertices: list[str], v: int) -> str:
    path = [v]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    path.reverse()
    return " \\to ".join(vertices[i] for i in path)


def _point_on_circle(cx: float, cy: float, r: float, tx: float, ty: float) -> tuple[float, float]:
    dx, dy = tx - cx, ty - cy
    d = math.hypot(dx, dy) or 1
    return cx + dx / d * r, cy + dy / d * r


def directed_graph_svg(
    vertices: list[str],
    positions: dict[int, tuple[float, float]],
    edges: list[tuple[int, int, int]],
    offsets: list[float],
    tree_edges: set[tuple[int, int]] = frozenset(),
    settled: set[int] = frozenset(),
    current: int | None = None,
    dist_labels: dict[int, str] | None = None,
) -> str:
    dist_labels = dist_labels or {}
    parts = [
        f'<svg viewBox="0 0 {CANVAS} {CANVAS}" width="{CANVAS}" height="{CANVAS}" '
        f'xmlns="http://www.w3.org/2000/svg" class="graph-diagram">',
        "<style>.graph-diagram text { font-family: Georgia, 'Times New Roman', serif; "
        "font-size: 12px; fill: var(--diagram-ink, #111); } "
        ".graph-diagram .vlabel { font-size: 14px; } "
        ".graph-diagram .dist { font-size: 10.5px; fill: var(--diagram-muted, #666); }</style>",
        '<defs>'
        '<marker id="dg-arrow" markerWidth="8" markerHeight="8" refX="6.5" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--diagram-ink, #111)" /></marker>'
        '<marker id="dg-arrow-muted" markerWidth="8" markerHeight="8" refX="6.5" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--diagram-line-muted, #ccc)" /></marker>'
        '</defs>',
    ]
    for (u, v, w), off in zip(edges, offsets):
        cx1, cy1 = positions[u]
        cx2, cy2 = positions[v]
        dx, dy = cx2 - cx1, cy2 - cy1
        d = math.hypot(dx, dy) or 1
        px, py = -dy / d, dx / d
        mx, my = (cx1 + cx2) / 2 + px * off, (cy1 + cy2) / 2 + py * off

        is_tree = (u, v) in tree_edges
        start = _point_on_circle(cx1, cy1, NODE_R, mx, my)
        end = _point_on_circle(cx2, cy2, NODE_R, mx, my)
        stroke = "var(--diagram-ink, #111)" if is_tree else "var(--diagram-line-muted, #ccc)"
        marker = "url(#dg-arrow)" if is_tree else "url(#dg-arrow-muted)"
        sw = 2.4 if is_tree else 1.2
        parts.append(
            f'<path d="M{start[0]:.1f},{start[1]:.1f} Q{mx:.1f},{my:.1f} '
            f'{end[0]:.1f},{end[1]:.1f}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
            f'marker-end="{marker}" />'
        )
        label_color = "var(--diagram-ink, #111)" if is_tree else "var(--diagram-muted, #888)"
        parts.append(
            f'<rect x="{mx - 8:.1f}" y="{my - 9:.1f}" width="16" height="16" '
            f'fill="var(--bg, #fdfdfb)" opacity="0.9" />'
        )
        parts.append(f'<text x="{mx:.1f}" y="{my + 4:.1f}" text-anchor="middle" fill="{label_color}">{w}</text>')

    for i, label in enumerate(vertices):
        cx, cy = positions[i]
        if i == current:
            fill = "var(--diagram-highlight, #ffe9a8)"
        elif i in settled:
            fill = "var(--diagram-track, #eee)"
        else:
            fill = "var(--diagram-surface, #fff)"
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{NODE_R}" fill="{fill}" '
            f'stroke="var(--diagram-ink, #111)" stroke-width="1.6" />'
        )
        parts.append(f'<text x="{cx:.1f}" y="{cy + 5:.1f}" text-anchor="middle" class="vlabel">{label}</text>')
        if i in dist_labels:
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + NODE_R + 14:.1f}" text-anchor="middle" class="dist">'
                f"{dist_labels[i]}</text>"
            )
    parts.append("</svg>")
    return "".join(parts)
