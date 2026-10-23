"""Stage 1A inference and classification (pure numpy). Used by the operating-characteristic study and the real analysis.

Data model. Each family statistic k is an array X_k of shape (M, N_k): one row per trained model, aligned by seed
index i across arms (so a contrast between arms is formed per seed, which keeps the pairing), one column per evaluation
system. Columns of statistics that share an evaluation set refer to the same systems (common random numbers).

Estimate: theta_k = mean of X_k. Two-level standard error (DERIVED, conservative):
    se_k^2 = var(row means) / M + var(column means) / N_k.
For X_mj = mu + u_m + e_j + eta_mj (seed effect u, system effect e, interaction eta) the exact variance of the grand
mean is s_u^2/M + s_e^2/N + s_eta^2/(MN); the estimator above has expectation s_u^2/M + s_e^2/N + 2 s_eta^2/(MN),
so it is conservative by s_eta^2/(MN).

Simultaneous band: theta_k +/- c se_k, with c the (1 - alpha) quantile of max_k |theta*_k - theta_k| / se*_k over a
hierarchical (Multi-)bootstrap that resamples models (one multiplicity vector over seed indices, shared by all
statistics) and systems (one multiplicity vector per evaluation set, shared by all statistics on that set). A Gaussian
approximation of the same quantile (``critical_value_gaussian``) is used for operating-characteristic simulations, where
a bootstrap inside each of thousands of simulated studies is unaffordable; the two are compared in tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

FLOAT = np.float64


@dataclass(frozen=True)
class Statistic:
    name: str
    values: np.ndarray        # (M, N)
    item_set: str             # evaluation set id; systems are resampled jointly within a set

    def __post_init__(self) -> None:
        v = np.asarray(self.values, dtype=FLOAT)
        if v.ndim != 2 or v.shape[0] < 2 or v.shape[1] < 2 or not np.all(np.isfinite(v)):
            raise ValueError(f"statistic {self.name}: need a finite (M >= 2, N >= 2) array")
        object.__setattr__(self, "values", v)


def two_level(values: np.ndarray, w: np.ndarray | None = None, v: np.ndarray | None = None) -> tuple[float, float]:
    """(theta, se) of the (optionally multiplicity-weighted) grand mean, with the two-level SE above."""
    x = values
    m_n, n_n = x.shape
    w = np.ones(m_n) if w is None else w
    v = np.ones(n_n) if v is None else v
    sw, sv = w.sum(), v.sum()
    rows = (x @ v) / sv                      # (M,) row means under item weights
    cols = (w @ x) / sw                      # (N,) column means under model weights
    theta = float(w @ rows / sw)
    var_r = float(w @ (rows - theta) ** 2 / (sw - 1.0))
    var_c = float(v @ (cols - theta) ** 2 / (sv - 1.0))
    se = math.sqrt(var_r / sw + var_c / sv)
    return theta, se


def estimates(stats: list[Statistic]) -> dict[str, tuple[float, float]]:
    return {s.name: two_level(s.values) for s in stats}


def _check_shapes(stats: list[Statistic]) -> tuple[int, dict[str, int]]:
    m = {s.values.shape[0] for s in stats}
    if len(m) != 1:
        raise ValueError("all statistics must have the same number of model rows (aligned seed indices)")
    sets: dict[str, int] = {}
    for s in stats:
        if sets.setdefault(s.item_set, s.values.shape[1]) != s.values.shape[1]:
            raise ValueError(f"item set {s.item_set} has inconsistent column counts")
    return m.pop(), sets


def critical_value_bootstrap(stats: list[Statistic], alpha: float, draws: int, rng: np.random.Generator,
                             ) -> tuple[float, dict]:
    """Studentized max-|t| critical value from the hierarchical bootstrap. Returns (c, diagnostics).

    Draws are never discarded; a non-finite or zero per-draw SE makes the analysis invalid (raises)."""
    m_n, sets = _check_shapes(stats)
    base = estimates(stats)
    tmax = np.empty(draws, dtype=FLOAT)
    for b in range(draws):
        w = rng.multinomial(m_n, np.full(m_n, 1.0 / m_n)).astype(FLOAT)
        vs = {k: rng.multinomial(n, np.full(n, 1.0 / n)).astype(FLOAT) for k, n in sets.items()}
        t = 0.0
        for s in stats:
            th, se = two_level(s.values, w, vs[s.item_set])
            if not (math.isfinite(se) and se > 0):
                raise FloatingPointError(f"bootstrap draw {b}: invalid SE for {s.name}")
            t = max(t, abs(th - base[s.name][0]) / se)
        tmax[b] = t
    k = int(math.ceil(draws * (1.0 - alpha))) - 1
    c = float(np.sort(tmax)[k])
    return c, {"draws": draws, "alpha": alpha, "tmax_median": float(np.median(tmax))}


def covariance_of_estimates(stats: list[Statistic]) -> np.ndarray:
    """Two-level covariance of the K estimates: cov(row means)/M + cov(column means)/N for statistics on the same
    item set (columns are the same systems), and only the model part across different item sets."""
    m_n, _ = _check_shapes(stats)
    rows = np.stack([s.values.mean(axis=1) for s in stats])          # (K, M)
    cov = np.cov(rows) / m_n
    cov = np.atleast_2d(cov)
    for a, sa in enumerate(stats):
        ca = sa.values.mean(axis=0)
        for b, sb in enumerate(stats):
            if sa.item_set == sb.item_set:
                cb = sb.values.mean(axis=0)
                cov[a, b] += float(np.cov(ca, cb)[0, 1]) / ca.size
    return cov


def critical_value_gaussian(cov: np.ndarray, alpha: float, rng: np.random.Generator, draws: int = 20000) -> float:
    """(1 - alpha) quantile of max_k |Z_k| / sd_k for Z ~ N(0, cov) (Monte Carlo)."""
    sd = np.sqrt(np.diag(cov))
    corr = cov / np.outer(sd, sd)
    evals, evecs = np.linalg.eigh(corr)
    root = evecs * np.sqrt(np.clip(evals, 0.0, None))
    z = rng.standard_normal((draws, corr.shape[0])) @ root.T
    tmax = np.abs(z).max(axis=1)
    return float(np.quantile(tmax, 1.0 - alpha, method="higher"))


# ------------------------------------------------------------------------------------------- classification

@dataclass(frozen=True)
class Band:
    estimate: float
    lo: float
    hi: float


def band(theta: float, se: float, c: float) -> Band:
    return Band(theta, theta - c * se, theta + c * se)


def classify_q1_held(r_pop: Band, g: Band, gap: float, epsilon: float) -> str:
    """Q1 on held-out systems (plan v2 section 4.4). ``gap`` = Delta(c) = E[KL(pop || stab)] on the same systems.

    POP-LIKE: hi(R_pop) < Delta/2 and lo(G) > Delta/2.
    STAB-LIKE: lo(R_pop) > Delta/2 and |G| < Delta/2 at both band ends.
    WORSE-THAN-STAB: lo(R_pop) > Delta + epsilon.
    INCONCLUSIVE otherwise."""
    half = gap / 2.0
    if r_pop.lo > gap + epsilon:
        return "WORSE-THAN-STAB"
    if r_pop.hi < half and g.lo > half:
        return "POP-LIKE"
    if r_pop.lo > half and g.lo > -half and g.hi < half:
        return "STAB-LIKE"
    return "INCONCLUSIVE"


def classify_behavioural(dist: dict[str, Band], contrasts: dict[tuple[str, str], Band],
                         separation: dict[tuple[str, str], float]) -> str:
    """Nearest-reference rule for probe / out-of-support sets and Q2 (plan v2 section 4.4).

    ``dist[X]`` = band of D_X = E[KL(X || model)]; ``contrasts[(Y, X)]`` = band of D_Y - D_X; ``separation[(X, Y)]`` =
    min(E KL(X||Y), E KL(Y||X)) for the references on the same systems (symmetric key order irrelevant).
    X-LIKE if hi(D_X) < s_X / 2, with s_X the smallest separation between X and any other reference, and
    lo(D_Y - D_X) > 0 for every other reference Y. NEITHER if lo(D_X) > s_X / 2 for every X. Else INCONCLUSIVE."""
    refs = list(dist)

    def sep(a, b):
        return separation.get((a, b), separation.get((b, a)))

    hits = []
    for x in refs:
        s_x = min(sep(x, y) for y in refs if y != x)
        if dist[x].hi < s_x / 2.0 and all(contrasts[(y, x)].lo > 0.0 for y in refs if y != x):
            hits.append(x)
    if len(hits) == 1:
        return f"{hits[0].upper()}-LIKE"
    if len(hits) > 1:            # impossible when the contrasts are coherent; guard anyway
        return "INCONCLUSIVE"
    if all(dist[x].lo > min(sep(x, y) for y in refs if y != x) / 2.0 for x in refs):
        return "NEITHER"
    return "INCONCLUSIVE"


def classify_memorisation(dist: dict[str, Band], contrasts: dict[tuple[str, str], Band],
                          separation: dict[tuple[str, str], float], general: tuple[str, ...] = ("pop", "stab")) -> str:
    """Q2 primary rule: memorising (library posterior) vs generalising (population or context-only posterior).

    LIB-LIKE if hi(D_lib) < s / 2 with s = min over Y in ``general`` of sep(lib, Y), and lo(D_Y - D_lib) > 0 for
    every Y.
    GENERALISING if for some Y in ``general``: hi(D_Y) < sep(lib, Y) / 2 and lo(D_lib - D_Y) > 0.
    NEITHER if lo(D_lib) > s / 2 and lo(D_Y) > sep(lib, Y) / 2 for every Y. Else INCONCLUSIVE.
    Which generalising reference is nearer is a secondary question (``classify_behavioural``)."""
    def sep(a, b):
        return separation.get((a, b), separation.get((b, a)))

    s = min(sep("lib", y) for y in general)
    lib_like = dist["lib"].hi < s / 2.0 and all(contrasts[(y, "lib")].lo > 0.0 for y in general)
    gen_like = any(dist[y].hi < sep("lib", y) / 2.0 and contrasts[("lib", y)].lo > 0.0 for y in general)
    if lib_like and not gen_like:
        return "LIB-LIKE"
    if gen_like and not lib_like:
        return "GENERALISING"
    if lib_like and gen_like:
        return "INCONCLUSIVE"
    if dist["lib"].lo > s / 2.0 and all(dist[y].lo > sep("lib", y) / 2.0 for y in general):
        return "NEITHER"
    return "INCONCLUSIVE"
