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
from dynaicl_neural.analysis import (Band, Statistic, band, classify_memorisation, classify_q1_held, critical_value_bootstrap,
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

    def model_dir(self, out: Path) -> Path:
        return out / "models" / f"R{self.replicate + 1}" / self.arm / self.size / f"seed{self.seed_index}"

    def eval_file(self, out: Path, step: int) -> Path:
        return out / "eval" / f"R{self.replicate + 1}" / self.arm / self.size / f"seed{self.seed_index}" / f"step{step}.npz"


def roots(cfg: Stage1Config, replicate: int) -> dict[str, int]:
    return {k: role_seed(v, replicate) for k, v in cfg.seed_roles.items()}


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
    return jobs


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
    f = job.eval_file(out, step)
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
            vals = [_load(j.eval_file(out, step))["C2"] for j in by_arm[a]]
            passed, upper = control_pass(vals, cfg.epsilon, z)
            flags[f"C2|{a}|{step}"] = {"pass": passed}
            ok &= passed
            if a == "UNIF":
                for r, n in C1_CELLS:
                    passed, _ = control_pass([_load(j.eval_file(out, step))[f"C1|{r}|{n}"] for j in by_arm[a]],
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

def q1_family(cfg: Stage1Config, jobs: list[Job], out: Path, rep: int, step: int) -> tuple[list[Statistic], dict]:
    cont = sorted((j for j in jobs if j.replicate == rep and j.arm == "CONT"), key=lambda j: j.seed_index)
    unif = sorted((j for j in jobs if j.replicate == rep and j.arm == "UNIF"), key=lambda j: j.seed_index)
    if [j.seed_index for j in cont] != [j.seed_index for j in unif]:
        raise ValueError("CONT and UNIF seed indices must match (pairing)")
    dc = [_load(j.eval_file(out, step)) for j in cont]
    du = [_load(j.eval_file(out, step)) for j in unif]
    ref = _load(out / "eval" / f"R{rep + 1}" / "reference.npz")
    stats, gaps = [], {}
    for r, n in Q1_CELLS:
        rc = np.stack([d[f"Q1|{r}|{n}"] for d in dc])
        ru = np.stack([d[f"Q1|{r}|{n}"] for d in du])
        stats.append(Statistic(f"R_pop|{r}|{n}", rc, "HELD"))
        stats.append(Statistic(f"G|{r}|{n}", ru - rc, "HELD"))
        gaps[(r, n)] = float(ref[f"Delta|{r}|{n}"].mean())
    return stats, gaps


def analyse_q1(cfg: Stage1Config, jobs: list[Job], out: Path, step: int) -> dict:
    per_rep = []
    for rep in range(cfg.replicates):
        stats, gaps = q1_family(cfg, jobs, out, rep, step)
        rng = NamedStreams(roots(cfg, 0)["bootstrap"]).stream("stage1_bootstrap_q1", rep)
        c, diag = critical_value_bootstrap(stats, cfg.alpha_q1, cfg.bootstrap_draws, rng)
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
