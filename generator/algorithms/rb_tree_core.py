"""Red-Black tree with CLRS insert and delete (+ fixups), instrumented to
record a fine-grained step trace: every individual recolor/rotation
produces its own snapshot, not just the tree after a whole insert/delete
call (unlike the algo-rb-tree-insert exercise, which only snapshots once
per key). Used by the interactive Red-Black tree visualizer.

Kept as its own standalone implementation (not shared with
algorithms/red_black_tree.py) so the already property-tested exercise
generator can't regress from changes made here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from tree_utils import TNode, render_tree_svg  # noqa: E402

RED = "RED"
BLACK = "BLACK"


class _Node:
    __slots__ = ("key", "color", "left", "right", "parent")

    def __init__(self, key=None, color=BLACK):
        self.key = key
        self.color = color
        self.left = None
        self.right = None
        self.parent = None


class RedBlackTree:
    def __init__(self):
        self.nil = _Node(color=BLACK)
        self.nil.left = self.nil.right = self.nil.parent = self.nil
        self.root = self.nil
        self.trace: list[dict] = []

    # -- basic helpers ----------------------------------------------------

    def _find(self, key) -> _Node | None:
        node = self.root
        while node is not self.nil:
            if key == node.key:
                return node
            node = node.left if key < node.key else node.right
        return None

    def contains(self, key) -> bool:
        return self._find(key) is not None

    def keys_inorder(self) -> list:
        out = []

        def visit(node):
            if node is self.nil:
                return
            visit(node.left)
            out.append(node.key)
            visit(node.right)

        visit(self.root)
        return out

    def _minimum(self, node: _Node) -> _Node:
        while node.left is not self.nil:
            node = node.left
        return node

    def _child_slot(self, node: _Node) -> tuple[str | None, str | None]:
        """Returns (parent's rendering id, "left"|"right") -- identifies the
        parent by object identity (str(id(...))), not by key, since keys
        need not be unique once duplicates are allowed."""
        p = node.parent
        if p is self.nil:
            return None, None
        return str(id(p)), ("left" if p.left is node else "right")

    def _left_rotate(self, x: _Node) -> None:
        y = x.right
        x.right = y.left
        if y.left is not self.nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is self.nil:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _right_rotate(self, x: _Node) -> None:
        y = x.left
        x.left = y.right
        if y.right is not self.nil:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is self.nil:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y

    def _transplant(self, u: _Node, v: _Node) -> None:
        if u.parent is self.nil:
            self.root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    # -- rendering ----------------------------------------------------------

    def _to_tnodes(self, phantom=None, highlight_node=None):
        """phantom: optional (parent_rendering_id, "left"|"right") -- draws
        a dashed empty-slot placeholder there, used while the delete-fixup's
        `x` pointer is conceptually sitting at a non-existent (nil) node."""
        nodes: dict[str, TNode] = {}

        def visit(node: _Node) -> str | None:
            if node is self.nil:
                return None
            left_id = visit(node.left)
            right_id = visit(node.right)
            nid = str(id(node))  # not str(node.key): duplicate keys must still render as distinct nodes
            is_red = node.color == RED
            is_hl = node is highlight_node
            nodes[nid] = TNode(
                id=nid,
                label=str(node.key),
                left=left_id,
                right=right_id,
                fill="var(--diagram-highlight, #ffe9a8)"
                if is_hl
                else ("var(--diagram-surface, #fff)" if is_red else "var(--diagram-node-dark, #222)"),
                stroke="var(--status-bad, #c0392b)" if is_red else "var(--diagram-ink, #111)",
                text_color=("var(--diagram-ink, #111)" if is_hl else ("var(--status-bad, #c0392b)" if is_red else "#fff")),
                highlight=is_hl,
            )
            return nid

        root_id = visit(self.root)

        if phantom is not None:
            parent_key, side = phantom
            if parent_key is not None:
                pid = str(parent_key)
                phantom_id = f"phantom-{pid}-{side}"
                nodes[phantom_id] = TNode(
                    id=phantom_id,
                    label="",
                    fill="var(--diagram-surface, #fff)",
                    stroke="var(--diagram-muted, #666)",
                    text_color="var(--diagram-muted, #666)",
                    dashed=True,
                )
                if pid in nodes:
                    setattr(nodes[pid], side, phantom_id)

        return nodes, root_id

    def _snapshot(self, note: str, phantom=None, highlight_node=None) -> None:
        nodes, root_id = self._to_tnodes(phantom=phantom, highlight_node=highlight_node)
        self.trace.append({"note": note, "diagram": render_tree_svg(nodes, root_id)})

    def diagram(self) -> str:
        nodes, root_id = self._to_tnodes()
        return render_tree_svg(nodes, root_id)

    # -- insert ---------------------------------------------------------

    def insert(self, key) -> bool:
        """Duplicate keys are allowed: ties descend right (standard BST
        convention), so a key equal to an existing node always ends up in
        that node's right subtree."""
        self.trace = []

        z = _Node(key, RED)
        z.left = z.right = self.nil
        y = self.nil
        x = self.root
        while x is not self.nil:
            y = x
            x = x.left if z.key < x.key else x.right
        z.parent = y
        if y is self.nil:
            self.root = z
        elif z.key < y.key:
            y.left = z
        else:
            y.right = z

        self._snapshot(f"Insert `{key}` as a red leaf.", highlight_node=z)
        self._insert_fixup(z)
        return True

    def _insert_fixup(self, z: _Node) -> None:
        while z.parent.color == RED:
            if z.parent is z.parent.parent.left:
                y = z.parent.parent.right
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                    self._snapshot(
                        f"Case 1 (uncle red): recolor parent, uncle, and grandparent; continue from `{z.key}`.",
                        highlight_node=z,
                    )
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                        self._snapshot(f"Case 2 (uncle black, triangle): left-rotate at `{z.key}`.", highlight_node=z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
                    self._snapshot("Case 3 (uncle black, line): recolor parent/grandparent, right-rotate.", highlight_node=z)
            else:
                y = z.parent.parent.left
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                    self._snapshot(
                        f"Case 1 (uncle red): recolor parent, uncle, and grandparent; continue from `{z.key}`.",
                        highlight_node=z,
                    )
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                        self._snapshot(f"Case 2 (uncle black, triangle): right-rotate at `{z.key}`.", highlight_node=z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)
                    self._snapshot("Case 3 (uncle black, line): recolor parent/grandparent, left-rotate.", highlight_node=z)
        if self.root.color != BLACK:
            self.root.color = BLACK
            self._snapshot("Recolor the root black.")

    # -- delete -----------------------------------------------------------

    def delete(self, key) -> bool:
        z = self._find(key)
        if z is None:
            return False
        self.trace = []

        y = z
        y_original_color = y.color
        if z.left is self.nil:
            x = z.right
            phantom_parent_key, phantom_side = self._child_slot(z)
            self._transplant(z, z.right)
        elif z.right is self.nil:
            x = z.left
            phantom_parent_key, phantom_side = self._child_slot(z)
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent is z:
                phantom_parent_key, phantom_side = str(id(y)), "right"
                x.parent = y
            else:
                phantom_parent_key, phantom_side = self._child_slot(y)
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        note = f"Remove `{key}`"
        if y is not z:
            note += f" by copying its in-order successor `{y.key}` into its place"
        note += ". The removed node was " + ("black" if y_original_color == BLACK else "red")
        note += ", so " + ("a fixup may be needed." if y_original_color == BLACK else "no fixup is needed -- done.")

        if x is self.nil:
            self._snapshot(note, phantom=(phantom_parent_key, phantom_side))
        else:
            self._snapshot(note, highlight_node=x)

        if y_original_color == BLACK:
            self._delete_fixup(x, phantom_parent_key, phantom_side)
        return True

    def _delete_fixup(self, x: _Node, phantom_parent_key, phantom_side) -> None:
        def note_snapshot(text: str) -> None:
            if x is self.nil:
                self._snapshot(text, phantom=(phantom_parent_key, phantom_side))
            else:
                self._snapshot(text, highlight_node=x)

        while x is not self.root and x.color == BLACK:
            if x is x.parent.left:
                w = x.parent.right
                if w.color == RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._left_rotate(x.parent)
                    w = x.parent.right
                    note_snapshot(f"Case 1 (sibling red): recolor and rotate; sibling is now `{w.key}`.")
                if w.left.color == BLACK and w.right.color == BLACK:
                    w.color = RED
                    x = x.parent
                    phantom_parent_key, phantom_side = None, None
                    note_snapshot("Case 2 (sibling's children both black): recolor sibling red, extra black moves up.")
                else:
                    if w.right.color == BLACK:
                        w.left.color = BLACK
                        w.color = RED
                        self._right_rotate(w)
                        w = x.parent.right
                        note_snapshot("Case 3 (sibling's near child red): recolor and rotate to line up case 4.")
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._left_rotate(x.parent)
                    x = self.root
                    phantom_parent_key, phantom_side = None, None
                    note_snapshot("Case 4 (sibling's far child red): recolor and rotate; extra black absorbed, done.")
            else:
                w = x.parent.left
                if w.color == RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._right_rotate(x.parent)
                    w = x.parent.left
                    note_snapshot(f"Case 1 (sibling red): recolor and rotate; sibling is now `{w.key}`.")
                if w.right.color == BLACK and w.left.color == BLACK:
                    w.color = RED
                    x = x.parent
                    phantom_parent_key, phantom_side = None, None
                    note_snapshot("Case 2 (sibling's children both black): recolor sibling red, extra black moves up.")
                else:
                    if w.left.color == BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._left_rotate(w)
                        w = x.parent.left
                        note_snapshot("Case 3 (sibling's near child red): recolor and rotate to line up case 4.")
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._right_rotate(x.parent)
                    x = self.root
                    phantom_parent_key, phantom_side = None, None
                    note_snapshot("Case 4 (sibling's far child red): recolor and rotate; extra black absorbed, done.")
        if x.color != BLACK:
            x.color = BLACK
            note_snapshot("Recolor black to absorb the extra black.")

    # -- validation (property-based testing) ------------------------------

    def validate(self) -> int:
        assert self.root.color == BLACK or self.root is self.nil

        def check(node: _Node) -> int:
            if node is self.nil:
                return 1
            if node.left is not self.nil:
                # "<=", not "<": with duplicate keys, a rotation can legally
                # move an equal-valued node from the right chain into a
                # left-child position (still consistent in-order overall --
                # that global check runs separately below).
                assert node.left.key <= node.key
                assert node.left.parent is node
            if node.right is not self.nil:
                assert node.right.key >= node.key
                assert node.right.parent is node
            if node.color == RED:
                assert node.left.color == BLACK and node.right.color == BLACK, "red-red violation"
            lh, rh = check(node.left), check(node.right)
            assert lh == rh, "black-height mismatch"
            return lh + (1 if node.color == BLACK else 0)

        black_height = check(self.root)
        keys = self.keys_inorder()
        assert keys == sorted(keys), "in-order traversal is not sorted -- BST property violated"
        return black_height
