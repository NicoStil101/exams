"""Exercise: single-level page table address translation.

Mirrors the classic exam question:

    "Assume the width of a virtual address to be n bit. There are P Byte of
    physical memory. Assume the size of a page and the size of a page frame
    to be equal. Address translation is done via a single-level page table.
    Assume a page size of S Byte. How many bits of the virtual address do
    you need for the page number, how many for the offset? How many bits of
    the physical address do you need for the frame number, how many for the
    offset? How many pages can be addressed?"

Parameters are randomized (virtual address width, physical memory size,
page size), but solving is pure arithmetic (log2 / subtraction), so the
answer is 100% deterministic given the generated parameters.
"""

from __future__ import annotations

import random

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, bits_for, fmt_bytes, new_seed  # noqa: E402

EXERCISE_ID = "os-paging-1level"
TITLE = "Single-Level Page Table: Address Translation"

# Keep numbers exam-realistic: small enough to reason about by hand.
_VIRTUAL_ADDR_BITS_CHOICES = range(8, 17)  # 8..16 bit virtual address


def _choose_params(rng: random.Random) -> tuple[int, int, int]:
    """Pick (virtual_address_bits, physical_memory_bytes, page_size_bytes)
    such that every derived quantity is a positive integer number of bits.
    """
    virtual_address_bits = rng.choice(list(_VIRTUAL_ADDR_BITS_CHOICES))

    # Physical memory is usually smaller than the virtual address space in
    # these exercises; keep physical_address_bits <= virtual_address_bits
    # but at least 6 bits (64 Byte) so the problem stays non-trivial.
    max_phys_bits = virtual_address_bits
    min_phys_bits = min(6, max_phys_bits - 1)
    physical_address_bits = rng.randint(min_phys_bits, max_phys_bits)

    # Offset (page size) bits: must leave at least 1 bit for both the page
    # number (out of virtual_address_bits) and the frame number (out of
    # physical_address_bits).
    max_offset_bits = min(virtual_address_bits, physical_address_bits) - 1
    offset_bits = rng.randint(1, max_offset_bits)

    physical_memory_bytes = 2**physical_address_bits
    page_size_bytes = 2**offset_bits
    return virtual_address_bits, physical_memory_bytes, page_size_bytes


