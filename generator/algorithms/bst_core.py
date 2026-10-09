"""Plain (unbalanced) Binary Search Tree with the classic BST property:
for any node x, every key y in x's left subtree satisfies y.key < x.key,
and every key y in x's right subtree satisfies y.key > x.key -- strict
on both sides. Unlike the Red-Black tree visualizer (which allows
duplicates by letting ties descend right), this tree rejects a key that
already exists, since a duplicate could satisfy neither side of that
strict inequality.

Standard CLRS TREE-INSERT / TREE-DELETE, with no rebalancing at all --
this can degenerate towards a linked list under an adversarial insertion
order, which is exactly the failure mode a red-black tree exists to
avoid. Instrumented with the same fine-grained step tracing used by the
RB-tree visualizer (rb_tree_core.py), kept as an independent, simpler
implementation since there's no color/fixup logic here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from tree_utils import TNode, render_tree_svg  # noqa: E402


class _Node:
    __slots__ = ("key", "left", "right", "parent")

    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.parent = None


class BinarySearchTree:
    def __init__(self):
        self.root: _Node | None = None
        self.trace: list[dict] = []

    # -- basic helpers ----------------------------------------------------

    def _find(self, key) -> _Node | None:
        node = self.root
        while node is not None:
            if key == node.key:
                return node
            node = node.left if key < node.key else node.right
        return None

    def contains(self, key) -> bool:
        return self._find(key) is not None

    def keys_inorder(self) -> list:
        out = []

        def visit(node):
            if node is None:
                return
            visit(node.left)
            out.append(node.key)
            visit(node.right)

        visit(self.root)
        return out

    def _minimum(self, node: _Node) -> _Node:
        while node.left is not None:
            node = node.left
        return node

    def _transplant(self, u: _Node, v: _Node | None) -> None:
        if u.parent is None:
            self.root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        if v is not None:
            v.parent = u.parent

    # -- rendering ----------------------------------------------------------

    def _to_tnodes(self, highlight_node=None):
        nodes: dict[str, TNode] = {}

        def visit(node: _Node) -> str | None:
            if node is None:
                return None
            left_id = visit(node.left)
            right_id = visit(node.right)
            nid = str(id(node))
            is_hl = node is highlight_node
            nodes[nid] = TNode(
                id=nid,
                label=str(node.key),
                left=left_id,
                right=right_id,
                fill="var(--diagram-highlight, #ffe9a8)" if is_hl else "var(--diagram-surface, #fff)",
                stroke="var(--diagram-ink, #111)",
                text_color="var(--diagram-ink, #111)",
                highlight=is_hl,
            )
            return nid

        root_id = visit(self.root)
        return nodes, root_id

    def _snapshot(self, note: str, highlight_node=None) -> None:
        nodes, root_id = self._to_tnodes(highlight_node=highlight_node)
        self.trace.append({"note": note, "diagram": render_tree_svg(nodes, root_id)})

    def diagram(self) -> str:
        nodes, root_id = self._to_tnodes()
        return render_tree_svg(nodes, root_id)

    # -- insert -------------------------------------------------------------

    def insert(self, key) -> bool:
        self.trace = []
        y = None
        x = self.root
        while x is not None:
            if key == x.key:
                self._snapshot(f"Compare `{key}` with `{x.key}`: already present -- rejected (no duplicates).", highlight_node=x)
                return False
            if key < x.key:
                self._snapshot(f"Compare `{key}` with `{x.key}`: `{key}` < `{x.key}`, go left.", highlight_node=x)
            else:
                self._snapshot(f"Compare `{key}` with `{x.key}`: `{key}` > `{x.key}`, go right.", highlight_node=x)
            y = x
            x = x.left if key < x.key else x.right

        z = _Node(key)
        z.parent = y
        if y is None:
            self.root = z
            self._snapshot(f"Insert `{key}` as the root (tree was empty).", highlight_node=z)
        else:
            if key < y.key:
                y.left = z
                side = "left"
            else:
                y.right = z
                side = "right"
            self._snapshot(f"Insert `{key}` as a new leaf ({side} child of `{y.key}`).", highlight_node=z)
        return True

    # -- delete ---------------------------------------------------------

    def delete(self, key) -> bool:
        z = self._find(key)
        if z is None:
            return False
        self.trace = []

        if z.left is None:
            self._snapshot(f"Remove `{key}`: no left child, so splice in its right subtree directly.", highlight_node=z)
            self._transplant(z, z.right)
        elif z.right is None:
            self._snapshot(f"Remove `{key}`: no right child, so splice in its left subtree directly.", highlight_node=z)
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            self._snapshot(
                f"Remove `{key}`: it has two children, so replace it with its in-order successor "
                f"`{y.key}` (the minimum of its right subtree).",
                highlight_node=y,
            )
            if y.parent is not z:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y

        self._snapshot("Resulting tree.")
        return True

    # -- validation (property-based testing) ------------------------------

    def validate(self) -> None:
        def check(node: _Node | None, lower, upper) -> None:
            if node is None:
                return
            assert lower is None or node.key > lower, "BST property violated (left-subtree bound)"
            assert upper is None or node.key < upper, "BST property violated (right-subtree bound)"
            if node.left is not None:
                assert node.left.parent is node
            if node.right is not None:
                assert node.right.parent is node
            check(node.left, lower, node.key)
            check(node.right, node.key, upper)

        check(self.root, None, None)
        keys = self.keys_inorder()
        assert keys == sorted(keys), "in-order traversal is not sorted"
        assert len(keys) == len(set(keys)), "duplicate keys present (should be impossible)"
