"""Exercise: maximum file size of an i-node based filesystem.

Randomised parameters: block size (power of two), block address width, the
number of direct references, and the counts of single/double/triple indirect
references. Everything is a power of two or a small integer, so the whole
computation is exact:

    P                = block_size / pointer_size      (pointers per block)
    max data blocks  = d + n1*P + n2*P^2 + n3*P^3
    max file size    = max_data_blocks * block_size

The block size is at least 1 KiB so the file size is an integer number of
KiB (used for the machine-checked answer). An inline SVG shows the classic
i-node picture: attribute fields, the direct block addresses, and the
indirect pointer chains.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # `core`

from core import Exercise, Step, bits_for, fmt_bytes, new_seed  # noqa: E402

EXERCISE_ID = "os-inode-max-filesize"
TITLE = "I-Nodes: Maximum File Size"

_BLOCK_SIZES = (1024, 2048, 4096)
_ADDRESS_BITS = (32, 64)
_DIRECT_CHOICES = (8, 10, 11, 12, 13, 15)
# (n1, n2, n3) counts of single/double/triple indirect references; the
# classic 1/1/1 layout is weighted highest, plus a few exam variations.
_INDIRECT_CONFIGS = ((1, 1, 1), (1, 1, 1), (1, 1, 1), (2, 1, 1), (1, 2, 1), (2, 1, 0))

_WORDS = {
    0: "no", 1: "one", 2: "two", 3: "three", 8: "eight", 10: "ten",
    11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
}

_INK = "var(--diagram-ink, #111)"
_SURFACE = "var(--diagram-surface, #fff)"


def _word(n: int) -> str:
    return _WORDS.get(n, str(n))


def _fmt_big(n: int) -> str:
    """Group digits so 17247252480 reads as 17\\,247\\,252\\,480 in TeX."""
    s = str(n)
    groups = []
    while s:
        groups.append(s[-3:])
        s = s[:-3]
    return "\\,".join(reversed(groups))


def _approx_size(n_bytes: int) -> str:
    for unit, size in (("TiB", 2**40), ("GiB", 2**30), ("MiB", 2**20)):
        if n_bytes >= size:
            return f"{n_bytes / size:.2f}\\ \\mathrm{{{unit}}}"
    return f"{n_bytes // 1024}\\ \\mathrm{{KiB}}"


def _striped_block(x: int, y: int, w: int = 22, h: int = 18) -> str:
    lines = "".join(
        f'<line x1="{x}" y1="{y + i * h // 4}" x2="{x + w}" y2="{y + i * h // 4}" '
        f'stroke="{_INK}" stroke-width="1"/>'
        for i in range(1, 4)
    )
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{_SURFACE}" '
        f'stroke="{_INK}" stroke-width="1.4"/>' + lines
    )


def _arrow(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{_INK}" '
        f'stroke-width="1.4" marker-end="url(#inode-arrow)"/>'
    )


def _diagram_svg(direct: int, n1: int, n2: int, n3: int) -> str:
    """The classic i-node figure: attribute rows, the direct address block,
    and one pointer chain per indirect level (one hop per indirection)."""
    box_x, box_w, row_h = 60, 160, 24
    attrs = ["Mode", "Link count", "Uid", "Gid", "File size", "Times"]
    rows: list[tuple[str, int]] = [(a, row_h) for a in attrs]
    rows.append((f"Addresses of first {direct} disk blocks", 44))
    levels = [("Single indirect", n1, 1), ("Double indirect", n2, 2)]
    if n3:
        levels.append(("Triple indirect", n3, 3))
    for label, count, _ in levels:
        rows.append((f"{label}" + (f" (×{count})" if count > 1 else ""), row_h))

    total_h = sum(h for _, h in rows)
    parts = [
        '<defs><marker id="inode-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 9 5 L 0 9 z" fill="{_INK}"/></marker></defs>',
        f'<text x="{box_x + box_w / 2}" y="14" text-anchor="middle" '
        f'font-size="13" font-weight="600" fill="{_INK}">i-node</text>',
    ]

    y = 24
    row_mid: dict[str, float] = {}
    for label, h in rows:
        parts.append(
            f'<rect x="{box_x}" y="{y}" width="{box_w}" height="{h}" fill="{_SURFACE}" '
            f'stroke="{_INK}" stroke-width="1.4"/>'
        )
        mid = y + h / 2
        row_mid[label.split(" (")[0]] = mid
        words = label.split()
        if h > row_h and len(words) > 4:  # wrap the direct-addresses label
            half = len(words) // 2
            for k, line in enumerate((" ".join(words[:half]), " ".join(words[half:]))):
                parts.append(
                    f'<text x="{box_x + box_w / 2}" y="{mid + (k - 0.5) * 13 + 4}" '
                    f'text-anchor="middle" font-size="11.5" fill="{_INK}">{line}</text>'
                )
        else:
            parts.append(
                f'<text x="{box_x + box_w / 2}" y="{mid + 4}" text-anchor="middle" '
                f'font-size="11.5" fill="{_INK}">{label}</text>'
            )
        y += h

    # one chain per indirect level: as many striped blocks as indirections,
    # then a fan of pointers to data blocks
    chain_x0, hop = box_x + box_w + 46, 64
    for label, _count, depth in levels:
        mid = row_mid[label]
        parts.append(_arrow(box_x + box_w, mid, chain_x0 - 2, mid))
        for i in range(depth):
            bx = chain_x0 + i * hop
            parts.append(_striped_block(bx, int(mid) - 9))
            if i + 1 < depth:
                parts.append(_arrow(bx + 22, mid, bx + hop - 2, mid))
        end_x = chain_x0 + (depth - 1) * hop + 22
        for dy in (-9, 9):
            parts.append(_arrow(end_x, mid + dy / 3, end_x + 26, mid + dy))
        parts.append(
            f'<text x="{end_x + 32}" y="{mid + 4}" font-size="11" fill="{_INK}">'
            f"pointers to {'disk blocks' if depth == 1 else 'blocks'}</text>"
        )

    width = chain_x0 + 3 * hop + 130
    height = total_h + 36
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" class="inode-diagram" '
        f'style="max-width: 100%; height: auto;">' + "".join(parts) + "</svg>"
    )


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    block = rng.choice(_BLOCK_SIZES)
    addr_bits = rng.choice(_ADDRESS_BITS)
    direct = rng.choice(_DIRECT_CHOICES)
    n1, n2, n3 = rng.choice(_INDIRECT_CONFIGS)

    ptr_bytes = addr_bits // 8
    pointers = block // ptr_bytes  # P
    m = bits_for(pointers)

    contrib = [direct, n1 * pointers, n2 * pointers**2, n3 * pointers**3]
    total_blocks = sum(contrib)
    filesize = total_blocks * block
    filesize_kib = filesize // 1024

    ref_text = (
        f"**{_word(direct)} direct, {_word(n1)} single-indirect, "
        f"{_word(n2)} double-indirect, and {_word(n3)} triple-indirect "
        f"reference{'s' if n3 != 1 else ''} to datablocks**"
    )

    prompt = (
        "Similar to the techniques used for main memory, long-term storage (i.e. HDDs, "
        "SSDs etc.) is managed in blocks of fixed size instead of individual Bytes. For "
        f"this exercise we assume the block size to be {fmt_bytes(block)} and the address "
        f"of a block to be {addr_bits} bits wide.\n\n"
        f"Amongst the usual attributes, the i-nodes in this filesystem store {ref_text}. "
        "What is the maximum filesize possible with this configuration?"
    )

    level_names = ("single", "double", "triple")
    steps: list[Step] = [
        Step(
            f"**Pointers per block.** A block address is {addr_bits} bits $= {ptr_bytes}$ "
            f"Byte wide, so one {fmt_bytes(block)} block holds "
            f"$P = \\frac{{{block}}}{{{ptr_bytes}}} = {pointers} = 2^{{{m}}}$ pointers."
        ),
        Step(
            f"**Direct references.** The {_word(direct)} direct references address "
            f"${direct}$ data blocks."
        ),
    ]
    descriptions = {
        1: "points to a block full of pointers to data blocks",
        2: "points to a block of pointers to single-indirect blocks",
        3: "points to a block of pointers to double-indirect blocks",
    }
    for name, count, power in zip(level_names, (n1, n2, n3), (1, 2, 3)):
        if count == 0:
            continue
        chain = " \\cdot ".join(["P"] * power)
        value = count * pointers**power
        prefix = "" if count == 1 else f"{count} \\cdot "
        steps.append(
            Step(
                f"**{name.capitalize()}-indirect.** Each {name}-indirect reference "
                f"{descriptions[power]}, addressing ${chain} = P^{power}$ data blocks each: "
                f"${prefix}P^{power} = {prefix}({pointers})^{power} = {value}$ blocks."
            )
        )
    if n3 == 0:
        steps.append(Step("**Triple-indirect.** None in this configuration."))

    sum_terms = " + ".join(str(c) for c in contrib if c)
    steps.append(
        Step(
            "**Total addressable data blocks.**\n\n"
            f"$$N = {direct} + {n1} \\cdot P + {n2} \\cdot P^2"
            + (f" + {n3} \\cdot P^3" if n3 else "")
            + f" = {sum_terms} = {_fmt_big(total_blocks)}.$$"
        )
    )
    steps.append(
        Step(
            "**Maximum file size.** Every data block stores "
            f"{fmt_bytes(block)}, so\n\n"
            f"$$N \\cdot {block}\\ \\mathrm{{Byte}} = {_fmt_big(filesize)}\\ \\mathrm{{Byte}} "
            f"= {_fmt_big(filesize_kib)}\\ \\mathrm{{KiB}} \\approx {_approx_size(filesize)}.$$"
        )
    )
    dom_count, dom_power, dom_blocks = next(
        (count, power, blocks)
        for count, power, blocks in ((n3, 3, contrib[3]), (n2, 2, contrib[2]), (n1, 1, contrib[1]))
        if count
    )
    dominant = f"P^{dom_power}" if dom_count == 1 else f"{dom_count} \\cdot P^{dom_power}"
    steps.append(
        Step(
            f"**Sanity check.** The ${dominant}$ term dominates the sum, so the result "
            f"must be just over ${dominant} \\cdot {block // 1024}\\ \\mathrm{{KiB}} "
            f"\\approx {_approx_size(dom_blocks * block)}$ ✓"
        )
    )

    final_answer = (
        f"$$\\text{{max filesize}} = {_fmt_big(total_blocks)} \\cdot {block}\\ \\mathrm{{Byte}} "
        f"= {_fmt_big(filesize_kib)}\\ \\mathrm{{KiB}} \\approx {_approx_size(filesize)}$$"
    )

    check_answers = [
        {"label": "Pointers per block $P$", "value": pointers, "type": "number"},
        {"label": "Maximum number of data blocks $N$", "value": total_blocks, "type": "number"},
        {"label": "Maximum file size", "value": filesize_kib, "type": "number", "unit": "KiB"},
    ]
    check_table = {
        "col_headers": ["data blocks"],
        "cell_hint": "number of data blocks addressable through each reference type",
        "rows": [
            {"label": label, "cells": [value]}
            for label, value in (
                ("direct", contrib[0]),
                ("single-indirect", contrib[1]),
                ("double-indirect", contrib[2]),
                ("triple-indirect", contrib[3]),
            )
            if value or label == "direct"
        ],
    }

    answers = {
        "block_size": block,
        "address_bits": addr_bits,
        "direct": direct,
        "indirect_counts": [n1, n2, n3],
        "pointers_per_block": pointers,
        "blocks_per_level": contrib,
        "total_blocks": total_blocks,
        "max_filesize_bytes": filesize,
        "max_filesize_kib": filesize_kib,
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        diagram=_diagram_svg(direct, n1, n2, n3),
        final_answer=final_answer,
        check_answers=check_answers,
        check_table=check_table,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate an i-node max filesize exercise.")
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
        print("\nCheck answers:", ex.check_answers)
        print("Check table:", ex.check_table)
        print("Answers:", ex.answers)
