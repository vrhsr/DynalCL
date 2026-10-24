"""Stage 1 neural code: seeds, samplers (laws, common random numbers, nesting), models (causality, head), training
determinism (CPU), adapter and evaluation statistics (exact oracles). Every mutation in dynaicl_neural/mutations.py must
make at least one test here fail (scripts/stage1_mutation_matrix.py)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch
from scipy import stats

from dynaicl.evaluation import harness
from dynaicl.references.predictive import GaussianMixturePredictive
from dynaicl_families.ar1_known_sigma import ContextStats, FiniteLibrary, population_prior, stability_prior
from dynaicl_families.separability import kl_per_context
from dynaicl_neural.adapter import ModelPredictor, mixture_logpdf, mixture_params
from dynaicl_neural.data import POP, ArmSpec, SequenceSampler, a_from_uniform, library_atoms
from dynaicl_neural.evaluate import kl_reference_to_model, q1_statistics
from dynaicl_neural.models import SIZES, ModelSpec, build_model, mixture_log_prob, model_inputs, n_parameters
from dynaicl_neural.seeds import load_roles, role_seed
from dynaicl_neural.train import TrainConfig, set_determinism, train_model

TEST_ROOT = 4242          # test-only roots (not in the seed manifest; never used for decisions)
TEST_LIB_ROOT = 4243


def test_seed_manifest_roles_are_disjoint_and_complete():
    roles = load_roles()
    assert role_seed("stage1_map") == 70001
    for r in ("pilot_train", "pilot_eval", "pilot_library", "pilot_bootstrap", "confirmatory_train",
              "confirmatory_eval", "confirmatory_library", "confirmatory_bootstrap", "engineering_smoke",
              "j0_benchmark"):
        assert r in roles
    flat = [s for v in roles.values() for s in v]
    assert len(flat) == len(set(flat))


def _draw(arm, n=20000, seed_index=0):
    s = SequenceSampler(arm, TEST_ROOT, TEST_LIB_ROOT, seed_index, n, 3)
    return s.next_batch()


def test_cont_arm_draws_the_population_prior():
    _, a = _draw(ArmSpec("CONT"))
    lo, hi = (-POP.rho - POP.mu0) / POP.tau0, (POP.rho - POP.mu0) / POP.tau0
    p = stats.kstest(a, stats.truncnorm(lo, hi, loc=POP.mu0, scale=POP.tau0).cdf).pvalue
    assert p > 1e-3, p


def test_unif_arm_draws_uniform():
    _, a = _draw(ArmSpec("UNIF"))
    assert stats.kstest(a, stats.uniform(-0.999, 1.998).cdf).pvalue > 1e-3


def test_common_random_numbers_across_arms():
    x_c, a_c = _draw(ArmSpec("CONT"), 500, 3)
    x_u, a_u = _draw(ArmSpec("UNIF"), 500, 3)
    x_l, a_l = _draw(ArmSpec("LIB", 4), 500, 3)
    assert np.array_equal(x_c[:, 0], x_u[:, 0]) and np.array_equal(x_c[:, 0], x_l[:, 0])     # same x_0
    for x, a in ((x_c, a_c), (x_u, a_u), (x_l, a_l)):                                          # same innovations
        eps = x[:, 1:] - a[:, None] * x[:, :-1]
        eps_c = x_c[:, 1:] - a_c[:, None] * x_c[:, :-1]
        assert np.allclose(eps, eps_c, atol=1e-12)
    assert stats.spearmanr(a_c, a_u).statistic > 0.999999                                      # same uniforms


def test_library_atoms_nested_and_used():
    a256 = library_atoms(TEST_LIB_ROOT, 7, 256)
    for k in (1, 2, 4, 64):
        assert np.array_equal(library_atoms(TEST_LIB_ROOT, 7, k), a256[:k])
    _, a = _draw(ArmSpec("LIB", 4), 2000, 7)
    assert set(np.unique(a)) <= set(a256[:4]) and np.unique(a).size == 4


def test_sequences_start_at_x0_with_the_r_mixture():
    x, _ = _draw(ArmSpec("UNIF"), 30000)
    sd = np.sqrt(np.mean(x[:, 0] ** 2))
    assert abs(sd - math.sqrt((0.25**2 + 1 + 16) / 3)) < 0.05


@pytest.mark.parametrize("size", ["S", "GRU", "SSM", "DW-deep"])
def test_causality_cut_context_equals_full_sequence(size):
    torch.manual_seed(0)
    model = build_model(SIZES[size])
    x, _ = _draw(ArmSpec("UNIF"), 32)
    full = torch.from_numpy(x.astype(np.float32))
    with torch.no_grad():
        out_full = model(model_inputs(full)).double().numpy()
    for n in (1, 2, 3):
        ctx = np.stack([harness.make_context(x[i], n).values for i in range(x.shape[0])])
        lw, mu, var = mixture_params(model, ctx)
        m = out_full.shape[2] // 3
        assert np.allclose(mu, out_full[:, n, m:2 * m], atol=1e-5), (size, n)


def test_mixture_head_log_prob_matches_scipy():
    rng = np.random.default_rng(1)
    params = torch.tensor(rng.normal(size=(50, 6)), dtype=torch.float64)
    y = torch.tensor(rng.normal(size=50), dtype=torch.float64)
    got = mixture_log_prob(params, y).numpy()
    p = params.numpy()
    w = np.exp(p[:, :2]) / np.exp(p[:, :2]).sum(1, keepdims=True)
    want = np.log((w * stats.norm.pdf(y.numpy()[:, None], p[:, 2:4], np.exp(p[:, 4:6]))).sum(1))
    assert np.max(np.abs(got - want)) < 1e-12


def test_parameter_counts_are_recorded():
    counts = {k: n_parameters(build_model(v)) for k, v in SIZES.items()}
    assert counts["S"] < counts["M"] < counts["L"]
    assert abs(counts["DW-shallow"] - counts["DW-deep"]) / counts["DW-deep"] < 0.05


def test_training_is_deterministic_on_cpu_and_initialisation_is_shared_across_arms():
    set_determinism()
    cfg = TrainConfig(steps=20, checkpoints=(20,), batch=16, warmup=5, log_every=10)
    spec = ModelSpec("transformer", 16, 1, 2)
    m1, r1 = train_model(spec, ArmSpec("UNIF"), 0, TEST_ROOT, TEST_LIB_ROOT, cfg, None)
    m2, _ = train_model(spec, ArmSpec("UNIF"), 0, TEST_ROOT, TEST_LIB_ROOT, cfg, None)
    for (k, v1), v2 in zip(m1.state_dict().items(), m2.state_dict().values()):
        assert torch.equal(v1, v2), k
    m3, r3 = train_model(spec, ArmSpec("CONT"), 0, TEST_ROOT, TEST_LIB_ROOT,
                         TrainConfig(steps=1, checkpoints=(1,), batch=16, warmup=5), None)
    assert r3.torch_seed == r1.torch_seed
    assert r1.losses and all(math.isfinite(v) for _, v in r1.losses)


def test_adapter_types_and_refusals():
    model = build_model(SIZES["S"])
    ctx = harness.make_context(np.array([0.3, 0.1, -0.2]), 2)
    pred = ModelPredictor(model, "test").predict(ctx, 1)
    assert isinstance(pred, GaussianMixturePredictive)
    assert np.isfinite(pred.logpdf(0.0))
    with pytest.raises(TypeError):
        mixture_params(model, np.zeros((2, 3), dtype=np.float32))
    with pytest.raises(NotImplementedError):
        ModelPredictor(model, "test").predict(ctx, 2)


def _lib_as_model(lib: FiniteLibrary, st: ContextStats):
    """Exact mixture parameters of a library posterior predictive (a 'model' that IS the library reference)."""
    lw = lib.posterior_log_weights(st)
    mu = lib.atoms[None, :] * st.last[:, None]
    return lw, mu, np.ones_like(mu)


def test_evaluation_oracle_library_model():
    rng = np.random.default_rng(2)
    x = np.stack([np.cumsum(rng.normal(size=4)) * 0.5 for _ in range(300)])
    st = ContextStats.from_contexts(x)
    lib = FiniteLibrary(np.array([0.1, 0.6]))
    params = _lib_as_model(lib, st)
    assert np.max(np.abs(kl_reference_to_model(lib, st, params))) < 1e-10
    pop, stab = population_prior(), stability_prior()
    assert np.allclose(kl_reference_to_model(pop, st, params), kl_per_context(pop, lib, st), atol=1e-12)
    y = rng.normal(size=300)
    assert np.allclose(mixture_logpdf(*params, y), lib.logpdf(st, y), atol=1e-12)


def test_q1_statistics_use_the_population_reference():
    rng = np.random.default_rng(3)
    x = np.stack([np.cumsum(rng.normal(size=3)) for _ in range(200)])
    st = ContextStats.from_contexts(x)
    pop, stab = population_prior(), stability_prior()
    cont = [_lib_as_model(FiniteLibrary(np.array([0.4])), st)]
    unif = [_lib_as_model(FiniteLibrary(np.array([0.0, 0.5])), st)]
    s = q1_statistics(cont, unif, st, pop, stab)
    assert np.allclose(s["R_pop"][0], kl_per_context(pop, FiniteLibrary(np.array([0.4])), st), atol=1e-12)
    assert np.allclose(s["G"][0], kl_per_context(pop, FiniteLibrary(np.array([0.0, 0.5])), st) - s["R_pop"][0])
    assert np.allclose(s["Delta"], kl_per_context(pop, stab, st), atol=1e-12)
