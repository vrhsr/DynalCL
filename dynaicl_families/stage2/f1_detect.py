"""F1-V9 detector run: apply $F1_MUTATION (if any), run the extra F1 detectors in their fast configuration, print JSON.

    F1_MUTATION=wrong_prior python -m dynaicl_families.stage2.f1_detect

Configuration (fixed before any mutation was run): structural checks (matched guard, leakage); calibration at
(n, r) in {(2, 1), (5, 4), (20, 0.25)} with 3000 items; optimality at n in {2, 10}, r = 1 with 4000 items against the
context-only reference and libraries of 2, 16 and 256 atoms; the known-sigma limit at n = 5. Statistical tests are
Bonferroni-corrected at family level 0.01 over the 3 x 6 calibration p-values and the 2 x 4 optimality z-tests (26 tests).
"""

from __future__ import annotations

import json
import sys
import traceback

from scipy import stats

FAMILY_ALPHA = 0.01
CAL_CELLS = ((2, 1.0), (5, 4.0), (20, 0.25))
OPT_CELLS = ((2, 1.0), (10, 1.0))
N_TESTS = len(CAL_CELLS) * 6 + len(OPT_CELLS) * 4


def run() -> dict:
    from dynaicl_families.stage2 import f1_checks as fc
    from dynaicl_families.stage2.f1_mutations import apply_from_env
    from dynaicl_families.stage2.seeds import role_seed
    name = apply_from_env()
    seed = role_seed("f1_v9_detectors")
    alpha = FAMILY_ALPHA / N_TESTS
    z_crit = float(stats.norm.isf(alpha))
    jobs = [("matched_guard", lambda: fc.matched_guard()), ("leakage", lambda: fc.leakage(seed))]
    jobs += [(f"calibration_n{n}_r{r}", (lambda n=n, r=r, k=k: fc.calibration_cell(n, r, 3000, seed + 10 + k, alpha)))
             for k, (n, r) in enumerate(CAL_CELLS)]
    jobs += [(f"optimality_n{n}_r{r}", (lambda n=n, r=r, k=k: fc.optimality_cell(n, r, 4000, seed + 20 + k, z_crit)))
             for k, (n, r) in enumerate(OPT_CELLS)]
    jobs.append(("known_sigma_limit", lambda: fc.known_sigma_limit(5, 1.0, 100, seed + 30)))
    out = {"mutation": name or "baseline", "family_alpha": FAMILY_ALPHA, "n_tests": N_TESTS, "alpha_per_test": alpha,
           "checks": {}}
    for key, fn in jobs:
        try:
            out["checks"][key] = fn()
        except Exception as exc:  # a crash is reported separately from an assertion-style failure
            out["checks"][key] = {"pass": False, "exception": f"{type(exc).__name__}: {exc}",
                                  "trace": traceback.format_exc(limit=3)}
    return out


if __name__ == "__main__":
    print(json.dumps(run(), default=float))
    sys.exit(0)
