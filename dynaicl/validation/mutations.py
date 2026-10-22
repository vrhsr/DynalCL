"""Negative controls (Section 5.G): inject known bugs and confirm the validation suite detects them.

Each mutation is a context manager that monkeypatches one module attribute and restores it on exit.
:func:`run_mutation_matrix` runs a set of checks under each mutation and records which detected it.
A detection is either a failed check or an exception (for example the matched-reference guard raising
UnmatchedReferenceError).

The pytest suite can also run under a mutation: set ``DYNAICL_MUTATION=<name>`` and tests/conftest.py
applies it for the whole session (see scripts/mutation_report.py --pytest).
"""

from __future__ import annotations

import contextlib
import time
import traceback

import numpy as np

from dynaicl.evaluation import harness
from dynaicl.references import conjugate, matched
from dynaicl.systems import ar1
from dynaicl.systems.conditions import LibraryCondition
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.priors import prior_from_spec


@contextlib.contextmanager
def _patched(module, attr: str, replacement):
    original = getattr(module, attr)
    setattr(module, attr, replacement)
    try:
        yield
    finally:
        setattr(module, attr, original)


@contextlib.contextmanager
def wrong_prior_variance():
    """P-GAUSS reference uses tau0 where tau0^2 is required (prior variance := prior sd)."""
    with _patched(conjugate, "gaussian_prior_moments", lambda prior: (float(prior.mu0), float(prior.tau0))):
        yield


@contextlib.contextmanager
def off_by_one_likelihood():
    """Transition pairs misaligned by one index: regressors x_0..x_{n-2} paired with targets x_2..x_n."""
    with _patched(ar1, "transition_pairs", lambda x: (x[:-2], x[2:])):
        yield


@contextlib.contextmanager
def future_leak():
    """The harness cuts contexts one step too long, so x_{n+1} (the h = 1 target) leaks into the context."""
    with _patched(harness, "make_context",
                  lambda trajectory, n: ContextWindow(np.array(trajectory[: n + 2], dtype=np.float64))):
        yield


def _unmatched_selector(original):
    def select(condition, settings=matched.QuadratureSettings()):
        if isinstance(condition, LibraryCondition):
            prior = prior_from_spec(condition.library.provenance["prior"])
            return matched.MatchedBayesReference(condition, matched.continuous_prior_predictor(prior, settings))
        return original(condition, settings)
    return select


@contextlib.contextmanager
def unmatched_reference():
    """Under E-LIB the harness selects the continuous-prior predictor as 'matched reference' (guard active)."""
    with _patched(matched, "matched_reference_for", _unmatched_selector(matched.matched_reference_for)):
        yield


@contextlib.contextmanager
def unmatched_reference_guard_bypassed():
    """As ``unmatched_reference``, with every fingerprint guard disabled, to test whether the STATISTICAL
    checks would catch the error without the guard."""
    with _patched(matched, "check_system_distribution", lambda *args, **kwargs: None), \
            _patched(matched, "matched_reference_for", _unmatched_selector(matched.matched_reference_for)):
        yield


MUTATIONS = {
    "wrong_prior_variance": wrong_prior_variance,
    "off_by_one_likelihood": off_by_one_likelihood,
    "future_leak": future_leak,
    "unmatched_reference": unmatched_reference,
    "unmatched_reference_guard_bypassed": unmatched_reference_guard_bypassed,
}


def run_check_safely(check) -> dict:
    t0 = time.time()
    try:
        result = check()
        status = "pass" if result.passed else "FAIL"
        detail = "" if result.passed else str({k: v for k, v in result.details.items() if k != "rows"})[:300]
    except Exception as exc:  # an exception is a detection (e.g. the matched-reference guard)
        status = f"ERROR:{type(exc).__name__}"
        detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()[:300]
    return {"status": status, "detail": detail, "seconds": round(time.time() - t0, 2)}


def run_mutation_matrix(checks: dict, mutations: dict = MUTATIONS, include_baseline: bool = True,
                        progress=None) -> dict:
    """{mutation: {check: {status, detail, seconds}}}; 'baseline' is the unmutated run.

    ``progress(mutation, check, row)`` is called after every check, so long runs show that they are alive.
    """
    def run_all(label):
        rows = {}
        for name, fn in checks.items():
            rows[name] = run_check_safely(fn)
            if progress is not None:
                progress(label, name, rows[name])
        return rows

    out = {}
    if include_baseline:
        out["baseline"] = run_all("baseline")
    for mname, mutation in mutations.items():
        with mutation():
            out[mname] = run_all(mname)
    return out


def detected(row: dict) -> bool:
    return row["status"] != "pass"
