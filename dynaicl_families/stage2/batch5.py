"""Batch 5 (docs/STAGE2_BATCH5_SPEC.md): split of the held-out population gap into a noise-level part and a dynamics
part (F1, F2), longer contexts and larger libraries (F2, F1), cumulative sequence-level gaps (1A, F1, F3), and the
theory quantities (prior KL budgets, nearest-atom limits). Reference-only; references, simulators and the F2 map's Monte
Carlo estimator are frozen or map code used read-only.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
from scipy import integrate, special, stats

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec
from dynaicl.systems.priors import StableCoefficientPrior

DELTA = 0.02
Z = 3.0
DRAW_FRACTION = 0.9
RS = (0.25, 1.0, 4.0)
QS = (0.0, 0.755, 2.56, 6.5)
F1_NS = (2, 3, 5, 10, 12, 14, 16, 18, 20, 25, 30, 40)
F1L_NS = (20, 40, 80, 160)
F1L_KS = (4, 8, 16, 32, 64)
F1L_DRAWS = 32
F2_NS = (2, 3, 5, 10, 20, 40, 80)
F2_NS_CTX = (10, 20, 40, 80)
F2_KS = (2, 16, 64, 256, 1024)
F2_DRAWS = 8
CUM_MAX = 160
F3_CUM_MAX = 40
NEW_LABEL = {"IDENTIFIABLE": "SEPARABLE", "UNIDENTIFIABLE": "NOT SEPARABLE"}


def unit_seed(root: int, *names) -> int:
    """Seed of a unit, derived from the role seed: SeedSequence(root, spawn_key=(sha256(name)[:4] per name))."""
    key = tuple(int.from_bytes(hashlib.sha256(str(n).encode()).digest()[:4], "little") for n in names)
    return int(np.random.SeedSequence(root, spawn_key=key).generate_state(1, dtype=np.uint32)[0])


def decide(mean: float, se: float) -> str:
    if mean - Z * se >= DELTA:
        return "SEPARABLE"
    if mean + Z * se < DELTA:
        return "NOT SEPARABLE"
    return "BORDERLINE"


def diff_row(d: np.ndarray, decision: bool, **keys) -> dict:
    mean, se = float(d.mean()), float(d.std(ddof=1) / math.sqrt(d.size))
    return {**keys, "estimate": mean, "se": se, "se_mc": 0.0, "n_items": int(d.size),
            "decision": decide(mean, se) if decision else ""}


# Parts of the split: (name, truth-side reference(s), other-side reference(s), decision?).
# T = D1 + N1 = N2 + D2 item by item; D and N are the symmetric (two-path average) parts.
SPLIT_PARTS = (("T", ("pop",), ("ctx",), True), ("D1", ("pop",), ("ctx_nm",), True),
               ("N1", ("ctx_nm",), ("ctx",), False), ("N2", ("pop",), ("ctx_dm",), True),
               ("D2", ("ctx_dm",), ("ctx",), False), ("D", ("pop", "ctx_dm"), ("ctx_nm", "ctx"), False),
               ("N", ("ctx_nm", "pop"), ("ctx", "ctx_dm"), False))


# ------------------------------------------------------------------------------------------------ A, C: F1

def f1_refs() -> dict:
    from dynaicl_families import ar1_unknown_sigma as uf
    return {"pop": uf.population_f1(), "ctx": uf.context_only_f1(),
            "ctx_nm": uf.UnknownScaleReference(uf.CoefficientPrior(0.999), uf.InverseGammaScale(3.0, 2.0)),
            "ctx_dm": uf.UnknownScaleReference(uf.CoefficientPrior(0.95, 0.4, 0.3), uf.LogUniformScale(0.01, 100.0))}


def _f1_split(r: float, n_items: int, seed: int, length: int):
    from dynaicl_families import sampling as sm
    cond = sm.F1PopulationCondition(initial_state=InitialStateSpec(0.0, r))
    return sm.simulate(cond, NamedStreams(seed), n_items, length)


def f1_split(r: float, n_items: int, seed: int, ns=F1_NS) -> list[dict]:
    """Section A: T, D1, N1, N2, D2 and the symmetric D, N per n (realised targets, paired, same items)."""
    from dynaicl_families import ar1_unknown_sigma as uf
    from dynaicl_families import sampling as sm
    split, refs, rows = _f1_split(r, n_items, seed, max(ns) + 1), f1_refs(), []
    for n in ns:
        ctx, y = sm.contexts_and_targets(split, n)
        st = uf.F1Stats.from_contexts(ctx)
        lp = {k: ref.logpdf(st, y) for k, ref in refs.items()}
        for part, a, b, dec in SPLIT_PARTS:
            d = sum(lp[k] for k in a) / len(a) - sum(lp[k] for k in b) / len(b)
            rows.append(diff_row(d, dec, family="F1", part=part, r=r, n=n))
    return rows


def f1_library_atoms(lib_root: int, draws: int, k_max: int) -> list[tuple[np.ndarray, np.ndarray]]:
    from dynaicl_families import sampling as sm
    cond, streams, out = sm.F1PopulationCondition(), NamedStreams(lib_root), []
    for d in range(draws):
        a, s = np.empty(k_max), np.empty(k_max)
        for j in range(k_max):
            a[j], s[j], _ = cond.draw_system(streams.item(f"b5_f1_library/draw{d}", j))
        out.append((a, s))
    return out


def f1_library_long(r: float, n_items: int, seed: int, lib_root: int, ns=F1L_NS, ks=F1L_KS,
                    draws=F1L_DRAWS) -> list[dict]:
    """Section C: held-out lib vs pop per draw at long contexts (exact library predictive)."""
    from dynaicl_families import ar1_unknown_sigma as uf
    from dynaicl_families import sampling as sm
    split, pop = _f1_split(r, n_items, seed, max(ns) + 1), uf.population_f1()
    atoms, rows = f1_library_atoms(lib_root, draws, max(ks)), []
    for n in ns:
        ctx, y = sm.contexts_and_targets(split, n)
        st = uf.F1Stats.from_contexts(ctx)
        lp_pop = pop.logpdf(st, y)
        for d, (a, s) in enumerate(atoms):
            for k in ks:
                row = diff_row(lp_pop - uf.ScaleLibrary(a[:k], s[:k]).logpdf(st, y), True, family="F1", r=r, n=n, K=k,
                               draw=d)
                rows.append(row)
    return rows


def summarise_draws(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    """Per cell: share of draws with lower bound >= delta, share with upper bound < delta, and the maps' 90% rule."""
    cells: dict[tuple, list[dict]] = {}
    for row in rows:
        cells.setdefault(tuple(row[k] for k in keys), []).append(row)
    out = []
    for key, grp in cells.items():
        se_all = [math.hypot(g["se"], g.get("se_mc", 0.0)) for g in grp]
        lo = [g["estimate"] - Z * s >= DELTA for g, s in zip(grp, se_all)]
        hi = [g["estimate"] + Z * s < DELTA for g, s in zip(grp, se_all)]
        mc = [g.get("decision") == "MC-LIMITED" for g in grp]
        f_lo, f_hi = sum(lo) / len(grp), sum(hi) / len(grp)
        dec = ("MC-LIMITED" if sum(mc) > 0.1 * len(grp) else "SEPARABLE" if f_lo >= DRAW_FRACTION
               else "NOT SEPARABLE" if f_hi >= DRAW_FRACTION else "PARTIAL")
        out.append({**dict(zip(keys, key)), "draws": len(grp),
                    "mean_estimate": float(np.mean([g["estimate"] for g in grp])), "frac_lo_ge_delta": f_lo,
                    "frac_hi_lt_delta": f_hi, "decision": dec})
    return out


