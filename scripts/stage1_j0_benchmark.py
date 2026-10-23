"""J0 throughput benchmark (PREREG_stage1 section 12): seconds per training step for every model size, alone and with
several concurrent training processes on one GPU. Random training sequences only (UNIF sampler, seed role j0_benchmark);
NOTHING is evaluated. GPU temperature and utilisation are logged before, during and after.

Usage (box, only after the user says the GPU is free):
    .venv-stage1/bin/python scripts/stage1_j0_benchmark.py --device cuda --out results_stage1/j0
Local smoke: python scripts/stage1_j0_benchmark.py --device cpu --steps 30 --sizes S --concurrency 1 --out <dir>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WARMUP_STEPS = 20


def one(size: str, steps: int, device: str, seed_index: int) -> dict:
    """Train one model for ``steps`` steps on random UNIF sequences; time the steps after the warm-up."""
    import torch
    from dynaicl_neural.data import ArmSpec
    from dynaicl_neural.models import SIZES, n_parameters
    from dynaicl_neural.seeds import role_seed
    from dynaicl_neural.train import TrainConfig, gpu_stats, set_determinism, train_model
    set_determinism()
    root = role_seed("j0_benchmark")
    cfg_w = TrainConfig(steps=WARMUP_STEPS, checkpoints=(WARMUP_STEPS,), warmup=5, log_every=WARMUP_STEPS)
    cfg = TrainConfig(steps=steps, checkpoints=(steps,), warmup=5, log_every=max(1, steps // 3))
    train_model(SIZES[size], ArmSpec("UNIF"), seed_index, root, root, cfg_w, None, device)   # warm-up (kernels, caches)
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()
    model, rec = train_model(SIZES[size], ArmSpec("UNIF"), seed_index, root, root, cfg, None, device)
    if device == "cuda":
        torch.cuda.synchronize()
    sec = time.time() - t0
    return {"size": size, "steps": steps, "seconds": sec, "sec_per_step": sec / steps, "params": n_parameters(model),
            "gpu_end": gpu_stats(), "final_loss": rec.losses[-1][1]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--sizes", nargs="+", default=["S", "M", "L", "DW-shallow", "DW-deep", "GRU", "SSM"])
    ap.add_argument("--concurrency", nargs="+", type=int, default=[1, 4, 8, 16])
    ap.add_argument("--child", nargs=3, metavar=("SIZE", "STEPS", "SEED_INDEX"), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.child:
        print(json.dumps(one(args.child[0], int(args.child[1]), args.device, int(args.child[2]))), flush=True)
        return 0
    from dynaicl_neural.train import gpu_stats
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"gpu_start": gpu_stats(), "single": [], "concurrent": []}
    for size in args.sizes:
        r = one(size, args.steps, args.device, 0)
        res["single"].append(r)
        print(f"single {size}: {r['sec_per_step'] * 1000:.1f} ms/step, {r['params']} params", flush=True)
    for c in args.concurrency:
        t0 = time.time()
        procs = [subprocess.Popen([sys.executable, __file__, "--out", str(out), "--device", args.device,
                                   "--child", "M", str(args.steps), str(i)], stdout=subprocess.PIPE, text=True,
                                  stdin=subprocess.DEVNULL) for i in range(c)]
        mid = gpu_stats()
        outs = [json.loads(p.communicate()[0].strip().splitlines()[-1]) for p in procs]
        wall = time.time() - t0
        steps_per_s = c * args.steps / wall
        res["concurrent"].append({"processes": c, "size": "M", "wall_seconds": wall, "aggregate_steps_per_s": steps_per_s,
                                  "per_process_sec_per_step": [o["sec_per_step"] for o in outs], "gpu_mid": mid})
        print(f"concurrency {c} (size M): {steps_per_s:.1f} aggregate steps/s, wall {wall:.0f}s", flush=True)
    res["gpu_end"] = gpu_stats()
    (out / "j0.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
