"""Exercise: LU factorisation of a 3x3 matrix by Gaussian elimination, plus
solving $Ax = b$ with forward and back substitution.

Construction: pick a unit lower triangular $L$ and an upper triangular $U$
with small integer entries and nonzero pivots, then set $A = LU$. Every
leading principal minor of $A$ is then a product of pivots and hence nonzero,
so $A$ has an LU factorisation without row interchanges, and (because the
factorisation with unit diagonal $L$ is unique) elimination recovers exactly
the $L$ and $U$ that were drawn. The right-hand side is $b = Ax$ for an
integer $x$, so forward/back substitution stays exact.

The solution does NOT read off the construction: it runs Gaussian elimination
on the entries of $A$ with exact rational arithmetic, then solves $Ly = b$ and
$Ux = y$ by substitution. Everything is a pure function of $A$ and $b$.
"""

from __future__ import annotations

import random
import sys
from fractions import Fraction
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.append(str(_here.parent))  # sibling `mat3_utils`
sys.path.append(str(_here.parents[1]))  # `core`

from core import Exercise, Step, new_seed  # noqa: E402
from mat3_utils import (  # noqa: E402
    Matrix3,
    matmul3,
    matvec3,
    to_latex_bmatrix,
    to_latex_col_vector,
)

EXERCISE_ID = "la-lu-factorisation"
TITLE = "LU Factorisation: Gaussian Elimination and Solving Ax = b"

_MULTIPLIER_CHOICES = (-2, -1, 1, 1, 2, 2, 3)
_PIVOT_CHOICES = (-2, -1, 1, 1, 2, 2, 3)
_UPPER_CHOICES = (-3, -2, -1, 0, 1, 1, 2, 3)
_SOLUTION_CHOICES = (-3, -2, -1, 1, 2, 3)

_MAX_A_ENTRY = 12
_MAX_B_ENTRY = 30


def _to_int_matrix(m: list[list[Fraction]]) -> Matrix3:
    for row in m:
        for value in row:
            assert value.denominator == 1, f"non-integer entry {value}"
    return [[int(value) for value in row] for row in m]


def _lu_decompose(a: Matrix3) -> tuple[list[list[Fraction]], list[list[Fraction]], list[Matrix3]]:
    """Gaussian elimination without pivoting: returns (L, U, stages), where
    `stages[k]` is the working matrix after eliminating below pivot k."""
    n = 3
    work = [[Fraction(value) for value in row] for row in a]
    lower = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    stages: list[Matrix3] = []
    for k in range(n - 1):
        pivot = work[k][k]
        if pivot == 0:
            raise ValueError(f"zero pivot in column {k + 1}; row interchange needed")
        for i in range(k + 1, n):
            factor = work[i][k] / pivot
            lower[i][k] = factor
            for j in range(k, n):
                work[i][j] -= factor * work[k][j]
        stages.append(_to_int_matrix(work))
    return lower, work, stages


def _forward_substitution(lower: Matrix3, b: list[int]) -> list[Fraction]:
    """Solve L y = b for unit lower triangular L."""
    y: list[Fraction] = []
    for i in range(3):
        y.append(Fraction(b[i]) - sum(lower[i][j] * y[j] for j in range(i)))
    return y


def _back_substitution(upper: Matrix3, y: list[Fraction]) -> list[Fraction]:
    """Solve U x = y for upper triangular U with nonzero diagonal."""
    x: list[Fraction | None] = [None, None, None]
    for i in reversed(range(3)):
        rest = sum(upper[i][j] * x[j] for j in range(i + 1, 3))
        x[i] = (y[i] - rest) / upper[i][i]
    return [value for value in x]  # type: ignore[misc]


def _to_int_vector(v: list[Fraction]) -> list[int]:
    for value in v:
        assert value.denominator == 1, f"non-integer entry {value}"
    return [int(value) for value in v]


def _max_abs(m: Matrix3) -> int:
    return max(abs(value) for row in m for value in row)


def _signed_term(coefficient: int, symbol: str) -> str:
    """" - 2R_1" / " + R_1" — a single signed term for a row operation."""
    sign = "-" if coefficient > 0 else "+"
    magnitude = abs(coefficient)
    body = symbol if magnitude == 1 else f"{magnitude}{symbol}"
    return f" {sign} {body}"


