"""Mutation hooks for the Stage 1 mutation matrix (scripts/stage1_mutation_matrix.py).

A mutation is active only when the environment variable STAGE1_MUTATION names it. Production runs refuse to start if
the variable is set (``assert_no_mutation``). Each hook sits at the one place where the corresponding bug would live.
"""

from __future__ import annotations

import os

ENV = "STAGE1_MUTATION"
KNOWN = (
    "wrong_prior_cont",        # CONT arm samples a from TN(0.2, 0.3) instead of TN(0.4, 0.3)
    "unpaired_seeds",          # the data stream depends on the arm, breaking common random numbers
    "library_not_nested",      # library atoms are redrawn per K instead of nested
    "missing_causal_mask",     # the transformer attends to future positions
    "target_in_input",         # the model input at position t includes x_{t+1}
    "off_by_one_position",     # the adapter reads the output at position n - 1 instead of n
    "wrong_reference",         # the evaluation uses stab where pop is required (regret against pop)
)


def active(name: str) -> bool:
    if name not in KNOWN:
        raise ValueError(f"unknown mutation {name!r}")
    return os.environ.get(ENV, "") == name


def assert_no_mutation() -> None:
    value = os.environ.get(ENV, "")
    if value:
        raise RuntimeError(f"{ENV}={value!r} is set; production runs refuse to start")
