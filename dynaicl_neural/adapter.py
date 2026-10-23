"""Evaluation adapter: trained model -> one-step predictive in float64 (PREREG_stage1 section 5).

The model sees only contexts cut by ``dynaicl.evaluation.harness.make_context`` (float64, cast to float32 for the
network) and returns the frozen ``GaussianMixturePredictive``. Only h = 1 is supported. Batch evaluation takes an
(N, n + 1) array whose rows were each produced by ``make_context`` and reads the output at the LAST position.
"""

from __future__ import annotations

import numpy as np
import torch

from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianMixturePredictive
from dynaicl.systems.context import ContextWindow
from dynaicl_neural import mutations
from dynaicl_neural.models import LOG_SD_MAX, LOG_SD_MIN, model_inputs

FLOAT = np.float64


@torch.no_grad()
def mixture_params(model: torch.nn.Module, contexts: np.ndarray, device: str = "cpu",
                   batch: int = 8192) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(log weights, means, variances), each (N, m) float64, for the predictive of x_{n+1} given each row x_0..x_n."""
    ctx = np.asarray(contexts)
    if ctx.dtype != np.float64 or ctx.ndim != 2:
        raise TypeError("contexts must be a float64 (N, n + 1) array cut by make_context")
    model.eval()
    pos = ctx.shape[1] - 1
    if mutations.active("off_by_one_position"):
        pos = max(0, pos - 1)
    outs = []
    for i0 in range(0, ctx.shape[0], batch):
        x = torch.from_numpy(ctx[i0:i0 + batch].astype(np.float32)).to(device)
        outs.append(model(model_inputs(x))[:, pos].double().cpu().numpy())
    p = np.concatenate(outs)
    m = p.shape[1] // 3
    logits, mu, log_sd = p[:, :m], p[:, m:2 * m], np.clip(p[:, 2 * m:], LOG_SD_MIN, LOG_SD_MAX)
    log_w = logits - np.logaddexp.reduce(logits, axis=1, keepdims=True)
    return log_w, mu, np.exp(2.0 * log_sd)


def mixture_logpdf(log_w: np.ndarray, mu: np.ndarray, var: np.ndarray, y: np.ndarray) -> np.ndarray:
    """log density of per-row mixtures at y of shape (N,) or (N, G); float64."""
    y = np.asarray(y, dtype=FLOAT)
    squeeze = y.ndim == 1
    yy = y[:, None] if squeeze else y
    comp = (log_w[:, None, :] - 0.5 * (yy[:, :, None] - mu[:, None, :]) ** 2 / var[:, None, :]
            - 0.5 * np.log(2.0 * np.pi * var[:, None, :]))
    out = np.logaddexp.reduce(comp, axis=2)
    return out[:, 0] if squeeze else out


class ModelPredictor(Predictor):
    """A trained model behind the frozen Predictor interface (one context at a time; for tests and spot checks)."""

    def __init__(self, model: torch.nn.Module, name: str, device: str = "cpu"):
        self.model, self.device = model, device
        self.description = PredictorDescription(
            name=name, category="trained-model", assumed_system_distribution=None,
            may_access=("context",), must_not_access=("true a", "future values", "evaluation systems"),
            uses_true_noise_scale=False, assumptions="neural network pretrained on a Stage 1 arm")

    def _predict(self, context: ContextWindow, horizon: int) -> GaussianMixturePredictive:
        if horizon != 1:
            raise NotImplementedError("Stage 1 models predict one step ahead only")
        lw, mu, var = mixture_params(self.model, context.values[None, :], self.device)
        return GaussianMixturePredictive(lw[0], mu[0], var[0], info={"model": self.description.name})
