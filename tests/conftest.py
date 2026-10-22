"""Session-wide mutation hook (Section 5.G).

``DYNAICL_MUTATION=<name> pytest`` runs the whole suite with one injected bug active, so
scripts/mutation_report.py can report exactly which tests detect which mutation. Without the
variable, nothing is patched.
"""

import os

import pytest

from dynaicl.validation.mutations import MUTATIONS

ACTIVE_MUTATION = os.environ.get("DYNAICL_MUTATION", "").strip()


@pytest.fixture(scope="session", autouse=True)
def _session_mutation():
    if not ACTIVE_MUTATION:
        yield
        return
    if ACTIVE_MUTATION not in MUTATIONS:
        raise pytest.UsageError(f"unknown DYNAICL_MUTATION {ACTIVE_MUTATION!r}; options: {sorted(MUTATIONS)}")
    with MUTATIONS[ACTIVE_MUTATION]():
        yield


def pytest_report_header(config):
    return f"DYNAICL_MUTATION={ACTIVE_MUTATION or '<none>'}"
