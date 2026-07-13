"""Shared framework for exam-prep exercise generators.

Every exercise generator (algorithms / operating_system / linear_algebra)
follows the same contract:

    generate(seed: int | None = None) -> Exercise

- `seed` fixes the random parameters. Same seed -> exact same exercise.
- Solving is always a pure function of the generated parameters (no
  randomness in the solution itself), so the answer is fully deterministic
  and reproducible from the seed alone.
- If `seed` is None, a fresh random seed is drawn and returned inside the
  Exercise so the caller (web UI) can display/store/share it, e.g. as a
  permalink like /exercise/os-paging?seed=1234.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field


@dataclass
class Step:
    """One line of a worked solution. `text` may contain inline math
    delimited with $...$ (rendered client-side, e.g. via KaTeX). `diagram`
    is optional trusted inline SVG markup rendered as-is beneath the text."""

    text: str
    diagram: str = ""


@dataclass
class Exercise:
    id: str  # stable identifier of the exercise type, e.g. "os-paging-1level"
    seed: int
    title: str
    prompt: str  # problem statement, markdown + $...$ latex math
    steps: list[Step] = field(default_factory=list)  # worked solution
    answers: dict = field(default_factory=dict)  # final answers, machine-checkable
    diagram: str = ""  # optional inline SVG markup illustrating the setup
    final_answer: str = ""  # optional short final result, rendered boxed + centered
    check_answers: list[dict] = field(default_factory=list)
    # each item: {"label", "value", "type": "number"|"text"|"hex", "unit"?}
    # rendered as an interactive input; on "Check" the field turns green/red.
    # "hex": input parsed as hex (optional 0x prefix) and compared numerically
    # to `value` if it's an int, or case-insensitively as text if `value` is a str
    # (e.g. "page fault").
    check_table: dict | None = None
    # {"col_headers": [str, ...], "rows": [{"label": str, "cells": [value, ...]}, ...],
    #  "cell_unit"?: str, "cell_hint"?: str}
    # rendered as a real HTML table: first column is the given (non-editable)
    # row label, every other column is a "Check"-graded number input. `value`
    # entries are numbers (or null to leave a column blank/uncheckable for a
    # given row). `cell_hint` is optional muted text shown under the table
    # (e.g. "enter the exponent n such that #entries = 2^n").

    def to_json(self, **kwargs) -> str:
        d = asdict(self)
        return json.dumps(d, **kwargs)


def new_seed(rng: random.Random | None = None) -> int:
    """Draw a fresh seed usable both for reproducing and for sharing."""
    source = rng or random.Random()
    return source.randrange(0, 2**31 - 1)


def bits_for(n: int) -> int:
    """Number of bits needed to represent n as a power of two exponent,
    i.e. log2(n), requiring n to be an exact power of two."""
    if n <= 0 or (n & (n - 1)) != 0:
        raise ValueError(f"{n} is not a positive power of two")
    return n.bit_length() - 1


def fmt_bytes(n: int) -> str:
    """Human readable byte size using binary units where it reads cleanly."""
    if n < 1024:
        return f"{n} Byte"
    for unit, size in (("GiB", 2**30), ("MiB", 2**20), ("KiB", 2**10)):
        if n >= size and n % size == 0:
            return f"{n // size} {unit} ({n} Byte)"
    return f"{n} Byte"
