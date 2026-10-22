"""Stage 0.6 frozen analysis and decision code (docs/PREREG_stage06.md sections 5-8).

Pure functions of per-item arrays. No file I/O, no seeds of its own: the caller passes the bootstrap generator.
The same code runs on the confirmatory per-item results and on the synthetic data of the decision dry run.

Notation. A cell is (q, h, r). ``gain_items[cell]`` is an (N, len(ns)) array of per-item paired gains
(population log score - stability log score, nats/forecast) for N systems (rows) and every context length n in
``ns`` (columns). Systems are the independent units; the contexts of one system are not independent.

* Primary estimand: gain(q, h, r) = mean over systems of the within-system mean over n in L (equal weight per n).
* Noise increment: increment(q, h, r) = gain(q, h, r) - gain(0, h, r), formed per system (paired).
* Family: 18 gains + 18 increments = 36 contrasts per replicate.
* Uncertainty: cluster bootstrap over whole systems. The SAME resampled system indices are applied to every
  contrast in a draw. Studentized max-|t| statistic, two-sided simultaneous band at familywise level 1 - alpha per replicate.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

FLOAT = np.float64
Z975 = float(stats.norm.isf(0.025))       # for the order-statistic interval of the critical value


class BootstrapFailure(RuntimeError):
    """A bootstrap draw produced a non-finite or zero studentization, or the critical value missed its MC tolerance.
    Draws are never discarded: any failure makes the replicate's analysis invalid (verdict BLOCKED)."""


# ------------------------------------------------------------------------------------------- estimands


def long_context_average(items: np.ndarray, ns: tuple[int, ...], long_context: tuple[int, ...]) -> np.ndarray:
    """(N, len(ns)) per-item gains -> (N,) per-system mean over n in L. Each n in L has weight 1 / |L|."""
    items = np.asarray(items, dtype=FLOAT)
    if items.ndim != 2 or items.shape[1] != len(ns):
        raise ValueError(f"expected (N, {len(ns)}) items, got {items.shape}")
    cols = [list(ns).index(n) for n in long_context]
    x = items[:, cols]
    if not np.all(np.isfinite(x)):
        raise FloatingPointError("non-finite per-item gain in the long-context region")
    return x.mean(axis=1)


def contrast_names(qs: tuple[float, ...], hs: tuple[int, ...], rs: tuple[float, ...]) -> list[tuple]:
    """The 36 primary contrasts in a fixed order: all gains, then all noise increments (positive q only)."""
    pos = qs[1:]
    return ([("gain", q, h, r) for q in pos for h in hs for r in rs]
            + [("increment", q, h, r) for q in pos for h in hs for r in rs])


def contrast_table(sys_gain: dict, qs, hs, rs) -> tuple[list[tuple], np.ndarray, list[tuple]]:
    """Per-system contrast matrix X (N, K) for every contrast whose cells are all present, plus the missing contrasts."""
    sizes = {np.asarray(v).shape for v in sys_gain.values()}
    if len(sizes) > 1:
        raise ValueError(f"cells disagree on the number of systems: {sorted(sizes)}")
    names, cols, missing = [], [], []
    for name in contrast_names(qs, hs, rs):
        kind, q, h, r = name
        need = [(q, h, r)] + ([(qs[0], h, r)] if kind == "increment" else [])
        if not all(c in sys_gain for c in need):
            missing.append(name)
            continue
        col = np.asarray(sys_gain[(q, h, r)], dtype=FLOAT)
        if kind == "increment":
            col = col - np.asarray(sys_gain[(qs[0], h, r)], dtype=FLOAT)
        names.append(name)
        cols.append(col)
    X = np.column_stack(cols) if cols else np.empty((0, 0))
    return names, X, missing


# ------------------------------------------------------------------------------------------- bootstrap


