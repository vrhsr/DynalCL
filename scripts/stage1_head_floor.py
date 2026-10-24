"""Head-family floor (plan v2 section 4.2): how well can an m-component Gaussian mixture represent each reference's
one-step predictive? For each context, fit q_m minimising KL(p || q_m) by weighted EM on the y-quadrature nodes of p
(EM on the cross-entropy sum_i w_i p(y_i) log q(y_i), which equals KL minimisation up to the entropy of p), then report
the KL floor. References only; CPU; contexts from the frozen generate_split / make_context path (seed role
stage1_head_floor = 70201, never used elsewhere).

The fitted KL is an UPPER bound on the true floor (EM finds a local optimum; two starts; m = 1 is the exact
moment-matched Gaussian; the floor for m is min over m' <= m because the families are nested).
Decision rule (pre-registered in PREREG_stage1 section 4): the head uses the smallest m in {1, 2, 4, 8} whose mean
floor is <= epsilon / 10 = 0.001 nats in every evaluated cell.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.rng import NamedStreams  # noqa: E402
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec  # noqa: E402
from dynaicl.systems.library import build_library_from_prior  # noqa: E402
from dynaicl_families.ar1_known_sigma import (ContextStats, FiniteLibrary, population_prior,  # noqa: E402
                                              stability_prior)
from dynaicl_families.sampling import (OutOfSupportCondition, ProbeGridCondition,  # noqa: E402
                                       contexts_and_targets, simulate)
from dynaicl_families.separability import POP_FROZEN, reference_window  # noqa: E402

SEED = 70201


NODES = 400                # per context: 50 panels x 8 Gauss-Legendre nodes over the reference's own window


def nodes_batch(lo, hi, q=8, panels=NODES // 8):
    """(C, NODES) nodes and weights; each context gets its own window [lo_i, hi_i]."""
    x, w = np.polynomial.legendre.leggauss(q)
    frac = np.arange(panels + 1) / panels
    edges = lo[:, None] + (hi - lo)[:, None] * frac[None, :]
    half, mid = 0.5 * np.diff(edges, axis=1), 0.5 * (edges[:, 1:] + edges[:, :-1])
    y = (mid[:, :, None] + half[:, :, None] * x).reshape(lo.size, -1)
    wt = (half[:, :, None] * w).reshape(lo.size, -1)
    return y, wt


def _mix_logpdf(y, pi, mu, var):
    lc = (np.log(pi)[:, None, :] - 0.5 * np.log(2 * np.pi * var)[:, None, :]
          - 0.5 * (y[:, :, None] - mu[:, None, :]) ** 2 / var[:, None, :])
    return lc, np.logaddexp.reduce(lc, axis=2)


def moment_matched_floor(y, wp, logp):
    """m = 1: the Gaussian minimising KL(p || q) matches p's mean and variance (DERIVED: standard result)."""
    mean = (wp * y).sum(axis=1)
    var = (wp * (y - mean[:, None]) ** 2).sum(axis=1)
    lq = -0.5 * np.log(2 * np.pi * var)[:, None] - 0.5 * (y - mean[:, None]) ** 2 / var[:, None]
    return (wp * (logp - lq)).sum(axis=1)


