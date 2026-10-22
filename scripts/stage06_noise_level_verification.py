"""Stage 0.6 Phase B: verify the proposed noise levels using PRIOR-BASED calculations only (no predictor scores, no effects).

    python scripts/stage06_noise_level_verification.py   -> docs/STAGE06_NOISE_LEVEL_VERIFICATION.md (+ .json)

1. Exact finite-n Fisher information I_n(a; q, r) = 0.5 tr(S^-1 S' S^-1 S') for y_0..y_n (latent x_0 prior included), with an
   analytic S'. Averaged over the population prior (truncated normal 0.4, 0.3 on +/-0.95; 80-node Gauss-Legendre).
2. Retention, under two definitions:
     R_ratio(n, r, q) = E_pi[I_n(a; q)] / E_pi[I_n(a; 0)]      (ratio of prior-averaged information)
     R_avg(n, r, q)   = E_pi[I_n(a; q) / I_n(a; 0)]            (prior average of per-a ratios; the Phase A definition)
3. Independent routes: (i) a finite-difference S'; (ii) the Monte Carlo variance of the score (a scalar Kalman log-likelihood,
   differentiated by central differences; design seed 61901).
4. A complementary Bayesian check: expected posterior variance of a under the prior predictive, with and without noise
   (production reference, validated in Phase B; design seed 61902), and the implied information ratio
   B = (1/EPV_q - 1/V_prior) / (1/EPV_0 - 1/V_prior).
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import integrate, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.references import kalman_quadrature as kq  # noqa: E402
from dynaicl.rng import NamedStreams  # noqa: E402
from dynaicl.systems.noisy import NoisyObservationCondition, NoisyObservationModel, generate_noisy_split  # noqa: E402
from dynaicl.systems.priors import StableCoefficientPrior  # noqa: E402
from dynaicl.systems.splits import SplitRole  # noqa: E402
from dynaicl.validation import noisy_oracles as O  # noqa: E402

QS = (0.755, 2.56, 6.5)
TARGETS = {0.755: 0.5, 2.56: 0.25, 6.5: 0.125}
RS = (0.25, 1.0, 4.0)
NS = tuple(range(2, 41))
POP = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)


def whittle(a, q):
    f = lambda lam: ((-(-2 * np.cos(lam) + 2 * a) / (1 - 2 * a * np.cos(lam) + a * a) ** 2)
                     / (1 / (1 - 2 * a * np.cos(lam) + a * a) + q)) ** 2
    return integrate.quad(f, -np.pi, np.pi, limit=200)[0] / (4 * np.pi)


def main() -> None:
    t0 = time.time()
    a_n, w_n = O.truncnorm_prior_nodes(0.4, 0.3, 0.95, 80)
    # ---- 1-2: exact finite-n Fisher information and both retention definitions
    I = {}  # (q, r, n) -> array over a nodes
    for q in (0.0, *QS):
        for r in RS:
            for n in NS:
                I[(q, r, n)] = np.array([O.fisher_information_exact(a, n, 1.0, math.sqrt(q), r) for a in a_n])
    R_ratio = {(q, r, n): float(w_n @ I[(q, r, n)] / (w_n @ I[(0.0, r, n)])) for q in QS for r in RS for n in NS}
    R_avg = {(q, r, n): float(w_n @ (I[(q, r, n)] / I[(0.0, r, n)])) for q in QS for r in RS for n in NS}
    asym_avg = {q: float(w_n @ np.array([whittle(a, q) / whittle(a, 0.0) for a in a_n])) for q in QS}
    asym_ratio = {q: float((w_n @ np.array([whittle(a, q) for a in a_n])) / (w_n @ np.array([whittle(a, 0.0) for a in a_n])))
                  for q in QS}
    # ---- 3(i): finite-difference derivative route
    fd_max = 0.0
    for q in QS:
        for r in RS:
            for n in (2, 5, 10, 20, 40):
                for a in (-0.5, 0.4, 0.9):
                    an = O.fisher_information_exact(a, n, 1.0, math.sqrt(q), r, "analytic")
                    fd = O.fisher_information_exact(a, n, 1.0, math.sqrt(q), r, "finite-difference")
                    fd_max = max(fd_max, abs(an - fd) / an)
    # ---- 3(ii): Monte Carlo score-variance route
    rng = np.random.default_rng(61901)
    mc_rows = []
    cases = [(a, n, q) for a in (0.0, 0.4, 0.8) for n in (5, 20, 40) for q in QS]
    z = float(stats.norm.isf(1e-3 / (2 * len(cases))))
    for a, n, q in cases:
        est, se = O.fisher_information_monte_carlo(a, n, 1.0, math.sqrt(q), 1.0, 2000, rng)
        ex = O.fisher_information_exact(a, n, 1.0, math.sqrt(q), 1.0)
        mc_rows.append({"a": a, "n": n, "q": q, "exact": ex, "mc": est, "se": se, "z": (est - ex) / se})
    mc_ok = all(abs(r_["z"]) <= z for r_ in mc_rows)
    # ---- 4: expected posterior variance (prior predictive), production reference
    epv = {}
    v_prior = float(w_n @ (a_n - w_n @ a_n) ** 2)
    streams = NamedStreams(61902)
    epv_ns = (2, 5, 10, 20, 40)
    for q in (0.0, *QS):
        for r in RS:
            model = NoisyObservationModel(1.0, math.sqrt(q), r)
            split = generate_noisy_split(NoisyObservationCondition(POP, model), SplitRole.EVALUATION, streams, 2000, 40)
            pop = kq.noisy_population_reference(POP, model)
            post = {}
            for s in range(0, 2000, 250):
                res = pop.batch_posterior(split.observations[s:s + 250, :41], epv_ns)
                for n in epv_ns:
                    w = np.exp(res[n][0])
                    m = w @ pop.nodes
                    v = (w * (pop.nodes[None, :] - m[:, None]) ** 2).sum(axis=1)
                    post.setdefault(n, []).append(v)
            for n in epv_ns:
                epv[(q, r, n)] = float(np.concatenate(post[n]).mean())
    B = {(q, r, n): (1 / epv[(q, r, n)] - 1 / v_prior) / (1 / epv[(0.0, r, n)] - 1 / v_prior) for q in QS for r in RS for n in epv_ns}

    # ---- report
    L = ["# Stage 0.6 noise-level verification (prior-based calculations only)", "",
         "Generated by `scripts/stage06_noise_level_verification.py`. No predictor scores or effect estimates are involved.",
         f"Population prior: truncated normal (0.4, 0.3) on (-0.95, 0.95), prior variance of a = {v_prior:.5f}. sigma_w = 1;",
         "q = sigma_v^2/sigma_w^2; r = sd(x_0)/sigma_w; n = transitions (y_0..y_n).", "",
         "## 1. Asymptotic (Whittle) retention: the Phase A rule", "",
         "| q | target | prior average of per-a ratios (Phase A definition) | ratio of prior averages |", "|---|---|---|---|"]
    for q in QS:
        L.append(f"| {q} | {TARGETS[q]} | {asym_avg[q]:.4f} | {asym_ratio[q]:.4f} |")
    L += ["", "## 2. Exact finite-n retention (Fisher information of y_0..y_n, latent x_0 prior included)", "",
          "Two definitions: **R_avg** = E_pi[I_q/I_0] (the Phase A definition) and **R_ratio** = E_pi[I_q]/E_pi[I_0].", ""]
    show = (2, 3, 5, 10, 15, 20, 30, 40)
    for defname, R in (("R_avg (prior average of ratios)", R_avg), ("R_ratio (ratio of prior averages)", R_ratio)):
        L += [f"### {defname}", "", "| q (target) | r | " + " | ".join(f"n={n}" for n in show) + " | range over n in 10..40 |",
              "|---|---|" + "---|" * (len(show) + 1)]
        for q in QS:
            for r in RS:
                long = [R[(q, r, n)] for n in NS if n >= 10]
                L.append(f"| {q} ({TARGETS[q]}) | {r} | " + " | ".join(f"{R[(q, r, n)]:.3f}" for n in show)
                         + f" | {min(long):.3f} - {max(long):.3f} |")
        L.append("")
    L += ["## 3. Independent cross-checks of the finite-n Fisher information", "",
          f"* Finite-difference S' vs analytic S' (q in all levels, r in {RS}, n in {{2, 5, 10, 20, 40}}, a in {{-0.5, 0.4, 0.9}}): "
          f"max relative difference **{fd_max:.2e}**.",
          f"* Monte Carlo score variance (2000 simulated contexts per case, r = 1, 27 cases, seed 61901): all |z| <= {z:.2f}: "
          f"**{mc_ok}**; max |z| = {max(abs(r_['z']) for r_ in mc_rows):.2f}.",
          "* Zero-noise anchor (tested in Phase B): I_n(a; 0) = sum_{t<n} V_t / sigma_w^2 exactly.", "",
          "## 4. Complementary Bayesian check: expected posterior variance of a (prior predictive, 2000 systems per cell)", "",
          "B = (1/EPV_q - 1/V_prior) / (1/EPV_0 - 1/V_prior): the information *gained beyond the prior*, relative to zero noise.", "",
          "| q (target) | r | " + " | ".join(f"n={n}: EPV / B" for n in epv_ns) + " |", "|---|---|" + "---|" * len(epv_ns)]
    for r in RS:
        L.append(f"| 0 | {r} | " + " | ".join(f"{epv[(0.0, r, n)]:.4f} / 1" for n in epv_ns) + " |")
    for q in QS:
        for r in RS:
            L.append(f"| {q} ({TARGETS[q]}) | {r} | " + " | ".join(f"{epv[(q, r, n)]:.4f} / {B[(q, r, n)]:.3f}" for n in epv_ns) + " |")
    L += ["", f"(runtime {time.time() - t0:.0f} s)"]
    out = ROOT / "docs" / "STAGE06_NOISE_LEVEL_VERIFICATION.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    data = {"R_avg": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in R_avg.items()},
            "R_ratio": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in R_ratio.items()},
            "asymptotic_avg": asym_avg, "asymptotic_ratio": asym_ratio, "fd_max_rel": fd_max, "mc_rows": mc_rows,
            "epv": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in epv.items()}, "B": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in B.items()},
            "v_prior": v_prior}
    (ROOT / "docs" / "STAGE06_NOISE_LEVEL_VERIFICATION.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {out} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
