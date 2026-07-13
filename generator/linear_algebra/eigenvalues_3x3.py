"""Exercise: eigenvalues and eigenvectors of a 3x3 integer matrix, where all
eigenvalues are guaranteed to satisfy 0 <= lambda < 6.

Construction: A = P D P^{-1} for a diagonal D holding 3 distinct chosen
eigenvalues and a unimodular integer P = L @ U (unit-lower times
unit-upper triangular, so P and P^{-1} are both guaranteed integer). This
hides the eigenvalues/eigenvectors inside an ordinary-looking integer
matrix.

The solution does NOT just read off the hidden construction: it
independently derives the characteristic polynomial from A's entries
(trace, sum of principal minors, determinant), finds the roots by testing
every candidate in the guaranteed range 0..5, and for each root computes
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

_OFFDIAG_CHOICES = (-2, -1, 1, 2)


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

    eigenvalues = sorted(rng.sample(range(6), 3))

    a, b, c, d, e, f = (rng.choice(_OFFDIAG_CHOICES) for _ in range(6))
    lower = [[1, 0, 0], [a, 1, 0], [b, c, 1]]
    upper = [[1, d, e], [0, 1, f], [0, 0, 1]]
    p = matmul3(lower, upper)
    p_inv = matmul3(_invert_unit_upper(upper), _invert_unit_lower(lower))

    a_mat = matmul3(matmul3(p, diag3(eigenvalues)), p_inv)

    tr = trace3(a_mat)
    c2 = principal_minor_sum3(a_mat)
    det = det3(a_mat)

    def char_poly(lam: int) -> int:
        return lam**3 - tr * lam**2 + c2 * lam - det

    found_roots = [lam for lam in range(6) if char_poly(lam) == 0]
    eigenvectors = {lam: _integer_eigenvector(a_mat, lam) for lam in found_roots}

    prompt = (
        f"Consider the matrix\n\n$$A = {to_latex_bmatrix(a_mat)}$$\n\n"
        f"All eigenvalues of $A$ are known to satisfy $0 \\le \\lambda < 6$. "
        f"Find all eigenvalues of $A$, and for each eigenvalue find a corresponding "
        f"eigenvector."
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
            "Since $0 \\le \\lambda < 6$, only $\\lambda = 0,1,2,3,4,5$ need to be tested: "
            "$" + ",\\;".join(f"p({lam})={char_poly(lam)}" for lam in range(6)) + "$."
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
