"""Stage 1A pipeline: plan jobs, train, evaluate, pilot rule, cap rule, confirmatory analysis and verdict.

Everything numerical here calls the tested modules (data, models, train, adapter, evaluate, analysis, references). The
layout on disk (all under one output directory):
    models/<rep>/<arm>/<size>/seed<i>/step<k>.pt, train_record.json     (stays on the box)
    eval/<rep>/<arm>/<size>/seed<i>/step<k>.npz                         per-context statistics (float32)
    eval/<rep>/reference.npz                                            reference-only quantities (Delta, separations)
Pilot outputs: pilot_decision.json (step budget, between-seed sds, model counts, pass flags; NO means or classes).
"""

from __future__ import annotations

import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec, LibraryCondition
from dynaicl.systems.library import SystemLibrary
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl_families.ar1_known_sigma import ContextStats, FiniteLibrary, population_prior, stability_prior
from dynaicl_families.sampling import OutOfSupportCondition, ProbeGridCondition, contexts_and_targets, simulate
from dynaicl_families.separability import POP_FROZEN, kl_per_context
from dynaicl_neural.analysis import (Band, Statistic, band, classify_behavioural, classify_memorisation, classify_q1_held,
                                     critical_value_bootstrap,
                                     two_level)
from dynaicl_neural.config import Stage1Config
from dynaicl_neural.data import ArmSpec, library_atoms
from dynaicl_neural.evaluate import kl_reference_to_model, realized_log_score
from dynaicl_neural.seeds import derived_seed, role_seed

Q1_CELLS = ((0.25, 1), (0.25, 2), (0.25, 3), (0.25, 5), (1.0, 1), (1.0, 2), (1.0, 3), (1.0, 5), (4.0, 1), (4.0, 2))
Q2_CELLS = tuple((s, r, n) for s in ("PROBE", "OOS") for r in (0.25, 1.0) for n in (5, 10, 20))
BEHAV_CELLS = tuple((s, r, n) for s in ("PROBE", "OOS") for r in (0.25, 1.0) for n in (1, 2, 3, 5, 10, 20))
C1_CELLS = tuple((r, n) for r in (0.25, 1.0, 4.0) for n in (1, 2, 3))
C2_N = 20
LENGTH = 22
PROBE_GRID = tuple(round(-0.95 + 0.05 * i, 2) for i in range(39))
UNIF_PRIOR = StableCoefficientPrior(rho=0.999, sigma=1.0, shape="uniform")


def arm_spec(name: str) -> ArmSpec:
    return ArmSpec("LIB", int(name.split("-")[1])) if name.startswith("LIB-") else ArmSpec(name)


@dataclass(frozen=True)
class Job:
    replicate: int
    arm: str
    size: str
    seed_index: int
    steps: int
    checkpoints: tuple[int, ...]

    def _tail(self) -> Path:
        return Path(f"R{self.replicate + 1}") / self.arm / self.size / f"steps{self.steps}" / f"seed{self.seed_index}"

    def model_dir(self, out: Path) -> Path:
        return out / "models" / self._tail()

    def eval_file(self, out: Path, step: int, controls_only: bool = False) -> Path:
        name = f"step{step}_controls.npz" if controls_only else f"step{step}.npz"
        return out / "eval" / self._tail() / name


def roots(cfg: Stage1Config, replicate: int) -> dict[str, int]:
    """Per-replicate roots for train / eval / library; the bootstrap root is one seed shared by all replicates (each
    replicate uses its own named stream of it). Found by the end-to-end test: indexing the bootstrap role by replicate
    would fail for R2."""
    return {k: role_seed(v, 0 if k == "bootstrap" else replicate) for k, v in cfg.seed_roles.items()}


# ------------------------------------------------------------------------------------------------ planning

