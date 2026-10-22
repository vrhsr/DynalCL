"""Stage 0.6 negative controls for the frozen analysis, decision, Tier-2 and runner code. Each mutation replaces one
function in memory (module attribute patch); files on disk are never modified. Each must be detected by a clean FAIL of
its intended check in checks_stage06_analysis (V20-V24)."""

from __future__ import annotations

import contextlib
import itertools
import math

import numpy as np
from scipy import stats

from dynaicl.experiments import stage06_analysis as A
from dynaicl.experiments import stage06_probe as P
from dynaicl.validation.mutations import _patched

_orig = {name: getattr(A, name) for name in ("long_context_average", "contrast_table", "bootstrap_draws",
                                             "critical_value", "max_t_statistics", "decide", "cell_flags",
                                             "tier2_criterion", "tier2_compare")}
_orig_p = {name: getattr(P, name) for name in ("verify_manifest", "load_unit", "check_seeds", "check_environment")}


# ------------------------------------------------------------------------------------------ estimand


@contextlib.contextmanager
def l_region_off_by_one():
    """The long-context average silently drops n = 10 (averages 11..40)."""
    def bad(items, ns, long_context):
        return _orig["long_context_average"](items, ns, tuple(long_context)[1:])
    with _patched(A, "long_context_average", bad):
        yield


@contextlib.contextmanager
def increment_wrong_baseline():
    """Noise increment taken against the next-lower noise level instead of the zero-noise control."""
    def bad(sys_gain, qs, hs, rs):
        names, X, missing = _orig["contrast_table"](sys_gain, qs, hs, rs)
        X = X.copy()
        for k, (kind, q, h, r) in enumerate(names):
            if kind == "increment":
                prev = qs[list(qs).index(q) - 1]
                X[:, k] = np.asarray(sys_gain[(q, h, r)]) - np.asarray(sys_gain[(prev, h, r)])
        return names, X, missing
    with _patched(A, "contrast_table", bad):
        yield


@contextlib.contextmanager
def items_as_independent_units():
    """(system, n) items treated as independent units: the 'per-system' vector is the flattened item matrix."""
    def bad(items, ns, long_context):
        cols = [list(ns).index(n) for n in long_context]
        return np.asarray(items, dtype=float)[:, cols].ravel()
    with _patched(A, "long_context_average", bad):
        yield


# ------------------------------------------------------------------------------------------ bootstrap


@contextlib.contextmanager
def independent_indices_per_contrast():
    """Each contrast is resampled with its own system indices (breaks the paired/cluster structure across contrasts)."""
    def bad(X, n_draws, rng, chunk):
        N, K = X.shape
        done = 0
        while done < n_draws:
            b = min(chunk, n_draws - done)
            th, se = np.empty((b, K)), np.empty((b, K))
            for k in range(K):
                idx = rng.integers(0, N, size=(b, N))
                s = X[:, k][idx]
                th[:, k], se[:, k] = s.mean(axis=1), s.std(axis=1, ddof=1) / math.sqrt(N)
            yield th, se
            done += b
    with _patched(A, "bootstrap_draws", bad):
        yield


@contextlib.contextmanager
def pointwise_critical_value():
    """The simultaneous critical value is replaced by the pointwise two-sided normal quantile."""
    def bad(T, alpha):
        cv = _orig["critical_value"](T, alpha)
        return {**cv, "c": float(stats.norm.isf(alpha / 2)), "rel_mc_error": 0.0}
    with _patched(A, "critical_value", bad):
        yield


@contextlib.contextmanager
def unstudentized_max_statistic():
    """max |theta* - theta| without dividing by the per-draw SE, then used as a multiplier of the SE."""
    def bad(X, n_draws, rng, chunk):
        theta = X.mean(axis=0)
        return np.concatenate([np.max(np.abs(th - theta), axis=1) for th, _ in A.bootstrap_draws(X, n_draws, rng, chunk)])
    with _patched(A, "max_t_statistics", bad):
        yield


@contextlib.contextmanager
def bootstrap_failures_dropped():
    """Degenerate draws (non-finite or zero SE) are silently discarded instead of failing the analysis."""
    def bad(X, n_draws, rng, chunk):
        theta = X.mean(axis=0)
        out = []
        for th, se in A.bootstrap_draws(X, n_draws, rng, chunk):
            keep = np.all(np.isfinite(th), axis=1) & np.all(np.isfinite(se) & (se > 0), axis=1)
            if keep.any():
                out.append(np.max(np.abs(th[keep] - theta) / se[keep], axis=1))
        return np.concatenate(out) if out else np.array([1.0])
    with _patched(A, "max_t_statistics", bad):
        yield


