"""Exercise: Red-Black tree, drawing the tree after every insertion.

Standard CLRS RB-INSERT + fixup (rotations/recoloring) with a shared BLACK
NIL sentinel. Every intermediate tree shown is the direct output of running
the real algorithm -- there is no hand-authored trace.

Drawing convention: black nodes are filled dark with white text; red nodes
are white-filled with a red outline and red text.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from core import Exercise, Step, new_seed  # noqa: E402
from tree_utils import TNode, render_tree_svg  # noqa: E402

EXERCISE_ID = "algo-rb-tree-insert"
TITLE = "Red-Black Tree: Sequential Insertions"

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

    def insert(self, key) -> None:
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
        self._insert_fixup(z)

    def _insert_fixup(self, z: _Node) -> None:
        while z.parent.color == RED:
            if z.parent is z.parent.parent.left:
                y = z.parent.parent.right
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)
        self.root.color = BLACK

    def validate(self) -> int:
        """Raise AssertionError on any RB-property violation; return the
        black-height otherwise (used by tests)."""
        assert self.root.color == BLACK or self.root is self.nil

        def check(node: _Node) -> int:
            if node is self.nil:
                return 1
            if node.left is not self.nil:
                assert node.left.key < node.key
                assert node.left.parent is node
            if node.right is not self.nil:
                assert node.right.key > node.key
                assert node.right.parent is node
            if node.color == RED:
                assert node.left.color == BLACK and node.right.color == BLACK, "red-red violation"
            lh, rh = check(node.left), check(node.right)
            assert lh == rh, "black-height mismatch"
            return lh + (1 if node.color == BLACK else 0)

        return check(self.root)


def _tree_to_tnodes(tree: RedBlackTree) -> tuple[dict[str, TNode], str | None]:
    nodes: dict[str, TNode] = {}

    def visit(node: _Node) -> str | None:
        if node is tree.nil:
            return None
        left_id = visit(node.left)
        right_id = visit(node.right)
        nid = str(node.key)
        is_red = node.color == RED
        nodes[nid] = TNode(
            id=nid,
            label=str(node.key),
            left=left_id,
            right=right_id,
            fill="var(--diagram-surface, #fff)" if is_red else "var(--diagram-node-dark, #222)",
            stroke="var(--status-bad, #c0392b)" if is_red else "var(--diagram-ink, #111)",
            text_color="var(--status-bad, #c0392b)" if is_red else "#fff",
        )
        return nid

    root_id = visit(tree.root)
    return nodes, root_id


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    n = rng.randint(6, 9)
    keys = rng.sample(range(1, 100), n)

    prompt = (
        "Insert the following keys, in order, into an initially empty red-black tree, "
        "applying the standard insertion fix-up (recoloring / rotations) after each "
        "insertion:\n\n```\n" + ", ".join(str(k) for k in keys) + "\n```\n\n"
        "Draw the tree after each insertion. Black nodes are drawn filled, red nodes are "
        "drawn with a red outline."
    )

    steps = [
        Step(
            "`RB-INSERT` places the new key as an ordinary BST leaf colored **red**, then "
            "`RB-INSERT-FIXUP` walks up from it: while its parent is red, it either "
            "recolors parent/uncle/grandparent (if the uncle is red) or rotates around "
            "the grandparent (if the uncle is black), and finally the root is colored black."
        )
    ]

    tree = RedBlackTree()
    for k in keys:
        tree.insert(k)
        nodes, root = _tree_to_tnodes(tree)
        steps.append(Step(text=f"Insert ${k}$:", diagram=render_tree_svg(nodes, root)))

    black_height = tree.validate()

    answers = {
        "keys": keys,
        "black_height": black_height,
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a red-black tree insertion exercise.")
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
        print("\nAnswers:", ex.answers)
