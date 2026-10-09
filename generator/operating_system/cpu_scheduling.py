"""Exercise: CPU scheduling — fill in the Gantt chart for four strategies.

Three processes with random arrival times and computing times are scheduled
under

    a) FCFS  — non-preemptive, queued in order of arrival
    b) SRTN  — preemptive; preemption happens on arrival of a new process only
    c) RR(1) — round-robin, time slot one unit, cyclic ordering by PID
    d) RR(2) — round-robin, time slot two units

Context switches take no time (at time 0 the first process can already use
the CPU). The parameters are rejection-sampled so that the CPU is never idle,
SRTN really preempts at least once, and the four resulting schedules are
pairwise different — otherwise a sub-task would grade another one's answer.

The student answers by clicking cells in one timeline grid per strategy
(`check_grids`, rendered by the web UI); every cell is graded on "Check".
All schedules are computed by pure simulation of the stated rules.

Tie-breaking conventions (also stated in the exercise text):
  - SRTN: a new arrival preempts only if its burst is *strictly* shorter than
    the running process's remaining time; on completion the arrived process
    with the shortest remaining time runs, ties broken by lower PID.
  - RR: the ready queue starts in PID order; a process arriving at time t is
    enqueued *before* a process whose time slice expires at t.
"""

from __future__ import annotations

import random
import sys
from collections import deque
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # `core`

from core import Exercise, Step, new_seed  # noqa: E402

EXERCISE_ID = "os-cpu-scheduling"
TITLE = "CPU Scheduling: FCFS, SRTN and Round-Robin"

_NUM_PROCS = 3
_BURST_RANGE = (3, 7)
_MAX_TOTAL = 16  # grid width == total burst (no idle by construction)


def _fcfs(procs: list[tuple[int, int, int]]) -> list[int]:
    """procs: (pid, arrival, burst). Returns pid running in each unit slot."""
    timeline: list[int] = []
    for pid, arrival, burst in sorted(procs, key=lambda p: (p[1], p[0])):
        while len(timeline) < arrival:  # guard; never hit with our sampling
            timeline.append(0)
        timeline.extend([pid] * burst)
    return timeline


def _srtn(procs: list[tuple[int, int, int]]) -> list[int]:
    remaining = {pid: burst for pid, _, burst in procs}
    arrival_of = {pid: arr for pid, arr, _ in procs}
    timeline: list[int] = []
    current = 0
    t = 0
    while any(remaining[p] > 0 for p in remaining):
        arrived = [p for p in remaining if arrival_of[p] <= t and remaining[p] > 0]
        if not arrived:
            timeline.append(0)
            t += 1
            continue
        shortest = min(arrived, key=lambda p: (remaining[p], p))
        if current == 0 or remaining.get(current, 0) == 0:
            current = shortest  # free choice at start / after a completion
        elif any(arrival_of[p] == t for p in arrived):
            # decision point on arrival: preempt only if strictly shorter
            if remaining[shortest] < remaining[current]:
                current = shortest
        timeline.append(current)
        remaining[current] -= 1
        t += 1
    return timeline


def _round_robin(procs: list[tuple[int, int, int]], quantum: int) -> list[int]:
    remaining = {pid: burst for pid, _, burst in procs}
    pending = deque(sorted(procs, key=lambda p: (p[1], p[0])))
    queue: deque[int] = deque()
    timeline: list[int] = []
    current = 0
    used = 0
    t = 0
    while pending or queue or current:
        # arrivals first: an arriving process is enqueued before a process
        # whose time slice expires at the same instant
        while pending and pending[0][1] <= t:
            queue.append(pending.popleft()[0])
        if current and remaining[current] == 0:
            current = 0
        elif current and used == quantum:
            queue.append(current)
            current = 0
        if not current and queue:
            current = queue.popleft()
            used = 0
        if current:
            timeline.append(current)
            remaining[current] -= 1
            used += 1
            t += 1
        elif pending:
            timeline.append(0)
            t += 1
        else:
            break
    return timeline


