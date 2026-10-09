"""Shared binary-tree SVG rendering for algorithms exercises (heaps, BSTs, RB-trees).

Layout: x-coordinate = inorder rank among drawn nodes, y-coordinate = depth.
This guarantees no overlaps for any binary tree shape without needing a
full "tidy tree" layout algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TNode:
    id: str
    label: str
    left: str | None = None
    right: str | None = None
    fill: str = "var(--diagram-surface, #fff)"
    stroke: str = "var(--diagram-ink, #111)"
    text_color: str = "var(--diagram-ink, #111)"
    highlight: bool = False
    dashed: bool = False


def _inorder_positions(nodes: dict[str, TNode], root_id: str | None) -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    counter = [0]

    def visit(node_id: str | None, depth: int) -> None:
        if node_id is None:
            return
        node = nodes[node_id]
        visit(node.left, depth + 1)
        positions[node_id] = (counter[0], depth)
        counter[0] += 1
        visit(node.right, depth + 1)

    visit(root_id, 0)
    return positions


def render_tree_svg(
    nodes: dict[str, TNode],
    root_id: str | None,
    node_r: int = 18,
    x_gap: int = 50,
    y_gap: int = 62,
) -> str:
    if root_id is None or not nodes:
        return (
            '<svg viewBox="0 0 160 50" width="160" height="50" '
            'xmlns="http://www.w3.org/2000/svg" class="tree-diagram">'
            '<text x="8" y="28" font-family="Georgia, serif" font-size="13" '
            'fill="var(--diagram-muted, #666)">'
            "(empty tree)</text></svg>"
        )

    positions = _inorder_positions(nodes, root_id)
    max_x = max(x for x, _ in positions.values())
    max_y = max(y for _, y in positions.values())
    width = (max_x + 1) * x_gap + node_r * 2
    height = (max_y + 1) * y_gap + node_r * 2

    def px(node_id: str) -> tuple[float, float]:
        x, y = positions[node_id]
        return node_r + x * x_gap + node_r, node_r + y * y_gap + node_r

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" class="tree-diagram">',
        "<style>.tree-diagram text { font-family: Georgia, 'Times New Roman', serif; "
        "font-size: 13px; } .tree-diagram line { stroke: var(--diagram-ink, #111); "
        "stroke-width: 1.4; }</style>",
    ]

    for nid, node in nodes.items():
        x1, y1 = px(nid)
        for child_id in (node.left, node.right):
            if child_id is not None and child_id in positions:
                x2, y2 = px(child_id)
                parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />')

    for nid, node in nodes.items():
        cx, cy = px(nid)
        sw = 3.2 if node.highlight else 1.6
        dash = ' stroke-dasharray="4,3"' if node.dashed else ""
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{node_r}" fill="{node.fill}" '
            f'stroke="{node.stroke}" stroke-width="{sw}"{dash} />'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" fill="{node.text_color}">{node.label}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
