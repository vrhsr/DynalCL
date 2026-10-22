"""Stage 0.6: AR(1) dynamics observed with additive Gaussian noise (docs/MATH_STAGE06.md section 2).

    x_0 ~ N(0, x0_sd^2) (x0_sd = r sigma_w), independent of a      x_t = a x_{t-1} + sigma_w eps_t, t >= 1
    y_t = x_t + sigma_v nu_t, t >= 0

**Latent vs observed initial value.** x_0 is the latent initial *state* (never observed). y_0 is the observed initial
*value*. It is noisy like every other observation. Predictors see only y_0..y_n.

The latent path is generated exactly as in Stage 0/0.5 (`generate_split`). The observation noise nu comes from a
**separate named stream** (``<role noise stream>_obs``), so the latent path for given seeds does not depend on sigma_v.
At sigma_v = 0, y equals the Stage 0.5 path.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import InitialStateSpec
from dynaicl.systems.priors import canonical_fingerprint
from dynaicl.systems.splits import ROLE_STREAMS, DataSplit, LeakageError, SplitRole, generate_split

FLOAT = np.float64
LIKELIHOOD_NOISY_ID = "ar1-latent-x0-additive-gaussian-obs/v1"


@dataclass(frozen=True)
class NoisyObservationModel:
    """Known noise levels and initial-state prior, shared by every noise-aware predictor (information parity)."""

    sigma_w: float
    sigma_v: float
    x0_sd: float

    def __post_init__(self) -> None:
        if not (self.sigma_w > 0 and self.sigma_v >= 0 and self.x0_sd > 0):
            raise ValueError("need sigma_w > 0, sigma_v >= 0, x0_sd > 0 (x0_sd = 0 with sigma_v = 0 is singular)")
        if not all(math.isfinite(v) for v in (self.sigma_w, self.sigma_v, self.x0_sd)):
            raise ValueError("noise levels must be finite")

    @property
    def q(self) -> float:
        """Noise ratio sigma_v^2 / sigma_w^2 (a-independent)."""
        return (self.sigma_v / self.sigma_w) ** 2

    @property
    def r(self) -> float:
        """Initial-state-to-process-noise ratio sd(x_0)/sigma_w."""
        return self.x0_sd / self.sigma_w

    @property
    def label(self) -> str:
        return f"additive-gaussian(sigma_w={self.sigma_w!r},sigma_v={self.sigma_v!r},x0_sd={self.x0_sd!r})"

    def spec(self) -> dict:
        return {"model": "additive-gaussian", "sigma_w": float(self.sigma_w), "sigma_v": float(self.sigma_v),
                "x0_prior": {"mean": 0.0, "sd": float(self.x0_sd), "independent_of_a": True}}


@dataclass(frozen=True)
class NoisyObservationCondition:
    """Held-out systems (E-CONT) from ``prior``, observed through ``model``.

    ``stream_code = 0`` equals Stage 0.5's E-CONT, so the same seeds give the same latent paths. This is needed for
    the Tier-1 regression against stored Stage 0.5 items.
    """

    prior: object
    model: NoisyObservationModel
    name: str = "E-CONT-NOISY"
    stream_code: int = 0

    @property
    def initial_state(self) -> InitialStateSpec:
        return InitialStateSpec(0.0, self.model.x0_sd)

    def system_distribution_fingerprint(self) -> str:
        """Fingerprint of everything the matched reference must share: the prior over a, the noise model and the x_0 prior."""
        return canonical_fingerprint({"system_distribution": self.prior.spec(), "observation": self.model.spec(),
                                      "likelihood": LIKELIHOOD_NOISY_ID})

    def fingerprint(self) -> str:
        return canonical_fingerprint({"name": self.name, "sdf": self.system_distribution_fingerprint()})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        a, s = self.prior.sample_systems(rng, 1)
        if abs(float(s[0]) - self.model.sigma_w) > 1e-15 * self.model.sigma_w:
            raise ValueError("prior sigma must equal model.sigma_w")
        return float(a[0]), float(s[0]), "continuous"


def obs_noise_stream(role: SplitRole) -> str:
    return ROLE_STREAMS[role][1] + "_obs"


@dataclass(frozen=True, eq=False)
class NoisySplit:
    """Latent split plus observation noise and observations. All arrays are read-only. ``observations`` is the
    only part predictors may see (through contexts). ``latent`` and ``obs_noise`` are evaluator-only."""

    latent: DataSplit
    obs_noise: np.ndarray        # (N, T + 1)
    observations: np.ndarray     # (N, T + 1)
    sigma_v: float

    def __post_init__(self) -> None:
        for name in ("obs_noise", "observations"):
            arr = np.array(getattr(self, name), dtype=FLOAT, copy=True)
            arr.setflags(write=False)
            object.__setattr__(self, name, arr)

    @property
    def size(self) -> int:
        return self.latent.size

    def observation_sha256(self, i: int) -> str:
        return hashlib.sha256(self.observations[i].tobytes()).hexdigest()


def generate_noisy_split(condition: NoisyObservationCondition, role: SplitRole, streams: NamedStreams,
                         n_items: int, length: int) -> NoisySplit:
    latent = generate_split(condition, role, streams, n_items, length)
    nu = np.empty((n_items, length + 1), dtype=FLOAT)
    for i in range(n_items):
        nu[i] = streams.item(obs_noise_stream(role), i, condition.stream_code).standard_normal(length + 1)
    y = latent.trajectories + condition.model.sigma_v * nu
    if not np.all(np.isfinite(y)):
        raise FloatingPointError("non-finite observations")
    return NoisySplit(latent, nu, y, condition.model.sigma_v)


def assert_no_obs_noise_overlap(first: NoisySplit, second: NoisySplit) -> None:
    """Observation-noise draws are never shared between roles or replicates (exact-equality test, as in Stage 0)."""
    if np.intersect1d(first.obs_noise.ravel(), second.obs_noise.ravel()).size:
        raise LeakageError("splits share observation-noise values")
