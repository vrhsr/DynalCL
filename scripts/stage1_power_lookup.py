"""Build the frozen power lookup (config/stage1_power_lookup.json) from the version-2 operating characteristics.

For each family and each M on the OC grid: s*(M) = the largest seed sd on the grid at which P_correct >= 0.8 for BOTH
reference positions (pi = 0 and pi = 1), every approximation error e <= 0.005 (Q1) or e in {0, 0.01} (Q2), and every
rho_cell (Q1). None if no grid value qualifies. The pilot rule picks the smallest M whose s*(M) covers 1.35 x the pilot
sd. Coarse s grids make the lookup conservative (a step function rounded down).

Usage: python scripts/stage1_power_lookup.py --oc results_stage1/oc_1A_v2 --out config/stage1_power_lookup.json
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

POWER = 0.8


def lookup(rows: list[dict], e_allowed: set[float]) -> dict:
    ok = defaultdict(lambda: defaultdict(list))       # M -> s -> [P_correct ...]
    for r in rows:
        if r["truth"] not in ("POP-LIKE", "STAB-LIKE", "LIB-LIKE", "GENERALISING") or float(r["e"]) not in e_allowed:
            continue
        ok[int(r["M"])][float(r["s"])].append(float(r["P_correct"]))
    out = {}
    for m in sorted(ok):
        good = [s for s, ps in ok[m].items() if ps and min(ps) >= POWER]
        out[str(m)] = max(good) if good else None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oc", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    oc = Path(args.oc)
    q1 = list(csv.DictReader(open(oc / "oc_q1_v2.csv", encoding="utf-8")))
    q2 = list(csv.DictReader(open(oc / "oc_q2_v2.csv", encoding="utf-8")))
    table = {"Q1": lookup(q1, {0.0, 0.005}), "Q2": lookup(q2, {0.0, 0.01}), "power": POWER,
             "source": str(oc), "note": "s*(M): largest grid seed sd with P_correct >= 0.8 in every qualifying setting"}
    Path(args.out).write_text(json.dumps(table, indent=1), encoding="utf-8")
    print(json.dumps(table, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
