"""Exercise: Banker's Algorithm (deadlock avoidance).

Given Has/Max/Available for a set of processes and resuable resource
types, this exercise asks:

  (a) How many distinct safe sequences of successful completion exist?
  (b) Is a given resource request safe to grant immediately?

Both are converted from the classic "select all that apply" checkbox
format into a single deterministic number / yes-or-no, found by an
exhaustive (brute-force, always-correct for n<=3 processes) safety search
-- directly analogous to asking for MST *weight* instead of reproducing
one exact spanning tree: the count and the yes/no verdict are each unique
even though there can be more than one safe sequence.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "os-bankers-algorithm"
TITLE = "Banker's Algorithm: Safety and Requests"

_PROC_COUNT = 3


def _vec_latex(v: list[int]) -> str:
    return "\\langle " + ", ".join(str(x) for x in v) + " \\rangle"


def _table_latex(resource_names: list[str], has: list[list[int]], max_claim: list[list[int]], need: list[list[int]] | None = None) -> str:
    n_res = len(resource_names)
    n_groups = 3 if need else 2
    cols = "|c|" + "c|" * (n_res * n_groups)
    header = (
        ["\\text{P}"]
        + [f"\\text{{Has}}_{{{r}}}" for r in resource_names]
        + [f"\\text{{Max}}_{{{r}}}" for r in resource_names]
    )
    if need:
        header += [f"\\text{{Need}}_{{{r}}}" for r in resource_names]
    rows = [" & ".join(header) + " \\\\"]
    for i in range(len(has)):
        cells = [f"P_{{{i}}}"] + [str(x) for x in has[i]] + [str(x) for x in max_claim[i]]
        if need:
            cells += [str(x) for x in need[i]]
        rows.append(" & ".join(cells) + " \\\\")
    body = " \\hline ".join(rows)
    return f"\\begin{{array}}{{{cols}}}\\hline {body} \\hline\\end{{array}}"


def _find_safe_sequences(
    n_procs: int, need: list[list[int]], has: list[list[int]], available: list[int]
) -> list[list[int]]:
    n_res = len(available)
    results: list[list[int]] = []

    def backtrack(remaining: set[int], avail: list[int], seq: list[int]) -> None:
        if not remaining:
            results.append(seq[:])
            return
        for p in sorted(remaining):
            if all(need[p][r] <= avail[r] for r in range(n_res)):
                new_avail = [avail[r] + has[p][r] for r in range(n_res)]
                seq.append(p)
                backtrack(remaining - {p}, new_avail, seq)
                seq.pop()

    backtrack(set(range(n_procs)), available[:], [])
    return results


def _sequence_trace(seq: list[int], has: list[list[int]], available: list[int]) -> str:
    n_res = len(available)
    avail = available[:]
    parts = [f"Available starts at ${_vec_latex(avail)}$"]
    for p in seq:
        avail = [avail[r] + has[p][r] for r in range(n_res)]
        parts.append(f"after $P_{{{p}}}$ finishes: ${_vec_latex(avail)}$")
    return ", ".join(parts)


def _is_request_safe(
    n_procs: int,
    need: list[list[int]],
    has: list[list[int]],
    available: list[int],
    p: int,
    request: list[int],
) -> tuple[bool, str]:
    n_res = len(available)
    if any(request[r] > need[p][r] for r in range(n_res)):
        return False, f"it exceeds $P_{{{p}}}$'s remaining need ${_vec_latex(need[p])}$"
    if any(request[r] > available[r] for r in range(n_res)):
        return False, f"it exceeds the available resources ${_vec_latex(available)}$ (the process must wait)"
    new_available = [available[r] - request[r] for r in range(n_res)]
    new_has = [row[:] for row in has]
    new_has[p] = [has[p][r] + request[r] for r in range(n_res)]
    new_need = [row[:] for row in need]
    new_need[p] = [need[p][r] - request[r] for r in range(n_res)]
    seqs = _find_safe_sequences(n_procs, new_need, new_has, new_available)
    if seqs:
        example = " \\to ".join(f"P_{{{i}}}" for i in seqs[0])
        return True, f"tentatively granting it still leaves a safe sequence, e.g. ${example}$"
    return False, "tentatively granting it leaves **no** safe sequence (the resulting state is unsafe)"


def _vec_table_only(resource_names: list[str], need: list[list[int]]) -> str:
    n_res = len(resource_names)
    cols = "|c|" + "c|" * n_res
    header = ["\\text{P}"] + [f"\\text{{Need}}_{{{r}}}" for r in resource_names]
    rows = [" & ".join(header) + " \\\\"]
    for i, row in enumerate(need):
        rows.append(" & ".join([f"P_{{{i}}}"] + [str(x) for x in row]) + " \\\\")
    body = " \\hline ".join(rows)
    return f"\\begin{{array}}{{{cols}}}\\hline {body} \\hline\\end{{array}}"


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    n_res = rng.choice([2, 3])
    resource_names = ["A", "B", "C"][:n_res]

    has = [[rng.randint(0, 4) for _ in range(n_res)] for _ in range(_PROC_COUNT)]
    max_claim = [[has[i][r] + rng.randint(1, 5) for r in range(n_res)] for i in range(_PROC_COUNT)]
    available = [rng.randint(1, 5) for _ in range(n_res)]
    need = [[max_claim[i][r] - has[i][r] for r in range(n_res)] for i in range(_PROC_COUNT)]

    safe_sequences = _find_safe_sequences(_PROC_COUNT, need, has, available)
    safe_count = len(safe_sequences)

    p_req = rng.randrange(_PROC_COUNT)
    request = [rng.randint(0, need[p_req][r] + 1) for r in range(n_res)]
    is_safe, reason = _is_request_safe(_PROC_COUNT, need, has, available, p_req, request)

    prompt = (
        f"The following table shows the current state of a system with three concurrent "
        f"processes ($P_0$-$P_2$) and {n_res} reusable resource types "
        f"({', '.join(resource_names)}).\n\n"
        f"$${_table_latex(resource_names, has, max_claim)}$$\n\n"
        f"Available resources: ${', '.join(resource_names)} = {_vec_latex(available)}$.\n\n"
        f"**(a)** How many distinct safe sequences of successful completion exist?\n\n"
        f"**(b)** Suppose $P_{{{p_req}}}$ issues the request "
        f"${', '.join(resource_names)} = {_vec_latex(request)}$. Is this request safe to grant "
        f"immediately, according to the Banker's algorithm?"
    )

    steps = [
        Step(
            "$\\text{Need}_i = \\text{Max}_i - \\text{Has}_i$ is the most each process could still "
            "request. The safety algorithm repeatedly looks for a process whose Need fits within "
            "the currently Available resources, lets it finish (adding its Has back to "
            "Available), and repeats; if every process can finish this way, the sequence found "
            "is *safe*. There can be more than one safe order, but whether a state is safe (and "
            "how many total safe orders exist) is unique."
        ),
        Step("$$" + _vec_table_only(resource_names, need) + "$$"),
    ]

    if safe_count:
        for seq in safe_sequences:
            arrow = " \\to ".join(f"P_{{{i}}}" for i in seq)
            steps.append(Step(f"Safe sequence $ {arrow} $: {_sequence_trace(seq, has, available)}."))
        steps.append(Step(f"**(a)** Total distinct safe sequences found: **{safe_count}**."))
    else:
        steps.append(
            Step(
                "**(a)** Exhaustively trying every process order, no process ever has "
                "$\\text{Need}_i \\le \\text{Available}$ far enough to let all three finish -- "
                "**no safe sequence exists** (this state is unsafe)."
            )
        )

    steps.append(
        Step(
            f"**(b)** Check $P_{{{p_req}}}$'s request ${_vec_latex(request)}$ against "
            f"$\\text{{Need}}_{{{p_req}}} = {_vec_latex(need[p_req])}$ and "
            f"$\\text{{Available}} = {_vec_latex(available)}$: {reason}. "
            f"The request is therefore **{'safe' if is_safe else 'not safe'}** to grant immediately."
        )
    )

    final_answer = (
        f"(a) {safe_count} safe sequence{'s' if safe_count != 1 else ''} &nbsp;&nbsp; "
        f"(b) {'yes' if is_safe else 'no'}"
    )

    check_answers = [
        {"label": "(a) Number of distinct safe sequences", "value": safe_count, "type": "number"},
        {
            "label": f"(b) Is P{p_req}'s request safe to grant immediately?",
            "value": "yes" if is_safe else "no",
            "type": "text",
            "options": ["yes", "no"],
        },
    ]

    answers = {
        "resource_names": resource_names,
        "has": has,
        "max": max_claim,
        "need": need,
        "available": available,
        "safe_sequences": safe_sequences,
        "safe_count": safe_count,
        "request_process": p_req,
        "request": request,
        "request_is_safe": is_safe,
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

    parser = argparse.ArgumentParser(description="Generate a Banker's algorithm exercise.")
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