# ------------------------------------------------------------------------------------------------ B: F2

def f2_variants() -> dict:
    from dynaicl_families.stage2 import f2_var as fv
    eye = np.eye(fv.D)
    return {"ctx": fv.context_only_f2(),
            "ctx_nm": fv.MNIWPrior("C_F2_NM", np.zeros((fv.D, fv.D)), 100.0 * eye, 7.0, 4.0 * eye, 0.999),
            "ctx_dm": fv.MNIWPrior("C_F2_DM", 0.4 * eye, 0.09 * eye, 1.5, 0.01 * eye, 0.95)}


def chunked_library_logpdf(lib, ctx: np.ndarray, y: np.ndarray, max_elements: float = 2e7) -> np.ndarray:
    """VarLibrary.logpdf builds (N, K, n, d) residuals; evaluate in item chunks to bound memory."""
    k, n = lib.a.shape[0], ctx.shape[1] - 1
    chunk = max(1, int(max_elements // (k * max(n, 1) * ctx.shape[2])))
    out = np.empty(ctx.shape[0])
    for i0 in range(0, ctx.shape[0], chunk):
        i1 = min(ctx.shape[0], i0 + chunk)
        out[i0:i1] = lib.logpdf(ctx[i0:i1], y[i0:i1, None, :])[:, 0]
    return out


def f2_heldout(r: float, n_items: int, seed: int, lib_root: int, ns=F2_NS, ns_ctx=F2_NS_CTX, ks=F2_KS,
               draws=F2_DRAWS) -> tuple[list[dict], list[dict]]:
    """Section B: (split rows, library rows per draw). Monte Carlo estimator and MC rule of the F2 map, unchanged."""
    from dynaicl_families.stage2 import f2_map as fm
    from dynaicl_families.stage2 import f2_var as fv
    pop, variants = fv.population_f2(), f2_variants()
    split = fv.simulate_f2(pop, r, NamedStreams(seed), n_items, max(ns) + 1, stream_code=11)
    libs = [fv.library_from_prior(pop, max(ks), NamedStreams(lib_root).stream(f"b5_f2_library/draw{d}"))
            for d in range(draws)]
    split_rows, lib_rows = [], []
    for n in ns:
        ctx, y = fv.contexts_and_targets(split, n)
        lp = {"pop": None}
        se = {}
        lp["pop"], se["pop"], _ = fm.truncated_scores(pop, ctx, y, unit_seed(seed, "pop", n))
        if n in ns_ctx:
            for name, prior in variants.items():
                lp[name], se[name], _ = fm.truncated_scores(prior, ctx, y, unit_seed(seed, name, n))
            for part, a, b, dec in SPLIT_PARTS:
                la = sum(lp[k] for k in a) / len(a)
                lb = sum(lp[k] for k in b) / len(b)
                sa = np.sqrt(sum(se[k] ** 2 for k in a)) / len(a)
                sb = np.sqrt(sum(se[k] ** 2 for k in b)) / len(b)
                g = fm.gap(la, lb, sa, sb)
                label = fm.classify(g)
                split_rows.append({"family": "F2", "part": part, "r": r, "n": n, "estimate": g["mean"], "se": g["se"],
                                   "se_mc": g["se_mc"], "n_items": g["n_items"],
                                   "decision": (NEW_LABEL.get(label, label) if dec or label == "MC-LIMITED" else ""),
                                   "items_over_se_flag": g["items_over_se_flag"]})
        for d, lib in enumerate(libs):
            for k in ks:
                sub = fv.VarLibrary(lib.a[:k], lib.sigma[:k])
                g = fm.gap(lp["pop"], chunked_library_logpdf(sub, ctx, y), se["pop"], None)
                label = fm.classify(g)
                lib_rows.append({"family": "F2", "r": r, "n": n, "K": k, "draw": d, "estimate": g["mean"],
                                 "se": g["se_items"], "se_mc": g["se_mc"], "n_items": g["n_items"],
                                 "decision": NEW_LABEL.get(label, label),
                                 "items_over_se_flag": g["items_over_se_flag"]})
    return split_rows, lib_rows


# ------------------------------------------------------------------------------------------------ D: cumulative gaps

def n0_logpdf(x0: np.ndarray, y: np.ndarray, log_density, lo: float, hi: float, panels: int = 64, nodes: int = 16,
              chunk: int = 4000) -> np.ndarray:
    """log p(x_1 | x_0) = log int pi(a) N(x_1; a x_0, 1) da by composite Gauss-Legendre over the prior's support."""
    g, w = np.polynomial.legendre.leggauss(nodes)
    e = np.linspace(lo, hi, panels + 1)
    half, mid = (e[1:] - e[:-1])[:, None] / 2, (e[1:] + e[:-1])[:, None] / 2
    a, wa = (mid + half * g).ravel(), (half * w).ravel()
    logw = np.log(wa) + log_density(a)
    out = np.empty(x0.size)
    for i0 in range(0, x0.size, chunk):
        i1 = min(x0.size, i0 + chunk)
        z = y[i0:i1, None] - a[None, :] * x0[i0:i1, None]
        out[i0:i1] = special.logsumexp(logw[None, :] - 0.5 * z * z, axis=1) - 0.5 * math.log(2 * math.pi)
    return out


def _tn_logpdf(a: np.ndarray) -> np.ndarray:
    return stats.truncnorm((-0.95 - 0.4) / 0.3, (0.95 - 0.4) / 0.3, loc=0.4, scale=0.3).logpdf(a)


def cumulative_1a(r: float, n_items: int, seed: int, nmax: int = CUM_MAX) -> list[dict]:
    """1A pop vs stab: n = 0 term by quadrature (node doubling reported), then every n = 1..nmax (frozen batch
    references); per-step and cumulative rows (item-level SE of the cumulative sum)."""
    from dynaicl_families import sampling as sm
    from dynaicl_families.ar1_known_sigma import ContextStats, population_prior, stability_prior
    prior = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)
    cond = ContinuousPriorCondition(prior, InitialStateSpec(0.0, r))
    split = sm.simulate(cond, NamedStreams(seed), n_items, nmax + 1)
    x0, x1 = np.array(split.trajectories[:, 0]), np.array(split.trajectories[:, 1])
    stab_ld = lambda a: np.full(a.shape, -math.log(1.998))  # noqa: E731
    d0 = n0_logpdf(x0, x1, _tn_logpdf, -0.95, 0.95) - n0_logpdf(x0, x1, stab_ld, -0.999, 0.999)
    d0_fine = (n0_logpdf(x0, x1, _tn_logpdf, -0.95, 0.95, panels=128)
               - n0_logpdf(x0, x1, stab_ld, -0.999, 0.999, panels=128))
    rows = [diff_row(d0, True, family="1A", variant="pop-stab", kind="step", r=r, n=0,
                     node_doubling_max_abs=float(np.max(np.abs(d0 - d0_fine))))]
    cum = d0.copy()
    rows.append(diff_row(cum, False, family="1A", variant="pop-stab", kind="cum", r=r, n=0))
    pop, stab = population_prior(), stability_prior()
    for n in range(1, nmax + 1):
        ctx, y = sm.contexts_and_targets(split, n)
        cs = ContextStats.from_contexts(ctx)
        d = pop.logpdf(cs, y) - stab.logpdf(cs, y)
        cum += d
        rows.append(diff_row(d, True, family="1A", variant="pop-stab", kind="step", r=r, n=n))
        rows.append(diff_row(cum, False, family="1A", variant="pop-stab", kind="cum", r=r, n=n))
    return rows


def cumulative_f1(r: float, n_items: int, seed: int, nmax: int = CUM_MAX) -> list[dict]:
    """F1 pop vs ctx and pop vs ctx_nm, n = 2..nmax; cumulative from n = 2."""
    from dynaicl_families import ar1_unknown_sigma as uf
    from dynaicl_families import sampling as sm
    split, refs = _f1_split(r, n_items, seed, nmax + 1), f1_refs()
    cums = {"pop-ctx": np.zeros(n_items), "pop-ctx_nm": np.zeros(n_items)}
    rows = []
    for n in range(2, nmax + 1):
        ctx, y = sm.contexts_and_targets(split, n)
        st = uf.F1Stats.from_contexts(ctx)
        lp_pop = refs["pop"].logpdf(st, y)
        for variant, other in (("pop-ctx", "ctx"), ("pop-ctx_nm", "ctx_nm")):
            d = lp_pop - refs[other].logpdf(st, y)
            cums[variant] += d
            rows.append(diff_row(d, True, family="F1", variant=variant, kind="step", r=r, n=n))
            rows.append(diff_row(cums[variant], False, family="F1", variant=variant, kind="cum", r=r, n=n))
    return rows


def cumulative_f3(q: float, r: float, n_items: int, seed: int, nmax: int = F3_CUM_MAX, chunk: int = 2000) -> list[dict]:
    """F3 pop vs stab (frozen Stage 0.6 references and simulator), n = 2..nmax, h = 1; cumulative from n = 2."""
    from dynaicl.evaluation.noisy_harness import build_noisy_evaluation
    from dynaicl.references.kalman_quadrature import noise_aware_stability_predictor, noisy_population_reference
    from dynaicl.systems.noisy import NoisyObservationCondition, generate_noisy_split
    from dynaicl.systems.splits import SplitRole
    from dynaicl_families.stage2 import f3_map as fm
    ns, hs = tuple(range(2, nmax + 1)), (1,)
    model = fm.model_for(q, r)
    cond = NoisyObservationCondition(fm.population_prior(), model, name="F3-CUMULATIVE", stream_code=0)
    split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(seed), n_items, nmax + 1)
    es = build_noisy_evaluation(split, ns, hs)
    pop, stab = noisy_population_reference(fm.population_prior(), model), noise_aware_stability_predictor(model)
    diffs = {n: [] for n in ns}
    for i0 in range(0, n_items, chunk):
        sl = slice(i0, min(n_items, i0 + chunk))
        tg = {k: v[sl] for k, v in es._targets.items()}
        a = pop.batch_scores(es.context_matrix[sl], tg, ns, hs)
        b = stab.batch_scores(es.context_matrix[sl], tg, ns, hs)
        for n in ns:
            diffs[n].append(a[(n, 1)][0] - b[(n, 1)][0])
    rows, cum = [], np.zeros(n_items)
    for n in ns:
        d = np.concatenate(diffs[n])
        cum += d
        rows.append(diff_row(d, True, family="F3", variant=f"q_{q}", kind="step", r=r, n=n))
        rows.append(diff_row(cum, False, family="F3", variant=f"q_{q}", kind="cum", r=r, n=n))
    return rows