def _segments(timeline: list[int]) -> list[tuple[int, int, int]]:
    """(pid, start, end) runs of consecutive equal slots."""
    segments: list[tuple[int, int, int]] = []
    for t, pid in enumerate(timeline):
        if segments and segments[-1][0] == pid and segments[-1][2] == t:
            segments[-1] = (pid, segments[-1][1], t + 1)
        else:
            segments.append((pid, t, t + 1))
    return segments


def _segments_latex(timeline: list[int]) -> str:
    return ",\\; ".join(
        f"P_{pid}\\!: {start}\\text{{–}}{end}" for pid, start, end in _segments(timeline)
    )


def _dispatches(timeline: list[int]) -> list[int]:
    """1 in slot t iff the dispatcher hands the CPU over at time t, i.e. a
    process (different from the one before) is dispatched — including t=0."""
    return [1 if t == 0 or timeline[t] != timeline[t - 1] else 0 for t in range(len(timeline))]


def _grid(title: str, timeline: list[int], hint: str = "") -> dict:
    rows = list(range(_NUM_PROCS, 0, -1))  # P3 on top, P1 at the bottom
    grid = {
        "title": title,
        "rows": ["Scheduling"] + [f"P{p}" for p in rows],
        "slots": len(timeline),
        "solution": [_dispatches(timeline)]
        + [[1 if slot == p else 0 for slot in timeline] for p in rows],
    }
    if hint:
        grid["hint"] = hint
    return grid


