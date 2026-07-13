"""Small integer 3x3 matrix helpers shared by linear-algebra exercises."""

from __future__ import annotations

Matrix3 = list[list[int]]


def identity3() -> Matrix3:
    return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def matmul3(a: Matrix3, b: Matrix3) -> Matrix3:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def diag3(values: list[int]) -> Matrix3:
    return [[values[i] if i == j else 0 for j in range(3)] for i in range(3)]


def to_latex_bmatrix(m: Matrix3) -> str:
    rows = " \\\\ ".join(" & ".join(str(v) for v in row) for row in m)
    return f"\\begin{{bmatrix}} {rows} \\end{{bmatrix}}"


def trace3(m: Matrix3) -> int:
    return m[0][0] + m[1][1] + m[2][2]


def det3(m: Matrix3) -> int:
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def principal_minor_sum3(m: Matrix3) -> int:
    """Sum of the three 2x2 principal minors (the $c_2$ coefficient of the
    characteristic polynomial $\\lambda^3 - tr(A)\\lambda^2 + c_2\\lambda - det(A)$)."""
    m11 = m[1][1] * m[2][2] - m[1][2] * m[2][1]
    m22 = m[0][0] * m[2][2] - m[0][2] * m[2][0]
    m33 = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    return m11 + m22 + m33


def sub3(a: Matrix3, b: Matrix3) -> Matrix3:
    return [[a[i][j] - b[i][j] for j in range(3)] for i in range(3)]


def scaled_identity3(lam: int) -> Matrix3:
    return [[lam if i == j else 0 for j in range(3)] for i in range(3)]


def matvec3(a: Matrix3, v: list[int]) -> list[int]:
    return [sum(a[i][k] * v[k] for k in range(3)) for i in range(3)]


def to_latex_col_vector(v: list[int]) -> str:
    rows = " \\\\ ".join(str(x) for x in v)
    return f"\\begin{{bmatrix}} {rows} \\end{{bmatrix}}"
