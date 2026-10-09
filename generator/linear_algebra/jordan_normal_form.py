"""Exercise: Jordan normal form of a 3x3 or 4x4 integer matrix.

Construction: draw a Jordan matrix $J$ (small integer eigenvalues, at least
one block of size $\\ge 2$) and a unimodular integer $P = LU$ (unit lower
times unit upper triangular, so $\\det P = 1$ and $P^{-1}$ is integral), then
set $A = P J P^{-1}$. Everything the student sees or computes is therefore an
integer: $A$, the characteristic polynomial, the eigenvalues, the matrices
$(A - \\lambda I)^k$ and their ranks, and $J$ itself — no fractions appear at
any point.

The solution does NOT read off the construction. From $A$ alone it computes
the characteristic polynomial, its integer roots with multiplicities, and the
kernel dimensions $d_k(\\lambda) = \\dim \\ker (A - \\lambda I)^k$; the number
of Jordan blocks of size exactly $k$ is then

    b_k = 2 d_k - d_{k-1} - d_{k+1},

which fixes $J$ up to the order of the blocks. The order is pinned down in
the problem statement (ascending eigenvalue, then descending block size) so
that the answer is unique and machine-checkable.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.append(str(_here.parent))
sys.path.append(str(_here.parents[1]))  # `core`

import sympy  # noqa: E402

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "la-jordan-normal-form"
TITLE = "Jordan Normal Form of a 3x3 / 4x4 Matrix"

Matrix = list[list[int]]

# Block structures per dimension: each entry is a list of block-size groups,
# one group per (distinct) eigenvalue. Every structure has at least one block
# of size >= 2, so the answer is never just a diagonal matrix.
_STRUCTURES: dict[int, tuple[tuple[tuple[int, ...], ...], ...]] = {
    3: (
        ((3,),),
        ((2, 1),),
        ((2,), (1,)),
    ),
    4: (
        ((4,),),
        ((3, 1),),
        ((2, 2),),
        ((2, 1, 1),),
        ((3,), (1,)),
        ((2,), (2,)),
        ((2, 1), (1,)),
        ((2,), (1, 1)),
        ((2,), (1,), (1,)),
    ),
}

_EIGENVALUE_CHOICES = (-2, 0, 2)  # even only: easy candidates, small arithmetic
_P_CHOICES = (-1, 0, 0, 1)
_MAX_A_ENTRY = 6
_MIN_OFFDIAGONAL_NONZERO = 4
_MIN_ZEROS = {3: 1, 4: 2}  # spread-out zeros keep the Laplace expansion short
_MAX_NEGATIVES = {3: 3, 4: 5}  # positive-dominant matrices
_ATTEMPTS_PER_STRUCTURE = 60  # bounded tries per drawn block structure (see below)


def _zero_pattern_ok(a_mat: Matrix, min_total: int) -> bool:
    """At least `min_total` zeros, none on the main diagonal, no row or
    column holding more than one, and one further zero must be obtainable by
    a single row operation R_i <- R_i -+ R_k (i.e. two rows agree up to sign
    somewhere)."""
    n = len(a_mat)
    if any(a_mat[i][i] == 0 for i in range(n)):
        return False
    row_zeros = [sum(1 for v in row if v == 0) for row in a_mat]
    col_zeros = [sum(1 for row in a_mat if row[j] == 0) for j in range(n)]
    if sum(row_zeros) < min_total or max(row_zeros) > 1 or max(col_zeros) > 1:
        return False
    return any(
        a_mat[i][j] != 0 and a_mat[i][j] in (a_mat[k][j], -a_mat[k][j])
        for i in range(n)
        for k in range(n)
        if i != k
        for j in range(n)
    )


def _bmatrix(m: Matrix) -> str:
    """LaTeX bmatrix for an integer matrix of any size."""
    rows = " \\\\ ".join(" & ".join(str(v) for v in row) for row in m)
    return f"\\begin{{bmatrix}} {rows} \\end{{bmatrix}}"


def _to_int_matrix(m: sympy.Matrix) -> Matrix:
    values = m.tolist()
    for row in values:
        for value in row:
            assert value.is_Integer, f"non-integer entry {value}"
    return [[int(value) for value in row] for row in values]


def _jordan_matrix(blocks: list[tuple[int, int]], n: int) -> Matrix:
    """Block-diagonal Jordan matrix from an ordered list of (eigenvalue, size)."""
    j = [[0] * n for _ in range(n)]
    offset = 0
    for eigenvalue, size in blocks:
        for i in range(size):
            j[offset + i][offset + i] = eigenvalue
            if i + 1 < size:
                j[offset + i][offset + i + 1] = 1
        offset += size
    return j


def _ordered_blocks(groups: list[tuple[int, tuple[int, ...]]]) -> list[tuple[int, int]]:
    """Canonical order: ascending eigenvalue, then descending block size."""
    ordered: list[tuple[int, int]] = []
    for eigenvalue, sizes in sorted(groups):
        for size in sorted(sizes, reverse=True):
            ordered.append((eigenvalue, size))
    return ordered


def _random_unimodular(rng: random.Random, n: int) -> tuple[sympy.Matrix, sympy.Matrix]:
    """P = L @ U with unit triangular integer factors, so det(P) = 1 and both
    P and P^{-1} are integer matrices."""
    while True:
        lower = sympy.eye(n)
        upper = sympy.eye(n)
        for i in range(n):
            for j in range(n):
                if i > j:
                    lower[i, j] = rng.choice(_P_CHOICES)
                elif i < j:
                    upper[i, j] = rng.choice(_P_CHOICES)
        p = lower * upper
        if p != sympy.eye(n):
            return p, p.inv()


def _kernel_dimensions(b: sympy.Matrix, n: int, algebraic: int) -> list[int]:
    """d_k = dim ker(B^k) for k = 0, 1, ... until the generalised eigenspace is
    exhausted (d_k = algebraic multiplicity), with one repeated value appended
    so that d_{k+1} can be read off for every relevant k."""
    dims = [0]
    power = sympy.eye(b.rows)
    while dims[-1] < algebraic:
        power = power * b
        dims.append(n - power.rank())
    dims.append(dims[-1])
    return dims


def _block_sizes(dims: list[int]) -> list[int]:
    """Blocks of size exactly k number 2*d_k - d_{k-1} - d_{k+1}; returned as a
    descending list of sizes."""
    sizes: list[int] = []
    for k in range(1, len(dims) - 1):
        count = 2 * dims[k] - dims[k - 1] - dims[k + 1]
        sizes.extend([k] * count)
    return sorted(sizes, reverse=True)


def _offdiagonal_nonzero(a: Matrix) -> int:
    return sum(1 for i, row in enumerate(a) for j, v in enumerate(row) if i != j and v)


def _no_duplicate_lines(a: Matrix) -> bool:
    """Reject matrices with two rows or two columns equal up to sign — those
    make the rank (and hence much of the answer) visible at a glance."""
    n = len(a)
    for i in range(n):
        for k in range(i + 1, n):
            if a[i] == a[k] or a[i] == [-v for v in a[k]]:
                return False
            col_i = [a[r][i] for r in range(n)]
            col_k = [a[r][k] for r in range(n)]
            if col_i == col_k or col_i == [-v for v in col_k]:
                return False
    return True


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    # The block structure is drawn first and given a bounded number of
    # attempts. With a single flat retry loop, structures whose conjugates
    # rarely satisfy the entry/zero-pattern filters would almost never be
    # seen and the easiest structure would swallow most seeds.
    while True:
        n = rng.choice((3, 4))
        structure = rng.choice(_STRUCTURES[n])
        # Derogatory structures (an eigenvalue with an extra size-1 block,
        # e.g. blocks 2+1 for the same lambda) force A = lambda*I + (low rank)
        # in which isolated off-diagonal zeros are rare or impossible — for
        # those the zero *minimum* is waived; the spread rules still apply.
        min_zeros = (
            0
            if any(len(sizes) >= 2 and min(sizes) == 1 for sizes in structure)
            else _MIN_ZEROS[n]
        )
        found = False
        for _ in range(_ATTEMPTS_PER_STRUCTURE):
            eigenvalues = rng.sample(_EIGENVALUE_CHOICES, len(structure))
            groups = list(zip(eigenvalues, structure))
            j_mat = _jordan_matrix(_ordered_blocks(groups), n)
            p, p_inv = _random_unimodular(rng, n)
            a_mat = _to_int_matrix(p * sympy.Matrix(j_mat) * p_inv)
            if max(abs(v) for row in a_mat for v in row) > _MAX_A_ENTRY:
                continue
            if sum(1 for row in a_mat for v in row if v < 0) > _MAX_NEGATIVES[n]:
                continue
            if not _zero_pattern_ok(a_mat, min_zeros):
                continue  # zeros (where required) spread out; a further one within reach
            if not any(abs(v) == 1 for row in a_mat for v in row):
                continue  # a +-1 entry keeps expansions and row operations cheap
            if _offdiagonal_nonzero(a_mat) < _MIN_OFFDIAGONAL_NONZERO:
                continue  # keep A from looking (block-)triangular already
            if not _no_duplicate_lines(a_mat):
                continue
            if a_mat == j_mat:
                continue
            found = True
            break
        if found:
            break

    # --- solve from A alone -------------------------------------------------
    a_sym = sympy.Matrix(a_mat)
    lam = sympy.Symbol("lambda")
    char_poly = a_sym.charpoly(lam)  # det(lambda*I - A), monic with integer coefficients
    char_expr = char_poly.as_expr()
    multiplicities = {int(root): int(mult) for root, mult in sympy.roots(char_poly).items()}

    per_eigenvalue = []
    for eigenvalue in sorted(multiplicities):
        algebraic = multiplicities[eigenvalue]
        shifted = a_sym - eigenvalue * sympy.eye(n)
        dims = _kernel_dimensions(shifted, n, algebraic)
        sizes = _block_sizes(dims)
        per_eigenvalue.append(
            {
                "eigenvalue": eigenvalue,
                "algebraic": algebraic,
                "geometric": dims[1],
                "kernel_dims": dims[1:-1],
                "dims_padded": dims,  # d_0 = 0 in front, d_{K+1} = d_K appended
                "block_sizes": sizes,
                "powers": [
                    _to_int_matrix(shifted**k) for k in range(1, len(dims) - 1)
                ],
            }
        )

    jordan = _jordan_matrix(
        _ordered_blocks([(e["eigenvalue"], tuple(e["block_sizes"])) for e in per_eigenvalue]), n
    )
    all_sizes = [size for e in per_eigenvalue for size in e["block_sizes"]]

    prompt = (
        f"Compute the Jordan normal form $J$ of the matrix\n\n$$A = {_bmatrix(a_mat)}.$$\n\n"
        "All eigenvalues of $A$ are even integers with $|\\lambda| \\le 2$. Order the Jordan blocks "
        "by ascending eigenvalue and, for equal eigenvalues, by descending block size."
    )

    trace_a = sum(a_mat[i][i] for i in range(n))
    eigen_sum = " + ".join(
        f"{e['algebraic']} \\cdot ({e['eigenvalue']})" for e in per_eigenvalue
    )

    steps: list[Step] = [
        Step(
            "**Characteristic polynomial.** With $\\chi_A(\\lambda) = \\det(\\lambda I - A)$:\n\n"
            f"$$\\chi_A(\\lambda) = {sympy.latex(char_expr)} = "
            f"{sympy.latex(sympy.factor(char_expr))}.$$\n\n"
            "So the eigenvalues and their **algebraic** multiplicities are "
            + ", ".join(
                f"$\\lambda = {e['eigenvalue']}$ with $m_{{{e['eigenvalue']}}} = {e['algebraic']}$"
                for e in per_eigenvalue
            )
            + f". Quick check: the eigenvalues must sum to the trace, ${eigen_sum} = {trace_a} "
            f"= \\mathrm{{tr}}(A)$."
        ),
        Step(
            "**What determines $J$.** For each eigenvalue $\\lambda$ set "
            "$d_k = \\dim\\ker (A - \\lambda I)^k = n - \\mathrm{rank}\\,(A - \\lambda I)^k$. "
            "Then $d_1$ (the **geometric** multiplicity) is the *number* of Jordan blocks for "
            "$\\lambda$, the chain stabilises at $d_k = m_\\lambda$ where $k$ is the *size of "
            "the largest* block, and the number of blocks of size exactly $k$ is\n\n"
            "$$b_k = 2 d_k - d_{k-1} - d_{k+1}, \\qquad d_0 = 0.$$"
        ),
    ]

    for e in per_eigenvalue:
        eigenvalue = e["eigenvalue"]
        lines = []
        for k, power in enumerate(e["powers"], start=1):
            exponent = "" if k == 1 else f"^{k}"
            lines.append(
                f"$$(A - ({eigenvalue})I){exponent} = {_bmatrix(power)}, \\qquad "
                f"\\mathrm{{rank}} = {n - e['kernel_dims'][k - 1]}, \\qquad "
                f"d_{k} = {e['kernel_dims'][k - 1]}.$$"
            )
        dims = e["dims_padded"]
        largest = len(e["kernel_dims"])
        b_terms = ", ".join(
            f"$b_{k} = 2\\cdot{dims[k]} - {dims[k - 1]} - {dims[k + 1]} = "
            f"{2 * dims[k] - dims[k - 1] - dims[k + 1]}$"
            for k in range(1, largest + 1)
        )
        block_count = len(e["block_sizes"])
        sizes_text = " + ".join(str(size) for size in e["block_sizes"])
        steps.append(
            Step(
                f"**Eigenvalue $\\lambda = {eigenvalue}$** (algebraic multiplicity "
                f"${e['algebraic']}$).\n\n"
                + "\n\n".join(lines)
                + f"\n\nThe chain stabilises at $d_{largest} = {e['algebraic']} = m_"
                f"{{{eigenvalue}}}$, so the largest block for this eigenvalue has size "
                f"${largest}$, and $d_1 = {e['geometric']}$ is the number of blocks. The formula "
                f"gives {b_terms}, i.e. $\\lambda = {eigenvalue}$ contributes "
                f"${block_count}$ Jordan block{'s' if block_count != 1 else ''} of size "
                f"${sizes_text}$ (total ${e['algebraic']}$, as required)."
            )
        )

    steps.append(
        Step(
            "**Assemble $J$.** Blocks in the required order — ascending eigenvalue, descending "
            "size — give\n\n"
            f"$$J = {_bmatrix(jordan)}.$$"
        )
    )
    steps.append(
        Step(
            "**Check.** $J$ is similar to $A$, so both must have the same trace and the same "
            f"characteristic polynomial: $\\mathrm{{tr}}(J) = {trace_a} = \\mathrm{{tr}}(A)$, and "
            f"the diagonal of $J$ lists every eigenvalue with its algebraic multiplicity ✓"
        )
    )

    final_answer = f"$$J = {_bmatrix(jordan)}$$"

    diagonal = [jordan[i][i] for i in range(n)]
    superdiagonal = [jordan[i][i + 1] for i in range(n - 1)]
    check_table = {
        "col_headers": [f"$i = {i + 1}$" for i in range(n)],
        "cell_hint": "the diagonal and the superdiagonal already determine $J$ (all other "
        "entries are $0$); blocks ordered by ascending eigenvalue, then descending size",
        "rows": [
            {"label": "diagonal $J_{ii}$", "cells": diagonal},
            {"label": "superdiagonal $J_{i,i+1}$", "cells": superdiagonal + [None]},
        ],
    }

    check_answers = [
        {"label": "Number of Jordan blocks in total", "value": len(all_sizes), "type": "number"},
        {"label": "Size of the largest Jordan block", "value": max(all_sizes), "type": "number"},
    ]

    answers = {
        "A": a_mat,
        "size": n,
        "characteristic_polynomial": str(char_expr),
        "eigenvalues": [
            {
                "eigenvalue": e["eigenvalue"],
                "algebraic_multiplicity": e["algebraic"],
                "geometric_multiplicity": e["geometric"],
                "kernel_dimensions": e["kernel_dims"],
                "block_sizes": e["block_sizes"],
            }
            for e in per_eigenvalue
        ],
        "J": jordan,
        "block_count": len(all_sizes),
        "largest_block": max(all_sizes),
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
        check_table=check_table,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Jordan normal form exercise.")
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
        print("Check answers:", ex.check_answers)
        print("Answers:", ex.answers)