def bootstrap_draws(X: np.ndarray, n_draws: int, rng: np.random.Generator, chunk: int):
    """Yield (theta_star (b, K), se_star (b, K)) for successive chunks of cluster-bootstrap draws.

    One draw resamples N whole systems with replacement. Its multiplicity vector is applied to EVERY column of X,
    so all contrasts in a draw share the same resampled systems. se_star is the per-draw standard error,
    sd_star (ddof = 1) / sqrt(N), computed from the same resample (studentization)."""
    N = X.shape[0]
    theta = X.mean(axis=0)
    Xc = X - theta
    Xc2 = Xc * Xc
    done = 0
    while done < n_draws:
        b = min(chunk, n_draws - done)
        idx = rng.integers(0, N, size=(b, N))
        counts = np.bincount((idx + (np.arange(b) * N)[:, None]).ravel(), minlength=b * N).reshape(b, N).astype(FLOAT)
        m1 = counts @ Xc / N
        m2 = counts @ Xc2 / N
        var = (m2 - m1 * m1) * N / (N - 1)
        yield theta + m1, np.sqrt(np.maximum(var, 0.0) / N)
        done += b


def max_t_statistics(X: np.ndarray, n_draws: int, rng: np.random.Generator, chunk: int) -> np.ndarray:
    """T*_b = max_k |theta*_bk - theta_k| / se*_bk over the K contrasts. Raises BootstrapFailure; never drops a draw."""
    theta = X.mean(axis=0)
    out = []
    for th, se in bootstrap_draws(X, n_draws, rng, chunk):
        if not (np.all(np.isfinite(th)) and np.all(np.isfinite(se)) and np.all(se > 0)):
            raise BootstrapFailure("bootstrap draw with a non-finite or zero standard error")
        out.append(np.max(np.abs(th - theta) / se, axis=1))
    return np.concatenate(out)


def critical_value(T: np.ndarray, alpha: float) -> dict:
    """c = the k-th smallest T*, k = ceil(B (1 - alpha)). Monte Carlo error: the distribution-free 95% interval for the
    (1 - alpha) quantile from order statistics at ranks B p -/+ 1.96 sqrt(B p (1 - p)); relative error = half its
    length / c (equivalently, a fraction of every band half-width, since half-width = c x SE)."""
    B = T.size
    p = 1.0 - alpha
    Ts = np.sort(T)
    k = int(math.ceil(B * p))
    c = float(Ts[k - 1])
    if not (math.isfinite(c) and c > 0):
        raise BootstrapFailure(f"degenerate critical value {c}")
    half = Z975 * math.sqrt(B * p * (1 - p))
    k_lo, k_hi = max(1, int(math.floor(B * p - half))), min(B, int(math.ceil(B * p + half)))
    lo, hi = float(Ts[k_lo - 1]), float(Ts[k_hi - 1])
    return {"c": c, "draws": B, "rank": k, "c_mc_interval": [lo, hi], "rel_mc_error": (hi - lo) / (2 * c)}


