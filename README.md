# Exam Prep

Randomized exam practice exercises with deterministic worked solutions,
organized by subject: **Algorithms**, **Operating Systems**, **Linear Algebra**.

## How it works

Each exercise is a Python module with one function:

```python
generate(seed: int | None = None) -> Exercise
```

- Parameters (numbers in the problem) are randomized using `seed`.
- The **solution is always derived by pure computation** from those
  parameters — never hardcoded or random — so the same seed always
  reproduces the exact same problem and answer.
- Press "New Random Exercise" in the web UI to get a fresh seed; the
  seed is shown so a specific problem can be reproduced later.

## Project layout

```
exam-prep/
  generator/
    core.py                        # shared Exercise/Step dataclasses + helpers
    registry.py                    # category -> exercise module lookup
    operating_system/
      paging_single_level.py       # single-level page table address translation
    algorithms/                    # (exercises to be added)
    linear_algebra/                # (exercises to be added)
  web/
    app.py                         # Flask app: overview + exercise pages + JSON API
    templates/
    static/                        # clean, LaTeX-style rendering via KaTeX
  venv/
```

## Run it

```bash
cd exam-prep
./venv/bin/python web/app.py
# -> http://127.0.0.1:5050
```

## Run a generator standalone (no web server)

```bash
cd exam-prep/generator/operating_system
python3 paging_single_level.py --seed 42        # human readable
python3 paging_single_level.py --seed 42 --json # machine readable
```

## Adding a new exercise

1. Create `generator/<category>/<name>.py` with a `generate(seed=None) -> Exercise`
   function (see `paging_single_level.py` for the pattern: pick random valid
   parameters with `random.Random(seed)`, then compute the solution purely
   from those parameters).
2. Register it in `generator/registry.py` under the right category.
