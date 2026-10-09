"""Exercise: eigenvalues and eigenvectors of a 3x3 integer matrix, where all
eigenvalues are guaranteed to be integers with |lambda| <= 4.

(Design note: eigenvalues were briefly even-only, but if every eigenvalue is
even then A = P(2E)P^{-1} is even in every entry, and matrices should contain
+-1 entries — 1s are what keep Laplace expansions and row operations cheap.
Tiny odd candidates give the best of both: p(+-1) is trivial to evaluate.)

Construction: A = P D P^{-1} for a diagonal D holding 3 distinct chosen
eigenvalues and a unimodular integer P = L @ U (unit-lower times
unit-upper triangular, so P and P^{-1} are both guaranteed integer). This
hides the eigenvalues/eigenvectors inside an ordinary-looking integer
matrix.

The solution does NOT just read off the hidden construction: it
independently derives the characteristic polynomial from A's entries
(trace, sum of principal minors, determinant), finds the roots by testing
every candidate in the guaranteed range -4..4, and for each root computes
the eigenspace via exact null-space reduction (sympy) of (A - lambda I).
Everything is a pure, deterministic function of the generated matrix.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.append(str(_here.parent))  # sibling `mat3_utils`
sys.path.append(str(_here.parents[1]))  # `core`

import sympy  # noqa: E402

from core import Exercise, Step, new_seed  # noqa: E402
from mat3_utils import (  # noqa: E402
    Matrix3,
    det3,
    diag3,
    matmul3,
    matvec3,
    principal_minor_sum3,
    scaled_identity3,
    sub3,
    to_latex_bmatrix,
    to_latex_col_vector,
    trace3,
)

EXERCISE_ID = "la-eigen-3x3"
TITLE = "Eigenvalues and Eigenvectors of a 3x3 Matrix"

_OFFDIAG_CHOICES = (-1, 0, 1)
_EIGENVALUE_CHOICES = tuple(range(-4, 5))  # integers up to |lambda| = 4
_MAX_ENTRY = 6  # small entries, mental arithmetic only
_MAX_NEGATIVES = 3  # positive-dominant matrices: at most a third of the entries negative


def _zero_pattern_ok(a_mat: Matrix3, min_total: int) -> bool:
    """Zeros that help a Laplace expansion without trivialising the matrix:
    at least `min_total` zero entries, none of them on the main diagonal, no
    row or column holding more than one, and one *further* zero must be
    obtainable by a single row operation R_i <- R_i -+ R_k (i.e. two rows
    agree up to sign somewhere)."""
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


def _no_duplicate_lines(a_mat: Matrix3) -> bool:
    """Reject matrices with two rows or two columns equal up to sign — those
    make the determinant/rank visible at a glance."""
    n = len(a_mat)
    for i in range(n):
        for k in range(i + 1, n):
            if a_mat[i] == a_mat[k] or a_mat[i] == [-v for v in a_mat[k]]:
                return False
            col_i = [a_mat[r][i] for r in range(n)]
            col_k = [a_mat[r][k] for r in range(n)]
            if col_i == col_k or col_i == [-v for v in col_k]:
                return False
    return True


def _invert_unit_lower(l: Matrix3) -> Matrix3:
    a, b, c = l[1][0], l[2][0], l[2][1]
    # (I + N)^{-1} = I - N + N^2 for strictly lower-triangular nilpotent N (N^3 = 0 in 3x3)
    return [[1, 0, 0], [-a, 1, 0], [a * c - b, -c, 1]]


def _invert_unit_upper(u: Matrix3) -> Matrix3:
    d, e, f = u[0][1], u[0][2], u[1][2]
    return [[1, -d, d * f - e], [0, 1, -f], [0, 0, 1]]


def _integer_eigenvector(a_mat: Matrix3, lam: int) -> list[int]:
    """Exact null-space basis vector of (A - lambda I), scaled to coprime
    integers with a fixed sign convention (first nonzero entry positive)."""
    m = sympy.Matrix(a_mat) - lam * sympy.eye(3)
    basis = m.nullspace()
    v = basis[0]
    denom_lcm = math.lcm(*[sympy.Rational(x).q for x in v])
    scaled = [int(x * denom_lcm) for x in v]
    g = math.gcd(*[abs(x) for x in scaled])
    scaled = [x // g for x in scaled]
    first_nonzero = next(x for x in scaled if x != 0)
    if first_nonzero < 0:
        scaled = [-x for x in scaled]
    return scaled


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    # Redraw until A is genuinely hand-computable: small entries, a helpful
    # (but not excessive) zero pattern for the Laplace expansion of
    # det(A - lambda I), and not triangular, so the eigenvalues cannot be
    # read straight off the diagonal.
    while True:
        eigenvalues = sorted(rng.sample(_EIGENVALUE_CHOICES, 3))

        a, b, c, d, e, f = (rng.choice(_OFFDIAG_CHOICES) for _ in range(6))
        lower = [[1, 0, 0], [a, 1, 0], [b, c, 1]]
        upper = [[1, d, e], [0, 1, f], [0, 0, 1]]
        p = matmul3(lower, upper)
        p_inv = matmul3(_invert_unit_upper(upper), _invert_unit_lower(lower))

        a_mat = matmul3(matmul3(p, diag3(eigenvalues)), p_inv)

        if max(abs(v) for row in a_mat for v in row) > _MAX_ENTRY:
            continue
        if sum(1 for row in a_mat for v in row if v < 0) > _MAX_NEGATIVES:
            continue
        if not _zero_pattern_ok(a_mat, 1):
            continue
        if not any(abs(v) == 1 for row in a_mat for v in row):
            continue  # a +-1 entry keeps expansions and row operations cheap
        if not _no_duplicate_lines(a_mat):
            continue
        is_upper = all(a_mat[i][j] == 0 for i in range(3) for j in range(3) if i > j)
        is_lower = all(a_mat[i][j] == 0 for i in range(3) for j in range(3) if i < j)
        if is_upper or is_lower:
            continue
        break

    tr = trace3(a_mat)
    c2 = principal_minor_sum3(a_mat)
    det = det3(a_mat)

    def char_poly(lam: int) -> int:
        return lam**3 - tr * lam**2 + c2 * lam - det

    found_roots = [lam for lam in _EIGENVALUE_CHOICES if char_poly(lam) == 0]
    eigenvectors = {lam: _integer_eigenvector(a_mat, lam) for lam in found_roots}

    prompt = (
        f"Consider the matrix\n\n$$A = {to_latex_bmatrix(a_mat)}$$\n\n"
        f"All eigenvalues of $A$ are known to be integers with $|\\lambda| \\le 4$. "
        f"Find all eigenvalues of $A$, and for each eigenvalue find a corresponding "
        f"eigenvector. Scale each eigenvector to coprime integers with a positive first "
        f"nonzero entry."
    )

    steps = [
        Step(
            "**Eigenvalues.** The characteristic polynomial of a $3\\times 3$ matrix is "
            "$p(\\lambda) = \\det(A - \\lambda I) = -\\lambda^3 + \\mathrm{tr}(A)\\,\\lambda^2 "
            "- c_2\\,\\lambda + \\det(A)$, or equivalently, as a monic polynomial, "
            "$\\lambda^3 - \\mathrm{tr}(A)\\,\\lambda^2 + c_2\\,\\lambda - \\det(A) = 0$, "
            "where $c_2$ is the sum of the principal $2\\times 2$ minors of $A$."
        ),
        Step(f"$\\mathrm{{tr}}(A) = {a_mat[0][0]} + {a_mat[1][1]} + {a_mat[2][2]} = {tr}$."),
        Step(
            "$c_2 = (a_{22}a_{33}-a_{23}a_{32}) + (a_{11}a_{33}-a_{13}a_{31}) + "
            f"(a_{{11}}a_{{22}}-a_{{12}}a_{{21}}) = {c2}$."
        ),
        Step(f"$\\det(A) = {det}$ (cofactor expansion along the first row)."),
        Step(
            "So the characteristic equation is "
            f"$\\lambda^3 - ({tr})\\lambda^2 + ({c2})\\lambda - ({det}) = 0$. "
            "Since the eigenvalues are integers with $|\\lambda| \\le 4$, only "
            "$\\lambda = -4, -3, \\dots, 4$ need to be tested: "
            "$"
            + ",\\;".join(f"p({lam})={char_poly(lam)}" for lam in _EIGENVALUE_CHOICES)
            + "$."
        ),
        Step(
            "The polynomial vanishes exactly at $\\lambda = "
            + ", ".join(str(r) for r in found_roots)
            + "$, which are therefore all the eigenvalues of $A$."
        ),
    ]

    steps.append(Step("**Eigenvectors.** For each eigenvalue, solve $(A - \\lambda I)\\,v = 0$."))
    for lam in found_roots:
        shifted = sub3(a_mat, scaled_identity3(lam))
        v = eigenvectors[lam]
        steps.append(
            Step(
                f"For $\\lambda = {lam}$: $A - {lam}I = {to_latex_bmatrix(shifted)}$ "
                f"row-reduces to a system with one free variable, giving eigenspace "
                f"$E_{{{lam}}} = \\mathrm{{span}}\\left\\{{ {to_latex_col_vector(v)} \\right\\}}$."
            )
        )

    eigenvector_set = ", ".join(to_latex_col_vector(eigenvectors[lam]) for lam in found_roots)
    final_answer = f"$$\\left\\{{ {eigenvector_set} \\right\\}}$$"

    answers = {
        "matrix": a_mat,
        "trace": tr,
        "principal_minor_sum": c2,
        "determinant": det,
        "eigenvalues": found_roots,
        "eigenvectors": {lam: eigenvectors[lam] for lam in found_roots},
    }

    ordinals = ("smallest", "middle", "largest")
    # The eigenvalues are asked for separately, so the eigenvector rows are
    # labelled by rank rather than by value — otherwise the table would give
    # the first part of the answer away.
    check_answers = [
        {
            "label": f"$\\lambda_{i + 1}$ ({ordinals[i]} eigenvalue)",
            "value": root,
            "type": "number",
        }
        for i, root in enumerate(found_roots)
    ]
    check_table = {
        "col_headers": ["entry 1", "entry 2", "entry 3"],
        "cell_hint": "one eigenvector per row, scaled to coprime integers with a positive "
        "first nonzero entry",
        "rows": [
            {
                "label": f"eigenvector for the {ordinals[i]} eigenvalue",
                "cells": list(eigenvectors[root]),
            }
            for i, root in enumerate(found_roots)
        ],
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

    parser = argparse.ArgumentParser(description="Generate a 3x3 eigenvalue/eigenvector exercise.")
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
