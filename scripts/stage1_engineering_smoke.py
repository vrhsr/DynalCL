"""UNIF-only engineering smoke test (allowed before the freeze; reveals nothing about Q1, which concerns CONT models on
population systems). Two UNIF models (size M, seed role engineering_smoke), trained for --steps steps, evaluated ONLY on
systems drawn from UNIF's own law against the stab reference (its Bayes predictor): the capability quantities of
controls C1 / C2. Also measures V-CAUSAL on the device and V-REPRO (model 0 retrained from its seed). GPU temperature and
utilisation are logged in the training records and here.

Usage (box, only after the user says the GPU is free):
    .venv-stage1/bin/python scripts/stage1_engineering_smoke.py --device cuda --steps 5000 --out results_stage1/eng_smoke
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.rng import NamedStreams  # noqa: E402
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec  # noqa: E402
from dynaicl.systems.priors import StableCoefficientPrior  # noqa: E402
from dynaicl_families.ar1_known_sigma import ContextStats, stability_prior  # noqa: E402
from dynaicl_families.sampling import contexts_and_targets, simulate  # noqa: E402
from dynaicl_neural.adapter import mixture_params  # noqa: E402
from dynaicl_neural.data import ArmSpec  # noqa: E402
from dynaicl_neural.evaluate import kl_reference_to_model, realized_log_score  # noqa: E402
from dynaicl_neural.models import SIZES, model_inputs  # noqa: E402
from dynaicl_neural.mutations import assert_no_mutation  # noqa: E402
from dynaicl_neural.seeds import derived_seed, role_seed  # noqa: E402
from dynaicl_neural.train import TrainConfig, gpu_stats, set_determinism, train_model  # noqa: E402

N_EVAL = 2000
CELLS = [(1.0, 1), (1.0, 2), (1.0, 3), (1.0, 20), (4.0, 1), (0.25, 3)]


def evaluate(model, device, eval_root):
    stab = stability_prior()
    out = {}
    for r, n in CELLS:
        cond = ContinuousPriorCondition(StableCoefficientPrior(rho=0.999, sigma=1.0, shape="uniform"),
                                        InitialStateSpec(0.0, r))
        split = simulate(cond, NamedStreams(eval_root), N_EVAL, 22)
        ctx, y = contexts_and_targets(split, n)
        st = ContextStats.from_contexts(ctx)
        params = mixture_params(model, ctx, device)
        kl = kl_reference_to_model(stab, st, params)
        realized = stab.logpdf(st, y) - realized_log_score(params, y)
        out[f"r{r}_n{n}"] = {"regret_vs_stab_RB": float(kl.mean()), "se_RB": float(kl.std(ddof=1) / np.sqrt(kl.size)),
                             "regret_vs_stab_realized": float(realized.mean()),
                             "se_realized": float(realized.std(ddof=1) / np.sqrt(realized.size))}
    return out


def causality(model, device, eval_root):
    import torch
    cond = ContinuousPriorCondition(StableCoefficientPrior(rho=0.999, sigma=1.0, shape="uniform"), InitialStateSpec())
    split = simulate(cond, NamedStreams(derived_seed(eval_root, "causality")), 1000, 21)
    x = np.array(split.trajectories)
    with torch.no_grad():
        full = model(model_inputs(torch.from_numpy(x.astype(np.float32)).to(device))).double().cpu().numpy()
    worst = 0.0
    for n in (1, 5, 19):
        ctx, _ = contexts_and_targets(split, n) if n + 2 <= x.shape[1] else (None, None)
        _, mu, _ = mixture_params(model, ctx, device)
        m = full.shape[2] // 3
        worst = max(worst, float(np.max(np.abs(mu - full[:, n, m:2 * m]))))
    return worst


def main(argv=None) -> int:
    assert_no_mutation()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--steps", type=int, default=5000)
    args = ap.parse_args(argv)
    set_determinism()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    root = role_seed("engineering_smoke")
    train_root, lib_root, eval_root = (derived_seed(root, lbl) for lbl in ("train", "library", "eval"))
    cfg = TrainConfig(steps=args.steps, checkpoints=(args.steps,), log_every=max(1, args.steps // 10))
    res = {"gpu_start": gpu_stats(), "steps": args.steps, "models": []}
    for i in (0, 1):
        t0 = time.time()
        model, rec = train_model(SIZES["M"], ArmSpec("UNIF"), i, train_root, lib_root, cfg, out / f"model{i}", args.device)
        res["models"].append({"seed_index": i, "train_seconds": rec.seconds, "final_loss": rec.losses[-1][1],
                              "eval": evaluate(model, args.device, eval_root), "eval_seconds": time.time() - t0 - rec.seconds,
                              "causality_max_abs_diff": causality(model, args.device, eval_root)})
        print(json.dumps(res["models"][-1]["eval"]), flush=True)
    model_r, _ = train_model(SIZES["M"], ArmSpec("UNIF"), 0, train_root, lib_root, cfg, None, args.device)
    ev_r = evaluate(model_r, args.device, eval_root)
    ev_0 = res["models"][0]["eval"]
    res["repro_max_abs_diff_nats"] = max(abs(ev_r[k]["regret_vs_stab_RB"] - ev_0[k]["regret_vs_stab_RB"]) for k in ev_0)
    res["gpu_end"] = gpu_stats()
    (out / "eng_smoke.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("repro max abs diff (nats):", res["repro_max_abs_diff_nats"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