# ------------------------------------------------------------------------------------------------ E: theory quantities

def kl_1a(bound: float) -> float:
    """KL(TN(0.4, 0.3^2; +/-0.95) || U(+/-bound)), bound >= 0.95 (adaptive quadrature)."""
    tn = stats.truncnorm((-0.95 - 0.4) / 0.3, (0.95 - 0.4) / 0.3, loc=0.4, scale=0.3)
    h = integrate.quad(lambda a: -tn.pdf(a) * tn.logpdf(a), -0.95, 0.95, limit=200)[0]
    return -h + math.log(2 * bound)


def kl_f1_sigma(lo: float, hi: float) -> dict:
    """KL of the population noise prior (sigma^2 ~ IG(3, 2)) from log sigma ~ U(log lo, log hi): the F1 sigma part."""
    ig = stats.invgamma(3, scale=2)

    def dens(s: float) -> float:          # density of s = log sigma under the population
        return ig.pdf(math.exp(2 * s)) * 2 * math.exp(2 * s)

    h = integrate.quad(lambda s: -dens(s) * math.log(dens(s)) if dens(s) > 0 else 0.0, -8, 8, limit=400)[0]
    outside = 1.0 - integrate.quad(dens, math.log(lo), math.log(hi), limit=200)[0]
    return {"kl": -h + math.log(math.log(hi / lo)), "pop_mass_outside": max(outside, 0.0)}