def _diagram_svg() -> str:
    """Render the generic virtual-address / physical-address bit-field
    diagram, matching the classic textbook layout: [page number | offset] on
    top, translated into [frame number | offset] below. This is a purely
    schematic figure (fixed proportions, symbolic n/k/m labels) -- it must
    NOT reveal the actual bit widths, since those are exactly what the
    exercise asks the student to work out."""
    w = 380
    row_h = 42
    y_top = 34
    gap = 64
    y_bottom = y_top + row_h + gap
    margin_r = 130
    view_w = w + margin_r
    view_h = y_bottom + row_h + 26

    # Fixed generic split, independent of the actual bit widths.
    pn_w, off1_w = 0.58 * w, 0.42 * w
    fn_w, off2_w = 0.42 * w, 0.58 * w

    return f'''<svg viewBox="0 0 {view_w} {view_h}" width="{view_w}" height="{view_h}" xmlns="http://www.w3.org/2000/svg" class="addr-diagram">
  <style>
    .addr-diagram text {{ font-family: Georgia, 'Times New Roman', serif; font-size: 13px; fill: var(--diagram-ink, #111); }}
    .addr-diagram .lbl {{ font-size: 11px; fill: var(--diagram-muted, #555); }}
    .addr-diagram rect {{ fill: var(--diagram-surface, #fff); stroke: var(--diagram-ink, #111); stroke-width: 1.3; }}
    .addr-diagram line {{ stroke: var(--diagram-ink, #111); stroke-width: 1.3; }}
  </style>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="var(--diagram-ink, #111)" />
    </marker>
  </defs>
  <text x="{pn_w / 2}" y="{y_top - 12}" text-anchor="middle" class="lbl"><tspan font-style="italic">n</tspan> bit</text>
  <text x="{pn_w + off1_w / 2}" y="{y_top - 12}" text-anchor="middle" class="lbl"><tspan font-style="italic">k</tspan> bit</text>
  <rect x="0" y="{y_top}" width="{pn_w}" height="{row_h}" />
  <rect x="{pn_w}" y="{y_top}" width="{off1_w}" height="{row_h}" />
  <text x="{pn_w / 2}" y="{y_top + row_h / 2 + 5}" text-anchor="middle">page number</text>
  <text x="{pn_w + off1_w / 2}" y="{y_top + row_h / 2 + 5}" text-anchor="middle">offset</text>
  <text x="{w + 14}" y="{y_top + row_h / 2 + 5}" class="lbl">virtual address</text>
  <line x1="{pn_w / 2}" y1="{y_top + row_h}" x2="{pn_w / 2}" y2="{y_bottom - 6}" marker-end="url(#arrow)" />
  <line x1="{pn_w + off1_w / 2}" y1="{y_top + row_h}" x2="{fn_w + off2_w / 2}" y2="{y_bottom - 6}" marker-end="url(#arrow)" />
  <text x="{w / 2}" y="{(y_top + row_h + y_bottom) / 2 + 4}" text-anchor="middle" class="lbl">address translation</text>
  <rect x="0" y="{y_bottom}" width="{fn_w}" height="{row_h}" />
  <rect x="{fn_w}" y="{y_bottom}" width="{off2_w}" height="{row_h}" />
  <text x="{fn_w / 2}" y="{y_bottom + row_h / 2 + 5}" text-anchor="middle">frame number</text>
  <text x="{fn_w + off2_w / 2}" y="{y_bottom + row_h / 2 + 5}" text-anchor="middle">offset</text>
  <text x="{w + 14}" y="{y_bottom + row_h / 2 + 5}" class="lbl">physical address</text>
  <text x="{fn_w / 2}" y="{y_bottom + row_h + 18}" text-anchor="middle" class="lbl"><tspan font-style="italic">m</tspan> bit</text>
  <text x="{fn_w + off2_w / 2}" y="{y_bottom + row_h + 18}" text-anchor="middle" class="lbl"><tspan font-style="italic">k</tspan> bit</text>
</svg>'''


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    virtual_address_bits, physical_memory_bytes, page_size_bytes = _choose_params(rng)

    offset_bits = bits_for(page_size_bytes)
    page_number_bits = virtual_address_bits - offset_bits
    physical_address_bits = bits_for(physical_memory_bytes)
    frame_number_bits = physical_address_bits - offset_bits
    num_addressable_pages = 2**page_number_bits
    num_frames = 2**frame_number_bits

    prompt = (
        f"Assume the width of a virtual address to be {virtual_address_bits} bit. "
        f"There are {fmt_bytes(physical_memory_bytes)} of physical memory. "
        f"Assume the size of a page and the size of a page frame to be equal "
        f"(you can assume this equality throughout the entire course). "
        f"Address translation is done via single-level page table.\n\n"
        f"**a)** Assume a page size of {fmt_bytes(page_size_bytes)}. Using $n$ for the "
        f"page-number width, $k$ for the offset width, and $m$ for the frame-number width "
        f"(as in the figure below), determine $k$, $n$, and $m$. How many pages can be "
        f"addressed?"
    )

    steps = [
        Step(
            f"Page size is {page_size_bytes} Byte $= 2^{{{offset_bits}}}$ Byte, "
            f"so the **offset** needs $k = {offset_bits}$ bits."
        ),
        Step(
            f"Virtual address width is {virtual_address_bits} bit, so the "
            f"**page number** needs $n = {virtual_address_bits} - {offset_bits} = "
            f"{page_number_bits}$ bits."
        ),
        Step(
            f"Physical memory is {physical_memory_bytes} Byte $= 2^{{{physical_address_bits}}}$ "
            f"Byte, so the physical address is {physical_address_bits} bit wide."
        ),
        Step(
            f"The **frame number** needs $m = {physical_address_bits} - {offset_bits} = "
            f"{frame_number_bits}$ bits (offset is still $k = {offset_bits}$ bits, "
            f"since page and frame size are equal)."
        ),
        Step(
            f"Number of addressable pages $= 2^n = 2^{{{page_number_bits}}} = "
            f"{num_addressable_pages}$."
        ),
    ]

    answers = {
        "offset_bits": offset_bits,
        "page_number_bits": page_number_bits,
        "physical_address_bits": physical_address_bits,
        "frame_number_bits": frame_number_bits,
        "num_addressable_pages": num_addressable_pages,
        "num_frames": num_frames,
    }

    diagram = _diagram_svg()

    check_answers = [
        {"label": "k (bits for the offset)", "value": offset_bits, "type": "number"},
        {"label": "n (bits for the page number)", "value": page_number_bits, "type": "number"},
        {"label": "m (bits for the frame number)", "value": frame_number_bits, "type": "number"},
        {"label": "Number of pages that can be addressed (2^n)", "value": num_addressable_pages, "type": "number"},
    ]

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        diagram=diagram,
        check_answers=check_answers,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a paging exercise.")
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
