"""Section 5.K: rolling-origin vs blocked vs leave-one-out bandwidth selection on the SAME contexts.

The question is measured, not assumed: for each (n, h), compare the selected bandwidth multipliers
and the held-out log score on the true x_{n+h} (which lies outside the context), with paired SEs.
"""

from __future__ import annotations

import math

import numpy as np

from dynaicl.baselines.kernel import SCHEMES, KernelAnalogPredictor, KernelSettings
from dynaicl.evaluation import harness
from dynaicl.metrics import scoring
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec
from dynaicl.systems.splits import SplitRole, generate_split


def compare_kernel_schemes(prior, ns=(10, 30, 80), hs=(1, 3), n_items: int = 600, root_seed: int = 801,
                           settings: KernelSettings = KernelSettings()) -> list[dict]:
    cond = ContinuousPriorCondition(prior, InitialStateSpec(0.0, 1.0))
    split = generate_split(cond, SplitRole.EVALUATION, NamedStreams(root_seed), n_items, max(ns) + max(hs) + 1)
    rows = []
    for n in ns:
        for h in hs:
            es = harness.build_evaluation_set(cond, split, n, h)
            tabs = {s: harness.score_predictor(KernelAnalogPredictor(s, settings), es, info_keys=("multiplier",))
                    for s in SCHEMES}
            row = {"n": n, "h": h, "n_items": n_items}
            for s, t in tabs.items():
                m = t.info["multiplier"]
                row[f"{s}_mean_log_score"] = float(t.log_score.mean())
                row[f"{s}_mean_multiplier"] = float(np.nanmean(m)) if np.isfinite(m).any() else math.nan
                row[f"{s}_plugin_rate"] = float(t.fallback.mean())
            for a, b in (("rolling_origin", "leave_one_out"), ("blocked", "leave_one_out"),
                         ("rolling_origin", "blocked")):
                d = scoring.paired_difference(tabs[a].log_score, tabs[b].log_score)
                ma, mb = tabs[a].info["multiplier"], tabs[b].info["multiplier"]
                both = np.isfinite(ma) & np.isfinite(mb)
                row[f"{a}-{b}_logscore_diff"] = d.mean
                row[f"{a}-{b}_se"] = d.se
                row[f"{a}-{b}_frac_same_bandwidth"] = float(np.mean(ma[both] == mb[both])) if both.any() else math.nan
                lr = np.log(ma[both] / mb[both])
                row[f"{a}-{b}_mean_log_bw_ratio"] = float(lr.mean()) if both.any() else math.nan
                row[f"{a}-{b}_log_bw_ratio_se"] = float(lr.std(ddof=1) / math.sqrt(lr.size)) if lr.size > 1 else math.nan
            rows.append(row)
    return rows