def plan_jobs(cfg: Stage1Config, decision: dict | None = None) -> list[Job]:
    """Pilot: fixed counts. Confirmatory: M1 (CONT, UNIF) and M2 (LIB arms) and budget B from the pilot decision."""
    jobs = []
    if cfg.phase == "pilot":
        for arm in cfg.primary_arms:
            jobs += [Job(0, arm, cfg.model, i, cfg.steps, cfg.checkpoints) for i in range(cfg.models_per_arm)]
        return jobs
    if decision is None or decision.get("status") != "RESOLVED":
        raise ValueError("confirmatory jobs need a RESOLVED pilot decision")
    b = int(decision["B"])
    ck = (b // 4, b // 2, b)
    for rep in range(cfg.replicates):
        for arm in cfg.primary_arms:
            m = decision["M1"] if arm in ("CONT", "UNIF") else decision["M2"]
            if m is None:
                continue                                    # that family is NOT RESOLVABLE: no models
            jobs += [Job(rep, arm, cfg.model, i, b, ck) for i in range(m)]
    return jobs + secondary_jobs(cfg, decision)


#: secondary families (PREREG section 9): (arm, size, budget multiplier) per variant; Q1-behavioural reuses primary models
SECONDARY = {
    "training-length-4B": (("CONT", "M", 4), ("UNIF", "M", 4)),
    "size-S": (("CONT", "S", 1), ("UNIF", "S", 1)),
    "size-L": (("CONT", "L", 1), ("UNIF", "L", 1)),
    "depth-width": (("CONT", "DW-shallow", 1), ("UNIF", "DW-shallow", 1), ("CONT", "DW-deep", 1), ("UNIF", "DW-deep", 1)),
    "architecture": (("CONT", "GRU", 1), ("UNIF", "GRU", 1), ("CONT", "SSM", 1), ("UNIF", "SSM", 1)),
    "Q2-size-L": (("LIB-4", "L", 1), ("LIB-16", "L", 1), ("LIB-64", "L", 1)),
    "Q1-behavioural": (),
}
M_SECONDARY_MAX = 32


def secondary_count(family: str, decision: dict) -> int:
    base = decision.get("M2") if family == "Q2-size-L" else decision.get("M1")
    return min(base, M_SECONDARY_MAX) if base else 0


def secondary_jobs(cfg: Stage1Config, decision: dict) -> list[Job]:
    jobs = []
    b = int(decision["B"])
    for fam in decision.get("secondary_kept", []):
        m = secondary_count(fam, decision)
        for rep in range(cfg.replicates):
            for arm, size, mult in SECONDARY[fam]:
                steps = b * mult
                jobs += [Job(rep, arm, size, i, steps, (steps // 4, steps // 2, steps)) for i in range(m)]
    return jobs


def primary_jobs(cfg: Stage1Config, jobs: list[Job], decision: dict) -> list[Job]:
    return [j for j in jobs if j.size == cfg.model and j.steps == int(decision["B"])]


def project_hours(cfg: Stage1Config, decision: dict, j0: dict, eval_sec: float) -> dict:
    """Projected GPU hours (with the cap rule's safety factor) of the primary experiment and of each secondary family.
    J0 gives the effective seconds per model-step for size M at the best concurrency; other sizes are scaled by their
    single-process seconds per step relative to M."""
    steps_j0 = j0["single"][0]["steps"]
    eff_m = min(c["wall_seconds"] / (c["processes"] * steps_j0) for c in j0["concurrent"])
    single = {s["size"]: s["sec_per_step"] for s in j0["single"]}
    eff = {size: eff_m * single[size] / single["M"] for size in single}
    b, k = int(decision["B"]), cfg.cap_rule.safety

    def hours(n_models, size, steps):
        return n_models * (steps * eff[size] + eval_sec) * k / 3600.0
    n_lib = sum(a.startswith("LIB-") for a in cfg.primary_arms)
    prim = cfg.replicates * (hours(2 * (decision.get("M1") or 0), cfg.model, b)
                             + hours(n_lib * (decision.get("M2") or 0), cfg.model, b))
    sec = {fam: cfg.replicates * sum(hours(secondary_count(fam, decision), size, b * mult)
                                     for _, size, mult in SECONDARY[fam]) for fam in cfg.secondary}
    return {"primary_hours": prim, "secondary_hours": sec, "eff_sec_per_model_step": eff}


def keep_secondary(cfg: Stage1Config, proj: dict) -> list[str]:
    """Drop secondary families in cfg.drop_order until primary + kept <= gpu_hours_limit (primary is never reduced)."""
    kept = list(cfg.secondary)
    for fam in cfg.drop_order:
        if proj["primary_hours"] + sum(proj["secondary_hours"][f] for f in kept) <= cfg.cap_rule.gpu_hours_limit:
            break
        if fam in kept:
            kept.remove(fam)
    return kept


def _train_one(job: Job, cfg_batch: int, out: str, device: str, roots_: dict) -> str:
    from dynaicl_neural.models import SIZES
    from dynaicl_neural.train import TrainConfig, set_determinism, train_model
    set_determinism()
    d = job.model_dir(Path(out))
    if (d / "train_record.json").exists():
        return f"{d} (exists)"
    tc = TrainConfig(steps=job.steps, checkpoints=job.checkpoints, batch=cfg_batch,
                     log_every=max(1, job.steps // 20), warmup=min(1000, max(1, job.steps // 10)))
    train_model(SIZES[job.size], arm_spec(job.arm), job.seed_index, roots_["train"], roots_["library"], tc, d, device)
    return str(d)


def run_training(cfg: Stage1Config, jobs: list[Job], out: Path, workers: int, device: str, log=print) -> None:
    rts = {rep: roots(cfg, rep) for rep in {j.replicate for j in jobs}}
    todo = [j for j in jobs if not (j.model_dir(out) / "train_record.json").exists()]
    log(f"training: {len(jobs)} models, {len(jobs) - len(todo)} done, {len(todo)} to run, workers={workers}")
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_train_one, j, cfg.batch, str(out), device, rts[j.replicate]) for j in todo]
        for k, f in enumerate(as_completed(futs), 1):
            log(f"[train {k}/{len(todo)}] {f.result()}")


# ------------------------------------------------------------------------------------------------ evaluation sets

def evaluation_sets(cfg: Stage1Config, replicate: int) -> dict:
    """Contexts and targets for every evaluated cell of one replicate (systems shared by all models: CRN)."""
    ev = roots(cfg, replicate)["eval"]
    streams = NamedStreams(ev)
    out: dict = {}
    for r in (0.25, 1.0, 4.0):
        x0 = InitialStateSpec(0.0, r)
        held = simulate(ContinuousPriorCondition(POP_FROZEN, x0), streams, cfg.eval.held_n, LENGTH)
        unif = simulate(ContinuousPriorCondition(UNIF_PRIOR, x0), streams, cfg.eval.control_n, LENGTH)
        probe = simulate(ProbeGridCondition(PROBE_GRID, 1.0, x0), streams, cfg.eval.probe_n, LENGTH)
        oos = simulate(OutOfSupportCondition(0.95, 0.999, 1.0, x0), streams, cfg.eval.oos_n, LENGTH)
        for n in sorted({c[1] for c in Q1_CELLS} | {C2_N}):
            out[("HELD", r, n)] = contexts_and_targets(held, n)
        for n in sorted({c[1] for c in C1_CELLS} | {C2_N}):
            out[("UNIFSYS", r, n)] = contexts_and_targets(unif, n)
        for n in sorted({c[2] for c in BEHAV_CELLS}):
            out[("PROBE", r, n)] = contexts_and_targets(probe, n)
            out[("OOS", r, n)] = contexts_and_targets(oos, n)
    return out


def inlib_set(cfg: Stage1Config, replicate: int, seed_index: int, atoms: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """C2 for a LIB model: its own library's systems (r = 1), at n = C2_N."""
    lib = SystemLibrary(atoms, np.ones_like(atoms), np.full(atoms.size, 1.0 / atoms.size))
    streams = NamedStreams(derived_seed(roots(cfg, replicate)["eval"], "stage1_inlib_c2", seed_index, atoms.size))
    split = simulate(LibraryCondition(lib, InitialStateSpec(0.0, 1.0)), streams, cfg.eval.control_n, LENGTH)
    return contexts_and_targets(split, C2_N)


# ------------------------------------------------------------------------------------------------ per-model evaluation

def evaluate_model(cfg: Stage1Config, job: Job, step: int, sets: dict, out: Path, device: str,
                   controls_only: bool = False) -> Path:
    """Write per-context statistics of one model checkpoint (float32) to eval/.../step<k>.npz."""
    import torch
    from dynaicl_neural.adapter import mixture_params
    from dynaicl_neural.models import SIZES, build_model
    f = job.eval_file(out, step, controls_only)
    if f.exists():
        return f
    model = build_model(SIZES[job.size])
    model.load_state_dict(torch.load(job.model_dir(out) / f"step{step}.pt", map_location=device))
    model.to(device)
    pop, stab = population_prior(), stability_prior()
    arm = arm_spec(job.arm)
    atoms = library_atoms(roots(cfg, job.replicate)["library"], job.seed_index, arm.k) if arm.kind == "LIB" else None
    lib = FiniteLibrary(atoms) if atoms is not None else None
    res: dict[str, np.ndarray] = {}

    def params_for(key):
        ctx, _ = sets[key]
        return mixture_params(model, ctx, device)

    # controls: C1 (UNIF on its own systems, short n), C2 (each arm on its own distribution, n = 20)
    if arm.kind == "UNIF":
        for r, n in C1_CELLS:
            st = ContextStats.from_contexts(sets[("UNIFSYS", r, n)][0])
            res[f"C1|{r}|{n}"] = kl_reference_to_model(stab, st, params_for(("UNIFSYS", r, n)))
        st = ContextStats.from_contexts(sets[("UNIFSYS", 1.0, C2_N)][0])
        res["C2"] = kl_reference_to_model(stab, st, params_for(("UNIFSYS", 1.0, C2_N)))
    elif arm.kind == "CONT":
        st = ContextStats.from_contexts(sets[("HELD", 1.0, C2_N)][0])
        res["C2"] = kl_reference_to_model(pop, st, params_for(("HELD", 1.0, C2_N)))
    else:
        ctx, _ = inlib_set(cfg, job.replicate, job.seed_index, atoms)
        res["C2"] = kl_reference_to_model(lib, ContextStats.from_contexts(ctx), mixture_params(model, ctx, device))
    if not controls_only:
        if arm.kind in ("CONT", "UNIF"):
            for r, n in Q1_CELLS:
                ctx, y = sets[("HELD", r, n)]
                st = ContextStats.from_contexts(ctx)
                p = params_for(("HELD", r, n))
                res[f"Q1|{r}|{n}"] = kl_reference_to_model(pop, st, p)
                res[f"Q1R|{r}|{n}"] = pop.logpdf(st, y) - realized_log_score(p, y)       # V-RB
            for s, r, n in BEHAV_CELLS:
                st = ContextStats.from_contexts(sets[(s, r, n)][0])
                p = params_for((s, r, n))
                res[f"B|{s}|{r}|{n}|pop"] = kl_reference_to_model(pop, st, p)
                res[f"B|{s}|{r}|{n}|stab"] = kl_reference_to_model(stab, st, p)
        else:
            for s, r, n in Q2_CELLS:
                st = ContextStats.from_contexts(sets[(s, r, n)][0])
                p = params_for((s, r, n))
                for name, ref in (("lib", lib), ("pop", pop), ("stab", stab)):
                    res[f"Q2|{s}|{r}|{n}|{name}"] = kl_reference_to_model(ref, st, p)
                # per-model reference separations (reference-only; the gate of PREREG section 6.2)
                res[f"SEP|{s}|{r}|{n}|lib-pop"] = np.minimum(kl_per_context(lib, pop, st), kl_per_context(pop, lib, st))
                res[f"SEP|{s}|{r}|{n}|lib-stab"] = np.minimum(kl_per_context(lib, stab, st),
                                                              kl_per_context(stab, lib, st))
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp.npz")
    np.savez(tmp, **{k: v.astype(np.float32) for k, v in res.items()})
    os.replace(tmp, f)
    return f


def reference_quantities(cfg: Stage1Config, replicate: int, sets: dict, out: Path) -> Path:
    """Delta = KL(pop || stab) per Q1 cell and pop-stab separations on the behavioural cells (reference-only)."""
    f = out / "eval" / f"R{replicate + 1}" / "reference.npz"
    if f.exists():
        return f
    pop, stab = population_prior(), stability_prior()
    res = {}
    for r, n in Q1_CELLS:
        res[f"Delta|{r}|{n}"] = kl_per_context(pop, stab, ContextStats.from_contexts(sets[("HELD", r, n)][0]))
    for s, r, n in BEHAV_CELLS:
        st = ContextStats.from_contexts(sets[(s, r, n)][0])
        res[f"SEP|{s}|{r}|{n}|pop-stab"] = np.minimum(kl_per_context(pop, stab, st), kl_per_context(stab, pop, st))
    f.parent.mkdir(parents=True, exist_ok=True)
    np.savez(f, **res)
    return f


# ------------------------------------------------------------------------------------------------ pilot rule

def _load(f: Path) -> dict[str, np.ndarray]:
    with np.load(f) as z:
        return {k: z[k].astype(np.float64) for k in z.files}


def control_pass(values: list[np.ndarray], epsilon: float, z: float) -> tuple[bool, float]:
    """Upper band (two-level SE, critical value z) of the arm-mean control regret below epsilon."""
    theta, se = two_level(np.stack(values))
    return theta + z * se < epsilon, theta + z * se


def pilot_decision(cfg: Stage1Config, jobs: list[Job], out: Path, cap: int) -> dict:
    """The frozen pilot rule (PREREG section 7). Writes no means or classes; only sds, flags, counts.

    B: smallest checkpoint where every arm passes C2 (and UNIF passes C1), with Bonferroni z over the control statistics.
    s1: largest between-seed sd over the Q1 statistics (R_pop of CONT; G formed per seed index); s2: largest over Q2
    statistics of the LIB arms. M = the smallest M in the frozen power lookup (OC-calibrated, >= min_models, <= cap)
    that supports ucl x s; none -> that family is NOT RESOLVABLE."""
    from scipy.stats import norm
    arms = sorted({j.arm for j in jobs})
    by_arm = {a: [j for j in jobs if j.arm == a] for a in arms}
    n_controls = len(arms) + len(C1_CELLS)
    z = float(norm.isf(0.05 / (2 * n_controls)))
    budget, flags = None, {}
    for step in jobs[0].checkpoints:
        ok = True
        for a in arms:
            vals = [_load(j.eval_file(out, step, True))["C2"] for j in by_arm[a]]
            passed, upper = control_pass(vals, cfg.epsilon, z)
            flags[f"C2|{a}|{step}"] = {"pass": passed}
            ok &= passed
            if a == "UNIF":
                for r, n in C1_CELLS:
                    passed, _ = control_pass([_load(j.eval_file(out, step, True))[f"C1|{r}|{n}"] for j in by_arm[a]],
                                             cfg.epsilon, z)
                    flags[f"C1|{r}|{n}|{step}"] = {"pass": passed}
                    ok &= passed
        if ok:
            budget = step
            break
    decision = {"status": "NOT RESOLVABLE (capability)" if budget is None else "RESOLVED", "B": budget,
                "control_flags": flags, "z_controls": z, "cap": cap}
    if budget is None:
        decision.update(M1=None, M2=None, s1=None, s2=None)
        return decision

    if not all(j.eval_file(out, budget).exists() for j in jobs):
        decision.update(status="NEEDS FULL EVALUATION AT B", M1=None, M2=None, s1=None, s2=None)
        return decision

    def sd_between(arr: np.ndarray) -> float:
        return float(np.std(arr.mean(axis=1), ddof=1))
    cont = [_load(j.eval_file(out, budget)) for j in sorted(by_arm.get("CONT", []), key=lambda j: j.seed_index)]
    unif = [_load(j.eval_file(out, budget)) for j in sorted(by_arm.get("UNIF", []), key=lambda j: j.seed_index)]
    s1 = 0.0
    for r, n in Q1_CELLS:
        rc = np.stack([d[f"Q1|{r}|{n}"] for d in cont])
        ru = np.stack([d[f"Q1|{r}|{n}"] for d in unif])
        s1 = max(s1, sd_between(rc), sd_between(ru - rc))
    s2 = 0.0
    for a in arms:
        if not a.startswith("LIB-"):
            continue
        ds = [_load(j.eval_file(out, budget)) for j in by_arm[a]]
        for s, r, n in Q2_CELLS:
            d = {name: np.stack([x[f"Q2|{s}|{r}|{n}|{name}"] for x in ds]) for name in ("lib", "pop", "stab")}
            for arr in (d["lib"], d["pop"], d["stab"], d["pop"] - d["lib"], d["stab"] - d["lib"]):
                s2 = max(s2, sd_between(arr))

    lookup = load_power_lookup()

    def count(s: float, family: str) -> int | None:
        """Smallest M in the frozen OC grid (<= cap) whose largest supported seed sd covers the UCL-adjusted s.
        The lookup is generated from the version-2 operating characteristics (audit A1) before the freeze."""
        for m_str, s_star in sorted(lookup[family].items(), key=lambda kv: int(kv[0])):
            m = int(m_str)
            if m >= cfg.min_models and m <= cap and s_star is not None and cfg.ucl_factor * s <= s_star:
                return m
        return None
    decision.update(s1=s1, s2=s2, M1=count(s1, "Q1"), M2=count(s2, "Q2"))
    if decision["M1"] is None and decision["M2"] is None:
        decision["status"] = "NOT RESOLVABLE (both families exceed the cap)"
    return decision


POWER_LOOKUP = Path(__file__).resolve().parents[1] / "config" / "stage1_power_lookup.json"


def load_power_lookup(path: Path = POWER_LOOKUP) -> dict:
    """{"Q1": {M: s*(M) or None}, "Q2": {...}} generated by scripts/stage1_power_lookup.py from the OC v2 results."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cap_from_j0(cfg: Stage1Config, sec_per_model_step: float, eval_sec_per_model: float, budget: int) -> int:
    """The frozen cap rule: the largest M (multiple of cap_rule.step, <= max_models) such that the projected primary
    experiment (replicates x arms x M models x (budget x sec_per_model_step + eval_sec_per_model) x safety) fits in
    gpu_hours_limit. ``sec_per_model_step`` is the J0 effective seconds per step per model at the best concurrency."""
    arms = len(cfg.primary_arms)
    per_model = (budget * sec_per_model_step + eval_sec_per_model) * cfg.cap_rule.safety
    best = 0
    for m in range(cfg.cap_rule.step, cfg.cap_rule.max_models + 1, cfg.cap_rule.step):
        if cfg.replicates * arms * m * per_model / 3600.0 <= cfg.cap_rule.gpu_hours_limit:
            best = m
    return best


# ------------------------------------------------------------------------------------------------ confirmatory analysis

def q1_family(cfg: Stage1Config, jobs: list[Job], out: Path, rep: int) -> tuple[list[Statistic], dict]:
    cont = sorted((j for j in jobs if j.replicate == rep and j.arm == "CONT"), key=lambda j: j.seed_index)
    unif = sorted((j for j in jobs if j.replicate == rep and j.arm == "UNIF"), key=lambda j: j.seed_index)
    if [j.seed_index for j in cont] != [j.seed_index for j in unif]:
        raise ValueError("CONT and UNIF seed indices must match (pairing)")
    dc = [_load(j.eval_file(out, j.steps)) for j in cont]
    du = [_load(j.eval_file(out, j.steps)) for j in unif]
    ref = _load(out / "eval" / f"R{rep + 1}" / "reference.npz")
    stats, gaps = [], {}
    for r, n in Q1_CELLS:
        rc = np.stack([d[f"Q1|{r}|{n}"] for d in dc])
        ru = np.stack([d[f"Q1|{r}|{n}"] for d in du])
        stats.append(Statistic(f"R_pop|{r}|{n}", rc, "HELD"))
        stats.append(Statistic(f"G|{r}|{n}", ru - rc, "HELD"))
        gaps[(r, n)] = float(ref[f"Delta|{r}|{n}"].mean())
    return stats, gaps


def analyse_q1(cfg: Stage1Config, jobs: list[Job], out: Path, alpha: float | None = None, label: str = "q1") -> dict:
    per_rep = []
    for rep in range(cfg.replicates):
        stats, gaps = q1_family(cfg, jobs, out, rep)
        rng = NamedStreams(roots(cfg, 0)["bootstrap"]).stream(f"stage1_bootstrap_{label}", rep)
        c, diag = critical_value_bootstrap(stats, cfg.alpha_q1 if alpha is None else alpha, cfg.bootstrap_draws, rng)
        est = {s.name: two_level(s.values) for s in stats}
        cells = {}
        for r, n in Q1_CELLS:
            rp, g = band(*est[f"R_pop|{r}|{n}"], c), band(*est[f"G|{r}|{n}"], c)
            cells[f"{r}|{n}"] = {"class": classify_q1_held(rp, g, gaps[(r, n)], cfg.epsilon), "Delta": gaps[(r, n)],
                                 "R_pop": asdict(rp), "G": asdict(g)}
        per_rep.append({"critical_value": c, "bootstrap": diag, "cells": cells})
    confirmed = {}
    for key in per_rep[0]["cells"]:
        cls = {p["cells"][key]["class"] for p in per_rep}
        confirmed[key] = cls.pop() if len(cls) == 1 else "INCONCLUSIVE (discordant)"
    pop_n = sum(v == "POP-LIKE" for v in confirmed.values())
    stab_n = sum(v == "STAB-LIKE" for v in confirmed.values())
    if pop_n >= 7 and stab_n == 0:
        answer = "CONT behaves like population Bayes"
    elif stab_n >= 7 and pop_n == 0:
        answer = "CONT behaves like the context-only comparator"
    else:
        answer = "mixed or inconclusive"
    return {"replicates": per_rep, "confirmed": confirmed, "answer": answer, "pop_like": pop_n, "stab_like": stab_n}


def _mirror(b: Band) -> Band:
    return Band(-b.estimate, -b.hi, -b.lo)


def q2_family(cfg: Stage1Config, jobs: list[Job], out: Path, rep: int) -> tuple[list[Statistic], dict]:
    """Q2 statistics for every LIB arm and cell. Arm-level gate (PREREG 6.2 as revised before the freeze): a (K, cell)
    is analysed if >= 90% of the arm's models have both library separations (lib vs pop, lib vs stab; mean min-KL over
    the cell's systems) >= delta; otherwise it is GATED OUT and reported. All of the arm's models enter a kept cell."""
    stats, meta = [], {}
    for arm in sorted({j.arm for j in jobs if j.arm.startswith("LIB-")}, key=lambda a: int(a.split("-")[1])):
        js = sorted((j for j in jobs if j.replicate == rep and j.arm == arm), key=lambda j: j.seed_index)
        if not js:
            continue
        ds = [_load(j.eval_file(out, j.steps)) for j in js]
        for s, r, n in Q2_CELLS:
            key = f"{s}|{r}|{n}"
            sep_lp = np.array([d[f"SEP|{key}|lib-pop"].mean() for d in ds])
            sep_ls = np.array([d[f"SEP|{key}|lib-stab"].mean() for d in ds])
            frac = float(np.mean((sep_lp >= cfg.delta) & (sep_ls >= cfg.delta)))
            sep_ps = float(_load(out / "eval" / f"R{rep + 1}" / "reference.npz")[f"SEP|{key}|pop-stab"].mean())
            meta[(arm, key)] = {"gate_fraction": frac, "kept": frac >= 0.9, "sep_lib_pop": float(sep_lp.mean()),
                                "sep_lib_stab": float(sep_ls.mean()), "sep_pop_stab": sep_ps}
            if frac < 0.9:
                continue
            d = {name: np.stack([x[f"Q2|{key}|{name}"] for x in ds]) for name in ("lib", "pop", "stab")}
            for name, arr in (("D_lib", d["lib"]), ("D_pop", d["pop"]), ("D_stab", d["stab"]),
                              ("C_pop_lib", d["pop"] - d["lib"]), ("C_stab_lib", d["stab"] - d["lib"])):
                stats.append(Statistic(f"{arm}|{key}|{name}", arr, f"{s}|{r}"))
    return stats, meta


def analyse_q2(cfg: Stage1Config, jobs: list[Job], out: Path, alpha: float | None = None, label: str = "q2") -> dict:
    per_rep = []
    for rep in range(cfg.replicates):
        stats, meta = q2_family(cfg, jobs, out, rep)
        cells = {}
        c = None
        if stats:
            rng = NamedStreams(roots(cfg, 0)["bootstrap"]).stream(f"stage1_bootstrap_{label}", rep)
            c, _ = critical_value_bootstrap(stats, cfg.alpha_q2 if alpha is None else alpha, cfg.bootstrap_draws, rng)
            est = {s.name: two_level(s.values) for s in stats}
        for (arm, key), mt in meta.items():
            if not mt["kept"]:
                cells[f"{arm}|{key}"] = {"class": "GATED OUT", **mt}
                continue
            b = {nm: band(*est[f"{arm}|{key}|{nm}"], c) for nm in ("D_lib", "D_pop", "D_stab", "C_pop_lib", "C_stab_lib")}
            dist = {"lib": b["D_lib"], "pop": b["D_pop"], "stab": b["D_stab"]}
            con = {("pop", "lib"): b["C_pop_lib"], ("lib", "pop"): _mirror(b["C_pop_lib"]),
                   ("stab", "lib"): b["C_stab_lib"], ("lib", "stab"): _mirror(b["C_stab_lib"])}
            sep = {("lib", "pop"): mt["sep_lib_pop"], ("lib", "stab"): mt["sep_lib_stab"], ("pop", "stab"): mt["sep_pop_stab"]}
            cells[f"{arm}|{key}"] = {"class": classify_memorisation(dist, con, sep), **mt,
                                     **{nm: asdict(v) for nm, v in b.items()}}
        per_rep.append({"critical_value": c, "cells": cells})
    confirmed = {}
    for key in per_rep[0]["cells"]:
        cls = {p["cells"][key]["class"] for p in per_rep}
        confirmed[key] = cls.pop() if len(cls) == 1 else "INCONCLUSIVE (discordant)"
    per_k = {}
    for arm in sorted({j.arm for j in jobs if j.arm.startswith("LIB-")}, key=lambda a: int(a.split("-")[1])):
        vals = [v for k, v in confirmed.items() if k.startswith(arm + "|") and v != "GATED OUT"]
        if not vals:
            per_k[arm] = "NO CELLS"
            continue
        top = max(set(vals), key=vals.count)
        per_k[arm] = top if vals.count(top) >= math.ceil(0.7 * len(vals)) else "MIXED"
    ks = sorted((int(a.split("-")[1]), v) for a, v in per_k.items())
    k_star = None
    for i, (k, v) in enumerate(ks):
        if v == "GENERALISING" and all(w != "LIB-LIKE" for _, w in ks[i + 1:]):
            k_star = k
            break
    if all(v == "LIB-LIKE" for _, v in ks):
        answer = "no transition up to the largest K"
    elif k_star is None:
        answer = "no clean transition"
    else:
        answer = f"K* = {k_star}"
    return {"replicates": per_rep, "confirmed": confirmed, "per_K": per_k, "K_star": k_star, "answer": answer}


def controls_and_validity(cfg: Stage1Config, jobs: list[Job], out: Path) -> dict:
    """C1, C2 (Bonferroni over all control statistics at 0.05) and V-RB (familywise 0.001) for every replicate."""
    from scipy.stats import norm
    arms = sorted({j.arm for j in jobs})
    n_c = cfg.replicates * (len(arms) + len(C1_CELLS))
    z = float(norm.isf(0.05 / (2 * n_c)))
    n_rb = cfg.replicates * 2 * len(Q1_CELLS)
    z_rb = float(norm.isf(0.001 / (2 * n_rb)))
    res = {"controls": {}, "v_rb": {}, "z_controls": z, "z_rb": z_rb}
    ok = True
    for rep in range(cfg.replicates):
        for a in arms:
            js = [j for j in jobs if j.replicate == rep and j.arm == a]
            data = [_load(j.eval_file(out, j.steps)) for j in js]
            passed, upper = control_pass([d["C2"] for d in data], cfg.epsilon, z)
            res["controls"][f"R{rep + 1}|C2|{a}"] = {"pass": passed, "upper": upper}
            ok &= passed
            if a == "UNIF":
                for r, n in C1_CELLS:
                    passed, upper = control_pass([d[f"C1|{r}|{n}"] for d in data], cfg.epsilon, z)
                    res["controls"][f"R{rep + 1}|C1|{r}|{n}"] = {"pass": passed, "upper": upper}
                    ok &= passed
            if a in ("CONT", "UNIF"):
                for r, n in Q1_CELLS:
                    diff = np.stack([d[f"Q1R|{r}|{n}"] - d[f"Q1|{r}|{n}"] for d in data])
                    theta, se = two_level(diff)
                    zz = theta / se
                    res["v_rb"][f"R{rep + 1}|{a}|{r}|{n}"] = {"z": zz, "pass": abs(zz) <= z_rb}
                    ok &= abs(zz) <= z_rb
    res["all_pass"] = bool(ok)
    return res


def verdict(checks: dict, q1: dict | None, q2: dict | None, decision: dict) -> str:
    """BLOCKED, NOT RESOLVABLE, PROCEED, REVISE (PREREG section 8)."""
    if not checks["all_pass"]:
        return "BLOCKED"
    if decision.get("status") != "RESOLVED":
        return "NOT RESOLVABLE"
    decisive_q1 = q1 is not None and q1["answer"] != "mixed or inconclusive"
    q2_kstar = q2 is not None and q2["K_star"] is not None
    return "PROCEED" if (decisive_q1 or q2_kstar) else "REVISE"


def analyse_behavioural(cfg: Stage1Config, jobs: list[Job], out: Path, alpha: float) -> dict:
    """Secondary Q1-behavioural: CONT and UNIF models vs pop and stab on PROBE / OOS cells (classify_behavioural)."""
    per_rep = []
    for rep in range(cfg.replicates):
        ref = _load(out / "eval" / f"R{rep + 1}" / "reference.npz")
        stats, sep = [], {}
        for arm in ("CONT", "UNIF"):
            js = sorted((j for j in jobs if j.replicate == rep and j.arm == arm), key=lambda j: j.seed_index)
            ds = [_load(j.eval_file(out, j.steps)) for j in js]
            for s, r, n in BEHAV_CELLS:
                key = f"{s}|{r}|{n}"
                dp = np.stack([d[f"B|{key}|pop"] for d in ds])
                dst = np.stack([d[f"B|{key}|stab"] for d in ds])
                stats += [Statistic(f"{arm}|{key}|D_pop", dp, f"{s}|{r}"),
                          Statistic(f"{arm}|{key}|D_stab", dst, f"{s}|{r}"),
                          Statistic(f"{arm}|{key}|C_stab_pop", dst - dp, f"{s}|{r}")]
                sep[key] = float(ref[f"SEP|{key}|pop-stab"].mean())
        rng = NamedStreams(roots(cfg, 0)["bootstrap"]).stream("stage1_bootstrap_behavioural", rep)
        c, _ = critical_value_bootstrap(stats, alpha, cfg.bootstrap_draws, rng)
        est = {st.name: two_level(st.values) for st in stats}
        cells = {}
        for arm in ("CONT", "UNIF"):
            for s, r, n in BEHAV_CELLS:
                key = f"{s}|{r}|{n}"
                if sep[key] < cfg.delta:
                    cells[f"{arm}|{key}"] = "UNIDENTIFIABLE (pop-stab separation < delta)"
                    continue
                dist = {"pop": band(*est[f"{arm}|{key}|D_pop"], c), "stab": band(*est[f"{arm}|{key}|D_stab"], c)}
                cs = band(*est[f"{arm}|{key}|C_stab_pop"], c)
                cells[f"{arm}|{key}"] = classify_behavioural(dist, {("stab", "pop"): cs, ("pop", "stab"): _mirror(cs)},
                                                             {("pop", "stab"): sep[key]})
        per_rep.append({"critical_value": c, "cells": cells})
    confirmed = {k: (per_rep[0]["cells"][k] if all(p["cells"][k] == per_rep[0]["cells"][k] for p in per_rep)
                     else "INCONCLUSIVE (discordant)") for k in per_rep[0]["cells"]}
    return {"replicates": per_rep, "confirmed": confirmed}


def analyse_secondary(cfg: Stage1Config, jobs: list[Job], out: Path, decision: dict) -> dict:
    """Every retained secondary family at alpha_secondary_total / len(cfg.secondary) per replicate; variants within a
    family split that level (Bonferroni)."""
    alpha = cfg.alpha_secondary_total / len(cfg.secondary)
    b = int(decision["B"])
    prim = primary_jobs(cfg, jobs, decision)
    res = {}
    for fam in decision.get("secondary_kept", []):
        if fam == "Q1-behavioural":
            res[fam] = analyse_behavioural(cfg, [j for j in prim if j.arm in ("CONT", "UNIF")], out, alpha)
            continue
        variants = sorted({size for _, size, _ in SECONDARY[fam]})
        res[fam] = {}
        for size in variants:
            spec = {(a, m) for a, s, m in SECONDARY[fam] if s == size}
            vj = [j for j in jobs if j.size == size and (j.arm, j.steps // b) in spec and j.steps % b == 0]
            if size == cfg.model:
                vj = [j for j in vj if j.steps != b]          # the 4B family must not reuse primary models
            if not vj:
                continue
            label = f"{fam}_{size}"
            res[fam][size] = (analyse_q2(cfg, vj, out, alpha / len(variants), label) if fam == "Q2-size-L"
                              else analyse_q1(cfg, vj, out, alpha / len(variants), label))
    return res
