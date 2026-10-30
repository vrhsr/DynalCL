"""Build paper/CLAIMS.md from paper/claims.yaml (tasks E1 and E4).

For every claim: read the evidence file from git (`git show <ref>:<path>`, so a clean checkout of any branch reproduces it),
record the resolved commit and the file's sha256, re-extract each number and compare with `expect`. Exit 1 if any VERIFIED
or DESIGN claim fails or its file is missing. PENDING claims are listed and never count as evidence.

    python paper/tools/build_claims.py            # writes paper/CLAIMS.md and paper/claims_resolved.json
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def git_blob(ref: str, path: str) -> tuple[bytes | None, str | None]:
    if ref == "none":
        return None, None
    commit = subprocess.run(["git", "rev-parse", ref], cwd=ROOT, capture_output=True, text=True)
    if commit.returncode != 0:
        return None, None
    blob = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True)
    return (blob.stdout if blob.returncode == 0 else None), commit.stdout.strip()


def _get(d, dotted: str):
    for part in dotted.split("."):
        d = d[part] if isinstance(d, dict) else d[int(part)]
    return d


def _rows(raw: bytes, where: dict, ge: dict | None = None, lt: dict | None = None) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    rows = [r for r in rows if all(str(r[k]) == str(v) for k, v in where.items())]
    rows = [r for r in rows if all(float(r[k]) >= float(v) for k, v in (ge or {}).items())]
    return [r for r in rows if all(float(r[k]) < float(v) for k, v in (lt or {}).items())]


def _same(got, want, tol) -> bool:
    if isinstance(want, (list, tuple)) and isinstance(got, (list, tuple)):
        return len(got) == len(want) and all(_same(g, w, tol) for g, w in zip(got, want))
    if isinstance(want, dict) and isinstance(got, dict):
        return set(got) == set(want) and all(_same(got[k], want[k], tol) for k in want)
    if isinstance(want, bool) or isinstance(got, bool) or isinstance(want, str):
        return got == want
    if isinstance(want, (int, float)) and isinstance(got, (int, float)):
        return math.isclose(float(got), float(want), rel_tol=0.0, abs_tol=tol)
    return got == want


def extract(raw: bytes, spec: dict):
    if "json" in spec:
        return _get(json.loads(raw), spec["json"])
    if "json_len" in spec:
        return len(_get(json.loads(raw), spec["json_len"]))
    if "yaml" in spec:
        return _get(yaml.safe_load(raw), spec["yaml"])
    if "csv_minmax" in spec:
        vals = [float(r[spec["csv_minmax"]]) for r in _rows(raw, spec.get("where", {}))]
        return [min(vals), max(vals)]
    if "contains" in spec:
        return spec["contains"] in raw.decode("utf-8")
    if "regex_int" in spec:
        import re
        m = re.search(spec["regex_int"], raw.decode("utf-8"))
        if m is None:
            raise ValueError(f"pattern not found: {spec['regex_int']}")
        return int(m.group(1))
    if "regex_float" in spec:
        import re
        m = re.search(spec["regex_float"], raw.decode("utf-8"))
        if m is None:
            raise ValueError(f"pattern not found: {spec['regex_float']}")
        return float(m.group(1))
    if "csv_count" in spec:
        return len(_rows(raw, spec.get("where", {}), spec.get("ge"), spec.get("lt")))
    if "json_keycount" in spec:
        # count entries of a dict keyed "a|b|c|..." whose '|'-separated fields match key_fields and whose value matches
        d = _get(json.loads(raw), spec["json_keycount"])
        kf = {int(i): str(v) for i, v in spec.get("key_fields", {}).items()}
        return sum(1 for k, v in d.items() if all(k.split("|")[i] == want for i, want in kf.items())
                   and ("value" not in spec or v == spec["value"]))
    if "csv_max" in spec:
        return max(float(r[spec["csv_max"]]) for r in _rows(raw, spec.get("where", {})))
    if "csv_max_int" in spec:
        return max(int(float(r[spec["csv_max_int"]])) for r in _rows(raw, spec.get("where", {})))
    if "csv_min_int" in spec:
        return min(int(float(r[spec["csv_min_int"]])) for r in _rows(raw, spec.get("where", {})))
    raise ValueError(f"unknown extractor {spec}")


def main() -> int:
    data = yaml.safe_load((ROOT / "paper" / "claims.yaml").read_text(encoding="utf-8"))
    out, ok_all = [], True
    for c in data["claims"]:
        src = c["source"]
        raw, commit = git_blob(src["ref"], src["path"])
        entry = {"id": c["id"], "label": c["label"], "text": c["text"], "ref": src["ref"], "path": src["path"],
                 "commit": commit, "sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None, "checks": []}
        if c["label"] == "PENDING":
            entry["status"] = "PENDING" + (" (file exists)" if raw is not None else "")
        elif raw is None:
            entry["status"] = "FAIL: evidence file missing"
            ok_all = False
        else:
            good = True
            for spec in c.get("extract", []):
                try:
                    got = extract(raw, spec)
                except Exception as exc:  # a broken extractor is a failure, never a pass
                    got = f"ERROR {type(exc).__name__}: {exc}"
                passed = _same(got, spec["expect"], float(spec.get("tol", 0.0)))
                entry["checks"].append({"spec": {k: v for k, v in spec.items() if k not in ("expect", "tol")},
                                        "expect": spec["expect"], "got": got, "pass": passed})
                good &= passed
            entry["status"] = "PASS" if good else "FAIL"
            ok_all &= good
        out.append(entry)
    (ROOT / "paper" / "claims_resolved.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    lines = ["# Claims-to-evidence table (generated by paper/tools/build_claims.py; do not edit by hand)", "",
             f"Overall: {'PASS' if ok_all else 'FAIL'} ({sum(e['status'] == 'PASS' for e in out)} verified, "
             f"{sum(e['status'].startswith('PENDING') for e in out)} pending)", "",
             "| id | label | claim | evidence (ref @ commit : path) | sha256 | status |", "|---|---|---|---|---|---|"]
    for e in out:
        ev = f"{e['ref']} @ {(e['commit'] or '-')[:7]} : `{e['path']}`"
        lines.append(f"| {e['id']} | {e['label']} | {e['text']} | {ev} | {(e['sha256'] or '-')[:12]} | {e['status']} |")
    (ROOT / "paper" / "CLAIMS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:3]))
    for e in out:
        if e["status"].startswith("FAIL"):
            print(e["id"], e["status"], [ch for ch in e["checks"] if not ch["pass"]])
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
