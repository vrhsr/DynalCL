"""Stage 0.6 noisy-observation probe: the frozen confirmatory runner (docs/PREREG_stage06.md + AMENDMENT_1).

    python -m dynaicl.experiments.stage06_probe verify  --config C --manifest M --expected-manifest-sha256 H
    python -m dynaicl.experiments.stage06_probe qualify --config C --manifest M --expected-manifest-sha256 H --out Q.json
    python -m dynaicl.experiments.stage06_probe run     --config C --manifest M --expected-manifest-sha256 H \
                                                          --checkpoint-dir D [--qualification Q.json] [--workers K]
    python -m dynaicl.experiments.stage06_probe analyze --config C --manifest M --expected-manifest-sha256 H --checkpoint-dir D
    (confirmatory config only, additionally:  --authorization A.json --snapshot S.zip   and the key in $DYNAICL_STAGE06_AUTH_KEY)

Outcomes (stage06_errors): ``REFUSED`` (exit 3, policy and guard failures) and ``CORRUPT`` (exit 4, integrity failures of data the
runner reads). Each names the offending path and the reason, writes nothing, and is raised at the specific check that failed.

Pre-flight (every command):
* the manifest's SHA-256 equals the expected value supplied OUTSIDE the workspace; every manifest file exists with
  its recorded SHA-256; the config's hash is one of the frozen config hashes, for the config's mode;
* seeds: the config's seeds are exactly the seed-role table's allocation for the mode, and no seed appears in two roles;
* environment: identical to the frozen environment manifest, or a passing qualification report produced by
  ``qualify`` in THIS environment for THIS manifest and config. A supplied qualification path must exist and be valid;
* checkpoints (resume): schema version, config hash, manifest hash, unit identity, array shapes / dtypes and the
  SHA-256 of every stored array file must match; unreadable, truncated or malformed unit files are CORRUPT. A mismatch is never
  repaired automatically;
* confirmatory ``run`` / ``analyze``: a valid authorization artifact (stage06_authorization), verified at start (including every
  resume) and again at completion; one run id per checkpoint directory; pilot and test configs take no authorization;
* ``analyze`` refuses while any unit is missing.
Test mode (pytest, validation seeds) may skip the manifest; confirmatory and pilot modes may not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing
import os
import platform
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from importlib import metadata
from pathlib import Path

import numpy as np
import yaml

from dynaicl.baselines.family import build_context_only_family
from dynaicl.config import stage06_seed_roles as SR
from dynaicl.config.schema import ConfigError
from dynaicl.config.stage06_schema import Stage06Config, stage06_config_from_dict
from dynaicl.evaluation import noisy_harness as nh
from dynaicl.experiments import stage06_analysis as A
from dynaicl.experiments import stage06_authorization as AU
from dynaicl.experiments.stage06_errors import Corrupt, Refusal
from dynaicl.metrics import calibration
from dynaicl.provenance import RunRecorder, sha256_file
from dynaicl.references import kalman_quadrature as kq
from dynaicl.references.matched import assert_matched
from dynaicl.rng import NamedStreams
from dynaicl.systems.noisy import (NoisyObservationCondition, NoisyObservationModel, assert_no_obs_noise_overlap,
                                   generate_noisy_split)
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import SplitRole, assert_no_unintended_overlap
from dynaicl.validation import checks_stage06 as C

ROOT = Path(__file__).resolve().parents[2]
UNIT_SCHEMA = "stage06-unit/v2"
MANIFEST_SCHEMA = "stage06-freeze-manifest/v1"
ENV_KEYS = ("python", "implementation", "numpy", "scipy", "pyyaml", "system", "machine")
SEED_ROLES = SR.MODE_ROLES
QUALIFICATION_CHECKS = ("V4", "V6", "V11", "V13")
SEED_TABLE_REL = "config/stage06_seed_manifest.yaml"


# ------------------------------------------------------------------------------------------ pre-flight


def current_environment() -> dict:
    def ver(name):
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "numpy": ver("numpy"), "scipy": ver("scipy"), "pyyaml": ver("pyyaml"),
            "system": platform.system(), "machine": platform.machine()}


def read_json_object(path, what: str) -> dict:
    """Read a JSON object file; every failure is a named CORRUPT (or REFUSED when the file is absent)."""
    p = Path(path)
    try:
        raw = p.read_bytes()
    except FileNotFoundError:
        raise Refusal(f"{what} not found", p)
    except OSError as exc:
        raise Refusal(f"{what} cannot be read ({type(exc).__name__})", p)
    if not raw.strip():
        raise Corrupt(f"{what} is empty", p)
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Corrupt(f"{what} is not valid JSON ({type(exc).__name__}: truncated or damaged?)", p)
    if not isinstance(obj, dict):
        raise Corrupt(f"{what} is not a JSON object", p)
    return obj


def load_config_once(path) -> tuple[Stage06Config, str]:
    """Read the config file ONCE: returns the validated config and the SHA-256 of exactly the bytes that were parsed."""
    p = Path(path)
    try:
        raw = p.read_bytes()
    except FileNotFoundError:
        raise Refusal("config file not found", p)
    except OSError as exc:
        raise Refusal(f"config file cannot be read ({type(exc).__name__})", p)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise Corrupt(f"config file is not valid YAML ({type(exc).__name__})", p)
    try:
        cfg = stage06_config_from_dict(data)
    except ConfigError as exc:
        raise Refusal(f"config file violates the Stage 0.6 schema: {exc}", p)
    return cfg, hashlib.sha256(raw).hexdigest()


def verify_manifest(manifest_path: Path, expected_sha256: str, root: Path | None = None) -> dict:
    root = ROOT if root is None else root
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise Refusal("freeze manifest not found", manifest_path)
    sha = sha256_file(manifest_path)
    if sha != (expected_sha256 or "").strip().lower():
        raise Refusal(f"manifest fingerprint mismatch: file {sha} != expected {expected_sha256}", manifest_path)
    m = read_json_object(manifest_path, "freeze manifest")
    if m.get("schema") != MANIFEST_SCHEMA:
        raise Refusal(f"incompatible manifest schema {m.get('schema')!r}", manifest_path)
    if not isinstance(m.get("files"), dict) or not isinstance(m.get("config_hashes"), dict) \
            or not isinstance(m.get("environment_manifest"), str) or not isinstance(m.get("created_utc"), str):
        raise Corrupt("freeze manifest lacks the fields files / config_hashes / environment_manifest / created_utc", manifest_path)
    bad = []
    for rel, h in sorted(m["files"].items()):
        p = root / rel
        if not p.is_file():
            bad.append(f"missing {rel}")
        elif sha256_file(p) != h:
            bad.append(f"changed {rel}")
    if bad:
        raise Refusal(f"fingerprint mismatch in {len(bad)} frozen file(s): " + "; ".join(bad[:10]), manifest_path)
    return {**m, "manifest_sha256": sha}


def check_config_frozen(cfg: Stage06Config, manifest: dict) -> None:
    frozen = manifest.get("config_hashes", {})
    match = [rel for rel, v in frozen.items() if v["config_hash"] == cfg.config_hash() and v["mode"] == cfg.experiment.mode]
    if not match:
        raise Refusal(f"config hash {cfg.config_hash()[:16]} (mode {cfg.experiment.mode}) is not a frozen config")


def check_seeds(cfg: Stage06Config, seed_manifest: Path) -> dict:
    roles = SR.load_roles(seed_manifest, strict=False)
    return SR.check_mode_seeds(roles, cfg.experiment.mode, list(cfg.seeds.evaluation), cfg.seeds.bootstrap)


def read_qualification(path, manifest: dict, cfg: Stage06Config, cur: dict) -> dict:
    """A supplied qualification report must exist and be well formed, and be bound to THIS environment, manifest and config."""
    p = Path(path)
    q = read_json_object(p, "qualification report")
    need = {"environment": dict, "manifest_sha256": str, "config_hash": str, "passed": bool}
    for k, t in need.items():
        if k not in q or isinstance(q[k], bool) != (t is bool) or not isinstance(q[k], t):
            raise Corrupt(f"qualification report: field {k!r} is missing or has the wrong type", p)
    if q["environment"] != cur:
        raise Refusal("qualification report was produced in a different environment (stale)", p)
    if q["manifest_sha256"] != manifest["manifest_sha256"] or q["config_hash"] != cfg.config_hash():
        raise Refusal("qualification report is for a different manifest or config (stale)", p)
    if q["passed"] is not True:
        raise Refusal("qualification report did not pass", p)
    return q


def check_environment(manifest: dict | None, qualification: Path | None, cfg: Stage06Config, root: Path | None = None) -> dict:
    root = ROOT if root is None else root
    cur = current_environment()
    if manifest is None:
        if qualification is not None:
            raise Refusal("test mode takes no qualification report")
        return {"status": "unchecked (test mode, no manifest)", "environment": cur}
    env_path = root / manifest["environment_manifest"]
    frozen = read_json_object(env_path, "frozen environment manifest").get("environment")
    if not isinstance(frozen, dict):
        raise Corrupt("frozen environment manifest has no 'environment' object", env_path)
    diffs = {k: [frozen.get(k), cur.get(k)] for k in ENV_KEYS if frozen.get(k) != cur.get(k)}
    if qualification is not None:
        if diffs:
            read_qualification(qualification, manifest, cfg, cur)
        else:
            read_json_object(qualification, "qualification report")
    if not diffs:
        return {"status": "identical", "environment": cur}
    if qualification is None:
        raise Refusal(f"environment differs from the frozen environment manifest {diffs}; run `qualify` in this "
                      "environment and pass --qualification")
    return {"status": "qualified", "differences": diffs, "environment": cur,
            "qualification_sha256": sha256_file(Path(qualification))}


def preflight(cfg: Stage06Config, manifest_path, expected_sha, qualification=None, root: Path | None = None) -> dict:
    root = ROOT if root is None else root
    manifest = None
    if manifest_path is not None or cfg.experiment.mode != "test":
        if manifest_path is None or expected_sha is None:
            raise Refusal(f"mode {cfg.experiment.mode} requires --manifest and --expected-manifest-sha256")
        manifest = verify_manifest(Path(manifest_path), expected_sha, root)
        check_config_frozen(cfg, manifest)
    SR.load_roles(root / SEED_TABLE_REL, strict=True)
    seeds = check_seeds(cfg, root / SEED_TABLE_REL)
    env = check_environment(manifest, qualification, cfg, root)
    return {"manifest_sha256": manifest["manifest_sha256"] if manifest else None, "seeds": seeds, "environment": env,
            "manifest": manifest}


# ------------------------------------------------------------------------------------------ confirmatory authorization


def snapshot_sha256(snapshot, manifest_rel: str, manifest_sha: str) -> str:
    """SHA-256 of the snapshot archive, after checking that the archive holds the very manifest that was verified."""
    p = Path(snapshot)
    if not p.is_file():
        raise Refusal("snapshot archive not found (--snapshot is required for a confirmatory run)", p)
    try:
        with zipfile.ZipFile(p) as z:
            data = z.read(manifest_rel)
    except KeyError:
        raise Refusal(f"snapshot archive does not contain the manifest {manifest_rel}", p)
    except (zipfile.BadZipFile, OSError) as exc:
        raise Corrupt(f"snapshot archive is not a readable zip ({type(exc).__name__})", p)
    if hashlib.sha256(data).hexdigest() != manifest_sha:
        raise Refusal("the manifest inside the snapshot archive differs from the verified manifest", p)
    return sha256_file(p)


def make_binding(cfg: Stage06Config, cfg_file_sha: str, pre: dict, snapshot, manifest_rel: str, root: Path | None = None) -> AU.Binding:
    root = ROOT if root is None else root
    manifest = pre["manifest"]
    prereg, amend = root / AU.PREREG_REL, root / AU.AMENDMENT_REL
    for f in (prereg, amend):
        if not f.is_file():
            raise Refusal("pre-registration document missing", f)
    return AU.Binding(manifest_sha256=manifest["manifest_sha256"],
                      snapshot_sha256=snapshot_sha256(snapshot, manifest_rel, manifest["manifest_sha256"]),
                      config_hash=cfg.config_hash(), config_file_sha256=cfg_file_sha, prereg_sha256=sha256_file(prereg),
                      amendment_sha256=sha256_file(amend), evaluation_seeds=tuple(cfg.seeds.evaluation),
                      bootstrap_seed=cfg.seeds.bootstrap, freeze_created_utc=manifest["created_utc"],
                      qualification_sha256=pre["environment"].get("qualification_sha256"))


def authorize_confirmatory(cfg: Stage06Config, cfg_file_sha: str, args, pre: dict, key: bytes, raw: bytes, *,
                           now=None, root: Path | None = None, allow_test_only: bool = False) -> AU.VerifiedGate:
    """Verify the authorization against the runner's own view of the frozen state. ``raw`` is the artifact's bytes (read once by
    the caller); nothing here reads the artifact file again. ``allow_test_only`` is reachable only from tests."""
    import datetime as dt
    root = ROOT if root is None else root
    try:
        manifest_rel = Path(args.manifest).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        raise Refusal("the manifest must lie inside the frozen tree", args.manifest)
    binding = make_binding(cfg, cfg_file_sha, pre, args.snapshot, manifest_rel, root)
    return AU.verify_authorization(raw, key, binding, now or dt.datetime.now(dt.timezone.utc), path=args.authorization,
                                   allow_test_only=allow_test_only)


def require_gate(cfg: Stage06Config, gate) -> None:
    """API-level guard: confirmatory execution functions refuse to run without a VerifiedGate."""
    if cfg.experiment.mode == "confirmatory" and not isinstance(gate, AU.VerifiedGate):
        raise Refusal("confirmatory execution requires a verified authorization")


# ------------------------------------------------------------------------------------------ units


def build_prior(cfg: Stage06Config) -> StableCoefficientPrior:
    p = cfg.prior
    return StableCoefficientPrior(rho=p.rho, sigma=cfg.model.sigma_w, shape=p.shape, mu0=p.mu0, tau0=p.tau0)


def build_model(cfg: Stage06Config, q: float, r: float) -> NoisyObservationModel:
    return NoisyObservationModel(cfg.model.sigma_w, math.sqrt(q) * cfg.model.sigma_w, r * cfg.model.sigma_w)


def build_settings(cfg: Stage06Config) -> kq.KalmanQuadratureSettings:
    s = cfg.quadrature
    return kq.KalmanQuadratureSettings(s.outer_bound, tuple(s.breakpoints), s.panels_per_unit, s.nodes_per_panel)


def plan_units(cfg: Stage06Config) -> list[tuple]:
    nq, nr = len(cfg.model.noise_ratios), len(cfg.model.initial_state_ratios)
    units = [("integrity",), ("tier1",)]
    units += [("primary", rep, qi, ri) for rep in range(2) for qi in range(nq) for ri in range(nr)]
    if cfg.secondary.naive_n_systems > 0:
        units += [("naive", rep, qi, ri) for rep in range(2) for qi in range(nq) for ri in range(nr)]
    return units


def expected_arrays(cfg: Stage06Config, unit: tuple) -> dict:
    H, N = len(cfg.grid.horizons), cfg.grid.n_systems
    if unit[0] == "primary":
        s = (H, len(cfg.grid.context_lengths), N)
        return {"pop_logscore": (s, "float64"), "stab_logscore": (s, "float64"),
                "pop_pit": (s, "float32"), "stab_pit": (s, "float32")}
    if unit[0] == "naive":
        s = (len(naive_members(cfg)), H, len(cfg.secondary.naive_context_lengths), cfg.secondary.naive_n_systems)
        return {"naive_logscore": (s, "float64"), "naive_pit": (s, "float32")}
    return {}


def naive_members(cfg: Stage06Config) -> list[str]:
    return sorted(build_context_only_family(cfg.model.sigma_w, stability_bound=cfg.comparator.stability_bound))


def _split(cfg: Stage06Config, rep: int, q: float, r: float, n_items: int):
    cond = NoisyObservationCondition(build_prior(cfg), build_model(cfg, q, r))
    return cond, generate_noisy_split(cond, SplitRole.EVALUATION, NamedStreams(cfg.seeds.evaluation[rep]), n_items,
                                      cfg.grid.trajectory_length)


def run_primary(cfg: Stage06Config, rep: int, qi: int, ri: int) -> tuple[dict, dict]:
    q, r = cfg.model.noise_ratios[qi], cfg.model.initial_state_ratios[ri]
    ns, hs, N = cfg.grid.context_lengths, cfg.grid.horizons, cfg.grid.n_systems
    cond, split = _split(cfg, rep, q, r, N)
    eset = nh.build_noisy_evaluation(split, ns, hs)
    settings = build_settings(cfg)
    pop = kq.noisy_population_reference(build_prior(cfg), cond.model, settings)
    assert_matched(pop, cond)
    stab = kq.noise_aware_stability_predictor(cond.model, bound=cfg.comparator.stability_bound, settings=settings)
    sp, ss = nh.score_noisy_batch(pop, eset), nh.score_noisy_batch(stab, eset)
    arr = {k: np.empty(expected_arrays(cfg, ("primary",))[k][0], dtype=expected_arrays(cfg, ("primary",))[k][1])
           for k in ("pop_logscore", "stab_logscore", "pop_pit", "stab_pit")}
    for hi, h in enumerate(hs):
        for ni, n in enumerate(ns):
            arr["pop_logscore"][hi, ni], arr["pop_pit"][hi, ni] = sp[(n, h)]
            arr["stab_logscore"][hi, ni], arr["stab_pit"][hi, ni] = ss[(n, h)]
    # in-run checks (never effect sizes)
    cal = [{"n": n, "h": h, "ks_p": calibration.ks_uniform_pvalue(sp[(n, h)][1])}
           for n in cfg.checks.calibration_context_lengths for h in hs]
    k = min(cfg.checks.numerical_items, N)
    tg = {key: v[:k] for key, v in eset._targets.items()}
    fine_p = pop.with_settings(settings.refined(2)).batch_scores(eset.context_matrix[:k], tg, ns, hs)
    fine_s = stab.with_settings(settings.refined(2)).batch_scores(eset.context_matrix[:k], tg, ns, hs)
    num = {"items": k, "max_gain_change": 0.0, "max_pop_change": 0.0, "max_stab_change": 0.0}
    for key in sp:
        dp, ds = fine_p[key][0] - sp[key][0][:k], fine_s[key][0] - ss[key][0][:k]
        num["max_gain_change"] = max(num["max_gain_change"], float(np.max(np.abs(dp - ds))))
        num["max_pop_change"] = max(num["max_pop_change"], float(np.max(np.abs(dp))))
        num["max_stab_change"] = max(num["max_stab_change"], float(np.max(np.abs(ds))))
    kr = min(cfg.checks.reproducibility_items, N)
    probe_ns = tuple(sorted({ns[0], ns[len(ns) // 2], ns[-1]}))
    rp = nh.score_noisy_per_context(pop, eset, ns=probe_ns, items=range(kr))
    rs_ = nh.score_noisy_per_context(stab, eset, ns=probe_ns, items=range(kr))
    rep_diff = max(max(float(np.max(np.abs(rp[key][j] - sp[key][j][:kr]))),
                       float(np.max(np.abs(rs_[key][j] - ss[key][j][:kr])))) for key in rp for j in (0, 1))
    meta = {"q": q, "r": r, "replicate": rep, "calibration": cal, "numerics": num,
            "reproducibility": {"items": kr, "context_lengths": list(probe_ns), "max_abs_diff": rep_diff},
            "reference_matched": True, "n_systems": N}
    return meta, arr


def run_naive(cfg: Stage06Config, rep: int, qi: int, ri: int) -> tuple[dict, dict]:
    q, r = cfg.model.noise_ratios[qi], cfg.model.initial_state_ratios[ri]
    hs, ns = cfg.grid.horizons, cfg.secondary.naive_context_lengths
    k = cfg.secondary.naive_n_systems
    _, split = _split(cfg, rep, q, r, cfg.grid.n_systems)
    eset = nh.build_noisy_evaluation(split, ns, hs)
    family = build_context_only_family(cfg.model.sigma_w, stability_bound=cfg.comparator.stability_bound)
    names = naive_members(cfg)
    spec = expected_arrays(cfg, ("naive",))
    arr = {key: np.empty(s, dtype=d) for key, (s, d) in spec.items()}
    for mi, name in enumerate(names):
        sc = nh.score_noisy_per_context(family[name], eset, ns=ns, items=range(k))
        for hi, h in enumerate(hs):
            for ni, n in enumerate(ns):
                arr["naive_logscore"][mi, hi, ni], arr["naive_pit"][mi, hi, ni] = sc[(n, h)]
    return {"q": q, "r": r, "replicate": rep, "members": names, "label": "secondary, noise-misspecified (noise-naive)",
            "n_systems": k}, arr


def run_integrity(cfg: Stage06Config) -> tuple[dict, dict]:
    """Independence of the confirmatory replicates from each other, from the selection split and from the Stage 0.5
    systems used by Tier-2; and distinct systems within each replicate (independent system-level units)."""
    roles = yaml.safe_load((ROOT / "config" / "stage06_seed_manifest.yaml").read_text(encoding="utf-8"))["roles"]
    q, r = cfg.model.noise_ratios[1], cfg.model.initial_state_ratios[0]
    N = cfg.grid.n_systems
    det, ok = {}, True
    cond, s1 = _split(cfg, 0, q, r, N)
    _, s2 = _split(cfg, 1, q, r, N)
    others = {"R1_vs_R2": (s1, s2)}
    for seed in roles["selection"]["seeds"]:
        sel = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(seed), N, cfg.grid.trajectory_length)
        others[f"R1_vs_selection_{seed}"] = (s1, sel)
        others[f"R2_vs_selection_{seed}"] = (s2, sel)
    cond0 = NoisyObservationCondition(build_prior(cfg), build_model(cfg, 0.0, r))
    s05 = yaml.safe_load((ROOT / cfg.tier2.stage05_run / "config.yaml").read_text(encoding="utf-8"))
    s05_len = max(s05["grid"]["context_lengths"]) + max(s05["grid"]["horizons"])
    for seed in s05["seeds"]["evaluation"]:      # the Stage 0.5 evaluation roots behind the Tier-2 reference values
        old = generate_noisy_split(cond0, SplitRole.EVALUATION, NamedStreams(seed), s05["replication"]["n_eval_items"],
                                   s05_len)
        others[f"R1_vs_stage05_{seed}"] = (s1, old)
        others[f"R2_vs_stage05_{seed}"] = (s2, old)
    for name, (a, b) in others.items():
        try:
            assert_no_unintended_overlap(a.latent, b.latent)
            assert_no_obs_noise_overlap(a, b)
            det[name] = "disjoint"
        except Exception as exc:      # recorded, never swallowed: ok = False makes the verdict BLOCKED
            det[name] = f"OVERLAP: {type(exc).__name__}: {exc}"
            ok = False
    for tag, s in (("R1", s1), ("R2", s2)):
        distinct = len(s.latent.trajectory_hashes()) == N and len(np.unique(s.latent.coefficients)) == N
        det[f"{tag}_distinct_systems"] = distinct
        ok &= distinct
    return {"ok": bool(ok), "details": det}, {}


def run_tier1(cfg: Stage06Config) -> tuple[dict, dict]:
    res = C.check_tier1_regression_stage05(ROOT / cfg.tier2.stage05_run, n_items=cfg.checks.tier1_items)
    tol_ok = res.details["tolerance"] == cfg.checks.tier1_tolerance
    return {"passed": bool(res.passed and tol_ok), "details": res.details, "tolerance_matches_config": tol_ok}, {}


def run_unit(cfg_dict: dict, unit: tuple) -> tuple[dict, dict, float]:
    cfg = stage06_config_from_dict(cfg_dict)
    t0 = time.time()
    kind = unit[0]
    if kind == "primary":
        meta, arr = run_primary(cfg, *unit[1:])
    elif kind == "naive":
        meta, arr = run_naive(cfg, *unit[1:])
    elif kind == "integrity":
        meta, arr = run_integrity(cfg)
    elif kind == "tier1":
        meta, arr = run_tier1(cfg)
    else:
        raise ValueError(f"unknown unit {unit}")
    return meta, arr, round(time.time() - t0, 2)


# ------------------------------------------------------------------------------------------ checkpoints


def unit_name(unit: tuple) -> str:
    return "_".join(map(str, unit))


def checkpoint_root(checkpoint_dir: Path, cfg: Stage06Config) -> Path:
    return Path(checkpoint_dir) / cfg.config_hash()[:16]


def record_checksum(record: dict) -> str:
    """SHA-256 of the canonical JSON of a unit record without its own checksum field (metadata is verified, not only the arrays)."""
    body = {k: v for k, v in record.items() if k != "record_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=True).encode("utf-8")).hexdigest()


def save_unit(ckpt: Path, unit: tuple, meta: dict, arrays: dict, seconds: float, cfg: Stage06Config,
              manifest_sha: str | None) -> None:
    """Arrays first (atomic replace), then the metadata with the arrays' SHA-256 (atomic replace). A unit counts as
    done only when its metadata exists, so an interruption between the two writes simply recomputes the unit."""
    ckpt.mkdir(parents=True, exist_ok=True)
    name = unit_name(unit)
    npz = ckpt / f"{name}.npz"
    tmp = ckpt / f"{name}.npz.tmp"
    with open(tmp, "wb") as fh:
        np.savez(fh, **arrays)
    os.replace(tmp, npz)
    record = {"schema": UNIT_SCHEMA, "config_hash": cfg.config_hash(), "manifest_sha256": manifest_sha,
              "unit": list(unit), "seconds": seconds, "npz_sha256": sha256_file(npz),
              "arrays": {k: [list(v.shape), str(v.dtype)] for k, v in arrays.items()}, "meta": meta}
    record["record_sha256"] = record_checksum(json.loads(json.dumps(record, default=_json_default)))
    tmpj = ckpt / f"{name}.json.tmp"
    tmpj.write_text(json.dumps(record, indent=1, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    os.replace(tmpj, ckpt / f"{name}.json")


UNIT_FIELDS = {"schema": str, "config_hash": str, "unit": list, "seconds": (int, float), "npz_sha256": str, "arrays": dict,
               "meta": dict, "record_sha256": str}


def _check_unit_record(rec: dict, name: str, js: Path) -> None:
    """Field presence and types of a unit metadata record. Missing or wrong-typed fields are CORRUPT."""
    for k, t in UNIT_FIELDS.items():
        if k not in rec:
            raise Corrupt(f"unit metadata lacks the field {k!r}", js)
        v = rec[k]
        if isinstance(v, bool) or not isinstance(v, t):
            raise Corrupt(f"unit metadata field {k!r} has the wrong type ({type(v).__name__})", js)
    if "manifest_sha256" not in rec or not (rec["manifest_sha256"] is None or isinstance(rec["manifest_sha256"], str)):
        raise Corrupt("unit metadata field 'manifest_sha256' is missing or not a string or null", js)
    if not rec["unit"] or not isinstance(rec["unit"][0], str) or not all(
            isinstance(x, int) and not isinstance(x, bool) for x in rec["unit"][1:]):
        raise Corrupt("unit metadata field 'unit' must be [kind, int, ...]", js)
    for k, v in rec["arrays"].items():
        ok = (isinstance(v, list) and len(v) == 2 and isinstance(v[0], list) and isinstance(v[1], str)
              and all(isinstance(x, int) and not isinstance(x, bool) for x in v[0]))
        if not ok:
            raise Corrupt(f"unit metadata arrays entry {k!r} must be [[int, ...], dtype]", js)


def load_unit(ckpt: Path, unit: tuple, cfg: Stage06Config, manifest_sha: str | None):
    """None if the unit is not done (no metadata file). Otherwise a checksum-verified (record, arrays), or REFUSED (policy:
    incompatible schema, other config or manifest) / CORRUPT (integrity: unreadable or truncated JSON, missing or wrong-typed
    fields, unit not matching its file, missing arrays file, checksum mismatch, unreadable arrays, wrong shapes)."""
    name = unit_name(unit)
    js, npz = ckpt / f"{name}.json", ckpt / f"{name}.npz"
    if not js.is_file():
        return None
    rec = read_json_object(js, "unit metadata")
    if not isinstance(rec.get("schema"), str):
        raise Corrupt("unit metadata lacks the string field 'schema'", js)
    if rec["schema"] != UNIT_SCHEMA:
        raise Refusal(f"incompatible output schema {rec['schema']!r} (expected {UNIT_SCHEMA!r})", js)
    _check_unit_record(rec, name, js)
    if record_checksum(rec) != rec["record_sha256"]:
        raise Corrupt("checksum mismatch of the unit metadata (the file was altered or damaged)", js)
    if rec["config_hash"] != cfg.config_hash() or rec["manifest_sha256"] != manifest_sha:
        raise Refusal("checkpoint was produced under a different config or manifest", js)
    if rec["unit"] != list(unit):
        raise Corrupt(f"unit identity {rec['unit']} inside the file does not match its file name {name}", js)
    if not npz.is_file():
        raise Corrupt("the arrays file named by the metadata is missing", npz)
    if sha256_file(npz) != rec["npz_sha256"]:
        raise Corrupt("checksum mismatch of the stored arrays", npz)
    try:
        with np.load(npz, allow_pickle=False) as z:
            arrays = {k: z[k] for k in z.files}
    except (ValueError, OSError, EOFError, zipfile.BadZipFile) as exc:
        raise Corrupt(f"arrays file is unreadable ({type(exc).__name__})", npz)
    exp = expected_arrays(cfg, unit)
    got = {k: (tuple(v.shape), str(v.dtype)) for k, v in arrays.items()}
    if got != {k: (tuple(s), d) for k, (s, d) in exp.items()}:
        raise Corrupt(f"arrays do not match the expected schema: {got} != {exp}", npz)
    return rec, arrays


def scan_checkpoint_dir(ckpt: Path, cfg: Stage06Config) -> None:
    """A checkpoint directory may hold only the planned units (plus the run lock and stale .tmp files, which are overwritten).
    Anything else, for example a second file claiming a unit, is CORRUPT."""
    if not ckpt.is_dir():
        return
    planned = {unit_name(u) for u in plan_units(cfg)}
    for f in sorted(ckpt.iterdir()):
        if f.name == AU.LOCK_NAME or f.name.endswith(".tmp"):
            continue
        stem = f.name[:-5] if f.name.endswith(".json") else f.name[:-4] if f.name.endswith(".npz") else None
        if stem is None or stem not in planned:
            raise Corrupt("unexpected file in the checkpoint directory (not a planned unit)", f)


def run_units(cfg: Stage06Config, ckpt: Path, manifest_sha: str | None, workers: int,
              max_new_units: int | None = None, gate=None) -> dict:
    require_gate(cfg, gate)
    units = plan_units(cfg)
    scan_checkpoint_dir(ckpt, cfg)
    done = {}
    for u in units:
        got = load_unit(ckpt, u, cfg, manifest_sha)
        if got is not None:
            done[u] = got
    print(f"checkpoint {ckpt}: {len(done)}/{len(units)} units already done", flush=True)
    todo = [u for u in units if u not in done]
    if max_new_units is not None:
        todo = todo[:max_new_units]
    t0 = time.time()

    def record(u, meta, arr, secs):
        save_unit(ckpt, u, meta, arr, secs, cfg, manifest_sha)
        done[u] = load_unit(ckpt, u, cfg, manifest_sha)
        print(f"[{len(done):3d}/{len(units)} units, {(time.time() - t0) / 60:6.1f} min] {unit_name(u)} ({secs:.0f}s)",
              flush=True)

    cfg_dict = cfg.to_dict()
    if workers > 1 and len(todo) > 1:
        for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):   # performance only: no
            os.environ.setdefault(var, "1")                                       # oversubscription in workers
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            futures = {pool.submit(run_unit, cfg_dict, u): u for u in todo}
            for fut in as_completed(futures):
                record(futures[fut], *fut.result())          # a failed unit raises here: the run stops, nothing skipped
    else:
        for u in todo:
            record(u, *run_unit(cfg_dict, u))
    return done


# ------------------------------------------------------------------------------------------ analysis


def stage05_tier2_reference(cfg: Stage06Config) -> dict:
    import csv
    run = ROOT / cfg.tier2.stage05_run
    sums = json.loads((run / "checksums.json").read_text(encoding="utf-8"))
    for rel in ("results/item_contrasts.npy", "results/item_contrasts_index.csv"):
        if sha256_file(run / rel) != sums[rel]:
            raise Refusal(f"Stage 0.5 artifact checksum mismatch: {rel}")
    arr = np.load(run / "results" / "item_contrasts.npy")
    with open(run / "results" / "item_contrasts_index.csv", encoding="utf-8") as fh:
        idx = list(csv.DictReader(fh))
    items = {(x["key"].split("|")[0], float(x["r"]), int(x["n"]), int(x["h"])): arr[int(x["row"])]
             for x in idx if x["condition"] == "E-CONT" and x["key"].endswith("matched_minus_frontier_ctx")}
    return {(r, h): np.concatenate([np.mean([items[(rep, r, n, h)] for n in cfg.tier2.context_lengths], axis=0)
                                    for rep in ("R1", "R2")])
            for r in cfg.model.initial_state_ratios for h in cfg.grid.horizons}


def critical_checks(cfg: Stage06Config, done: dict, tier2: dict | None) -> tuple[dict, dict]:
    prim = [rec for u, (rec, _) in done.items() if u[0] == "primary"]
    pvals = [c["ks_p"] for rec in prim for c in rec["meta"]["calibration"]]
    level = cfg.checks.calibration_family_alpha / max(1, len(pvals))
    num = max(rec["meta"]["numerics"]["max_gain_change"] for rec in prim)
    rep = max(rec["meta"]["reproducibility"]["max_abs_diff"] for rec in prim)
    details = {"integrity": done[("integrity",)][0]["meta"], "tier1": done[("tier1",)][0]["meta"],
               "calibration": {"tests": len(pvals), "per_test_level": level, "min_p": min(pvals)},
               "numerics": {"max_gain_change_node_doubling": num, "budget": cfg.checks.error_budget},
               "reproducibility": {"max_abs_diff": rep, "tolerance": cfg.checks.reproducibility_tolerance},
               "tier2": tier2["outcome"] if tier2 else None}
    flags = {"integrity": bool(details["integrity"]["ok"]), "tier1": bool(details["tier1"]["passed"]),
             "calibration": min(pvals) >= level, "numerics": num <= cfg.checks.error_budget,
             "reproducibility": rep <= cfg.checks.reproducibility_tolerance,
             "tier2": tier2 is not None and tier2["outcome"] == "PASS"}
    return flags, details


def gain_items_for(cfg: Stage06Config, done: dict, rep: int) -> dict:
    """{(q, h, r): (N, len(ns)) per-item population - stability gains} for one replicate."""
    out = {}
    for qi, q in enumerate(cfg.model.noise_ratios):
        for ri, r in enumerate(cfg.model.initial_state_ratios):
            u = ("primary", rep, qi, ri)
            if u not in done:
                continue
            arr = done[u][1]
            g = arr["pop_logscore"] - arr["stab_logscore"]
            for hi, h in enumerate(cfg.grid.horizons):
                out[(q, h, r)] = g[hi].T
    return out


def analyze(cfg: Stage06Config, done: dict, gate=None) -> dict:
    require_gate(cfg, gate)
    missing = [unit_name(u) for u in plan_units(cfg) if u not in done]
    if missing:
        raise Refusal(f"missing cells/units ({len(missing)}): {missing[:6]}; resume the run first")
    qs, hs, rs, ns = cfg.model.noise_ratios, cfg.grid.horizons, cfg.model.initial_state_ratios, cfg.grid.context_lengths
    out = {"mode": cfg.experiment.mode}
    if cfg.experiment.mode == "pilot":
        flags, details = critical_checks(cfg, done, None)
        flags.pop("tier2")
        out.update({"critical_checks": flags, "check_details": details,
                    "note": "pilot: runtime and numerics only; no effect estimate is computed"})
        return out
    reps_items = [gain_items_for(cfg, done, rep) for rep in range(2)]
    t2_cols = [list(ns).index(n) for n in cfg.tier2.context_lengths]
    s06 = {(f"R{rep + 1}", r, h): reps_items[rep][(0.0, h, r)][:, t2_cols].mean(axis=1)
           for rep in range(2) for r in rs for h in hs}
    tier2 = A.tier2_compare(s06, stage05_tier2_reference(cfg), cfg.tier2.alpha, cfg.tier2.power, cfg.analysis.delta)
    flags, details = critical_checks(cfg, done, tier2)
    boot = NamedStreams(cfg.seeds.bootstrap)
    an = cfg.analysis
    reps = [A.analyze_replicate(reps_items[rep], ns, cfg.grid.long_context, qs, hs, rs, an.delta, an.alpha,
                                an.bootstrap_draws, an.bootstrap_chunk, an.critical_value_rel_mc_error,
                                boot.stream("stage06_bootstrap", rep)) for rep in range(2)]
    decision = A.decide(reps, flags, qs, hs, rs, an.min_scales)
    curves = [{"replicate": f"R{rep + 1}", "q": q, "h": h, "r": r, **row}
              for rep in range(2) for (q, h, r), x in sorted(reps_items[rep].items()) for row in A.n_curves(x, ns)]
    pooled = []
    for (q, h, r) in sorted(reps_items[0]):
        v = [A.long_context_average(reps_items[k][(q, h, r)], ns, cfg.grid.long_context) for k in range(2)]
        pooled.append({"q": q, "h": h, "r": r, "pooled_gain_descriptive": float(np.mean([x.mean() for x in v]))})
    out.update({"critical_checks": flags, "check_details": details, "tier2": tier2, "decision": decision,
                "replicates": [{k: v for k, v in rp.items() if k != "flags"} | {"flags": {"|".join(map(str, c)): f
                               for c, f in rp["flags"].items()}} for rp in reps],
                "n_curves": curves, "pooled_descriptive": pooled, "naive_secondary": naive_table(cfg, done)})
    return out


def naive_table(cfg: Stage06Config, done: dict) -> list[dict]:
    """Secondary, noise-misspecified: mean of (noise-naive member - noise-aware stability) per cell; descriptive."""
    rows = []
    ns = cfg.grid.context_lengths
    for u, (rec, arr) in sorted(done.items()):
        if u[0] != "naive":
            continue
        _, rep, qi, ri = u
        prim = done[("primary", rep, qi, ri)][1]
        k = rec["meta"]["n_systems"]
        for mi, name in enumerate(rec["meta"]["members"]):
            for hi, h in enumerate(cfg.grid.horizons):
                for ni, n in enumerate(cfg.secondary.naive_context_lengths):
                    d = arr["naive_logscore"][mi, hi, ni] - prim["stab_logscore"][hi, ns.index(n), :k]
                    rows.append({"replicate": f"R{rep + 1}", "q": cfg.model.noise_ratios[qi],
                                 "r": cfg.model.initial_state_ratios[ri], "h": h, "n": n, "member": name,
                                 "mean_naive_minus_noise_aware_stability": float(d.mean()),
                                 "se": float(d.std(ddof=1) / math.sqrt(k)) if k > 1 else float("nan")})
    return rows


# ------------------------------------------------------------------------------------------ report


def render_report(cfg: Stage06Config, res: dict, pre: dict) -> str:
    L = [f"# Stage 0.6: {cfg.experiment.name} ({res['mode']})", "",
         f"Manifest SHA-256: {pre['manifest_sha256']}; config hash {cfg.config_hash()}; environment: "
         f"{pre['environment']['status']}.", ""]
    L += ["## Critical checks", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in res["critical_checks"].items()]
    L += ["", "```", json.dumps(res["check_details"], indent=1, default=_json_default), "```", ""]
    if res["mode"] == "pilot":
        return "\n".join(L + [res["note"], ""])
    d = res["decision"]
    L += [f"## Verdict: **{d['verdict']}**", ""] + [f"- {x}" for x in d["reasons"]]
    L += ["", f"Stricter variant (the same adjacent pair at >= {cfg.analysis.min_scales} scales; descriptive): "
          f"{d['strict_variant_holds']} {d['strict_same_pair']}", "", f"Q(h, r): {d['Q']}", ""]
    t2 = res["tier2"]
    L += [f"## Tier-2 zero-noise reproduction: **{t2['outcome']}** (z_crit {t2['criterion']['z_crit']:.3f}, max combined "
          f"SE {t2['criterion']['max_combined_se']:.5f})", "", "| rep | r | h | Stage 0.6 | Stage 0.5 | combined SE | z |",
          "|---|---|---|---|---|---|---|"]
    for x in t2["rows"]:
        L.append(f"| {x['replicate']} | {x['r']} | {x['h']} | {x['stage06_mean']:+.4f} | {x['stage05_mean']:+.4f} | "
                 f"{x['combined_se']:.5f} | {x['z']:+.2f} |")
    for i, rp in enumerate(res["replicates"]):
        cv = rp.get("critical_value", {})
        L += ["", f"## Replicate R{i + 1}: simultaneous band (c = {cv.get('c', float('nan')):.4f}, {cv.get('draws')} draws, "
              f"relative MC error {cv.get('rel_mc_error', float('nan')):.4f}); ok = {rp['ok']} {rp.get('error') or ''}", "",
              "| kind | q | h | r | estimate | SE | adjusted lower | adjusted upper |", "|---|---|---|---|---|---|---|---|"]
        for c in rp["contrasts"]:
            L.append(f"| {c['kind']} | {c['q']} | {c['h']} | {c['r']} | {c['estimate']:+.4f} | {c['se']:.4f} | "
                     f"{c['lo']:+.4f} | {c['hi']:+.4f} |")
        L += ["", "| cell (q, h, r) | G+ | I+ | G- | NEG | SUPPORTED |", "|---|---|---|---|---|---|"]
        for cell, f in rp["flags"].items():
            L.append(f"| {cell} | {f['G+']} | {f['I+']} | {f['G-']} | {f['NEG']} | {f['SUPPORTED']} |")
    L += ["", "Descriptive only: n-curves (n_curves.csv), the pooled L-gains (pooled_descriptive.csv) and the noise-naive "
          "secondary baselines (naive_secondary.csv; noise-misspecified)."]
    return "\n".join(L) + "\n"


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"not JSON serialisable: {type(obj).__name__}")


def write_results(cfg: Stage06Config, res: dict, pre: dict, runs_dir: str, command: list[str], gate=None) -> Path:
    require_gate(cfg, gate)
    kw = {"run_id": AU.results_dir_name(gate)} if isinstance(gate, AU.VerifiedGate) else {}
    rec = RunRecorder(cfg, runs_dir=runs_dir, command=command, **kw)
    rec.write_json("summary.json", {k: v for k, v in res.items() if k not in ("n_curves", "naive_secondary")})
    if res["mode"] != "pilot":
        rec.write_csv("n_curves.csv", res["n_curves"])
        rec.write_csv("pooled_descriptive.csv", res["pooled_descriptive"])
        rec.write_csv("naive_secondary.csv", res["naive_secondary"])
        rec.write_csv("tier2.csv", res["tier2"]["rows"])
    rec.write_text("report.md", render_report(cfg, res, {k: v for k, v in pre.items() if k != "manifest"}))
    prereg = ROOT / "docs" / "PREREG_stage06.md"
    extra = {"preflight": {k: v for k, v in pre.items() if k != "manifest"},
             "preregistration": {"path": "docs/PREREG_stage06.md", "sha256": sha256_file(prereg) if prereg.is_file() else None}}
    if isinstance(gate, AU.VerifiedGate):       # no key, no signature: only what identifies the authorization
        extra["authorization"] = {"run_id": gate.run_id, "artifact_sha256": gate.artifact_sha256, "issued_utc": gate.issued_utc,
                                  "expires_utc": gate.expires_utc}
    rec.finalize({"evaluation": [NamedStreams(s).describe() for s in cfg.seeds.evaluation],
                  "bootstrap": NamedStreams(cfg.seeds.bootstrap).describe()}, extra=extra)
    return rec.dir


# ------------------------------------------------------------------------------------------ qualification / CLI


def qualify(cfg: Stage06Config, manifest_path, expected_sha, out: Path) -> dict:
    manifest = verify_manifest(Path(manifest_path), expected_sha)
    check_config_frozen(cfg, manifest)
    results = {}
    for key in QUALIFICATION_CHECKS:
        t0 = time.time()
        r = C.ALL_CHECKS_STAGE06[key]()
        results[key] = {"name": r.name, "passed": bool(r.passed), "details": r.details, "seconds": round(time.time() - t0, 1)}
        print(f"qualification {key} {r.name}: {'PASS' if r.passed else 'FAIL'} ({results[key]['seconds']} s)", flush=True)
    rep = {"environment": current_environment(), "manifest_sha256": manifest["manifest_sha256"],
           "config_hash": cfg.config_hash(), "checks": results, "passed": all(v["passed"] for v in results.values())}
    out = Path(out)
    if str(out.resolve()).startswith(str(ROOT.resolve())) and any(
            (ROOT / rel).resolve() == out.resolve() for rel in manifest["files"]):
        raise Refusal("the qualification report must be written outside the frozen file set", out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    return rep


def read_artifact_once(path) -> bytes:
    p = Path(path)
    try:
        return p.read_bytes()
    except FileNotFoundError:
        raise Refusal("authorization artifact not found", p)
    except OSError as exc:
        raise Refusal(f"authorization artifact cannot be read ({type(exc).__name__})", p)


def gate_session(cfg: Stage06Config, cfg_file_sha: str, args, pre: dict, *, key: bytes | None = None, raw: bytes | None = None,
                 now=None, root: Path | None = None, allow_test_only: bool = False):
    """Confirmatory only. Verify the frozen files (again), the authorization, and (at start) claim the run id. ``key`` and
    ``raw`` are kept by the caller in memory between the start and completion checks; the artifact file is read once."""
    if cfg.experiment.mode != "confirmatory":
        if getattr(args, "authorization", None):
            raise Refusal("pilot and test configurations take no authorization artifact")
        return None, None, None
    if not getattr(args, "authorization", None) or not getattr(args, "snapshot", None):
        raise Refusal("a confirmatory run needs --authorization and --snapshot (and the key in "
                      f"{AU.KEY_ENV} or an interactive prompt)")
    if raw is None:
        raw = read_artifact_once(args.authorization)
    if key is None:
        key = AU.obtain_key()
    manifest = verify_manifest(Path(args.manifest), args.expected_manifest_sha256, root)   # frozen files, again (root None -> ROOT)
    pre = {**pre, "manifest": manifest}
    gate = authorize_confirmatory(cfg, cfg_file_sha, args, pre, key, raw, now=now, root=root, allow_test_only=allow_test_only)
    return gate, key, raw


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Stage 0.6 noisy-observation probe (frozen runner)")
    ap.add_argument("command", choices=("verify", "qualify", "run", "analyze"))
    ap.add_argument("--config", required=True)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--expected-manifest-sha256", default=None)
    ap.add_argument("--qualification", default=None)
    ap.add_argument("--authorization", default=None, help="confirmatory only: the signed authorization artifact")
    ap.add_argument("--snapshot", default=None, help="confirmatory only: the frozen snapshot archive")
    ap.add_argument("--checkpoint-dir", default=None)
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-new-units", type=int, default=None, help="stop after this many new units (resume test)")
    args = ap.parse_args(argv)
    command = [sys.executable, "-m", "dynaicl.experiments.stage06_probe", *(argv if argv is not None else sys.argv[1:])]
    try:
        cfg, cfg_file_sha = load_config_once(args.config)
        if args.command == "qualify":
            if not args.out:
                raise Refusal("qualify needs --out (outside the frozen file set)")
            rep = qualify(cfg, args.manifest, args.expected_manifest_sha256, Path(args.out))
            print(f"qualification {'PASSED' if rep['passed'] else 'FAILED'} -> {args.out}")
            return 0 if rep["passed"] else 2
        pre = preflight(cfg, args.manifest, args.expected_manifest_sha256, args.qualification)
        gate = key = raw = None
        if cfg.experiment.mode == "confirmatory" and (args.command in ("run", "analyze") or args.authorization):
            gate, key, raw = gate_session(cfg, cfg_file_sha, args, pre)
        elif args.authorization:
            raise Refusal("pilot and test configurations take no authorization artifact")
        shown = {k: v for k, v in pre.items() if k != "manifest"}
        print(f"pre-flight OK: manifest {pre['manifest_sha256']}, environment {pre['environment']['status']}, "
              f"seeds {shown['seeds']}" + (f", authorization run_id {gate.run_id}" if gate else ""), flush=True)
        if args.command == "verify":
            return 0
        if not args.checkpoint_dir:
            raise Refusal("run/analyze need --checkpoint-dir")
        ckpt = checkpoint_root(Path(args.checkpoint_dir), cfg)
        if gate is not None:
            AU.check_results_dirs(Path(args.runs_dir), cfg.config_hash(), gate)
            state = AU.claim_run(ckpt, gate, cfg.config_hash(), pre["manifest_sha256"])
            print(f"run lock: {state} (run_id {gate.run_id})", flush=True)
        if args.command == "run":
            done = run_units(cfg, ckpt, pre["manifest_sha256"], args.workers, args.max_new_units, gate=gate)
            if len(done) < len(plan_units(cfg)):
                print(f"stopped after --max-new-units: {len(done)}/{len(plan_units(cfg))} units done; rerun to resume")
                return 0
        else:
            scan_checkpoint_dir(ckpt, cfg)
            done = {u: got for u in plan_units(cfg) if (got := load_unit(ckpt, u, cfg, pre["manifest_sha256"])) is not None}
        if gate is not None:                      # completion: frozen files and authorization verified again, from memory
            gate, _, _ = gate_session(cfg, cfg_file_sha, args, pre, key=key, raw=raw)
        res = analyze(cfg, done, gate=gate)
        out = write_results(cfg, res, pre, args.runs_dir, command, gate=gate)
        print(out)
        if res["mode"] != "pilot":
            print(f"VERDICT: {res['decision']['verdict']}")
        return 0
    except Corrupt as exc:
        print(f"CORRUPT: {exc}", file=sys.stderr)
        return Corrupt.exit_code
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return Refusal.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