def _log_mniw(prior, b: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Untruncated MNIW log density at (B, Sigma) (MATH_F2 section 2): IW(nu0, Psi0) x MN(B0, V0, Sigma)."""
    d, nu = prior.d, prior.nu0
    sinv, logdet_s = np.linalg.inv(s), np.linalg.slogdet(s)[1]
    lp_iw = (0.5 * nu * np.linalg.slogdet(prior.psi0)[1] - 0.5 * nu * d * math.log(2.0)
             - special.multigammaln(0.5 * nu, d) - 0.5 * (nu + d + 1) * logdet_s
             - 0.5 * np.einsum("ij,nji->n", prior.psi0, sinv))
    diff = b - prior.b0
    quad = np.einsum("nij,nji->n", sinv, np.swapaxes(diff, 1, 2) @ np.linalg.inv(prior.v0) @ diff)
    lp_mn = -0.5 * (d * d * math.log(2 * math.pi) + d * np.linalg.slogdet(prior.v0)[1] + d * logdet_s + quad)
    return lp_iw + lp_mn


def kl_f2(other, n_draws: int, seed: int) -> dict:
    """Monte Carlo KL(P_F2 || other): E_P[log p(theta) - log q(theta)] with truncation normalisers by acceptance."""
    from dynaicl_families.stage2 import f2_var as fv
    pop = fv.population_f2()
    rng = np.random.default_rng(seed)
    b, s, _ = fv.sample_truncated_prior(pop, n_draws, rng)

    def accept(prior) -> tuple[float, float]:
        bb, _ = fv.sample_mniw(prior.b0, prior.v0, prior.nu0, prior.psi0, n_draws, rng)
        p = float(np.mean(fv.spectral_radius(bb) < prior.c))
        return p, math.sqrt(p * (1 - p) / n_draws)

    zp, zp_se = accept(pop)
    zq, zq_se = accept(other)
    if np.any(fv.spectral_radius(b) >= other.c):
        raise ValueError("population support not inside the comparator's support")
    terms = _log_mniw(pop, b, s) - _log_mniw(other, b, s)
    kl = float(terms.mean()) - math.log(zp) + math.log(zq)
    se = math.sqrt(float(terms.var(ddof=1)) / n_draws + (zp_se / zp) ** 2 + (zq_se / zq) ** 2)
    return {"kl": kl, "se": se, "z_pop": zp, "z_other": zq, "n_draws": n_draws}


def nearest_atom_scalar(known_sigma: bool, k: int, n_sys: int, n_lib: int, seed: int) -> dict:
    """Large-n limit E[min_k KL_stationary(theta || theta_k)] of the held-out library gap (scalar families)."""
    rng = np.random.default_rng(seed)
    tn = stats.truncnorm((-0.95 - 0.4) / 0.3, (0.95 - 0.4) / 0.3, loc=0.4, scale=0.3)
    ig = stats.invgamma(3, scale=2)
    a = tn.rvs(size=n_sys, random_state=rng)
    s2 = np.ones(n_sys) if known_sigma else ig.rvs(size=n_sys, random_state=rng)
    per_lib = []
    for _ in range(n_lib):
        ak = tn.rvs(size=k, random_state=rng)
        sk2 = np.ones(k) if known_sigma else ig.rvs(size=k, random_state=rng)
        ex2 = s2 / (1 - a ** 2)
        kl = 0.5 * np.log(sk2[None] / s2[:, None]) + (s2[:, None] + (a[:, None] - ak[None]) ** 2 * ex2[:, None]) / (
            2 * sk2[None]) - 0.5
        per_lib.append(float(kl.min(axis=1).mean()))
    return {"mean": float(np.mean(per_lib)), "se": float(np.std(per_lib, ddof=1) / math.sqrt(n_lib)),
            "frac_libs_ge_delta": float(np.mean(np.array(per_lib) >= DELTA))}


def nearest_atom_f2(k: int, n_sys: int, n_lib: int, seed: int) -> dict:
    """As nearest_atom_scalar for F2: per-step KL between N(A x, Sigma) and N(A_k x, Sigma_k), x stationary."""
    from dynaicl_families.stage2 import f2_var as fv
    rng = np.random.default_rng(seed)
    pop = fv.population_f2()
    b, s, _ = fv.sample_truncated_prior(pop, n_sys, rng)
    a = np.swapaxes(b, 1, 2)
    eye = np.eye(4)
    p = np.array([np.linalg.solve(eye - np.kron(a[i], a[i]), s[i].reshape(4)).reshape(2, 2) for i in range(n_sys)])
    ld = np.linalg.slogdet(s)[1]
    per_lib = []
    for _ in range(n_lib):
        bk, sk, _ = fv.sample_truncated_prior(pop, k, rng)
        ak, ski = np.swapaxes(bk, 1, 2), np.linalg.inv(sk)
        ldk = np.linalg.slogdet(sk)[1]
        best = np.empty(n_sys)
        for i in range(n_sys):
            dd = a[i][None] - ak
            quad = np.einsum("kij,kij->k", dd, ski @ dd @ p[i])
            kl = 0.5 * (np.einsum("kij,ji->k", ski, s[i]) + quad - 2 + ldk - ld[i])
            best[i] = kl.min()
        per_lib.append(float(best.mean()))
    return {"mean": float(np.mean(per_lib)), "se": float(np.std(per_lib, ddof=1) / math.sqrt(n_lib)),
            "frac_libs_ge_delta": float(np.mean(np.array(per_lib) >= DELTA))}


def theory(root: int, n_draws: int = 200_000, n_sys: int = 2000, n_lib: int = 32, n_sys_f2: int = 400,
           n_lib_f2: int = 8) -> dict:
    """Section E (local): prior KL budgets and nearest-atom limits; Monte Carlo seeds derived from the role seed."""
    var, ranges = f2_variants(), ((0.1, 10.0), (0.01, 100.0), (0.001, 1000.0))
    out = {"kl_1a": {str(b): kl_1a(b) for b in (0.95, 0.999, 0.9999)},
           "kl_f1_sigma": {f"{lo}_{hi}": kl_f1_sigma(lo, hi) for lo, hi in ranges},
           "kl_f2": {k: kl_f2(var[k], n_draws, unit_seed(root, "kl_f2", k)) for k in ("ctx", "ctx_nm", "ctx_dm")},
           "nearest_atom": {"known_sigma": {}, "unknown_sigma": {}, "f2": {}}}
    out["kl_f1_total_map_comparator"] = out["kl_1a"]["0.999"] + out["kl_f1_sigma"]["0.01_100.0"]["kl"]
    for k in (1, 2, 4, 8, 16, 32, 64, 256):
        na = out["nearest_atom"]
        na["known_sigma"][str(k)] = nearest_atom_scalar(True, k, n_sys, n_lib, unit_seed(root, "na1", k))
        na["unknown_sigma"][str(k)] = nearest_atom_scalar(False, k, n_sys, n_lib, unit_seed(root, "na2", k))
    for k in (2, 16, 64, 256, 1024):
        out["nearest_atom"]["f2"][str(k)] = nearest_atom_f2(k, n_sys_f2, n_lib_f2, unit_seed(root, "na3", k))
    return out
