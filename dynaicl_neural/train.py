"""Training loop for one Stage 1 model (PREREG_stage1 section 4).

AdamW (lr 1e-3, weight decay 0.01), linear warmup over 1000 steps then cosine decay to 0 at the final step, batch 256,
gradient-norm clip 1.0, float32, loss = mean NLL of x_{t+1} given x_0..x_t over t = 0..19. Deterministic settings are
applied by ``set_determinism`` (call it before CUDA initialises). GPU temperature and utilisation are logged at the
start,
every ``log_every`` steps and at the end (``gpu_stats``; None on machines without nvidia-smi).
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch

from dynaicl_neural.data import ArmSpec, SequenceSampler
from dynaicl_neural.models import ModelSpec, build_model, mixture_log_prob, model_inputs
from dynaicl_neural.seeds import derived_seed


@dataclass(frozen=True)
class TrainConfig:
    steps: int
    checkpoints: tuple[int, ...]
    batch: int = 256
    length: int = 20
    lr: float = 1e-3
    weight_decay: float = 0.01
    warmup: int = 1000
    clip: float = 1.0
    log_every: int = 1000

    def __post_init__(self) -> None:
        if not self.checkpoints or max(self.checkpoints) != self.steps or min(self.checkpoints) < 1:
            raise ValueError("checkpoints must lie in [1, steps] and include the final step")


@dataclass
class TrainRecord:
    arm: str
    seed_index: int
    model: dict
    steps: int
    seconds: float = 0.0
    losses: list = field(default_factory=list)          # (step, mean loss over the last log window)
    gpu: list = field(default_factory=list)             # (step, stats)
    torch_seed: int = 0
    device: str = "cpu"


def set_determinism() -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False


def gpu_stats() -> dict | None:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=temperature.gpu,utilization.gpu,memory.used",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout
        t, u, mem = (float(v) for v in out.strip().splitlines()[0].split(","))
        return {"temperature_c": t, "utilization_pct": u, "memory_mib": mem, "time": time.time()}
    except Exception as exc:  # telemetry must never break training
        return {"error": str(exc)}


def lr_at(step: int, cfg: TrainConfig) -> float:
    if step < cfg.warmup:
        return cfg.lr * (step + 1) / cfg.warmup
    frac = (step - cfg.warmup) / max(1, cfg.steps - cfg.warmup)
    return 0.5 * cfg.lr * (1.0 + math.cos(math.pi * min(1.0, frac)))


def train_model(spec: ModelSpec, arm: ArmSpec, seed_index: int, train_root: int, library_root: int,
                cfg: TrainConfig, out_dir: Path | None, device: str = "cpu") -> tuple[torch.nn.Module, TrainRecord]:
    """Train one model; save state dicts at ``cfg.checkpoints`` into out_dir (if given) and a JSON training record.

    The torch seed derives from (train_root, "stage1_init", seed_index), independent of the arm, so seed index i has the
    same initialisation in every arm (common random numbers)."""
    tseed = derived_seed(train_root, "stage1_init", seed_index)
    torch.manual_seed(tseed)
    model = build_model(spec).to(device)
    sampler = SequenceSampler(arm, train_root, library_root, seed_index, cfg.batch, cfg.length)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    rec = TrainRecord(arm.name, seed_index, spec.to_dict(), cfg.steps, torch_seed=tseed, device=device)
    rec.gpu.append((0, gpu_stats()))
    t0 = time.time()
    window = []
    for step in range(cfg.steps):
        for g in opt.param_groups:
            g["lr"] = lr_at(step, cfg)
        x_np, _ = sampler.next_batch()
        x = torch.from_numpy(x_np.astype(np.float32)).to(device)
        params = model(model_inputs(x[:, :-1]))
        loss = -mixture_log_prob(params, x[:, 1:]).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.clip)
        opt.step()
        window.append(float(loss.detach()))
        done = step + 1
        if done % cfg.log_every == 0 or done == cfg.steps:
            rec.losses.append((done, float(np.mean(window))))
            window = []
            rec.gpu.append((done, gpu_stats()))
        if out_dir is not None and done in cfg.checkpoints:
            out_dir.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), out_dir / f"step{done}.pt")
    rec.seconds = time.time() - t0
    if out_dir is not None:
        (out_dir / "train_record.json").write_text(json.dumps(rec.__dict__, indent=1), encoding="utf-8")
    return model, rec
