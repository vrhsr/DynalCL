"""Stage 0.6 Phase B selection-data audit. SELECTION DATA ONLY (root seed 63001); no population-aware scores are computed.

    python scripts/stage06_selection_audit.py   -> docs/STAGE06_SELECTION_AUDIT.md

Question 1 (decision rule from the user): does any VALID noise-aware context-only alternative beat the noise-aware
stability-only comparator? Candidates, each with the same likelihood, known noise levels, x_0 prior and nodes:
the arcsine-prior Bayes predictor and the grid-MLE plug-in.
Question 2 (diagnostic sanity check): does the noise-aware stability predictor weakly beat the noise-naive Stage 0.5
predictors?
Paired differences (candidate - stability, nats/forecast) with SE = sd/sqrt(N). "Beats" = mean > 3 SE.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.baselines.family import build_context_only_family  # noqa: E402
from dynaicl.evaluation import noisy_harness as nh  # noqa: E402
from dynaicl.references import kalman_quadrature as kq  # noqa: E402
from dynaicl.rng import NamedStreams  # noqa: E402
from dynaicl.systems.noisy import NoisyObservationCondition, NoisyObservationModel, generate_noisy_split  # noqa: E402
from dynaicl.systems.priors import StableCoefficientPrior  # noqa: E402
from dynaicl.systems.splits import SplitRole  # noqa: E402

POP = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)
QS, RS, NS, HS = (0.0, 0.755, 2.56, 6.5), (0.25, 1.0, 4.0), (2, 5, 10, 20, 40), (1, 5)
N_AWARE, N_SLOW, NS_NAIVE = 1000, 300, (2, 10, 40)


def main() -> None:
    t0 = time.time()
    streams = NamedStreams(63001)
    rows = []
    for q in QS:
        for r in RS:
            model = NoisyObservationModel(1.0, math.sqrt(q), r)
            split = generate_noisy_split(NoisyObservationCondition(POP, model), SplitRole.SELECTION, streams, N_AWARE, 45)
            eset = nh.build_noisy_evaluation(split, NS, HS)
            stab = nh.score_noisy_batch(kq.noise_aware_stability_predictor(model), eset)
            arc = nh.score_noisy_batch(kq.noise_aware_arcsine_predictor(model), eset)
            mle = nh.score_noisy_per_context(kq.NoiseAwareMlePlugInPredictor(model), eset, items=range(N_SLOW))
            naive = {name: nh.score_noisy_per_context(p, eset, ns=NS_NAIVE, items=range(N_SLOW))
                     for name, p in build_context_only_family(1.0, stability_bound=0.999).items()}
            for (n, h) in eset._targets:
                cands = {"noise_aware_arcsine_bayes": (arc[(n, h)][0], stab[(n, h)][0]),
                         "noise_aware_mle_plugin": (mle[(n, h)][0], stab[(n, h)][0][:N_SLOW])}
                if n in NS_NAIVE:
                    for name, sc in naive.items():
                        cands["naive:" + name] = (sc[(n, h)][0], stab[(n, h)][0][:N_SLOW])
                for name, (c, s) in cands.items():
                    d = c - s
                    rows.append({"q": q, "r": r, "n": n, "h": h, "candidate": name, "mean": float(d.mean()),
                                 "se": float(d.std(ddof=1) / math.sqrt(d.size)), "N": int(d.size)})
    aware = [x for x in rows if not x["candidate"].startswith("naive:")]
    naive_rows = [x for x in rows if x["candidate"].startswith("naive:")]
    beats = [x for x in aware if x["mean"] > 3 * x["se"]]
    naive_beats = [x for x in naive_rows if x["mean"] > 3 * x["se"]]
    L = ["# Stage 0.6 selection-data audit (selection seed 63001; no population-aware scores computed)", "",
         "Paired differences **candidate - noise-aware stability** in nats/forecast (positive = candidate better). "
         f"Noise-aware candidates: N = {N_AWARE} (arcsine) and {N_SLOW} (MLE plug-in). Noise-naive: N = {N_SLOW}, n in {NS_NAIVE}.", "",
         "## Q1: does a valid noise-aware context-only alternative beat stability-only?", "",
         f"Cells where an alternative is better by > 3 SE: **{len(beats)} of {len(aware)}**.", ""]
    for x in beats:
        L.append(f"- {x['candidate']} q={x['q']} r={x['r']} n={x['n']} h={x['h']}: {x['mean']:+.4f} +/- {x['se']:.4f}")
    L += ["", "| candidate | q | r | h | " + " | ".join(f"n={n}" for n in NS) + " |", "|---|---|---|---|" + "---|" * len(NS)]
    for cand in ("noise_aware_arcsine_bayes", "noise_aware_mle_plugin"):
        for q in QS:
            for r in RS:
                for h in HS:
                    cells = []
                    for n in NS:
                        x = next(y for y in aware if y["candidate"] == cand and y["q"] == q and y["r"] == r and y["n"] == n and y["h"] == h)
                        cells.append(f"{x['mean']:+.4f} ({x['se']:.4f})")
                    L.append(f"| {cand} | {q} | {r} | {h} | " + " | ".join(cells) + " |")
    L += ["", "## Q2 (diagnostic): noise-naive Stage 0.5 predictors vs noise-aware stability", "",
          f"Cells where a noise-naive predictor is better by > 3 SE: **{len(naive_beats)} of {len(naive_rows)}**.", ""]
    for x in naive_beats:
        L.append(f"- {x['candidate']} q={x['q']} r={x['r']} n={x['n']} h={x['h']}: {x['mean']:+.4f} +/- {x['se']:.4f}")
    L += ["", "| candidate | q | " + " | ".join(f"r={r} n={n} h={h}" for r in RS for n in NS_NAIVE for h in HS) + " |",
          "|---|---|" + "---|" * (len(RS) * len(NS_NAIVE) * len(HS))]
    for cand in sorted({x["candidate"] for x in naive_rows}):
        for q in QS:
            cells = []
            for r in RS:
                for n in NS_NAIVE:
                    for h in HS:
                        x = next(y for y in naive_rows if y["candidate"] == cand and y["q"] == q and y["r"] == r and y["n"] == n and y["h"] == h)
                        cells.append(f"{x['mean']:+.3f}")
                    del n
            L.append(f"| {cand} | {q} | " + " | ".join(cells) + " |")
    L += ["", f"(runtime {time.time() - t0:.0f} s)"]
    out = ROOT / "docs" / "STAGE06_SELECTION_AUDIT.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}; Q1 beats: {len(beats)}/{len(aware)}; Q2 naive beats: {len(naive_beats)}/{len(naive_rows)}; {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