def fit_floor_batch(y, wp, logp, m, rng, iters=400, tol=1e-12):
    """Weighted EM vectorised over contexts, two starts (components at p's quantiles; random), early stop when the
    largest per-context change of the objective is below ``tol``. Returns the per-context best KL(p || q_m), an UPPER
    bound on the true floor (EM finds a local optimum)."""
    c = y.shape[0]
    mean_p = (wp * y).sum(axis=1)
    sd_p = np.sqrt((wp * (y - mean_p[:, None]) ** 2).sum(axis=1))
    cdf = np.cumsum(wp, axis=1)
    best = np.full(c, np.inf)
    for start in ("quantile", "random"):
        if start == "quantile":
            qs = (np.arange(m) + 0.5) / m
            idx = np.stack([np.searchsorted(cdf[i], qs).clip(0, y.shape[1] - 1) for i in range(c)])
            mu = np.take_along_axis(y, idx, axis=1)
        else:
            mu = mean_p[:, None] + sd_p[:, None] * rng.standard_normal((c, m))
        var = np.repeat((sd_p[:, None] / m) ** 2, m, axis=1)
        pi = np.full((c, m), 1.0 / m)
        prev = np.full(c, np.inf)
        for _ in range(iters):
            lc, lq = _mix_logpdf(y, pi, mu, var)
            obj = (wp * (logp - lq)).sum(axis=1)
            if np.max(np.abs(prev - obj)) < tol:
                break
            prev = obj
            r = np.exp(lc - lq[:, :, None]) * wp[:, :, None]
            nk = r.sum(axis=1) + 1e-300
            pi = nk / nk.sum(axis=1, keepdims=True)
            mu = (r * y[:, :, None]).sum(axis=1) / nk
            var = np.maximum((r * (y[:, :, None] - mu[:, None, :]) ** 2).sum(axis=1) / nk,
                             1e-6 * sd_p[:, None] ** 2)
        _, lq = _mix_logpdf(y, pi, mu, var)
        best = np.minimum(best, (wp * (logp - lq)).sum(axis=1))
    return best


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--contexts", type=int, default=150)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    streams = NamedStreams(SEED)
    lib_atoms = {k: build_library_from_prior(POP_FROZEN, k, streams,
                                             stream_name="stage1_head_floor_library").coefficients
                 for k in (2, 8, 32, 256)}
    refs = {"pop": population_prior(), "stab": stability_prior(), "lib2": FiniteLibrary(lib_atoms[2]),
            "lib8": FiniteLibrary(lib_atoms[8]), "lib32": FiniteLibrary(lib_atoms[32]),
            "lib256": FiniteLibrary(lib_atoms[256])}
    rows = []
    for r in (0.25, 1.0, 4.0):
        x0 = InitialStateSpec(0.0, r)
        conds = {"HELD": ContinuousPriorCondition(POP_FROZEN, x0),
                 "PROBE": ProbeGridCondition(tuple(round(-0.95 + 0.05 * i, 2) for i in range(39)), 1.0, x0),
                 "OOS": OutOfSupportCondition(0.95, 0.999, 1.0, x0)}
        for set_name, cond in conds.items():
            split = simulate(cond, streams, args.contexts, 22)
            for n in (1, 3, 5, 20):
                ctx, _ = contexts_and_targets(split, n)
                st = ContextStats.from_contexts(ctx)
                for ref_name, ref in refs.items():
                    lo, hi = reference_window(ref, st)
                    y, w = nodes_batch(lo, hi)
                    logp = ref.logpdf(st, y)
                    wp = w * np.exp(logp)
                    wp = wp / wp.sum(axis=1, keepdims=True)
                    floors = {1: moment_matched_floor(y, wp, logp)}
                    prev = floors[1]
                    for m in (2, 4, 8):
                        # nested families: an m-mixture can reproduce any m'-mixture with m' < m, so the floor is
                        # min(EM result, previous floor); EM is skipped where the previous floor is already < 5e-4
                        if prev.max() < 5e-4:
                            floors[m] = prev.copy()
                        else:
                            floors[m] = np.minimum(prev, fit_floor_batch(y, wp, logp, m, rng))
                        prev = floors[m]
                    for m, f in floors.items():
                        f = np.asarray(f)
                        rows.append({"set": set_name, "r": r, "n": n, "ref": ref_name, "m": m, "mean_floor": f.mean(),
                                     "p95_floor": float(np.quantile(f, 0.95)), "max_floor": f.max(),
                                     "contexts": f.size})
                print(f"r={r} {set_name} done", flush=True)
    with open(out / "head_floor.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    worst = {m: max(r_["mean_floor"] for r_ in rows if r_["m"] == m) for m in (1, 2, 4, 8)}
    chosen = next((m for m in (1, 2, 4, 8) if worst[m] <= 0.001), None)
    print("worst mean floor per m:", {m: f"{v:.2e}" for m, v in worst.items()}, "-> chosen m:", chosen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
