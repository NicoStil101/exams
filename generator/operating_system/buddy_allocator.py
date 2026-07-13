"""Exercise: dynamic memory allocation with a buddy-system allocator.

A pool of 2^total_order pages (page size 4 KiB) is managed by a buddy
allocator: allocate(n) rounds n up to the nearest power-of-two number of
pages and hands out a block of exactly that size (splitting a larger free
block if necessary); free(x) returns a block and coalesces it with its
buddy whenever the buddy is entirely free. "Over-allocation" is the total
internal-fragmentation waste (rounding-up waste) summed over every block
that is *currently* allocated.

The sequence of allocate()/free() operations is randomized, but the whole
trace -- every intermediate memory layout and the over-allocation after
each step -- is produced by directly simulating the (deterministic) buddy
algorithm, never guessed or hand-authored.
"""

from __future__ import annotations

import random
import string
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "os-buddy-allocator"
TITLE = "Dynamic Memory Allocation: Buddy System"

PAGE_SIZE = 4096
TOTAL_ORDER = 5  # 2^5 = 32 pages of physical memory
TOTAL_PAGES = 1 << TOTAL_ORDER


class BuddyAllocator:
    def __init__(self, total_order: int = TOTAL_ORDER, page_size: int = PAGE_SIZE):
        self.total_order = total_order
        self.page_size = page_size
        self.free_lists: dict[int, list[int]] = {k: [] for k in range(total_order + 1)}
        self.free_lists[total_order] = [0]
        self.allocated: dict[str, tuple[int, int, int]] = {}  # name -> (start, order, size_bytes)

    def order_for_bytes(self, size_bytes: int) -> int:
        pages_needed = -(-size_bytes // self.page_size)  # ceil division
        order = 0
        while (1 << order) < pages_needed:
            order += 1
        return order

    def max_available_order(self) -> int | None:
        available = [k for k, starts in self.free_lists.items() if starts]
        return max(available) if available else None

    def can_allocate(self, size_bytes: int) -> bool:
        order = self.order_for_bytes(size_bytes)
        return order <= self.total_order and any(
            self.free_lists[k] for k in range(order, self.total_order + 1)
        )

    def allocate(self, name: str, size_bytes: int) -> bool:
        order = self.order_for_bytes(size_bytes)
        if order > self.total_order:
            return False
        k = order
        while k <= self.total_order and not self.free_lists[k]:
            k += 1
        if k > self.total_order:
            return False
        start = self.free_lists[k].pop(0)
        while k > order:
            k -= 1
            buddy_start = start + (1 << k)
            self.free_lists[k].append(buddy_start)
            self.free_lists[k].sort()
        self.allocated[name] = (start, order, size_bytes)
        return True

    def free(self, name: str) -> None:
        start, order, _ = self.allocated.pop(name)
        while order < self.total_order:
            buddy_start = start ^ (1 << order)
            if buddy_start in self.free_lists[order]:
                self.free_lists[order].remove(buddy_start)
                start = min(start, buddy_start)
                order += 1
            else:
                break
        self.free_lists[order].append(start)
        self.free_lists[order].sort()

    def blocks(self) -> list[tuple[int, int, int, str | None]]:
        """(start, end_inclusive, order, name_or_None) for every block
        currently partitioning the address space, sorted by start."""
        items = []
        for name, (start, order, _) in self.allocated.items():
            items.append((start, start + (1 << order) - 1, order, name))
        for order, starts in self.free_lists.items():
            for start in starts:
                items.append((start, start + (1 << order) - 1, order, None))
        items.sort(key=lambda t: t[0])
        return items

    def over_allocation(self) -> int:
        return sum(
            (1 << order) * self.page_size - size_bytes
            for _, order, size_bytes in self.allocated.values()
        )


def _random_alloc_size(rng: random.Random, alloc: BuddyAllocator) -> int | None:
    max_order = alloc.max_available_order()
    if max_order is None:
        return None
    # Mild bias toward smaller blocks so a single request doesn't tend to
    # swallow a large fraction of the pool right away -- but linear, not
    # exponential, so mid/large orders still show up often instead of the
    # trace being dominated by 4/8 KiB (order 0/1) blocks.
    orders = list(range(max_order + 1))
    weights = [(max_order - k) + 2 for k in orders]
    desired_order = rng.choices(orders, weights=weights)[0]
    if desired_order == 0:
        pages_needed = 1
    else:
        pages_needed = rng.randint((1 << (desired_order - 1)) + 1, 1 << desired_order)
    lo = (pages_needed - 1) * alloc.page_size + 1
    hi = pages_needed * alloc.page_size
    if rng.random() < 0.15:
        return hi  # occasional exact fit -> zero waste, like `E` in the reference example
    return rng.randint(lo, hi)


def _generate_trace(rng: random.Random, num_vars: int) -> tuple[BuddyAllocator, list[tuple]]:
    alloc = BuddyAllocator()
    variables = list(string.ascii_uppercase[:num_vars])
    next_idx = 0
    live: list[str] = []
    ops: list[tuple] = []  # ("alloc", name, size_bytes) | ("free", name)

    guard = 0
    while next_idx < num_vars:
        guard += 1
        if guard > 500:
            break
        do_free = live and rng.random() < 0.28
        if do_free:
            name = rng.choice(live)
            alloc.free(name)
            live.remove(name)
            ops.append(("free", name))
            continue
        size = _random_alloc_size(rng, alloc)
        if size is None:
            if live:
                name = rng.choice(live)
                alloc.free(name)
                live.remove(name)
                ops.append(("free", name))
                continue
            break
        name = variables[next_idx]
        assert alloc.allocate(name, size)
        live.append(name)
        ops.append(("alloc", name, size))
        next_idx += 1

    remaining = live[:]
    rng.shuffle(remaining)
    for name in remaining:
        alloc.free(name)
        ops.append(("free", name))

    return alloc, ops


def _hatch_defs() -> str:
    return (
        '<defs><pattern id="hatch" width="6" height="6" patternTransform="rotate(45)" '
        'patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="var(--diagram-surface, #fff)"/>'
        '<line x1="0" y1="0" x2="0" y2="6" stroke="var(--diagram-ink, #111)" stroke-width="1.4"/></pattern></defs>'
    )


def _diagram_svg(blocks: list[tuple[int, int, int, str | None]], page_px: int = 22) -> str:
    box_h = 42
    top = 14
    width = TOTAL_PAGES * page_px
    height = top + box_h + 30
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" class="mem-diagram">',
        "<style>.mem-diagram text { font-family: Georgia, 'Times New Roman', serif; "
        "fill: var(--diagram-ink, #111); } .mem-diagram .lbl{font-size:12px;} "
        ".mem-diagram .tick{font-size:9px; fill: var(--diagram-muted, #666);}</style>",
        _hatch_defs(),
    ]
    for start, end, order, name in blocks:
        x = start * page_px
        w = (end - start + 1) * page_px
        cx = x + w / 2
        cy = top + box_h / 2
        fill = "url(#hatch)" if name else "var(--diagram-surface, #fff)"
        parts.append(
            f'<rect x="{x}" y="{top}" width="{w}" height="{box_h}" fill="{fill}" '
            f'stroke="var(--diagram-ink, #111)" stroke-width="1.3" />'
        )
        if name:
            label_w = max(20, 9 * len(name) + 12)
            parts.append(
                f'<rect x="{cx - label_w / 2}" y="{cy - 10}" width="{label_w}" height="20" '
                f'fill="var(--diagram-surface, #fff)" stroke="var(--diagram-ink, #111)" stroke-width="1" />'
            )
            parts.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" class="lbl">{name}</text>')
        else:
            parts.append(
                f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" class="lbl" font-style="italic">'
                f'B<tspan baseline-shift="sub" font-size="9">{order}</tspan></text>'
            )
    for p in range(TOTAL_PAGES + 1):
        x = p * page_px
        parts.append(f'<line x1="{x}" y1="{top + box_h}" x2="{x}" y2="{top + box_h + 5}" stroke="var(--diagram-ink, #111)" stroke-width="1" />')
    for p in range(TOTAL_PAGES):
        x = p * page_px + page_px / 2
        parts.append(f'<text x="{x}" y="{top + box_h + 16}" text-anchor="middle" class="tick">{p}</text>')
    parts.append(f'<text x="{width}" y="{top - 2}" text-anchor="end" class="tick">page size = 4&#8239;KiB</text>')
    parts.append("</svg>")
    return "".join(parts)


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    num_vars = rng.randint(5, 7)
    alloc, ops = _generate_trace(rng, num_vars)

    code_lines = []
    for op in ops:
        if op[0] == "alloc":
            _, name, size = op
            code_lines.append(f"{name} = allocate({size});")
        else:
            code_lines.append(f"free({op[1]});")
    code_block = "\n".join(code_lines)

    prompt = (
        f"A buddy-system allocator manages {TOTAL_PAGES} pages of physical memory "
        f"({PAGE_SIZE} Byte each, {TOTAL_PAGES * PAGE_SIZE} Byte total). Every "
        f"`allocate(n)` call rounds the number of required pages up to the next power of two "
        f"and returns a block of exactly that size; `free(x)` returns a block and merges it with "
        f"its buddy whenever the buddy is completely free. The following operations are "
        f"executed in order:\n\n```\n{code_block}\n```\n\n"
        f"For each operation, determine the resulting memory layout and the total "
        f"over-allocation (internal fragmentation, summed over all currently allocated "
        f"blocks). What is the total over-allocation immediately after the final operation?"
    )

    steps = [
        Step(
            "Each `allocate(n)` needs $\\lceil n / 4096 \\rceil$ pages, rounded up to the "
            "next power of two; that determines its **order** $k$ (block size $2^k$ pages). "
            "`free(x)` merges $x$'s block with its buddy (address $\\oplus\\, 2^k$) whenever "
            "that buddy is entirely free, repeating upward as long as merging is possible."
        )
    ]

    replay = BuddyAllocator()
    for op in ops:
        if op[0] == "alloc":
            _, name, size = op
            replay.allocate(name, size)
            order = replay.allocated[name][1]
            waste = (1 << order) * PAGE_SIZE - size
            pages_needed = -(-size // PAGE_SIZE)
            pages_needed_word = "page" if pages_needed == 1 else "pages"
            block_pages_word = "page" if (1 << order) == 1 else "pages"
            action_text = (
                f"`{name} = allocate({size})`: needs "
                f"$\\lceil {size}/4096 \\rceil = {pages_needed}$ {pages_needed_word} &rarr; "
                f"order {order} block ({1 << order} {block_pages_word}), waste = "
                f"${1 << order}\\cdot 4096 - {size} = {waste}$ Byte."
            )
        else:
            name = op[1]
            replay.free(name)
            action_text = f"`free({name})`."

        diagram = _diagram_svg(replay.blocks())
        over_alloc = replay.over_allocation()
        steps.append(
            Step(
                text=f"{action_text} Total over-allocation now $= {over_alloc}$ Byte.",
                diagram=diagram,
            )
        )

    final_over_alloc = replay.over_allocation()
    final_answer = f"Total over-allocation after the last operation: **{final_over_alloc} Byte**"

    answers = {
        "operations": [list(op) for op in ops],
        "final_over_allocation": final_over_alloc,
        "total_pages": TOTAL_PAGES,
        "page_size": PAGE_SIZE,
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

    parser = argparse.ArgumentParser(description="Generate a buddy-allocator exercise.")
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
