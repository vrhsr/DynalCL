"""Section 5.K: kernel bandwidth-selection schemes on the same simulated contexts.

This test MEASURES the differences and prints them. It does not assume which scheme is optimistic, so
it only asserts structural facts (finite, paired, the default scheme is rolling-origin)."""

import math

from dynaicl.baselines.kernel import KernelAnalogPredictor
from dynaicl.validation.checks import P_STABLE_TN
from dynaicl.validation.kernel_schemes import compare_kernel_schemes


def test_k_scheme_comparison_reported():
    rows = compare_kernel_schemes(P_STABLE_TN)
    print("\n n  h | log score  RO      BLK     LOO   | RO-LOO (SE)        BLK-LOO (SE)       | mean multiplier RO/BLK/LOO"
          " | frac same bw RO=LOO")
    for r in rows:
        print(f"{r['n']:3d} {r['h']:2d} | {r['rolling_origin_mean_log_score']:7.4f} {r['blocked_mean_log_score']:7.4f} "
              f"{r['leave_one_out_mean_log_score']:7.4f} | "
              f"{r['rolling_origin-leave_one_out_logscore_diff']:+.4f} ({r['rolling_origin-leave_one_out_se']:.4f}) "
              f"{r['blocked-leave_one_out_logscore_diff']:+.4f} ({r['blocked-leave_one_out_se']:.4f}) | "
              f"{r['rolling_origin_mean_multiplier']:.2f}/{r['blocked_mean_multiplier']:.2f}/"
              f"{r['leave_one_out_mean_multiplier']:.2f} | {r['rolling_origin-leave_one_out_frac_same_bandwidth']:.2f}")
        for k, v in r.items():   # bandwidth ratios may be undefined (no validation folds); scores never are
            if k.endswith(("_logscore_diff", "_mean_log_score")) or (k.endswith("_se") and "bw" not in k):
                assert math.isfinite(v), (k, v)


def test_k_default_scheme_is_rolling_origin():
    assert KernelAnalogPredictor().scheme == "rolling_origin"
