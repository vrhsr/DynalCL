"""Apply the frozen decision rules of docs/STAGE1_SEPARABILITY_MAP_SPEC.md section 4 to <out>/map_rows.csv.

Writes <out>/map_decisions.csv, <out>/map_checks.json and <out>/MAP_REPORT.md. Exit code 0 if the map is VALID, 1 if
INVALID (a validity check failed; the map must then not be used).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from scipy.stats import norm

DELTA = 0.02
Z_CELL = 3.0
DRAW_FRACTION = 0.9
CHECK_FAMILYWISE = 0.001

PRIMARY = {   # (set, pair) -> how the cell estimate is formed
    ("HELD", "pop|stab"): ("single", "KL(pop||stab)"),
    ("PROBE", "pop|stab"): ("min", ("KL(pop||stab)", "KL(stab||pop)")),
    ("OOS", "pop|stab"): ("min", ("KL(pop||stab)", "KL(stab||pop)")),
    ("HELD", "lib|pop"): ("single", "KL(pop||lib)"),
    ("HELD", "lib|stab"): ("min", ("KL(lib||stab)", "KL(stab||lib)")),
    ("INLIB", "lib|pop"): ("single", "realized LS(lib)-LS(pop)"),
    ("INLIB", "lib|stab"): ("single", "realized LS(lib)-LS(stab)"),
    ("PROBE", "lib|pop"): ("min", ("KL(lib||pop)", "KL(pop||lib)")),
    ("PROBE", "lib|stab"): ("min", ("KL(lib||stab)", "KL(stab||lib)")),
    ("OOS", "lib|pop"): ("min", ("KL(lib||pop)", "KL(pop||lib)")),
    ("OOS", "lib|stab"): ("min", ("KL(lib||stab)", "KL(stab||lib)")),
}


def load(out: Path) -> list[dict]:
    rows = list(csv.DictReader(open(out / "map_rows.csv", encoding="utf-8")))
    for r in rows:
        r["r"] = float(r["r"])
        r["n"], r["K"], r["draw"], r["n_items"] = int(r["n"]), int(r["K"]), int(r["draw"]), int(r["n_items"])
        r["mean"], r["sd"] = float(r["mean"]), float(r["sd"])
        r["se"] = r["sd"] / math.sqrt(r["n_items"])
    return rows


def cell_estimates(rows: list[dict]) -> dict:
    """{(set, pair, r, n, K, draw): (estimate, se)} by the PRIMARY rule."""
    by = defaultdict(dict)
    for r in rows:
        by[(r["set"], r["pair"], r["r"], r["n"], r["K"], r["draw"])][r["estimator"]] = r
    est = {}
    for key, ests in by.items():
        rule = PRIMARY.get((key[0], key[1]))
        if rule is None:
            continue
        if rule[0] == "single":
            e = ests[rule[1]]
        else:
            e = min((ests[name] for name in rule[1]), key=lambda x: x["mean"])
        est[key] = (e["mean"], e["se"])
    return est


def classify(lo: float, hi: float) -> str:
    return "IDENTIFIABLE" if lo >= DELTA else ("UNIDENTIFIABLE" if hi < DELTA else "BORDERLINE")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args(argv).out)
    rows = load(out)

    checks = [r for r in rows if r["estimator"] == "CHECK realized-minus-KL"]
    c = max(1, len(checks))
    z_c = float(norm.isf(CHECK_FAMILYWISE / (2 * c)))
    worst = max((abs(r["mean"]) / r["se"] for r in checks if r["se"] > 0), default=0.0)
    valid = worst <= z_c
    checks_out = {"n_agreement_checks": len(checks), "z_critical": z_c, "max_abs_z": worst, "agreement_pass": valid,
                  "note": "KL window mass and disjointness are enforced at run time (the run aborts on failure)."}

    est = cell_estimates(rows)
    decisions = []
    groups = defaultdict(list)
    for (s, pair, r, n, k, d), (m, se) in sorted(est.items()):
        lo, hi = m - Z_CELL * se, m + Z_CELL * se
        if pair == "pop|stab":
            decisions.append({"set": s, "pair": pair, "r": r, "n": n, "K": 0, "estimate": m, "se": se, "lo": lo,
                              "hi": hi, "draws": 1, "frac_lo_ge_delta": float(lo >= DELTA),
                              "frac_hi_lt_delta": float(hi < DELTA), "decision": classify(lo, hi)})
        else:
            groups[(s, pair, r, n, k)].append((m, lo, hi))
    for (s, pair, r, n, k), vals in sorted(groups.items()):
        ms = sorted(v[0] for v in vals)
        f_lo = sum(v[1] >= DELTA for v in vals) / len(vals)
        f_hi = sum(v[2] < DELTA for v in vals) / len(vals)
        dec = ("IDENTIFIABLE" if f_lo >= DRAW_FRACTION else ("UNIDENTIFIABLE" if f_hi >= DRAW_FRACTION else "PARTIAL"))
        q = lambda p: ms[min(len(ms) - 1, int(p * (len(ms) - 1) + 0.5))]  # noqa: E731
        decisions.append({"set": s, "pair": pair, "r": r, "n": n, "K": k, "estimate": sum(ms) / len(ms), "se": "",
                          "lo": q(0.1), "hi": q(0.9), "draws": len(vals), "frac_lo_ge_delta": f_lo,
                          "frac_hi_lt_delta": f_hi, "decision": dec})
    keys = ["set", "pair", "r", "n", "K", "estimate", "se", "lo", "hi", "draws", "frac_lo_ge_delta", "frac_hi_lt_delta",
            "decision"]
    with open(out / "map_decisions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(decisions)
    n_single = sum(1 for d in decisions if d["pair"] == "pop|stab")
    checks_out["expected_false_identifiable_cells_upper_bound"] = n_single * float(norm.sf(Z_CELL))
    checks_out["map_valid"] = valid
    (out / "map_checks.json").write_text(json.dumps(checks_out, indent=1), encoding="utf-8")

    L = ["# Stage 1A separability map: report", "",
         f"Rules: docs/STAGE1_SEPARABILITY_MAP_SPEC.md section 4 (delta = {DELTA}, "
         f"bound = estimate +/- {Z_CELL} SE; Q2 "
         f"draw fraction {DRAW_FRACTION}).", "",
         f"**Validity: {'VALID' if valid else 'INVALID'}.** Agreement checks: {len(checks)}, max |z| = {worst:.2f}, "
         f"critical {z_c:.2f}.", "", "## Q1 (pop vs stab)", "",
         "| set | r | n | estimate | lo | hi | decision |", "|---|---|---|---|---|---|---|"]
    for d in decisions:
        if d["pair"] == "pop|stab":
            L.append(f"| {d['set']} | {d['r']} | {d['n']} | {d['estimate']:+.4f} | {d['lo']:+.4f} | {d['hi']:+.4f} | "
                     f"{d['decision']} |")
    L += ["", "## Q2 (library vs pop / stab): decision per (set, pair, r, n, K); estimate = mean over draws; "
          "lo / hi = 10th / 90th percentile over draws", "",
          "| set | pair | r | n | K | mean | p10 | p90 | frac lo>=delta | decision |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for d in decisions:
        if d["pair"] != "pop|stab":
            L.append(f"| {d['set']} | {d['pair']} | {d['r']} | {d['n']} | {d['K']} | {d['estimate']:+.4f} | "
                     f"{d['lo']:+.4f} | {d['hi']:+.4f} | {d['frac_lo_ge_delta']:.2f} | {d['decision']} |")
    (out / "MAP_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"map {'VALID' if valid else 'INVALID'}: {len(decisions)} decisions; report {out / 'MAP_REPORT.md'}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
