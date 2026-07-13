"""Exercise: number of single-level page table entries for combinations of
page size and virtual address width.

For a page of size 2^k Byte and a virtual address of v bits, the page
number is v - k bits wide, so a single-level page table needs 2^(v-k)
entries -- one per possible page number. Since that count is astronomically
large for wide addresses (2^52, ...), the student enters the *exponent*
(v - k) rather than the literal integer, exactly like the reference exam
sheet writes answers as "2^20" rather than spelling out the number.

Rendered as a real fill-in table: the "Page size" column is given, every
other column (offset, and one #entries column per virtual address width)
is a graded input.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, bits_for, new_seed  # noqa: E402

EXERCISE_ID = "os-page-table-entries"
TITLE = "Page Table Entries: Page Size vs. Virtual Address Width"

_PAGE_SIZE_CHOICES_KIB = [1, 2, 4, 8, 16, 32, 64]
_VA_WIDTH_CHOICES = [16, 24, 32, 48, 64]


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    page_sizes_kib = sorted(rng.sample(_PAGE_SIZE_CHOICES_KIB, 3))
    va_widths = sorted(rng.sample(_VA_WIDTH_CHOICES, 3))

    rows = []
    for size_kib in page_sizes_kib:
        page_bytes = size_kib * 1024
        offset_bits = bits_for(page_bytes)
        exponents = [v - offset_bits for v in va_widths]
        rows.append(
            {
                "size_kib": size_kib,
                "page_bytes": page_bytes,
                "offset_bits": offset_bits,
                "exponents": exponents,
            }
        )

    prompt = (
        f"Calculate the number of entries a single-level page table would need for all "
        f"combinations of page size and width of a virtual address below.\n\n"
        f"- Width of a virtual address (this determines the size of the virtual address "
        f"space): {', '.join(str(v) for v in va_widths)} bit\n"
        f"- Page size: {', '.join(str(s) + ' KiB' for s in page_sizes_kib)}\n\n"
        f"Fill in the offset width and, for each virtual-address width, the number of page "
        f"table entries **as an exponent of 2** (e.g. enter `20` for $2^{{20}}$ entries)."
    )

    steps = [
        Step(
            "The offset is $k = \\log_2(\\text{page size})$ bits. For a virtual address of "
            "$v$ bits, the page number is $v - k$ bits wide, so a single-level page table "
            "needs one entry per possible page number: $2^{v-k}$ entries. Because that count "
            "is enormous for wide addresses, it's conventional to give the answer as the "
            "exponent $v - k$ rather than the literal integer."
        )
    ]
    for row in rows:
        exp_text = ", ".join(
            f"$v={v}$: $2^{{{v}}} / 2^{{{row['offset_bits']}}} = 2^{{{e}}}$"
            for v, e in zip(va_widths, row["exponents"])
        )
        steps.append(
            Step(
                f"Page size {row['size_kib']} KiB $= {row['page_bytes']}$ Byte "
                f"$= 2^{{{row['offset_bits']}}}$ Byte $\\Rightarrow k = {row['offset_bits']}$. {exp_text}."
            )
        )

    check_table = {
        "col_headers": ["offset (bit)"] + [f"{v} Bit" for v in va_widths],
        "cell_hint": "enter the exponent n such that #entries = 2^n (offset is a plain bit count)",
        "rows": [
            {
                "label": f"{row['size_kib']} KiB = {row['page_bytes']} Byte = 2^{row['offset_bits']} Byte",
                "cells": [row["offset_bits"]] + row["exponents"],
            }
            for row in rows
        ],
    }

    answers = {
        "page_sizes_kib": page_sizes_kib,
        "va_widths": va_widths,
        "rows": rows,
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        check_table=check_table,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a page-table-entries exercise.")
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
        print("\nCheck table:", ex.check_table)
        print("Answers:", ex.answers)
