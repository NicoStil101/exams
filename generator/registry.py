"""Registry mapping categories -> exercise generator modules.

Adding a new exercise later is just: write a module with a `generate(seed)`
function returning an Exercise (see core.py), then list it here.
"""

from __future__ import annotations

from operating_system import paging_single_level
from operating_system import buddy_allocator
from operating_system import bankers_algorithm
from operating_system import page_table_translation
from operating_system import page_table_entries
from operating_system import petri_net_reachability
from linear_algebra import eigenvalues_3x3
from algorithms import heapsort, red_black_tree, mst_weight, dijkstra, bellman_ford

CATEGORIES: dict[str, dict] = {
    "operating-system": {
        "label": "Operating Systems",
        "exercises": {
            paging_single_level.EXERCISE_ID: {
                "label": paging_single_level.TITLE,
                "module": paging_single_level,
            },
            buddy_allocator.EXERCISE_ID: {
                "label": buddy_allocator.TITLE,
                "module": buddy_allocator,
            },
            bankers_algorithm.EXERCISE_ID: {
                "label": bankers_algorithm.TITLE,
                "module": bankers_algorithm,
            },
            page_table_translation.EXERCISE_ID: {
                "label": page_table_translation.TITLE,
                "module": page_table_translation,
            },
            page_table_entries.EXERCISE_ID: {
                "label": page_table_entries.TITLE,
                "module": page_table_entries,
            },
            petri_net_reachability.EXERCISE_ID: {
                "label": petri_net_reachability.TITLE,
                "module": petri_net_reachability,
            },
        },
    },
    "algorithms": {
        "label": "Algorithms",
        "exercises": {
            heapsort.EXERCISE_ID: {
                "label": heapsort.TITLE,
                "module": heapsort,
            },
            red_black_tree.EXERCISE_ID: {
                "label": red_black_tree.TITLE,
                "module": red_black_tree,
            },
            mst_weight.EXERCISE_ID: {
                "label": mst_weight.TITLE,
                "module": mst_weight,
            },
            dijkstra.EXERCISE_ID: {
                "label": dijkstra.TITLE,
                "module": dijkstra,
            },
            bellman_ford.EXERCISE_ID: {
                "label": bellman_ford.TITLE,
                "module": bellman_ford,
            },
        },
    },
    "linear-algebra": {
        "label": "Linear Algebra",
        "exercises": {
            eigenvalues_3x3.EXERCISE_ID: {
                "label": eigenvalues_3x3.TITLE,
                "module": eigenvalues_3x3,
            },
        },
    },
}


def get_module(exercise_id: str):
    for category in CATEGORIES.values():
        entry = category["exercises"].get(exercise_id)
        if entry:
            return entry["module"]
    raise KeyError(f"Unknown exercise id: {exercise_id}")