# ------------------------------------------------------------------------------------------ decision


def _decide_variant(replicates, critical, qs, hs, rs, min_scales, *, single_rep=False, ignore_neg=False,
                    ignore_missing=False, stop_any=False, min_scales_override=None):
    """A copy of the frozen decide() with one switchable bug."""
    cells = [(q, h, r) for q in qs[1:] for h in hs for r in rs]
    pairs = A.adjacent_pairs(qs)
    reasons = []
    if len(replicates) != 2:
        reasons.append("replicates")
    if [k for k, v in critical.items() if not v]:
        reasons.append("critical")
    for rep in replicates:
        if not rep.get("ok"):
            reasons.append("invalid")
        if not ignore_missing and [c for c in cells if c not in rep.get("flags", {})]:
            reasons.append("missing")
        if not ignore_neg and [c for c in cells if rep.get("flags", {}).get(c, {}).get("NEG")]:
            reasons.append("neg")
    if reasons:
        return {"verdict": "BLOCKED", "reasons": reasons, "Q": {}, "strict_same_pair": {}, "strict_variant_holds": False}
    agg = any if single_rep else all
    fl = lambda rep, c: rep["flags"].get(c, {"SUPPORTED": False, "G-": False})  # noqa: E731

    def supported(c):
        return agg(fl(rep, c)["SUPPORTED"] for rep in replicates)
    ms = min_scales if min_scales_override is None else min_scales_override
    Q = {(h, r): [p for p in pairs if all(supported((q, h, r)) for q in p)] for h in hs for r in rs}
    if [h for h in hs if sum(bool(Q[(h, r)]) for r in rs) >= ms]:
        verdict = "GO"
    elif (any if stop_any else all)(all(fl(rep, c)["G-"] for c in cells) for rep in replicates):
        verdict = "STOP"
    else:
        verdict = "REVISE"
    strict = {h: [p for p in pairs if sum(p in Q[(h, r)] for r in rs) >= ms] for h in hs}
    return {"verdict": verdict, "reasons": reasons, "Q": {}, "strict_same_pair": {},
            "strict_variant_holds": any(bool(v) for v in strict.values())}


def _decide_mutation(**kw):
    @contextlib.contextmanager
    def ctx():
        def bad(replicates, critical, qs, hs, rs, min_scales):
            return _decide_variant(replicates, critical, qs, hs, rs, min_scales, **kw)
        with _patched(A, "decide", bad):
            yield
    return ctx


go_single_replicate = _decide_mutation(single_rep=True)        # SUPPORTED in ONE replicate counts
go_one_scale = _decide_mutation(min_scales_override=1)          # Q(h, r) at one scale suffices
stop_single_replicate = _decide_mutation(stop_any=True)         # STOP from one replicate
negative_gain_not_blocked = _decide_mutation(ignore_neg=True)   # significantly negative gains ignored
missing_cell_not_blocked = _decide_mutation(ignore_missing=True)  # missing cells ignored


@contextlib.contextmanager
def go_non_adjacent_pairs():
    """Any two positive-noise levels count as a 'pair' (adjacency dropped)."""
    def bad(qs):
        return list(itertools.combinations(list(qs[1:]), 2))
    with _patched(A, "adjacent_pairs", bad):
        yield


@contextlib.contextmanager
def go_ignores_increment():
    """SUPPORTED = G+ only (the zero-noise control contrast I+ is ignored)."""
    def bad(names, band, delta):
        f = _orig["cell_flags"](names, band, delta)
        return {c: {**v, "SUPPORTED": v["G+"]} for c, v in f.items()}
    with _patched(A, "cell_flags", bad):
        yield


@contextlib.contextmanager
def gain_flag_uses_upper_bound():
    """G+ computed from the adjusted UPPER bound."""
    def bad(names, band, delta):
        f = _orig["cell_flags"](names, band, delta)
        pos = {n: i for i, n in enumerate(names)}
        out = {}
        for c, v in f.items():
            gp = float(band["hi"][pos[("gain", *c)]]) > delta
            out[c] = {**v, "G+": gp, "SUPPORTED": gp and v["I+"]}
        return out
    with _patched(A, "cell_flags", bad):
        yield


# ------------------------------------------------------------------------------------------ Tier-2


