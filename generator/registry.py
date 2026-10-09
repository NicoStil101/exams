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
from operating_system import cpu_scheduling, inode_max_filesize, petri_net_reachability
from linear_algebra import (
    eigenvalues_3x3,
    jordan_normal_form,
    lu_factorisation,
    matrix_transformation,
    singular_value_decomposition,
)
from algorithms import heapsort, red_black_tree, mst_weight, dijkstra, bellman_ford

CATEGORIES: dict[str, dict] = {
    "operating-system": {
        "label": "Operating Systems",
        "semester": "26s",
        "icon": "cpu",
        "tools": [],
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
            inode_max_filesize.EXERCISE_ID: {
                "label": inode_max_filesize.TITLE,
                "module": inode_max_filesize,
            },
            cpu_scheduling.EXERCISE_ID: {
                "label": cpu_scheduling.TITLE,
                "module": cpu_scheduling,
            },
        },
    },
    "algorithms": {
        "label": "Algorithms",
        "semester": "26s",
        "icon": "network",
        # web endpoint names of interactive tools shown on the subject page
        "tools": [
            {"label": "Red-Black Tree Visualizer", "endpoint": "rb_visualizer_page", "icon": "git-fork"},
            {"label": "BST Visualizer", "endpoint": "bst_visualizer_page", "icon": "binary"},
            {"label": "Heap Visualizer", "endpoint": "heap_visualizer_page", "icon": "triangle"},
        ],
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
        "semester": "26s",
        "icon": "sigma",
        "tools": [],
        "exercises": {
            eigenvalues_3x3.EXERCISE_ID: {
                "label": eigenvalues_3x3.TITLE,
                "module": eigenvalues_3x3,
            },
            matrix_transformation.EXERCISE_ID: {
                "label": matrix_transformation.TITLE,
                "module": matrix_transformation,
            },
            lu_factorisation.EXERCISE_ID: {
                "label": lu_factorisation.TITLE,
                "module": lu_factorisation,
            },
            jordan_normal_form.EXERCISE_ID: {
                "label": jordan_normal_form.TITLE,
                "module": jordan_normal_form,
            },
            singular_value_decomposition.EXERCISE_ID: {
                "label": singular_value_decomposition.TITLE,
                "module": singular_value_decomposition,
            },
        },
    },
    "robot-control": {
        "label": "Einführung in die Roboterregelung",
        "semester": "26w",
        "icon": "bot",
        "tools": [],
        "exercises": {},
    },
    "databases": {
        "label": "Grundlagen Datenbanken",
        "semester": "26w",
        "icon": "database",
        "tools": [],
        "exercises": {},
    },
    "it-security": {
        "label": "IT-Sicherheit",
        "semester": "26w",
        "icon": "shield-check",
        "tools": [],
        "exercises": {},
    },
    "analysis": {
        "label": "Analysis",
        "semester": "26w",
        "icon": "chart-spline",
        "tools": [],
        "exercises": {},
    },
    "artificial-intelligence": {
        "label": "Fundamentals of Artificial Intelligence",
        "semester": "26w",
        "icon": "brain",
        "tools": [],
        "exercises": {},
    },
}


def semester_sort_key(semester: str) -> tuple[int, int]:
    """"25w" -> (25, 1), "26s" -> (26, 0): chronological order (summer before winter)."""
    return int(semester[:-1]), 1 if semester.endswith("w") else 0


def get_module(exercise_id: str):
    for category in CATEGORIES.values():
        entry = category["exercises"].get(exercise_id)
        if entry:
            return entry["module"]
    raise KeyError(f"Unknown exercise id: {exercise_id}")
