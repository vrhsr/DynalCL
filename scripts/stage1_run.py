"""Stage 1A runner (PREREG_stage1). Subcommands:

  train         --config C --out O [--decision D] [--workers W] [--device cuda]
  evaluate      --config C --out O [--decision D] [--controls-only] [--device cuda]
  pilot-decide  --config config/stage1_pilot.yaml --out O --confirmatory-config config/stage1.yaml --j0 J0 --smoke S
  analyze       --config config/stage1.yaml --out O --decision D

Confirmatory `train`, `evaluate` and `analyze` additionally need the frozen state and the user's authorization:
  --manifest docs/FREEZE_MANIFEST_STAGE1.json --expected-manifest-sha256 H --snapshot dist/stage1_frozen_snapshot.zip
  --authorization A.json --run-id R     (key in DYNAICL_STAGE1_AUTH_KEY; never stored)
Exit codes: 0 done, 3 REFUSED. Production runs refuse if a mutation is set (STAGE1_MUTATION).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_neural import pipeline as pl  # noqa: E402
from dynaicl_neural.authorization import Binding, Refused, claim_run, obtain_key, sha256_file, verify  # noqa: E402
from dynaicl_neural.config import load_config  # noqa: E402
from dynaicl_neural.mutations import assert_no_mutation  # noqa: E402
from dynaicl_neural.seeds import load_roles  # noqa: E402


def log_to(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    f = out / "run_log.txt"

    def log(msg: str) -> None:
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
        print(line, flush=True)
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return log


def gate(args, cfg, cfg_sha: str, out: Path) -> None:
    """Confirmatory gate: manifest, frozen files, snapshot, authorization artifact, run lock."""
    import subprocess
    for need in ("manifest", "expected_manifest_sha256", "snapshot", "authorization", "run_id", "decision"):
        if not getattr(args, need, None):
            raise Refused(f"confirmatory runs need --{need.replace('_', '-')}")
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "stage1_freeze.py"), "verify", "--manifest",
                         args.manifest, "--expected-sha256", args.expected_manifest_sha256], cwd=ROOT).returncode
    if rc != 0:
        raise Refused("frozen state does not verify")
    frozen = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))["files"]
    if str(Path(args.config).as_posix()) not in frozen:
        raise Refused("the config is not in the freeze manifest")
    roles = load_roles()
    seeds = tuple(s for r in cfg.seed_roles.values() for s in roles[r])
    binding = Binding(sha256_file(ROOT / args.manifest), sha256_file(ROOT / args.snapshot), cfg_sha,
                      sha256_file(ROOT / "docs" / "PREREG_stage1.md"), sha256_file(Path(args.decision)), seeds)
    key, is_test = obtain_key()
    payload = verify(Path(args.authorization).read_bytes(), key, is_test, binding, dt.datetime.now(dt.timezone.utc))
    if payload["run_id"] != args.run_id:
        raise Refused("run id differs from the authorization")
    claim_run(out, args.run_id)


def main(argv=None) -> int:
    assert_no_mutation()
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("train", "evaluate", "pilot-decide", "analyze"))
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--decision")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--confirmatory-config")
    ap.add_argument("--j0")
    ap.add_argument("--smoke")
    for g in ("manifest", "expected-manifest-sha256", "snapshot", "authorization", "run-id"):
        ap.add_argument(f"--{g}")
    args = ap.parse_args(argv)
    cfg, cfg_sha = load_config(Path(args.config))
    out = Path(args.out)
    log = log_to(out)
    try:
        if cfg.phase == "confirmatory" and args.cmd in ("train", "evaluate", "analyze"):
            gate(args, cfg, cfg_sha, out)
        decision = json.loads(Path(args.decision).read_text(encoding="utf-8")) if args.decision else None
    except Refused as exc:
        log(f"REFUSED: {exc}")
        return 3
    jobs = pl.plan_jobs(cfg, decision)
    if args.cmd == "train":
        pl.run_training(cfg, jobs, out, args.workers, args.device, log)
    elif args.cmd == "evaluate":
        if cfg.phase == "pilot" and not args.controls_only and not (decision and decision.get("B")):
            raise SystemExit("pilot full evaluation needs --decision with the step budget B")
        for rep in sorted({j.replicate for j in jobs}):
            sets = pl.evaluation_sets(cfg, rep)
            pl.reference_quantities(cfg, rep, sets, out)
            for j in (x for x in jobs if x.replicate == rep):
                if cfg.phase == "pilot":
                    # pass 1: controls at every checkpoint (chooses B); pass 2: full statistics at B
                    steps = j.checkpoints if args.controls_only else (int(decision["B"]),)
                else:
                    steps = (j.steps,)                           # confirmatory: each model at its final step
                for st in steps:
                    pl.evaluate_model(cfg, j, st, sets, out, args.device, controls_only=args.controls_only)
                log(f"evaluated {j.arm} {j.size} steps={steps} seed {j.seed_index} R{rep + 1}")
    elif args.cmd == "pilot-decide":
        ccfg, _ = load_config(Path(args.confirmatory_config))
        j0 = json.loads(Path(args.j0).read_text(encoding="utf-8"))
        smoke = json.loads(Path(args.smoke).read_text(encoding="utf-8"))
        steps_j0 = j0["single"][0]["steps"]
        # effective GPU seconds per model-step for size M at the best measured concurrency (wall time includes
        # warm-up and process start-up, so this is conservative)
        eff = min(c["wall_seconds"] / (c["processes"] * steps_j0) for c in j0["concurrent"])
        eval_sec = max(m["eval_seconds"] for m in smoke["models"])
        provisional = pl.pilot_decision(cfg, jobs, out, ccfg.cap_rule.max_models)   # B from the controls
        b = provisional["B"]
        cap = pl.cap_from_j0(ccfg, eff, eval_sec, b) if b else 0
        decision = pl.pilot_decision(cfg, jobs, out, cap) if b else provisional
        decision.update({"j0_effective_sec_per_step": eff, "eval_sec_per_model": eval_sec, "config_sha256": cfg_sha})
        if decision["status"] == "RESOLVED":
            proj = pl.project_hours(ccfg, decision, j0, eval_sec)
            decision["projection"] = proj
            decision["secondary_kept"] = pl.keep_secondary(ccfg, proj)
        (out / "pilot_decision.json").write_text(json.dumps(decision, indent=1), encoding="utf-8")
        log(f"pilot decision: {decision['status']} B={decision['B']} M1={decision.get('M1')} M2={decision.get('M2')} "
            f"cap={cap} secondary={decision.get('secondary_kept')}")
    else:
        prim = pl.primary_jobs(cfg, jobs, decision)
        checks = pl.controls_and_validity(cfg, prim, out)
        q1 = pl.analyse_q1(cfg, [j for j in prim if j.arm in ("CONT", "UNIF")], out) if decision.get("M1") else None
        q2 = pl.analyse_q2(cfg, [j for j in prim if j.arm.startswith("LIB-")], out) if decision.get("M2") else None
        secondary = pl.analyse_secondary(cfg, jobs, out, decision)
        result = {"verdict": pl.verdict(checks, q1, q2, decision), "checks": checks, "q1": q1, "q2": q2,
                  "secondary": secondary, "decision": decision, "config_sha256": cfg_sha}
        (out / "results.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
        log(f"verdict: {result['verdict']}; Q1: {q1 and q1['answer']}; Q2: {q2 and q2['answer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
