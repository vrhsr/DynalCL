"""Stage 1 sequence models with a Gaussian-mixture output head (PREREG_stage1 section 4).

Every model maps x_0..x_T (shape (B, T + 1)) to mixture parameters at every position t (shape (B, T + 1, 3m)); the
parameters at position t describe the predictive density of x_{t+1} given x_0..x_t. Causality is by construction
(masked attention; recurrences run forward) and TESTED by comparing cut contexts with full sequences.

Attention is written out explicitly (no fused kernels) so that ``torch.use_deterministic_algorithms(True)`` holds on
GPU.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import torch
from torch import nn

from dynaicl_neural import mutations

LOG_SD_MIN, LOG_SD_MAX = -7.0, 7.0


@dataclass(frozen=True)
class ModelSpec:
    family: str            # "transformer", "gru", "ssm"
    d: int
    layers: int
    heads: int = 1
    m: int = 2             # mixture components (head floor: m = 2)
    max_len: int = 128

    def to_dict(self) -> dict:
        return asdict(self)


SIZES = {
    "S": ModelSpec("transformer", 32, 2, 2),
    "M": ModelSpec("transformer", 64, 4, 4),
    "L": ModelSpec("transformer", 128, 8, 8),
    "DW-shallow": ModelSpec("transformer", 96, 2, 4),
    "DW-deep": ModelSpec("transformer", 48, 8, 4),
    "GRU": ModelSpec("gru", 128, 2),
    "SSM": ModelSpec("ssm", 64, 4),
    "XS": ModelSpec("transformer", 16, 1, 2),          # tests only (end-to-end pipeline test); never in a run config
}


def mixture_log_prob(params: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """log p(y) for mixture parameters (..., 3m) = [logits | means | log sds] and targets y (...)."""
    m = params.shape[-1] // 3
    logits, mu, log_sd = params[..., :m], params[..., m:2 * m], params[..., 2 * m:]
    log_sd = log_sd.clamp(LOG_SD_MIN, LOG_SD_MAX)
    log_w = torch.log_softmax(logits, dim=-1)
    z = (y.unsqueeze(-1) - mu) / torch.exp(log_sd)
    comp = log_w - 0.5 * z * z - log_sd - 0.5 * math.log(2.0 * math.pi)
    return torch.logsumexp(comp, dim=-1)


def sinusoidal_positions(max_len: int, d: int) -> torch.Tensor:
    pos = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
    div = torch.exp(torch.arange(0, d, 2, dtype=torch.float32) * (-math.log(10000.0) / d))
    pe = torch.zeros(max_len, d)
    pe[:, 0::2] = torch.sin(pos * div)
    pe[:, 1::2] = torch.cos(pos * div[: d // 2])
    return pe


class Block(nn.Module):
    def __init__(self, d: int, heads: int):
        super().__init__()
        self.h = heads
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, d = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(d, dim=-1)
        q, k, v = (z.view(b, t, self.h, d // self.h).transpose(1, 2) for z in (q, k, v))
        att = (q @ k.transpose(-1, -2)) / math.sqrt(d // self.h)
        if not mutations.active("missing_causal_mask"):
            mask = torch.ones(t, t, dtype=torch.bool, device=x.device).triu(1)
            att = att.masked_fill(mask, float("-inf"))
        y = torch.softmax(att, dim=-1) @ v
        x = x + self.proj(y.transpose(1, 2).reshape(b, t, d))
        return x + self.mlp(self.ln2(x))


class CausalTransformer(nn.Module):
    def __init__(self, spec: ModelSpec):
        super().__init__()
        if spec.d % spec.heads:
            raise ValueError("d must be divisible by heads")
        self.spec = spec
        self.embed = nn.Linear(1, spec.d)
        self.register_buffer("pe", sinusoidal_positions(spec.max_len, spec.d), persistent=False)
        self.blocks = nn.ModuleList([Block(spec.d, spec.heads) for _ in range(spec.layers)])
        self.ln = nn.LayerNorm(spec.d)
        self.head = nn.Linear(spec.d, 3 * spec.m)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.shape[1] > self.spec.max_len:
            raise ValueError("sequence longer than max_len")
        h = self.embed(x.unsqueeze(-1)) + self.pe[: x.shape[1]]
        for blk in self.blocks:
            h = blk(h)
        return self.head(self.ln(h))


class GRUModel(nn.Module):
    def __init__(self, spec: ModelSpec):
        super().__init__()
        self.spec = spec
        self.embed = nn.Linear(1, spec.d)
        self.rnn = nn.GRU(spec.d, spec.d, num_layers=spec.layers, batch_first=True)
        self.head = nn.Linear(spec.d, 3 * spec.m)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h, _ = self.rnn(self.embed(x.unsqueeze(-1)))
        return self.head(h)


class DiagonalLinearSSMLayer(nn.Module):
    """h_t = lambda * h_{t-1} + B u_t (lambda in (0, 1) per channel), y_t = u_t + MLP(LN(C h_t))."""

    def __init__(self, d: int):
        super().__init__()
        self.lam_logit = nn.Parameter(torch.linspace(-2.0, 4.0, d))
        self.inp, self.out = nn.Linear(d, d), nn.Linear(d, d)
        self.ln = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        lam = torch.sigmoid(self.lam_logit)
        b_u = self.inp(u)
        h = torch.zeros_like(b_u[:, 0])
        hs = []
        for t in range(u.shape[1]):
            h = lam * h + b_u[:, t]
            hs.append(h)
        hseq = torch.stack(hs, dim=1)
        return u + self.mlp(self.ln(self.out(hseq)))


class LinearSSM(nn.Module):
    def __init__(self, spec: ModelSpec):
        super().__init__()
        self.spec = spec
        self.embed = nn.Linear(1, spec.d)
        self.layers = nn.ModuleList([DiagonalLinearSSMLayer(spec.d) for _ in range(spec.layers)])
        self.head = nn.Linear(spec.d, 3 * spec.m)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.embed(x.unsqueeze(-1))
        for layer in self.layers:
            h = layer(h)
        return self.head(h)


def build_model(spec: ModelSpec) -> nn.Module:
    return {"transformer": CausalTransformer, "gru": GRUModel, "ssm": LinearSSM}[spec.family](spec)


def model_inputs(x: torch.Tensor) -> torch.Tensor:
    """The network input for sequences x_0..x_T. Mutation ``target_in_input`` shifts the next value into position t."""
    if mutations.active("target_in_input"):
        nxt = torch.cat([x[:, 1:], x[:, -1:]], dim=1)
        return 0.5 * (x + nxt)
    return x


def n_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
