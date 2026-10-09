"""Exercise: singular value decomposition $A = U \\Sigma V^{\\top}$ of a small
integer matrix ($2\\times 2$ or $3\\times 2$, as in the exam item).

An SVD cannot avoid irrational numbers — the singular values are square roots
and the singular vectors are unit vectors. What *can* be avoided is messy
arithmetic, so the matrix is drawn by rejection sampling until

  * $A$ has full column rank,
  * the Gram matrix $G = A^{\\top}A$ has **distinct positive integer**
    eigenvalues (so $\\sigma_i = \\sqrt{\\lambda_i}$ is an exact surd), and
  * the eigenvectors are integer vectors with entries $\\le 3$ in absolute
    value, and $G$ is not diagonal (otherwise the exercise is trivial).

Every step of the computation is then integer arithmetic — Gram matrix,
characteristic polynomial, eigenvalues, primitive direction vectors
$\\tilde v_i$, $\\tilde u_i \\parallel A \\tilde v_i$ — and the irrational part
is confined to the final normalisation $v_i = \\tilde v_i / \\sqrt{\\|\\tilde
v_i\\|^2}$.

Uniqueness (needed for machine-checkable answers): the singular values are
distinct and ordered descending, the sign of each $v_i$ is fixed by the
problem statement (first nonzero entry positive), and $u_i = A v_i / \\sigma_i$
then follows with no freedom left. For a $3\\times 2$ matrix the third column
of the full $U$ spans $\\ker(A^{\\top})$ and is sign-fixed the same way.
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

EXERCISE_ID = "la-svd"
TITLE = "Singular Value Decomposition of a 2x2 / 3x2 Matrix"

Matrix = list[list[int]]

_SHAPES = ((2, 2), (3, 2))
_ENTRY_RANGE = 3
_MAX_EIGENVALUE = 50
_MAX_DIRECTION_ENTRY = 3
_MAX_NORM_SQUARED = 14


def _int_bmatrix(m: Matrix) -> str:
    rows = " \\\\ ".join(" & ".join(str(v) for v in row) for row in m)
    return f"\\begin{{bmatrix}} {rows} \\end{{bmatrix}}"


def _latex_bmatrix(rows: list[list[str]]) -> str:
    body = " \\\\ ".join(" & ".join(row) for row in rows)
    return f"\\begin{{bmatrix}} {body} \\end{{bmatrix}}"


def _primitive(vector: list[sympy.Rational], sign_fix: bool = True) -> list[int]:
    """Scale a rational vector to coprime integers. With `sign_fix` the first
    nonzero entry is made positive; otherwise the direction is kept."""
    denominators = [sympy.Rational(x).q for x in vector]
    scaled = [int(sympy.Rational(x) * sympy.ilcm(*denominators)) for x in vector]
    divisor = sympy.igcd(*[abs(x) for x in scaled])
    scaled = [x // divisor for x in scaled]
    if sign_fix and next(x for x in scaled if x != 0) < 0:
        scaled = [-x for x in scaled]
    return scaled


def _norm_squared(vector: list[int]) -> int:
    return sum(x * x for x in vector)


def _unit_vector_latex(direction: list[int], norm_sq: int) -> str:
    column = _int_bmatrix([[x] for x in direction])
    if norm_sq == 1:
        return column
    return f"\\tfrac{{1}}{{\\sqrt{{{norm_sq}}}}}\\, {column}"


def _orthonormal_matrix_latex(directions: list[list[int]], norms: list[int]) -> str:
    """Columns `directions[j] / sqrt(norms[j])`. A common denominator is
    factored out; otherwise every entry carries its own radical."""
    rows = len(directions[0])
    if len(set(norms)) == 1:
        columns = [[str(directions[j][i]) for j in range(len(directions))] for i in range(rows)]
        matrix = _latex_bmatrix(columns)
        if norms[0] == 1:
            return matrix
        return f"\\tfrac{{1}}{{\\sqrt{{{norms[0]}}}}}\\, {matrix}"
    entries: list[list[str]] = []
    for i in range(rows):
        row: list[str] = []
        for j, direction in enumerate(directions):
            value, norm_sq = direction[i], norms[j]
            if value == 0 or norm_sq == 1:
                row.append(str(value))
            else:
                sign = "-" if value < 0 else ""
                row.append(f"{sign}\\tfrac{{{abs(value)}}}{{\\sqrt{{{norm_sq}}}}}")
        entries.append(row)
    return _latex_bmatrix(entries)


def _sigma_latex(eigenvalues: list[int], m: int, n: int) -> str:
    rows: list[list[str]] = []
    for i in range(m):
        row: list[str] = []
        for j in range(n):
            if i == j and i < len(eigenvalues):
                row.append(sympy.latex(sympy.sqrt(eigenvalues[i])))
            else:
                row.append("0")
        rows.append(row)
    return _latex_bmatrix(rows)


def _sigma_symbol(eigenvalue: int) -> str:
    return sympy.latex(sympy.sqrt(eigenvalue))


def _analyse(a_mat: Matrix, m: int, n: int) -> dict | None:
    """Full SVD data derived from `a_mat` alone, or None if the matrix does not
    lead to a clean exercise (see the module docstring for the criteria)."""
    a_sym = sympy.Matrix(a_mat)
    if a_sym.rank() < n:
        return None
    gram = a_sym.T * a_sym
    if all(gram[i, j] == 0 for i in range(n) for j in range(n) if i != j):
        return None  # diagonal Gram matrix => standard basis vectors, too easy
    lam = sympy.Symbol("lambda")
    char_poly = gram.charpoly(lam)
    roots = sympy.roots(char_poly)
    if len(roots) != n or not all(root.is_Integer for root in roots):
        return None  # need distinct integer eigenvalues
    eigenvalues = sorted((int(root) for root in roots), reverse=True)
    if eigenvalues[-1] <= 0 or eigenvalues[0] > _MAX_EIGENVALUE:
        return None

    v_dirs = []
    for eigenvalue in eigenvalues:
        basis = (gram - eigenvalue * sympy.eye(n)).nullspace()
        if len(basis) != 1:
            return None
        v_dirs.append(_primitive(list(basis[0])))
    v_norms = [_norm_squared(d) for d in v_dirs]

    # u_i = A v_i / sigma_i: take the direction of the integer vector A ṽ_i
    # (its sign is inherited from v_i and must not be re-fixed).
    u_products = [[int(x) for x in (a_sym * sympy.Matrix(d))] for d in v_dirs]
    u_dirs = [_primitive(product, sign_fix=False) for product in u_products]
    u_factors = []
    for product, direction in zip(u_products, u_dirs):
        index = next(i for i, x in enumerate(direction) if x != 0)
        u_factors.append(product[index] // direction[index])
    u_norms = [_norm_squared(d) for d in u_dirs]

    kernel_dir = None
    if m > n:  # complete U with an orthonormal basis of ker(A^T)
        kernel_dir = _primitive(list(a_sym.T.nullspace()[0]))
        u_dirs.append(kernel_dir)
        u_norms.append(_norm_squared(kernel_dir))

    all_dirs = v_dirs + u_dirs
    if max(abs(x) for d in all_dirs for x in d) > _MAX_DIRECTION_ENTRY:
        return None
    if max(v_norms + u_norms) > _MAX_NORM_SQUARED:
        return None  # keep the normalisation factors 1/sqrt(k) small

    return {
        "gram": [[int(gram[i, j]) for j in range(n)] for i in range(n)],
        "char_expr": char_poly.as_expr(),
        "eigenvalues": eigenvalues,
        "v_dirs": v_dirs,
        "v_norms": v_norms,
        "u_products": u_products,
        "u_dirs": u_dirs,
        "u_factors": u_factors,
        "u_norms": u_norms,
        "kernel_dir": kernel_dir,
    }


def _draw(rng: random.Random) -> tuple[Matrix, int, int, dict]:
    # The shape is fixed before the rejection loop, otherwise the shape with
    # the higher acceptance rate would dominate.
    m, n = rng.choice(_SHAPES)
    while True:
        a_mat = [[rng.randint(-_ENTRY_RANGE, _ENTRY_RANGE) for _ in range(n)] for _ in range(m)]
        data = _analyse(a_mat, m, n)
        if data is not None:
            return a_mat, m, n, data


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    a_mat, m, n, data = _draw(rng)

    a_sym = sympy.Matrix(a_mat)
    gram_int = data["gram"]
    char_expr = data["char_expr"]
    eigenvalues = data["eigenvalues"]
    v_dirs, v_norms = data["v_dirs"], data["v_norms"]
    u_products, u_factors = data["u_products"], data["u_factors"]
    u_dirs, u_norms = data["u_dirs"], data["u_norms"]
    kernel_dir = data["kernel_dir"]

    u_sym = sympy.Matrix.hstack(
        *[sympy.Matrix(d) / sympy.sqrt(k) for d, k in zip(u_dirs, u_norms)]
    )
    v_sym = sympy.Matrix.hstack(
        *[sympy.Matrix(d) / sympy.sqrt(k) for d, k in zip(v_dirs, v_norms)]
    )
    sigma_sym = sympy.zeros(m, n)
    for i, value in enumerate(eigenvalues):
        sigma_sym[i, i] = sympy.sqrt(value)
    assert sympy.simplify(u_sym * sigma_sym * v_sym.T - a_sym) == sympy.zeros(m, n)
    assert sympy.simplify(u_sym.T * u_sym - sympy.eye(m)) == sympy.zeros(m, m)
    assert sympy.simplify(v_sym.T * v_sym - sympy.eye(n)) == sympy.zeros(n, n)

    frobenius = sum(v * v for row in a_mat for v in row)

    prompt = (
        f"Compute the singular value decomposition $A = U\\Sigma V^{{\\top}}$ of the "
        f"${m}\\times {n}$ matrix\n\n$$A = {_int_bmatrix(a_mat)}.$$\n\n"
        "List the singular values in descending order and give all singular values and "
        "singular vectors exactly (no decimal approximations). Normalise each right singular "
        "vector $v_i$ so that its first nonzero entry is positive; the left singular vectors "
        "then follow from $u_i = \\tfrac{1}{\\sigma_i} A v_i$"
        + (
            ", and complete $U$ to an orthonormal basis of $\\mathbb{R}^3$ with a third vector "
            "whose first nonzero entry is positive."
            if m > n
            else "."
        )
    )

    steps: list[Step] = [
        Step(
            "**Recipe.** $A^{\\top}A$ is symmetric positive semidefinite; its eigenvalues are "
            "$\\sigma_i^2$ and its orthonormal eigenvectors are the right singular vectors "
            "$v_i$. The left singular vectors follow from $A v_i = \\sigma_i u_i$. All of the "
            "arithmetic below stays in the integers — only the final normalisation introduces "
            "square roots."
        ),
        Step(
            "**Gram matrix and its eigenvalues.**\n\n"
            f"$$A^{{\\top}}A = {_int_bmatrix(gram_int)}, \\qquad "
            f"\\chi(\\lambda) = {sympy.latex(char_expr)} = "
            f"{sympy.latex(sympy.factor(char_expr))}.$$\n\n"
            "So $"
            + ", \\quad ".join(
                f"\\sigma_{i + 1}^2 = {value}" for i, value in enumerate(eigenvalues)
            )
            + "$, i.e. $"
            + ", \\quad ".join(
                f"\\sigma_{i + 1} = {_sigma_symbol(value)}" for i, value in enumerate(eigenvalues)
            )
            + "$. Check: $\\sum_i \\sigma_i^2 = "
            + " + ".join(str(value) for value in eigenvalues)
            + f" = {frobenius}$, which is the sum of the squares of all entries of $A$ "
            "(the squared Frobenius norm), and $\\prod_i \\sigma_i^2 = "
            f"{sympy.prod(eigenvalues)} = \\det(A^{{\\top}}A)$."
        ),
    ]

    for i, (value, direction, norm_sq) in enumerate(zip(eigenvalues, v_dirs, v_norms), start=1):
        shifted = [
            [gram_int[r][c] - (value if r == c else 0) for c in range(n)] for r in range(n)
        ]
        steps.append(
            Step(
                f"**Right singular vector $v_{i}$** (eigenvector for $\\lambda = {value}$).\n\n"
                f"$$A^{{\\top}}A - {value}I = {_int_bmatrix(shifted)} \\;\\Rightarrow\\; "
                f"\\tilde v_{i} = {_int_bmatrix([[x] for x in direction])}, \\qquad "
                f"\\|\\tilde v_{i}\\|^2 = {norm_sq}, \\qquad "
                f"v_{i} = {_unit_vector_latex(direction, norm_sq)}.$$"
            )
        )

    for i, (value, direction, product, factor, norm_sq) in enumerate(
        zip(eigenvalues, v_dirs, u_products, u_factors, u_norms), start=1
    ):
        steps.append(
            Step(
                f"**Left singular vector $u_{i} = \\tfrac{{1}}{{\\sigma_{i}}} A v_{i}$.** "
                "Multiply the *integer* direction first:\n\n"
                f"$$A\\,\\tilde v_{i} = {_int_bmatrix(a_mat)}"
                f"{_int_bmatrix([[x] for x in direction])} = "
                f"{_int_bmatrix([[x] for x in product])}"
                + (
                    f" = {factor}\\,{_int_bmatrix([[x] for x in u_dirs[i - 1]])}"
                    if abs(factor) != 1
                    else ""
                )
                + ".$$\n\n"
                f"Normalising gives $u_{i} = {_unit_vector_latex(u_dirs[i - 1], norm_sq)}$ "
                f"(equivalently $u_{i} = \\tfrac{{1}}{{{_sigma_symbol(value)}}} A v_{i}$)."
            )
        )

    if kernel_dir is not None:
        steps.append(
            Step(
                "**Third column of $U$.** $u_1, u_2$ span the image of $A$; the full $U$ needs "
                "one more unit vector, orthogonal to both, i.e. a basis vector of "
                "$\\ker(A^{\\top}) = (\\operatorname{im} A)^{\\perp}$:\n\n"
                f"$$A^{{\\top}}u = 0 \\;\\Rightarrow\\; \\tilde u_3 = "
                f"{_int_bmatrix([[x] for x in kernel_dir])}, \\qquad u_3 = "
                f"{_unit_vector_latex(kernel_dir, u_norms[2])}.$$\n\n"
                "Orthogonality is easy to confirm with integer dot products: "
                f"$\\tilde u_1 \\cdot \\tilde u_3 = "
                f"{sum(x * y for x, y in zip(u_dirs[0], kernel_dir))}$ and "
                f"$\\tilde u_2 \\cdot \\tilde u_3 = "
                f"{sum(x * y for x, y in zip(u_dirs[1], kernel_dir))}$."
            )
        )

    reduced_note = ""
    if m > n:
        reduced_note = (
            "\n\nDropping the last column of $U$ and the zero row of $\\Sigma$ gives the "
            "reduced SVD $A = \\hat U \\hat\\Sigma V^{\\top}$ with "
            f"$\\hat\\Sigma = {_sigma_latex(eigenvalues, n, n)}$."
        )
    steps.append(
        Step(
            "**Assemble.**\n\n"
            f"$$U = {_orthonormal_matrix_latex(u_dirs, u_norms)}, \\qquad "
            f"\\Sigma = {_sigma_latex(eigenvalues, m, n)}, \\qquad "
            f"V = {_orthonormal_matrix_latex(v_dirs, v_norms)},$$\n\n"
            "so that $A = U\\Sigma V^{\\top}$." + reduced_note
        )
    )
    steps.append(
        Step(
            "**Check.** The columns of $U$ and of $V$ are orthonormal — with integer "
            f"directions, $\\tilde v_1 \\cdot \\tilde v_2 = "
            f"{sum(x * y for x, y in zip(v_dirs[0], v_dirs[1]))}$ and "
            f"$\\tilde u_1 \\cdot \\tilde u_2 = "
            f"{sum(x * y for x, y in zip(u_dirs[0], u_dirs[1]))}$ — and "
            f"$\\|A\\tilde v_i\\|^2 = \\sigma_i^2\\,\\|\\tilde v_i\\|^2$ holds for both $i$: "
            + ", ".join(
                f"${_norm_squared(product)} = {value}\\cdot{norm_sq}$"
                for product, value, norm_sq in zip(u_products, eigenvalues, v_norms)
            )
            + " ✓"
        )
    )

    final_answer = (
        f"$$A = U\\Sigma V^{{\\top}} = {_orthonormal_matrix_latex(u_dirs, u_norms)}\\; "
        f"{_sigma_latex(eigenvalues, m, n)}\\; "
        f"\\left({_orthonormal_matrix_latex(v_dirs, v_norms)}\\right)^{{\\top}}$$"
    )

    def _padded(values: list[int]) -> list[int | None]:
        return list(values) + [None] * (3 - len(values))

    rows = [{"label": "$\\sigma_i^2$ (descending)", "cells": _padded(eigenvalues)}]
    rows += [
        {"label": f"$\\tilde v_{i + 1}$ (integer direction)", "cells": _padded(direction)}
        for i, direction in enumerate(v_dirs)
    ]
    rows += [
        {"label": f"$\\tilde u_{i + 1}$ (integer direction)", "cells": _padded(direction)}
        for i, direction in enumerate(u_dirs)
    ]
    rows += [{"label": "$\\|\\tilde v_i\\|^2$", "cells": _padded(v_norms)}]
    rows += [{"label": "$\\|\\tilde u_i\\|^2$", "cells": _padded(u_norms)}]
    check_table = {
        "col_headers": ["1", "2", "3"],
        "cell_hint": "everything here is an integer: enter the eigenvalues of $A^{\\top}A$, the "
        "singular-vector directions scaled to coprime integers ($\\tilde v_i$ with first nonzero "
        "entry positive, $\\tilde u_i$ in the direction of $A\\tilde v_i$), and their squared "
        "lengths — the singular vectors themselves are $\\tilde v_i/\\|\\tilde v_i\\|$ and "
        "$\\tilde u_i/\\|\\tilde u_i\\|$",
        "rows": rows,
    }

    answers = {
        "A": a_mat,
        "shape": [m, n],
        "gram": gram_int,
        "eigenvalues": eigenvalues,
        "singular_values": [str(sympy.sqrt(value)) for value in eigenvalues],
        "v_directions": v_dirs,
        "v_norms_squared": v_norms,
        "u_directions": u_dirs,
        "u_norms_squared": u_norms,
        "frobenius_squared": frobenius,
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

    parser = argparse.ArgumentParser(description="Generate a singular value decomposition exercise.")
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
