"""Exercise: translate virtual addresses to physical addresses using a
partially-populated page table (some pages have no frame -> page fault).

Direct hex-address input, checked instantly (green/red), instead of a
multiple-choice list of decoy addresses.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "os-page-table-translation"
TITLE = "Page Table: Virtual-to-Physical Address Translation"


def _hex(n: int, digits: int) -> str:
    return f"0x{n:0{digits}X}"


def _page_table_latex(
    num_pages: int, page_to_frame: dict[int, int], n_hex_digits: int, p_hex_digits: int
) -> str:
    cols = "|c|c|c|c|"
    rows = [
        "\\text{Page (Dec)} & \\text{Page (Hex)} & \\text{Frame (Dec)} & \\text{Frame (Hex)} \\\\"
    ]
    for page in range(num_pages):
        page_hex = f"\\texttt{{{_hex(page, n_hex_digits)}}}"
        if page in page_to_frame:
            frame = page_to_frame[page]
            frame_hex = f"\\texttt{{{_hex(frame, p_hex_digits)}}}"
            rows.append(f"{page} & {page_hex} & {frame} & {frame_hex} \\\\")
        else:
            rows.append(f"{page} & {page_hex} & - & - \\\\")
    body = " \\hline ".join(rows)
    return f"\\begin{{array}}{{{cols}}}\\hline {body} \\hline\\end{{array}}"


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    n_bits = rng.choice([3, 4])  # page-number bits
    k_bits = rng.choice([4, 5, 6, 7, 8])  # offset bits (page size)
    # Physical memory has capacity for as many frames as there are pages
    # (m_bits = n_bits, a realistic 1:1 sizing) -- faults come from a *lazy
    # allocation* gap (most, but not all, pages have actually been mapped to
    # a frame yet), not from physical memory being tiny relative to the
    # address space. This keeps the frame width realistic and lets most
    # addresses be genuine hits the student has to compute.
    m_bits = n_bits

    num_pages = 1 << n_bits
    num_frames_available = 1 << m_bits
    page_size = 1 << k_bits
    virtual_bits = n_bits + k_bits
    physical_bits = m_bits + k_bits
    v_hex_digits = max(1, -(-virtual_bits // 4))
    p_hex_digits = max(1, -(-physical_bits // 4))
    n_hex_digits = max(1, -(-n_bits // 4))

    # Map a high fraction of pages (mostly hits), leaving a handful of
    # deliberate gaps so page faults are still possible to encounter.
    fill_fraction = rng.uniform(0.7, 0.9)
    num_mapped = min(num_frames_available, max(1, round(num_pages * fill_fraction)))
    num_mapped = min(num_mapped, num_pages - 1)  # always leave >= 1 fault possible

    mapped_pages = sorted(rng.sample(range(num_pages), num_mapped))
    frame_ids = rng.sample(range(num_frames_available), num_mapped)
    page_to_frame = dict(zip(mapped_pages, frame_ids))
    unmapped_pages = [p for p in range(num_pages) if p not in page_to_frame]

    # Exactly one guaranteed fault (so the exercise still covers that case),
    # the rest are hits -- most of the 3 addresses require a real calculation.
    chosen: list[int] = []
    if unmapped_pages:
        chosen.append(rng.choice(unmapped_pages))
    hit_pool = [p for p in mapped_pages if p not in chosen]
    rng.shuffle(hit_pool)
    chosen.extend(hit_pool[: 3 - len(chosen)])
    while len(chosen) < 3:
        p = rng.choice(range(num_pages))
        if p not in chosen:
            chosen.append(p)
    rng.shuffle(chosen)
    chosen = chosen[:3]

    questions = []
    for page in chosen:
        offset = rng.randint(0, page_size - 1)
        virt_addr = page * page_size + offset
        va_hex = _hex(virt_addr, v_hex_digits)
        if page in page_to_frame:
            frame = page_to_frame[page]
            phys_addr = frame * page_size + offset
            questions.append(
                {
                    "va_hex": va_hex,
                    "page": page,
                    "offset": offset,
                    "frame": frame,
                    "answer": phys_addr,
                    "answer_hex": _hex(phys_addr, p_hex_digits),
                    "fault": False,
                }
            )
        else:
            questions.append(
                {
                    "va_hex": va_hex,
                    "page": page,
                    "offset": offset,
                    "frame": None,
                    "answer": "page fault",
                    "answer_hex": "page fault",
                    "fault": True,
                }
            )

    table_latex = _page_table_latex(num_pages, page_to_frame, n_hex_digits, p_hex_digits)

    prompt = (
        f"A system uses {virtual_bits}-bit virtual addresses, a page size of {page_size} Byte "
        f"($k = {k_bits}$ offset bits, $n = {n_bits}$ page-number bits), and "
        f"{physical_bits}-bit physical addresses ($m = {m_bits}$ frame-number bits). "
        f"The following shows the page table. A `-` means there is no page entry (a reference "
        f"to that page is a **page fault**).\n\n$${table_latex}$$\n\n"
        f"Translate each virtual address below to a physical address (as hex, e.g. `0x1A`), or "
        f"enter `page fault` if the page is not mapped."
    )

    steps = [
        Step(
            f"Split each virtual address into a page number (top $n={n_bits}$ bits) and an "
            f"offset (bottom $k={k_bits}$ bits): $\\text{{page}} = \\lfloor \\text{{addr}} / "
            f"{page_size} \\rfloor$, $\\text{{offset}} = \\text{{addr}} \\bmod {page_size}$. "
            f"Look up the page in the table: if it has a frame, the physical address is "
            f"$\\text{{frame}} \\times {page_size} + \\text{{offset}}$; otherwise it's a page fault."
        )
    ]
    for q in questions:
        if q["fault"]:
            steps.append(
                Step(
                    f"`{q['va_hex']}`: page {q['page']}, offset {q['offset']} &rarr; page {q['page']} "
                    f"has no frame in the table &rarr; **page fault**."
                )
            )
        else:
            steps.append(
                Step(
                    f"`{q['va_hex']}`: page {q['page']}, offset {q['offset']} &rarr; frame "
                    f"{q['frame']} &rarr; physical address $= {q['frame']} \\times {page_size} + "
                    f"{q['offset']} = {q['answer']}$ = `{q['answer_hex']}`."
                )
            )

    check_answers = [
        {
            "label": f"Physical address for virtual address {q['va_hex']}",
            "value": q["answer"],
            "type": "hex",
        }
        for q in questions
    ]

    final_answer = " &nbsp;&nbsp; ".join(f"`{q['va_hex']}` &rarr; `{q['answer_hex']}`" for q in questions)

    answers = {
        "n_bits": n_bits,
        "k_bits": k_bits,
        "m_bits": m_bits,
        "page_size": page_size,
        "page_to_frame": page_to_frame,
        "questions": questions,
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        final_answer=final_answer,
        check_answers=check_answers,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a page-table translation exercise.")
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
