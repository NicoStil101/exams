"""Exercise: representing matrix of a linear map on P_2 with respect to the
standard basis, when the map is given by its action on a *different* basis.

Setup: $V = \\langle 1, x, x^2\\rangle$, $A = \\{1, x, x^2\\}$ the standard
basis, $B = \\{b_1, b_2, b_3\\}$ an alternative basis, and $\\varphi$ defined
by the three images $\\varphi(b_j)$.

Construction: the coordinate matrix $S = T_B^A(\\mathrm{id})$ (columns =
coordinates of the $b_j$ in $A$) is drawn with $\\det S = \\pm 1$, so that
$S^{-1}$ is again an integer matrix and the answer stays free of fractions.
The images $\\varphi(b_j)$ are drawn independently.

The solution is a pure computation from those parameters:
    T_A(phi)       = M @ S^{-1}   with M = T_B^A(phi)
    T_A(phi o phi) = T_A(phi)^2
    T_B(phi)       = S_{B,A} @ T_A(phi) @ S_{B,A}^{-1}   with S_{B,A} = S^{-1}
using an exact integer inverse (adjugate / det with det = +-1). The
conjugation collapses to S^{-1} @ M, which the worked solution uses as an
independent check of part (b).
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.append(str(_here.parent))  # sibling `mat3_utils`
sys.path.append(str(_here.parents[1]))  # `core`

from core import Exercise, Step, new_seed  # noqa: E402
from mat3_utils import (  # noqa: E402
    Matrix3,
    column3,
    columns3,
    det3,
    inverse3_unimodular,
    matmul3,
    matvec3,
    to_latex_bmatrix,
    to_latex_col_vector,
)

EXERCISE_ID = "la-matrix-transformation"
TITLE = "Matrix Transformations: Representing Matrix of a Linear Map"

_BASIS_CHOICES = (0, 0, 1, 1, 1, -1)
_IMAGE_CHOICES = (0, 0, 1, 1, 1, -1, 2)
_MONOMIALS = ([1, 0, 0], [0, 1, 0], [0, 0, 1])

_MAX_ENTRY = 6  # |entry| bound on T_A(phi)
_MAX_ENTRY_SQUARED = 20  # |entry| bound on T_A(phi o phi)


def _terms_latex(coeffs: list[int], symbols: list[str]) -> str:
    """Render sum(coeff * symbol) with proper signs, e.g. [1, -1, 2] over
    ["", "x", "x^2"] -> "1 - x + 2x^2". An empty symbol is the constant 1."""
    parts: list[tuple[str, str]] = []
    for coeff, symbol in zip(coeffs, symbols):
        if coeff == 0:
            continue
        magnitude = abs(coeff)
        if not symbol:
            body = str(magnitude)
        else:
            body = symbol if magnitude == 1 else f"{magnitude}{symbol}"
        parts.append(("-" if coeff < 0 else "+", body))
    if not parts:
        return "0"
    head = ("-" if parts[0][0] == "-" else "") + parts[0][1]
    return head + "".join(f" {sign} {body}" for sign, body in parts[1:])


def _poly_latex(coeffs: list[int]) -> str:
    """Coefficient vector [c0, c1, c2] -> "c0 + c1 x + c2 x^2"."""
    return _terms_latex(coeffs, ["", "x", "x^2"])


def _basis_combo_latex(coeffs: list[int]) -> str:
    return _terms_latex(coeffs, ["b_1", "b_2", "b_3"])


def _max_abs(m: Matrix3) -> int:
    return max(abs(v) for row in m for v in row)


def _draw_column(rng: random.Random, choices: tuple[int, ...]) -> list[int]:
    while True:
        col = [rng.choice(choices) for _ in range(3)]
        if any(col):
            return col


def _draw_basis(rng: random.Random) -> list[list[int]]:
    """Three coordinate vectors forming a basis of V whose coordinate matrix
    is unimodular (det = +-1), so the change of basis back to A is integral."""
    while True:
        basis = [_draw_column(rng, _BASIS_CHOICES) for _ in range(3)]
        s = columns3(basis)
        if det3(s) not in (1, -1):
            continue
        if sum(1 for col in basis if sum(1 for c in col if c) >= 2) < 2:
            continue  # keep B visibly different from the standard basis
        return basis


def _draw_images(rng: random.Random) -> list[list[int]]:
    """The three images phi(b_j) as coordinate vectors w.r.t. A."""
    if rng.random() < 0.35:
        return [list(m) for m in rng.sample(_MONOMIALS, 3)]
    while True:
        images = [_draw_column(rng, _IMAGE_CHOICES) for _ in range(3)]
        if len({tuple(v) for v in images}) == 3:
            return images


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    while True:
        basis = _draw_basis(rng)
        images = _draw_images(rng)
        s = columns3(basis)  # T_B^A(id): columns are the b_j in A-coordinates
        s_inv = inverse3_unimodular(s)  # T_A^B(id)
        m = columns3(images)  # T_B^A(phi): columns are the phi(b_j) in A-coordinates
        t = matmul3(m, s_inv)  # T_A(phi)
        t_squared = matmul3(t, t)  # T_A(phi o phi)
        t_b = matmul3(s_inv, m)  # T_B(phi) = S_{B,A} T_A(phi) S_{B,A}^{-1}
        if t == identity:
            continue
        if (
            _max_abs(t) <= _MAX_ENTRY
            and _max_abs(t_b) <= _MAX_ENTRY
            and _max_abs(t_squared) <= _MAX_ENTRY_SQUARED
        ):
            break

    det_s = det3(s)
    basis_latex = ", ".join(_poly_latex(b) for b in basis)

    prompt = (
        "Let $V = \\langle 1, x, x^2 \\rangle$ be the vector space of polynomials of "
        "degree at most 2. Let $A = \\{1, x, x^2\\}$ be the standard basis of $V$, and let\n\n"
        f"$$B = \\{{b_1, b_2, b_3\\}} = \\{{ {basis_latex} \\}}$$\n\n"
        "be an alternative basis. A linear map $\\varphi : V \\to V$ is defined by its "
        "action on the basis $B$:\n\n"
        "$$"
        + ", \\quad ".join(
            f"\\varphi(b_{j + 1}) = {_poly_latex(images[j])}" for j in range(3)
        )
        + ".$$\n\n"
        "(a) Compute $T_A(\\varphi)$ and $T_A(\\varphi \\circ \\varphi)$.\n\n"
        "(b) Find $T_B(\\varphi)$ by determining the basis change matrix $S_{B,A}$ "
        "(characterised by $[v]_B = S_{B,A}\\,[v]_A$) and applying the transformation "
        "formula."
    )

    steps: list[Step] = [
        Step(
            "**What the columns mean.** For bases $C$ (source) and $D$ (target), the $j$-th "
            "column of $T_C^D(\\varphi)$ is the coordinate vector of $\\varphi(c_j)$ with "
            "respect to $D$; $T_A(\\varphi)$ is short for $T_A^A(\\varphi)$. The map is given "
            "on $B$, not on $A$, so it cannot be read off directly — the change of basis "
            "$A \\to B$ has to be inserted first."
        ),
        Step(
            "**Coordinates of $B$ in $A$.** Writing each $b_j$ in the standard basis gives the "
            "columns of $S := T_B^A(\\mathrm{id})$:\n\n"
            + "$$"
            + ", \\quad ".join(
                f"[b_{j + 1}]_A = {to_latex_col_vector(basis[j])}" for j in range(3)
            )
            + f", \\qquad S = {to_latex_bmatrix(s)}.$$"
        ),
        Step(
            "**Coordinates of the images in $A$.** The given images $\\varphi(b_j)$ are already "
            "polynomials, so their $A$-coordinates are their coefficient vectors. They form the "
            "columns of $M := T_B^A(\\varphi)$:\n\n"
            f"$$M = {to_latex_bmatrix(m)}.$$"
        ),
        Step(
            "**Putting it together.** For $v \\in V$ we have $[v]_B = S^{-1}[v]_A$ and "
            "$[\\varphi(v)]_A = M\\,[v]_B$, hence "
            "$[\\varphi(v)]_A = M S^{-1} [v]_A$ for every $v$. Therefore\n\n"
            "$$T_A(\\varphi) = T_B^A(\\varphi) \\cdot T_A^B(\\mathrm{id}) = M \\cdot S^{-1}.$$"
        ),
        Step(
            f"**Inverting $S$.** $\\det(S) = {det_s}$, so $S$ is invertible and "
            "$S^{-1} = \\tfrac{1}{\\det(S)}\\,\\mathrm{adj}(S)$ is again an integer matrix:\n\n"
            f"$$S^{{-1}} = {to_latex_bmatrix(s_inv)}.$$"
        ),
        Step(
            "**The representing matrix.**\n\n"
            f"$$T_A(\\varphi) = M S^{{-1}} = {to_latex_bmatrix(m)} {to_latex_bmatrix(s_inv)} "
            f"= {to_latex_bmatrix(t)}.$$"
        ),
    ]

    # Independent check of the first column: express 1 in the basis B, apply phi
    # by linearity, and compare with column 1 of T_A(phi).
    coeffs_of_one = matvec3(s_inv, [1, 0, 0])  # [1]_B
    phi_of_one = column3(t, 0)
    image_terms = _terms_latex(coeffs_of_one, [f"({_poly_latex(img)})" for img in images])
    steps.append(
        Step(
            "**Check (first column).** Column 1 of $T_A(\\varphi)$ must be "
            f"$[\\varphi(1)]_A$. From $[1]_B = S^{{-1}}{to_latex_col_vector([1, 0, 0])} "
            f"= {to_latex_col_vector(coeffs_of_one)}$ we get "
            f"$1 = {_basis_combo_latex(coeffs_of_one)}$, so by linearity "
            f"$\\varphi(1) = {image_terms} = {_poly_latex(phi_of_one)}$, which is exactly the "
            "first column of the matrix above."
        )
    )

    steps.append(
        Step(
            "**Composition.** Representing matrices are multiplicative: "
            "$T_A(\\psi \\circ \\varphi) = T_A(\\psi)\\,T_A(\\varphi)$. With $\\psi = \\varphi$,\n\n"
            f"$$T_A(\\varphi \\circ \\varphi) = T_A(\\varphi)^2 = {to_latex_bmatrix(t)}"
            f"{to_latex_bmatrix(t)} = {to_latex_bmatrix(t_squared)}.$$"
        )
    )

    steps.append(
        Step(
            "**(b) The basis change matrix $S_{B,A}$.** It is the matrix turning "
            "$A$-coordinates into $B$-coordinates, $[v]_B = S_{B,A}\\,[v]_A$. Since the columns "
            "of $S$ are the $b_j$ written in $A$, $S$ does the opposite, $[v]_A = S\\,[v]_B$, "
            "hence\n\n"
            f"$$S_{{B,A}} = T_A^B(\\mathrm{{id}}) = S^{{-1}} = {to_latex_bmatrix(s_inv)}, "
            f"\\qquad S_{{B,A}}^{{-1}} = S = {to_latex_bmatrix(s)}.$$"
        )
    )
    steps.append(
        Step(
            "**Transformation formula.** Changing the basis on both sides conjugates the "
            "representing matrix: $T_B(\\varphi) = S_{B,A}\\,T_A(\\varphi)\\,S_{B,A}^{-1}$ "
            "(read right to left: $B \\to A$, apply $\\varphi$ in $A$, then $A \\to B$). "
            "Therefore\n\n"
            f"$$T_B(\\varphi) = {to_latex_bmatrix(s_inv)}{to_latex_bmatrix(t)}"
            f"{to_latex_bmatrix(s)} = {to_latex_bmatrix(t_b)}.$$"
        )
    )
    steps.append(
        Step(
            "**Check.** The same matrix comes out of the definition directly: column $j$ of "
            "$T_B(\\varphi)$ is $[\\varphi(b_j)]_B = S^{-1}[\\varphi(b_j)]_A$, i.e. "
            f"$T_B(\\varphi) = S^{{-1}}M = {to_latex_bmatrix(s_inv)}{to_latex_bmatrix(m)} "
            f"= {to_latex_bmatrix(t_b)}$ ✓ "
            "(note that $T_A(\\varphi)$ and $T_B(\\varphi)$ are similar, so they share trace "
            f"$= {t[0][0] + t[1][1] + t[2][2]}$ and determinant $= {det3(t)}$.)"
        )
    )

    final_answer = (
        f"$$T_A(\\varphi) = {to_latex_bmatrix(t)}, \\qquad "
        f"T_A(\\varphi \\circ \\varphi) = {to_latex_bmatrix(t_squared)}, \\qquad "
        f"T_B(\\varphi) = {to_latex_bmatrix(t_b)}$$"
    )

    check_table = {
        "col_headers": ["column 1", "column 2", "column 3"],
        "cell_hint": "enter the entries of each matrix row by row",
        "rows": [
            {"label": f"$T_A(\\varphi)$, row {i + 1}", "cells": list(t[i])} for i in range(3)
        ]
        + [
            {"label": f"$T_A(\\varphi \\circ \\varphi)$, row {i + 1}", "cells": list(t_squared[i])}
            for i in range(3)
        ]
        + [
            {"label": f"$T_B(\\varphi)$, row {i + 1}", "cells": list(t_b[i])} for i in range(3)
        ],
    }

    answers = {
        "basis_B": basis,
        "images": images,
        "S": s,
        "det_S": det_s,
        "S_inverse": s_inv,
        "S_BA": s_inv,
        "M": m,
        "T_A_phi": t,
        "T_A_phi_squared": t_squared,
        "T_B_phi": t_b,
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

    parser = argparse.ArgumentParser(description="Generate a matrix-transformation exercise.")
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
