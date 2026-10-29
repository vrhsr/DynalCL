"""pytest plugin: apply the F2 mutation named in $F2_MUTATION before any test module is imported.

Usage: F2_MUTATION=wrong_prior python -m pytest -p dynaicl_families.stage2.f2_plugin tests_stage2/test_f2_references.py"""

from __future__ import annotations


def pytest_configure(config):
    from dynaicl_families.stage2.f2_mutations import apply_from_env
    config._f2_mutation = apply_from_env()


def pytest_report_header(config):
    return f"F2 mutation: {getattr(config, '_f2_mutation', None) or 'none (clean)'}"