def generate(seed: int | None = None) -> Exercise:
    rng = random.Random(seed)
    if seed is None:
        seed = new_seed(rng)
        rng = random.Random(seed)

    while True:
        bursts = [rng.randint(*_BURST_RANGE) for _ in range(_NUM_PROCS)]
        if sum(bursts) > _MAX_TOTAL:
            continue
        a2 = rng.randint(1, min(bursts[0], 4))
        a3 = rng.randint(a2 + 1, min(bursts[0] + bursts[1], a2 + 5))
        arrivals = [0, a2, a3]
        procs = [(pid + 1, arrivals[pid], bursts[pid]) for pid in range(_NUM_PROCS)]

        fcfs = _fcfs(procs)
        srtn = _srtn(procs)
        rr1 = _round_robin(procs, 1)
        rr2 = _round_robin(procs, 2)
        timelines = (fcfs, srtn, rr1, rr2)

        if any(0 in tl for tl in timelines):
            continue  # keep the CPU busy throughout
        if len({tuple(tl) for tl in timelines}) != 4:
            continue  # each sub-task should have its own answer
        if len(_segments(srtn)) <= _NUM_PROCS:
            continue  # require at least one real SRTN preemption
        break

    total = sum(bursts)
    table = "\n".join(
        ["Process   Arrival   Computing time"]
        + [f"P{pid}        {arr}         {burst}" for pid, arr, burst in procs]
    )

    prompt = (
        "The following processes are to be scheduled on a single CPU. Context switches "
        "take no time, i.e. at time 0 the first process can already use the CPU.\n\n"
        f"```\n{table}\n```\n\n"
        "Determine the schedule for each of the strategies below by clicking the cells "
        "of the timeline grids: mark cell $[t, t+1)$ in the row of the process that is "
        "running during that unit of time. In the **Scheduling** row, mark slot "
        "$[t, t+1)$ whenever the dispatcher hands the CPU over at time $t$, i.e. "
        "whenever a different process is dispatched (including the first dispatch at "
        "$t = 0$).\n\n"
        "Conventions: for SRTN, a newly arriving process preempts only if its computing "
        "time is *strictly* shorter than the remaining time of the running process; ties "
        "are broken by lower PID. For Round-Robin, the ready queue starts in PID order "
        "and a process arriving at time $t$ is enqueued *before* a process whose time "
        "slice expires at $t$."
    )

    grids = [
        _grid(
            "a) First-Come-First-Served (FCFS): non-preemptive, processes are queued "
            "in their order of arrival.",
            fcfs,
        ),
        _grid(
            "b) Shortest Remaining Time Next (SRTN): preemptive, the process with the "
            "shortest remaining time is chosen. Preemptions happen on arrival of a new "
            "process only.",
            srtn,
        ),
        _grid(
            "c) Round-Robin with time slots of **one unit** and cyclic ordering of "
            "processes. All processes have the same priority; they are ordered by PID.",
            rr1,
        ),
        _grid(
            "d) Round-Robin with time slots of **two units** and cyclic ordering of "
            "processes. All processes have the same priority; they are ordered by PID.",
            rr2,
        ),
    ]

    # --- worked solution ---------------------------------------------------
    remaining_at = {}  # SRTN remaining time bookkeeping for the narration
    rem = {pid: burst for pid, _, burst in procs}
    for t, pid in enumerate(srtn):
        remaining_at[t] = dict(rem)
        rem[pid] -= 1

    srtn_notes = []
    for pid, arr, burst in procs[1:]:
        running = srtn[arr]
        prev = srtn[arr - 1] if arr > 0 else 0
        rem_prev = remaining_at[arr][prev]
        if running == pid:
            srtn_notes.append(
                f"at $t = {arr}$, $P_{pid}$ arrives needing ${burst} < {rem_prev}$ "
                f"(remaining time of $P_{prev}$) and preempts it"
            )
        else:
            srtn_notes.append(
                f"at $t = {arr}$, $P_{pid}$ arrives needing ${burst} \\ge "
                f"{rem_prev}$ (remaining time of $P_{prev}$), so no preemption"
            )

    def dispatch_times(timeline: list[int]) -> str:
        return ", ".join(str(t) for t, mark in enumerate(_dispatches(timeline)) if mark)

    steps = [
        Step(
            "**a) FCFS.** Processes run to completion in arrival order "
            f"$P_1, P_2, P_3$:\n\n$${_segments_latex(fcfs)}.$$\n\n"
            f"The dispatcher runs at $t = {dispatch_times(fcfs)}$."
        ),
        Step(
            "**b) SRTN.** " + "; ".join(srtn_notes) + ". After each completion the "
            "arrived process with the shortest remaining time continues:\n\n"
            f"$${_segments_latex(srtn)}.$$\n\n"
            f"The dispatcher runs at $t = {dispatch_times(srtn)}$."
        ),
        Step(
            "**c) Round-Robin, slot = 1.** Every unit the running process moves to the "
            "back of the ready queue (arrivals enter the queue first):\n\n"
            f"$${_segments_latex(rr1)}.$$\n\n"
            f"The dispatcher runs at $t = {dispatch_times(rr1)}$."
        ),
        Step(
            "**d) Round-Robin, slot = 2.** As in c) but a process keeps the CPU for up "
            "to two units (a final single unit if only one remains):\n\n"
            f"$${_segments_latex(rr2)}.$$\n\n"
            f"The dispatcher runs at $t = {dispatch_times(rr2)}$."
        ),
        Step(
            "**Check.** Every process runs for exactly its computing time in every "
            "schedule, and the CPU is busy from $0$ to $"
            + str(total)
            + "$ throughout — the makespan is the same for all four strategies; only "
            "the interleaving differs. The Scheduling row is marked exactly at the "
            "starts of the segments listed above (one dispatch per context switch, "
            "plus the first dispatch at $t = 0$)."
        ),
    ]

    answers = {
        "processes": [
            {"pid": pid, "arrival": arr, "burst": burst} for pid, arr, burst in procs
        ],
        "total_time": total,
        "fcfs": fcfs,
        "srtn": srtn,
        "rr_q1": rr1,
        "rr_q2": rr2,
        "dispatches": {
            "fcfs": _dispatches(fcfs),
            "srtn": _dispatches(srtn),
            "rr_q1": _dispatches(rr1),
            "rr_q2": _dispatches(rr2),
        },
    }

    return Exercise(
        id=EXERCISE_ID,
        seed=seed,
        title=TITLE,
        prompt=prompt,
        steps=steps,
        answers=answers,
        check_grids=grids,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a CPU scheduling exercise.")
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
        print("\nGrids:")
        for grid in ex.check_grids:
            print(" ", grid["title"])
            for label, row in zip(grid["rows"], grid["solution"]):
                print("   ", label, "".join("#" if c else "." for c in row))
        print("Answers:", ex.answers)