def simultaneous_band(X: np.ndarray, alpha: float, schedule: tuple[int, ...], chunk: int, rng: np.random.Generator,
                      rel_tol: float) -> dict:
    """Studentized max-|t| simultaneous band theta_k +/- c se_k, se_k = sd_k / sqrt(N). Draws follow the frozen
    schedule: start at schedule[0]; if the critical value's relative MC error exceeds rel_tol, continue the SAME
    generator up to the next total. Failing at the last total raises BootstrapFailure."""
    if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] < 1:
        raise BootstrapFailure(f"contrast matrix has shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise BootstrapFailure("non-finite per-system contrast")
    N = X.shape[0]
    theta = X.mean(axis=0)
    se = X.std(axis=0, ddof=1) / math.sqrt(N)
    if not (np.all(np.ptp(X, axis=0) > 0) and np.all(se > 0)):
        raise BootstrapFailure("a contrast is constant across systems (zero standard error)")
    T = np.empty(0)
    cv = None
    for total in schedule:
        T = np.concatenate([T, max_t_statistics(X, total - T.size, rng, chunk)])
        cv = critical_value(T, alpha)
        if cv["rel_mc_error"] <= rel_tol:
            break
    else:
        raise BootstrapFailure(f"critical-value MC error {cv['rel_mc_error']:.4f} > {rel_tol} after {T.size} draws")
    c = cv["c"]
    return {"theta": theta, "se": se, "lo": theta - c * se, "hi": theta + c * se, **cv}


# ------------------------------------------------------------------------------------------- flags / replicate


def cell_flags(names: list[tuple], band: dict, delta: float) -> dict:
    """Per positive-noise cell: G+ (gain lower bound > delta), I+ (increment lower bound > 0), G- (gain upper bound
    < delta), NEG (gain upper bound < 0), SUPPORTED = G+ and I+. Only cells with both contrasts present are returned."""
    pos = {name: i for i, name in enumerate(names)}
    out = {}
    for (kind, q, h, r), i in pos.items():
        if kind != "gain" or ("increment", q, h, r) not in pos:
            continue
        j = pos[("increment", q, h, r)]
        g_lo, g_hi, i_lo = float(band["lo"][i]), float(band["hi"][i]), float(band["lo"][j])
        gp, ip = g_lo > delta, i_lo > 0.0
        out[(q, h, r)] = {"G+": gp, "I+": ip, "G-": g_hi < delta, "NEG": g_hi < 0.0, "SUPPORTED": gp and ip}
    return out


def analyze_replicate(gain_items: dict, ns: tuple[int, ...], long_context: tuple[int, ...], qs, hs, rs,
                      delta: float, alpha: float, schedule: tuple[int, ...], chunk: int, rel_tol: float,
                      rng: np.random.Generator) -> dict:
    """One replicate: L-averages, the 36-contrast band, flags. Any failure is returned (never raised), with ok = False."""
    res = {"ok": False, "error": None, "missing": [], "flags": {}, "contrasts": []}
    try:
        sys_gain = {cell: long_context_average(v, ns, long_context) for cell, v in gain_items.items()}
        names, X, missing = contrast_table(sys_gain, qs, hs, rs)
        res["missing"] = missing
        band = simultaneous_band(X, alpha, schedule, chunk, rng, rel_tol)
    except (BootstrapFailure, FloatingPointError, ValueError) as exc:
        res["error"] = f"{type(exc).__name__}: {exc}"
        return res
    res["flags"] = cell_flags(names, band, delta)
    res["contrasts"] = [{"kind": k, "q": q, "h": h, "r": r, "estimate": float(band["theta"][i]),
                         "se": float(band["se"][i]), "lo": float(band["lo"][i]), "hi": float(band["hi"][i])}
                        for i, (k, q, h, r) in enumerate(names)]
    res["critical_value"] = {k: band[k] for k in ("c", "draws", "rank", "c_mc_interval", "rel_mc_error")}
    res["n_systems"] = int(X.shape[0])
    res["ok"] = True
    return res


# ------------------------------------------------------------------------------------------- decision


def adjacent_pairs(qs: tuple[float, ...]) -> list[tuple[float, float]]:
    pos = list(qs[1:])
    return list(zip(pos, pos[1:]))


def decide(replicates: list[dict], critical: dict, qs, hs, rs, min_scales: int) -> dict:
    """Frozen decision rule (PREREG_stage06 section 7). Order: BLOCKED, GO, STOP, REVISE.

    BLOCKED: a critical check failed, a replicate's analysis failed (incl. bootstrap), a primary cell is missing in
    either replicate, or a primary gain is significantly negative (adjusted upper bound < 0) in either replicate.
    Q(h, r): some adjacent positive-noise pair (q_i, q_i+1) has both cells SUPPORTED in both replicates.
    GO: for some h, Q(h, r) holds for at least ``min_scales`` scales r.
    STOP: G- for all 18 gains in both replicates.
    REVISE: otherwise (valid but narrower, or inconclusive)."""
    cells = [(q, h, r) for q in qs[1:] for h in hs for r in rs]
    pairs = adjacent_pairs(qs)
    reasons = []
    if len(replicates) != 2:
        reasons.append(f"expected 2 replicates, got {len(replicates)}")
    failed = sorted(k for k, v in critical.items() if not v)
    if failed:
        reasons.append("critical checks failed: " + ", ".join(failed))
    for i, rep in enumerate(replicates):
        tag = f"R{i + 1}"
        if not rep.get("ok"):
            reasons.append(f"{tag}: analysis invalid ({rep.get('error')})")
        miss = [c for c in cells if c not in rep.get("flags", {})]
        if miss:
            reasons.append(f"{tag}: {len(miss)} missing primary cells, e.g. {miss[0]}")
        neg = [c for c in cells if rep.get("flags", {}).get(c, {}).get("NEG")]
        if neg:
            reasons.append(f"{tag}: significantly negative gain in {neg}")
    Q, strict = {}, {}
    if reasons:
        verdict = "BLOCKED"
    else:
        def supported(c):
            return all(rep["flags"][c]["SUPPORTED"] for rep in replicates)
        Q = {(h, r): [p for p in pairs if all(supported((q, h, r)) for q in p)] for h in hs for r in rs}
        go_h = [h for h in hs if sum(bool(Q[(h, r)]) for r in rs) >= min_scales]
        if go_h:
            verdict = "GO"
            reasons.append(f"Q(h, r) holds for >= {min_scales} scales at h in {go_h}")
        elif all(rep["flags"][c]["G-"] for rep in replicates for c in cells):
            verdict = "STOP"
            reasons.append("all 18 gains have adjusted upper bound < delta in both replicates")
        else:
            verdict = "REVISE"
            reasons.append("valid, but neither the GO nor the STOP condition holds")
        strict = {h: [p for p in pairs if sum(p in Q[(h, r)] for r in rs) >= min_scales] for h in hs}
    return {"verdict": verdict, "reasons": reasons,
            "Q": {f"h={h}|r={r}": [list(p) for p in v] for (h, r), v in Q.items()},
            "strict_same_pair": {f"h={h}": [list(p) for p in v] for h, v in strict.items()},
            "strict_variant_holds": any(bool(v) for v in strict.values())}


# ------------------------------------------------------------------------------------------- descriptive


def n_curves(gain_items: np.ndarray, ns: tuple[int, ...]) -> list[dict]:
    """Descriptive per-n mean gain and its system-level SE (secondary; not used in the verdict)."""
    x = np.asarray(gain_items, dtype=FLOAT)
    N = x.shape[0]
    return [{"n": int(n), "mean": float(x[:, j].mean()), "se": float(x[:, j].std(ddof=1) / math.sqrt(N))}
            for j, n in enumerate(ns)]


# ------------------------------------------------------------------------------------------- Tier-2


def tier2_criterion(n_tests: int, alpha: float, power: float, delta: float) -> dict:
    """Two-sided Bonferroni cutoff over n_tests, and the precision condition: the combined SE must not exceed
    delta / (z_crit + z_power), i.e. a discrepancy of size delta would be detected with probability >= power."""
    z_crit = float(stats.norm.isf(alpha / (2 * n_tests)))
    z_pow = float(stats.norm.ppf(power))
    return {"n_tests": n_tests, "z_crit": z_crit, "z_power": z_pow, "max_combined_se": delta / (z_crit + z_pow)}


def tier2_compare(stage06: dict, stage05: dict, alpha: float, power: float, delta: float) -> dict:
    """Fresh-seed zero-noise reproduction. ``stage06[(rep, r, h)]`` and ``stage05[(r, h)]`` are per-system means of the
    paired gain over the Tier-2 context lengths at q = 0. Each Stage 0.6 replicate is compared with the pooled Stage 0.5
    systems: z = (m06 - m05) / sqrt(se06^2 + se05^2). Outcome: FAIL if any |z| > z_crit; else UNINFORMATIVE if any
    combined SE exceeds the precision bound (never reported as a pass); else PASS."""
    crit = tier2_criterion(len(stage06), alpha, power, delta)
    rows = []
    for (rep, r, h), x in sorted(stage06.items()):
        y = stage05[(r, h)]
        m6, s6 = float(np.mean(x)), float(np.std(x, ddof=1) / math.sqrt(len(x)))
        m5, s5 = float(np.mean(y)), float(np.std(y, ddof=1) / math.sqrt(len(y)))
        se = math.sqrt(s6 * s6 + s5 * s5)
        z = (m6 - m5) / se
        rows.append({"replicate": rep, "r": r, "h": h, "stage06_mean": m6, "stage06_se": s6, "stage05_mean": m5,
                     "stage05_se": s5, "combined_se": se, "z": z, "fail": abs(z) > crit["z_crit"],
                     "informative": se <= crit["max_combined_se"]})
    if any(x["fail"] for x in rows):
        outcome = "FAIL"
    elif not all(x["informative"] for x in rows):
        outcome = "UNINFORMATIVE"
    else:
        outcome = "PASS"
    return {"outcome": outcome, "criterion": crit, "rows": rows}