@contextlib.contextmanager
def tier2_unadjusted_cutoff():
    """The Tier-2 cutoff ignores the multiplicity adjustment (two-sided 1% for one test)."""
    def bad(n_tests, alpha, power, delta):
        return _orig["tier2_criterion"](1, alpha, power, delta)
    with _patched(A, "tier2_criterion", bad):
        yield


@contextlib.contextmanager
def tier2_uninformative_as_pass():
    """An imprecise Tier-2 comparison is reported as PASS."""
    def bad(stage06, stage05, alpha, power, delta):
        res = _orig["tier2_compare"](stage06, stage05, alpha, power, delta)
        return {**res, "outcome": "PASS" if res["outcome"] == "UNINFORMATIVE" else res["outcome"]}
    with _patched(A, "tier2_compare", bad):
        yield


# ------------------------------------------------------------------------------------------ runner


@contextlib.contextmanager
def manifest_file_hashes_not_checked():
    """Only the manifest's own hash is checked; the frozen files themselves are not."""
    def bad(manifest_path, expected_sha256, root=P.ROOT):
        import json
        sha = P.sha256_file(manifest_path)
        if sha != expected_sha256:
            raise P.Refusal("manifest fingerprint mismatch")
        return {**json.loads(open(manifest_path, encoding="utf-8").read()), "manifest_sha256": sha}
    with _patched(P, "verify_manifest", bad):
        yield


@contextlib.contextmanager
def checkpoint_checksum_not_checked():
    """Resumed checkpoints are loaded without verifying the arrays' SHA-256."""
    def bad(ckpt, unit, cfg, manifest_sha):
        real = P.sha256_file

        def lenient(path):
            if str(path).endswith(".npz"):
                import json
                js = str(path)[:-4] + ".json"
                return json.loads(open(js, encoding="utf-8").read())["npz_sha256"]
            return real(path)
        P.sha256_file = lenient
        try:
            return _orig_p["load_unit"](ckpt, unit, cfg, manifest_sha)
        finally:
            P.sha256_file = real
    with _patched(P, "load_unit", bad):
        yield


@contextlib.contextmanager
def seed_collision_not_checked():
    """Seeds shared between roles are not detected."""
    def bad(cfg, seed_manifest):
        import yaml
        roles = yaml.safe_load(open(seed_manifest, encoding="utf-8").read())["roles"]
        ev_role, _ = P.SEED_ROLES[cfg.experiment.mode]
        if not set(cfg.seeds.evaluation) | {cfg.seeds.bootstrap} <= set(roles[ev_role]["seeds"]):
            raise P.Refusal("seeds not allocated")
        return {}
    with _patched(P, "check_seeds", bad):
        yield


@contextlib.contextmanager
def environment_difference_ignored():
    """A different environment is accepted without qualification."""
    def bad(manifest, qualification, cfg, root=P.ROOT):
        return {"status": "identical", "environment": P.current_environment()}
    with _patched(P, "check_environment", bad):
        yield


MUTATIONS_STAGE06_ANALYSIS = {
    "l_region_off_by_one": l_region_off_by_one,
    "increment_wrong_baseline": increment_wrong_baseline,
    "items_as_independent_units": items_as_independent_units,
    "independent_indices_per_contrast": independent_indices_per_contrast,
    "pointwise_critical_value": pointwise_critical_value,
    "unstudentized_max_statistic": unstudentized_max_statistic,
    "bootstrap_failures_dropped": bootstrap_failures_dropped,
    "go_single_replicate": go_single_replicate,
    "go_non_adjacent_pairs": go_non_adjacent_pairs,
    "go_ignores_increment": go_ignores_increment,
    "go_one_scale": go_one_scale,
    "stop_single_replicate": stop_single_replicate,
    "negative_gain_not_blocked": negative_gain_not_blocked,
    "missing_cell_not_blocked": missing_cell_not_blocked,
    "gain_flag_uses_upper_bound": gain_flag_uses_upper_bound,
    "tier2_unadjusted_cutoff": tier2_unadjusted_cutoff,
    "tier2_uninformative_as_pass": tier2_uninformative_as_pass,
    "manifest_file_hashes_not_checked": manifest_file_hashes_not_checked,
    "checkpoint_checksum_not_checked": checkpoint_checksum_not_checked,
    "seed_collision_not_checked": seed_collision_not_checked,
    "environment_difference_ignored": environment_difference_ignored,
}
