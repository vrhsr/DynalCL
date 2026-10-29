"""F2-V11 detector run: apply $F2_MUTATION (if any), run the extra F2 detectors in their fast configuration, print JSON.

Configuration (fixed before any mutation was run): structural checks (matched guard, leakage, spectral radius);
calibration at (n, r) in {(5, 1), (20, 0.25)} with 300 items; optimality at n = 10, r = 1 with 800 items against libraries
of 2 / 16 / 64 atoms and the context-only reference. Statistical tests Bonferroni-corrected at family level 0.01 over the
2 x 9 calibration p-values and the 4 optimality z-tests (22 tests). Seed role f2_v_mutation.
"""

from __future__ import annotations

import json
import sys
import traceback

from scipy import stats

FAMILY_ALPHA = 0.01
CAL_CELLS = ((5, 1.0), (20, 0.25))
N_TESTS = len(CAL_CELLS) * 9 + 4


def run() -> dict:
    from dynaicl_families.stage2 import f2_checks as fc
    from dynaicl_families.stage2.f2_mutations import apply_from_env
    from dynaicl_families.stage2.seeds import role_seed
    name = apply_from_env()
    seed = role_seed("f2_v_mutation")
    alpha = FAMILY_ALPHA / N_TESTS
    z_crit = float(stats.norm.isf(alpha))
    jobs = [("matched_guard", fc.matched_guard), ("leakage", lambda: fc.leakage(seed)),
            ("spectral_radius", lambda: fc.spectral_radius_check(seed + 1))]
    jobs += [(f"calibration_n{n}_r{r}", (lambda n=n, r=r, k=k: fc.calibration_cell(n, r, 300, seed + 10 + k, alpha)))
             for k, (n, r) in enumerate(CAL_CELLS)]
    jobs.append(("optimality_n10_r1.0", lambda: fc.optimality_cell(10, 1.0, 800, seed + 20, z_crit)))
    out = {"mutation": name or "baseline", "family_alpha": FAMILY_ALPHA, "n_tests": N_TESTS, "alpha_per_test": alpha,
           "checks": {}}
    for key, fn in jobs:
        try:
            out["checks"][key] = fn()
        except Exception as exc:
            out["checks"][key] = {"pass": False, "exception": f"{type(exc).__name__}: {exc}",
                                  "trace": traceback.format_exc(limit=3)}
    return out


if __name__ == "__main__":
    print(json.dumps(run(), default=float))
    sys.exit(0)
