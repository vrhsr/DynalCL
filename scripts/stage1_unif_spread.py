"""PROPOSED (not yet approved): early read of seed-to-seed spread from UNIF-only models, before the freeze.

UNIF is outside the hypothesis (Q1 concerns CONT models on population systems), so this reveals nothing about Q1 or Q2.
8 UNIF models (size M, seed role `unif_spread`), trained to --steps, evaluated ONLY on systems from UNIF's own law
against
stab (UNIF's Bayes predictor): per-context regret KL(stab || model) in the Q1-shaped cells (r in {0.25, 1, 4} x n in
{1, 2, 3, 5}) and at n = 20. Output: per cell, the arm-mean regret (a capability number) and the BETWEEN-SEED sd of the
per-model mean regret (the quantity that decides Q1 feasibility through the frozen lookup). Training runs --workers
models
concurrently on the GPU; GPU temperature and utilisation are logged.

Usage (box, only on the user's approval):
    .venv-stage1/bin/python scripts/stage1_unif_spread.py --device cuda --steps <B> --workers 8 --out
    results_stage1/unif_spread
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N_MODELS = 8
N_EVAL = 4000
CELLS = [(r, n) for r in (0.25, 1.0, 4.0) for n in (1, 2, 3, 5)] + [(1.0, 20)]


def _train(i: int, steps: int, device: str, out: str, checkpoints: tuple[int, ...]) -> str:
    from dynaicl_neural.data import ArmSpec
    from dynaicl_neural.models import SIZES
    from dynaicl_neural.seeds import derived_seed, role_seed
    from dynaicl_neural.train import TrainConfig, set_determinism, train_model
    set_determinism()
    root = role_seed("unif_spread")
    d = Path(out) / f"model{i}"
    if (d / "train_record.json").exists():
        return str(d)
    cfg = TrainConfig(steps=steps, checkpoints=checkpoints, log_every=max(1, steps // 20),
                      warmup=min(1000, max(1, steps // 10)))
    train_model(SIZES["M"], ArmSpec("UNIF"), i, derived_seed(root, "train"), derived_seed(root, "library"), cfg, d,
                device)
    return str(d)


def provenance(args) -> dict:
    """Commit, tree state, environment and arguments (added after the first run, which wrote none; disclosure S20)."""
    import platform
    import subprocess

    import numpy
    import torch

    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"git_commit": git("rev-parse", "HEAD"), "git_status_porcelain": git("status", "--porcelain"),
            "python": sys.version, "numpy": numpy.__version__, "torch": torch.__version__,
            "platform": platform.platform(), "args": vars(args),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def main(argv=None) -> int:
    from dynaicl.rng import NamedStreams
    from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec
    from dynaicl.systems.priors import StableCoefficientPrior
    from dynaicl_families.ar1_known_sigma import ContextStats, stability_prior
    from dynaicl_families.sampling import contexts_and_targets, simulate
    from dynaicl_neural.mutations import assert_no_mutation
    from dynaicl_neural.seeds import derived_seed, role_seed
    from dynaicl_neural.train import gpu_stats
    assert_no_mutation()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--steps", type=int, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--checkpoints", type=int, nargs="*", default=None,
                    help="extra checkpoints to evaluate (the final step is always included)")
    args = ap.parse_args(argv)
    cks = tuple(sorted(set((args.checkpoints or []) + [args.steps])))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"gpu_start": gpu_stats(), "steps": args.steps, "n_models": N_MODELS, "provenance": provenance(args)}
    t0 = time.time()
    # spawn, not fork: CUDA cannot be used in a child forked from a parent that has touched CUDA (and on Windows)
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")) as ex:
        list(ex.map(_train, range(N_MODELS), [args.steps] * N_MODELS, [args.device] * N_MODELS,
                    [str(out)] * N_MODELS, [cks] * N_MODELS))
    res["train_wall_seconds"] = time.time() - t0
    res["gpu_after_training"] = gpu_stats()

    import torch
    from dynaicl_neural.adapter import mixture_params
    from dynaicl_neural.evaluate import kl_reference_to_model
    from dynaicl_neural.models import SIZES, build_model
    stab = stability_prior()
    eval_root = derived_seed(role_seed("unif_spread"), "eval")
    res["by_checkpoint"] = {}
    for ck in cks:
        per_model = {f"{r}|{n}": [] for r, n in CELLS}
        for i in range(N_MODELS):
            model = build_model(SIZES["M"])
            model.load_state_dict(torch.load(out / f"model{i}" / f"step{ck}.pt", map_location=args.device))
            model.to(args.device)
            for r, n in CELLS:
                cond = ContinuousPriorCondition(StableCoefficientPrior(rho=0.999, sigma=1.0, shape="uniform"),
                                                InitialStateSpec(0.0, r))
                ctx, _ = contexts_and_targets(simulate(cond, NamedStreams(eval_root), N_EVAL, 22), n)
                kl = kl_reference_to_model(stab, ContextStats.from_contexts(ctx),
                                           mixture_params(model, ctx, args.device))
                per_model[f"{r}|{n}"].append(float(kl.mean()))
        cells = {k: {"arm_mean_regret": float(np.mean(v)), "between_seed_sd": float(np.std(v, ddof=1)),
                     "ucl_sd_x1.35": float(1.35 * np.std(v, ddof=1)), "per_model_mean": v}
                 for k, v in per_model.items()}
        q1_like = [k for k in cells if not k.endswith("|20")]
        res["by_checkpoint"][str(ck)] = {"cells": cells, "max_between_seed_sd_q1_like_cells":
                                         max(cells[k]["between_seed_sd"] for k in q1_like)}
    res["gpu_end"] = gpu_stats()
    res["total_wall_seconds"] = time.time() - t0
    (out / "unif_spread.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({"train_wall_seconds": res["train_wall_seconds"],
                      "max_sd_by_checkpoint": {k: v["max_between_seed_sd_q1_like_cells"]
                                               for k, v in res["by_checkpoint"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
