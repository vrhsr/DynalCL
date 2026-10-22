"""KL divergence between two one-step predictives, per context, by composite Gauss-Legendre quadrature in y.

KL(p || q) = int p(y) [log p(y) - log q(y)] dy. NUMERICALLY APPROXIMATED with verified convergence:
* the window is supplied by the caller and must hold p's mass; the integrated mass of p is returned so the caller
  can assert it (``mass_error``), which catches a window that misses mass;
* panels are at most ``panel_width`` wide (default sigma / 2). Every density used here is a mixture of Gaussians
  with component sd >= sigma, so each panel spans at most half a component sd, and 8-node Gauss-Legendre on it is
  accurate far below the error budget (DERIVED; TESTED by node doubling and by the closed-form Gaussian KL).

Used for (i) the Rao-Blackwellised estimate of truth-matched score gaps (E_D[LS(A) - LS(B)] = E_D[KL(A || B)] when A
is Bayes for D) and (ii) behavioural divergences where no reference is true (probe and out-of-support sets).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

FLOAT = np.float64


def _legendre(q: int) -> tuple[np.ndarray, np.ndarray]:
    return np.polynomial.legendre.leggauss(q)


def kl_quadrature(logp: Callable[[np.ndarray, np.ndarray], np.ndarray],
                  logq: Callable[[np.ndarray, np.ndarray], np.ndarray],
                  lo: np.ndarray, hi: np.ndarray, panel_width: float, nodes_per_panel: int = 8,
                  chunk: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Per-context KL(p || q) on windows [lo_i, hi_i].

    ``logp(idx, y)`` / ``logq(idx, y)`` return log densities for the contexts ``idx`` (int array, length n) at nodes
    ``y`` of shape (n, G). Returns (kl, mass) with mass = int_window p (should be 1 within the caller's tolerance).
    """
    lo = np.asarray(lo, dtype=FLOAT)
    hi = np.asarray(hi, dtype=FLOAT)
    if np.any(hi <= lo) or not panel_width > 0:
        raise ValueError("invalid quadrature window")
    x, w = _legendre(nodes_per_panel)
    n_all = lo.shape[0]
    kl = np.empty(n_all, dtype=FLOAT)
    mass = np.empty(n_all, dtype=FLOAT)
    panels_all = np.maximum(1, np.ceil((hi - lo) / panel_width).astype(int))
    order = np.argsort(panels_all, kind="stable")          # group contexts with similar panel counts
    for c0 in range(0, n_all, chunk):
        idx = order[c0:c0 + chunk]
        p = int(panels_all[idx].max())
        a = lo[idx]
        b = hi[idx]
        edges = a[:, None] + (b - a)[:, None] * (np.arange(p + 1) / p)
        half = 0.5 * (edges[:, 1:] - edges[:, :-1])
        mid = 0.5 * (edges[:, 1:] + edges[:, :-1])
        nodes = (mid[:, :, None] + half[:, :, None] * x).reshape(idx.size, p * nodes_per_panel)
        weights = (half[:, :, None] * w).reshape(idx.size, p * nodes_per_panel)
        lp = logp(idx, nodes)
        lq = logq(idx, nodes)
        pw = np.exp(lp) * weights
        mass[idx] = pw.sum(axis=1)
        # where p underflows to 0 the term is 0 regardless of log q (also guards -inf * 0)
        diff = np.where(pw > 0, lp - lq, 0.0)
        kl[idx] = (pw * diff).sum(axis=1)
    return kl, mass


def gaussian_kl(m1, s1, m2, s2) -> np.ndarray:
    """Closed-form KL(N(m1, s1^2) || N(m2, s2^2)) (test oracle)."""
    m1, s1, m2, s2 = (np.asarray(v, dtype=FLOAT) for v in (m1, s1, m2, s2))
    return np.log(s2 / s1) + (s1**2 + (m1 - m2) ** 2) / (2.0 * s2**2) - 0.5