def _row_op_latex(target: int, source: int, factor: int) -> str:
    """The elimination step $R_i \\gets R_i - l_{ij} R_j$ written out."""
    if factor == 0:
        return f"$R_{target}$ stays unchanged (the entry is already $0$)"
    return f"$R_{target} \\gets R_{target}{_signed_term(factor, f'R_{source}')}$"


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    while True:
        l21, l31, l32 = (rng.choice(_MULTIPLIER_CHOICES) for _ in range(3))
        u11, u22, u33 = (rng.choice(_PIVOT_CHOICES) for _ in range(3))
        u12, u13, u23 = (rng.choice(_UPPER_CHOICES) for _ in range(3))
        lower_drawn = [[1, 0, 0], [l21, 1, 0], [l31, l32, 1]]
        upper_drawn = [[u11, u12, u13], [0, u22, u23], [0, 0, u33]]
        a_mat = matmul3(lower_drawn, upper_drawn)
        x_solution = [rng.choice(_SOLUTION_CHOICES) for _ in range(3)]
        b_vec = matvec3(a_mat, x_solution)
        if _max_abs(a_mat) > _MAX_A_ENTRY or max(abs(v) for v in b_vec) > _MAX_B_ENTRY:
            continue
        if any(value == 0 for row in a_mat for value in row):
            continue  # a zero entry would make the elimination look degenerate
        break

    # Solve from A and b alone, independently of how they were built.
    lower_frac, upper_frac, stages = _lu_decompose(a_mat)
    lower = _to_int_matrix(lower_frac)
    upper = _to_int_matrix(upper_frac)
    y_frac = _forward_substitution(lower, b_vec)
    y_vec = _to_int_vector(y_frac)
    x_vec = _to_int_vector(_back_substitution(upper, y_frac))
    stage1 = stages[0]

    prompt = (
        "Consider the matrix and the right-hand side\n\n"
        f"$$A = {to_latex_bmatrix(a_mat)}, \\qquad b = {to_latex_col_vector(b_vec)}.$$\n\n"
        "$A$ can be factored without row interchanges.\n\n"
        "(a) Determine the $LU$ factorisation $A = LU$ by Gaussian elimination, where $L$ is "
        "unit lower triangular (ones on the diagonal) and $U$ is upper triangular.\n\n"
        "(b) Use the factorisation to solve $Ax = b$, i.e. solve $Ly = b$ by forward "
        "substitution and then $Ux = y$ by back substitution."
    )

    steps: list[Step] = [
        Step(
            "**Method.** Gaussian elimination turns $A$ into the upper triangular matrix $U$. "
            "In step $k$ every row below the pivot $u_{kk}$ is reduced by "
            "$R_i \\gets R_i - l_{ik} R_k$ with the multiplier $l_{ik} = a_{ik}^{(k-1)} / "
            "a_{kk}^{(k-1)}$. Those multipliers are exactly the entries of $L$ below the "
            "diagonal — no extra work is needed, they only have to be recorded."
        ),
        Step(
            f"**Step 1 (pivot $u_{{11}} = {a_mat[0][0]}$).** "
            f"$l_{{21}} = \\frac{{{a_mat[1][0]}}}{{{a_mat[0][0]}}} = {lower[1][0]}$ and "
            f"$l_{{31}} = \\frac{{{a_mat[2][0]}}}{{{a_mat[0][0]}}} = {lower[2][0]}$, so "
            f"{_row_op_latex(2, 1, lower[1][0])} and {_row_op_latex(3, 1, lower[2][0])}:\n\n"
            f"$$A \\;\\longrightarrow\\; {to_latex_bmatrix(stage1)}.$$"
        ),
        Step(
            f"**Step 2 (pivot $u_{{22}} = {stage1[1][1]}$).** "
            f"$l_{{32}} = \\frac{{{stage1[2][1]}}}{{{stage1[1][1]}}} = {lower[2][1]}$, so "
            f"{_row_op_latex(3, 2, lower[2][1])}:\n\n"
            f"$$U = {to_latex_bmatrix(upper)}.$$"
        ),
        Step(
            "**Collect the multipliers.** Putting $l_{21}, l_{31}, l_{32}$ below the unit "
            "diagonal gives\n\n"
            f"$$L = {to_latex_bmatrix(lower)}.$$"
        ),
        Step(
            "**Sanity check.** Multiplying back reproduces the original matrix: "
            f"$LU = {to_latex_bmatrix(lower)}{to_latex_bmatrix(upper)} = "
            f"{to_latex_bmatrix(matmul3(lower, upper))} = A$. "
            "(Also note $\\det(A) = \\det(U) = "
            f"{upper[0][0]} \\cdot {upper[1][1]} \\cdot {upper[2][2]} = "
            f"{upper[0][0] * upper[1][1] * upper[2][2]}$, since $\\det(L) = 1$.)"
        ),
        Step(
            "**(b) Forward substitution $Ly = b$.** $L$ is unit lower triangular, so $y$ falls "
            "out from top to bottom:\n\n"
            f"$$y_1 = {b_vec[0]}, \\quad "
            f"y_2 = {b_vec[1]}{_signed_term(lower[1][0], 'y_1')} = {y_vec[1]}, \\quad "
            f"y_3 = {b_vec[2]}{_signed_term(lower[2][0], 'y_1')}"
            f"{_signed_term(lower[2][1], 'y_2')} = {y_vec[2]},$$\n\n"
            f"that is $y = {to_latex_col_vector(y_vec)}$."
        ),
        Step(
            "**Back substitution $Ux = y$.** Now work from the bottom row upwards:\n\n"
            f"$$x_3 = \\frac{{{y_vec[2]}}}{{{upper[2][2]}}} = {x_vec[2]}, \\quad "
            f"x_2 = \\frac{{{y_vec[1]} - ({upper[1][2]})\\cdot({x_vec[2]})}}{{{upper[1][1]}}} "
            f"= {x_vec[1]}, \\quad "
            f"x_1 = \\frac{{{y_vec[0]} - ({upper[0][1]})\\cdot({x_vec[1]}) - "
            f"({upper[0][2]})\\cdot({x_vec[2]})}}{{{upper[0][0]}}} = {x_vec[0]}.$$"
        ),
        Step(
            f"**Check.** $A x = {to_latex_bmatrix(a_mat)}{to_latex_col_vector(x_vec)} = "
            f"{to_latex_col_vector(matvec3(a_mat, x_vec))} = b$ ✓"
        ),
    ]

    final_answer = (
        f"$$L = {to_latex_bmatrix(lower)}, \\qquad U = {to_latex_bmatrix(upper)}, \\qquad "
        f"x = {to_latex_col_vector(x_vec)}$$"
    )

    # Structurally zero cells are left blank (not gradable); the unit diagonal
    # of L stays gradable because knowing it is part of the convention.
    check_table = {
        "col_headers": ["column 1", "column 2", "column 3"],
        "cell_hint": "$L$ is unit lower triangular, $U$ upper triangular; greyed cells are "
        "structurally zero. $y$ and $x$ are entered component by component.",
        "rows": [
            {
                "label": f"$L$, row {i + 1}",
                "cells": [lower[i][j] if j <= i else None for j in range(3)],
            }
            for i in range(3)
        ]
        + [
            {
                "label": f"$U$, row {i + 1}",
                "cells": [upper[i][j] if j >= i else None for j in range(3)],
            }
            for i in range(3)
        ]
        + [
            {"label": "$y^{\\top}$ (from $Ly = b$)", "cells": list(y_vec)},
            {"label": "$x^{\\top}$ (from $Ux = y$)", "cells": list(x_vec)},
        ],
    }

    answers = {
        "A": a_mat,
        "b": b_vec,
        "L": lower,
        "U": upper,
        "stage_after_step_1": stage1,
        "y": y_vec,
        "x": x_vec,
        "det_A": upper[0][0] * upper[1][1] * upper[2][2],
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        final_answer=final_answer,
        check_table=check_table,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate an LU factorisation exercise.")
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
