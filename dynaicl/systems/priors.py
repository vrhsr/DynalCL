"""Prior regimes over AR(1) systems (Section 2.2): P-GAUSS, P-NIG, P-STABLE.

A prior here is a *system distribution*: a distribution over (a, sigma). Each prior has a canonical
fingerprint, which the matched-reference guard compares (references/matched.py).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

import numpy as np
from scipy import special

FLOAT = np.float64

#: Identifier of the likelihood family shared by every condition in Stage 0.
LIKELIHOOD_ID = "ar1-gaussian-conditional-on-x0/v1"


def canonical_fingerprint(spec: dict) -> str:
    """SHA-256 of canonical JSON (sorted keys, repr-exact floats)."""
    blob = json.dumps(spec, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _check_positive(name: str, value: float) -> None:
    if not (isinstance(value, (int, float)) and math.isfinite(value) and value > 0):
        raise ValueError(f"{name} must be a finite positive number, got {value!r}")


@dataclass(frozen=True)
class GaussianCoefficientPrior:
    """P-GAUSS: a ~ N(mu0, tau0^2), sigma known. Untruncated, so P(abs(a) >= 1) > 0."""

    mu0: float
    tau0: float
    sigma: float
    family: str = "P-GAUSS"

    def __post_init__(self) -> None:
        _check_positive("tau0", self.tau0)
        _check_positive("sigma", self.sigma)

    @property
    def support(self) -> tuple[float, float]:
        return (-math.inf, math.inf)

    def spec(self) -> dict:
        return {"family": self.family, "mu0": float(self.mu0), "tau0": float(self.tau0),
                "sigma": float(self.sigma), "likelihood": LIKELIHOOD_ID}

    def fingerprint(self) -> str:
        return canonical_fingerprint(self.spec())

    def explosive_probability(self) -> float:
        """P(abs(a) >= 1) = Phi((-1 - mu0)/tau0) + 1 - Phi((1 - mu0)/tau0). Analytically exact."""
        return float(special.ndtr((-1.0 - self.mu0) / self.tau0) + special.ndtr((self.mu0 - 1.0) / self.tau0))

    def coefficient_logpdf(self, a: np.ndarray) -> np.ndarray:
        a = np.asarray(a, dtype=FLOAT)
        z = (a - self.mu0) / self.tau0
        return -0.5 * z * z - math.log(self.tau0) - 0.5 * math.log(2.0 * math.pi)

    def sample_systems(self, rng: np.random.Generator, size: int) -> tuple[np.ndarray, np.ndarray]:
        a = self.mu0 + self.tau0 * rng.standard_normal(size)
        return a.astype(FLOAT), np.full(size, self.sigma, dtype=FLOAT)


@dataclass(frozen=True)
class NormalInverseGammaPrior:
    """P-NIG: a | sigma^2 ~ N(mu0, sigma^2 / lambda0), sigma^2 ~ InverseGamma(alpha0, beta0)."""

    mu0: float
    lambda0: float
    alpha0: float
    beta0: float
    family: str = "P-NIG"

    def __post_init__(self) -> None:
        for n in ("lambda0", "alpha0", "beta0"):
            _check_positive(n, getattr(self, n))

    def spec(self) -> dict:
        return {"family": self.family, "mu0": float(self.mu0), "lambda0": float(self.lambda0),
                "alpha0": float(self.alpha0), "beta0": float(self.beta0), "likelihood": LIKELIHOOD_ID}

    def fingerprint(self) -> str:
        return canonical_fingerprint(self.spec())

    def explosive_probability(self) -> float:
        """P(abs(a) >= 1): a is marginally Student-t(2 alpha0, mu0, beta0/(alpha0 lambda0)). Analytically exact."""
        scale = math.sqrt(self.beta0 / (self.alpha0 * self.lambda0))
        dof = 2.0 * self.alpha0
        return float(special.stdtr(dof, (-1.0 - self.mu0) / scale) + special.stdtr(dof, (self.mu0 - 1.0) / scale))

    def joint_logpdf(self, a: np.ndarray, sigma2: np.ndarray) -> np.ndarray:
        """log p(a, sigma^2), used by the test-only brute-force oracle."""
        a = np.asarray(a, dtype=FLOAT)
        s2 = np.asarray(sigma2, dtype=FLOAT)
        log_ig = (self.alpha0 * math.log(self.beta0) - special.gammaln(self.alpha0)
                  - (self.alpha0 + 1.0) * np.log(s2) - self.beta0 / s2)
        var_a = s2 / self.lambda0
        log_n = -0.5 * np.log(2.0 * math.pi * var_a) - 0.5 * (a - self.mu0) ** 2 / var_a
        return log_ig + log_n

    def sample_systems(self, rng: np.random.Generator, size: int) -> tuple[np.ndarray, np.ndarray]:
        sigma2 = self.beta0 / rng.gamma(shape=self.alpha0, scale=1.0, size=size)
        a = self.mu0 + np.sqrt(sigma2 / self.lambda0) * rng.standard_normal(size)
        return a.astype(FLOAT), np.sqrt(sigma2).astype(FLOAT)


@dataclass(frozen=True)
class StableCoefficientPrior:
    """P-STABLE: a on (-rho, rho), rho < 1, sigma known.

    shape = "uniform": a ~ U(-rho, rho).
    shape = "truncated_normal": a ~ N(mu0, tau0^2) truncated to (-rho, rho).
    """

    rho: float
    sigma: float
    shape: str = "uniform"
    mu0: float | None = None
    tau0: float | None = None
    family: str = "P-STABLE"

    def __post_init__(self) -> None:
        if not (0.0 < self.rho < 1.0):
            raise ValueError("P-STABLE requires 0 < rho < 1")
        _check_positive("sigma", self.sigma)
        if self.shape == "uniform":
            if self.mu0 is not None or self.tau0 is not None:
                raise ValueError("uniform P-STABLE takes no mu0/tau0")
        elif self.shape == "truncated_normal":
            if self.mu0 is None or self.tau0 is None:
                raise ValueError("truncated_normal P-STABLE requires mu0 and tau0")
            _check_positive("tau0", self.tau0)
        else:
            raise ValueError(f"unknown P-STABLE shape {self.shape!r}")

    @property
    def support(self) -> tuple[float, float]:
        return (-self.rho, self.rho)

    def spec(self) -> dict:
        d = {"family": self.family, "shape": self.shape, "rho": float(self.rho),
             "sigma": float(self.sigma), "likelihood": LIKELIHOOD_ID}
        if self.shape == "truncated_normal":
            d.update(mu0=float(self.mu0), tau0=float(self.tau0))
        return d

    def fingerprint(self) -> str:
        return canonical_fingerprint(self.spec())

    def explosive_probability(self) -> float:
        return 0.0

    def _tn_bounds(self) -> tuple[float, float]:
        return (-self.rho - self.mu0) / self.tau0, (self.rho - self.mu0) / self.tau0

    def coefficient_logpdf(self, a: np.ndarray) -> np.ndarray:
        """Normalised log density; -inf outside [-rho, rho] (boundary included: measure zero, but it keeps
        nodes that collapse onto the boundary in float64 finite)."""
        a = np.asarray(a, dtype=FLOAT)
        inside = np.abs(a) <= self.rho
        if self.shape == "uniform":
            val = np.full(a.shape, -math.log(2.0 * self.rho), dtype=FLOAT)
        else:
            lo, hi = self._tn_bounds()
            log_z = math.log(special.ndtr(hi) - special.ndtr(lo))
            z = (a - self.mu0) / self.tau0
            val = -0.5 * z * z - math.log(self.tau0) - 0.5 * math.log(2.0 * math.pi) - log_z
        return np.where(inside, val, -np.inf)

    def gaussian_prior_terms(self) -> tuple[float, float]:
        """(precision, precision * mean) of the Gaussian factor of the prior; (0, 0) for uniform."""
        if self.shape == "uniform":
            return 0.0, 0.0
        return 1.0 / self.tau0**2, self.mu0 / self.tau0**2

    def sample_systems(self, rng: np.random.Generator, size: int) -> tuple[np.ndarray, np.ndarray]:
        u = rng.uniform(size=size)
        if self.shape == "uniform":
            a = -self.rho + 2.0 * self.rho * u
        else:
            lo, hi = self._tn_bounds()
            plo, phi = special.ndtr(lo), special.ndtr(hi)
            a = self.mu0 + self.tau0 * special.ndtri(plo + u * (phi - plo))
            a = np.clip(a, np.nextafter(-self.rho, 0.0), np.nextafter(self.rho, 0.0))
        return a.astype(FLOAT), np.full(size, self.sigma, dtype=FLOAT)


ContinuousPrior = GaussianCoefficientPrior | NormalInverseGammaPrior | StableCoefficientPrior


def prior_from_spec(spec: dict) -> ContinuousPrior:
    """Inverse of ``prior.spec()`` (the likelihood entry must match LIKELIHOOD_ID)."""
    spec = dict(spec)
    if spec.pop("likelihood", LIKELIHOOD_ID) != LIKELIHOOD_ID:
        raise ValueError("prior spec has a different likelihood")
    family = spec.pop("family")
    if family == "P-GAUSS":
        return GaussianCoefficientPrior(**spec)
    if family == "P-NIG":
        return NormalInverseGammaPrior(**spec)
    if family == "P-STABLE":
        return StableCoefficientPrior(**spec)
    raise ValueError(f"unknown prior family {family!r}")
