"""pytest plugin: apply the F1 mutation named in $F1_MUTATION before any test module is imported.

Usage: F1_MUTATION=wrong_prior python -m pytest -p dynaicl_families.stage2.f1_plugin tests_stage1/test_f1_references.py
Lets the frozen F1 tests act as detectors without editing them."""

from __future__ import annotations


def pytest_configure(config):
    from dynaicl_families.stage2.f1_mutations import apply_from_env
    name = apply_from_env()
    config._f1_mutation = name


def pytest_report_header(config):
    return f"F1 mutation: {getattr(config, '_f1_mutation', None) or 'none (clean)'}"
