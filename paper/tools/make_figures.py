"""Generate the manuscript figures from the pinned result files (pgfplots code; nothing drawn by hand).

Every plotted series is declared in the `figures:` block of paper/numbers.yaml by a pinned file key (the same
`files:` / `refs:` pins as the macros and tables) and a row filter, so new results (batches 4 and 5) are added by
pinning a file and declaring a series there; this script needs no change. Run by paper/build.py after make_tables.py.

generated/fig_gap.tex     : held-out population vs context-only gap against n (log-log), one panel per declared panel,
                            one line per value of the `series` column; filled marks = separable (lower bound >= delta),
                            open marks = not separable or borderline, crosses = MC-limited; dashed line = delta.
generated/fig_library.tex : left, share of (cell, library draw) pairs separable against K; right, the nearest-system
                            limit against K (theory file) with delta. Declared `provisional` until the F2 library map
                            reaches the largest K of the theory file.
generated/fig_cumulative.tex : cumulative held-out gap against n with the prior budget (dashed).
generated/fig_delta.tex   : largest separable n against the margin delta, per map and series (post hoc, S51).
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import io
import json
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BS = "\\"
COLORS = ("blue!75!black", "red!75!black", "green!45!black", "orange!90!black", "violet!80!black")
MARKS = ("*", "square*", "triangle*", "diamond*", "pentagon*")
SEPARABLE = {"IDENTIFIABLE", "SEPARABLE"}


def _bc():
    spec = importlib.util.spec_from_file_location("build_claims", ROOT / "paper" / "tools" / "build_claims.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_claims"] = mod
    spec.loader.exec_module(mod)
    return mod


def _raw(bc, data, key) -> bytes:
    f = data["files"][key]
    raw, _ = bc.git_blob(data["refs"][f["ref"]], f["path"])
    if raw is None:
        raise SystemExit(f"FAIL: {key} missing at its pinned commit")
    return gzip.decompress(raw) if f["path"].endswith(".gz") else raw


def _rows(bc, data, key, where: dict) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(_raw(bc, data, key).decode("utf-8"))))
    return [r for r in rows if all(str(r[k]) == str(v) for k, v in where.items())]


def _se(row: dict) -> float:
    if row.get("se", "") != "":
        return math.hypot(float(row["se"]), float(row.get("se_mc") or 0.0))
    return (float(row["estimate"]) - float(row["lo"])) / 3.0          # 1A / F1 files store lo = estimate - 3 SE


def _style(i: int) -> tuple[str, str]:
    return COLORS[i % len(COLORS)], MARKS[i % len(MARKS)]


def _coords(points) -> str:
    return " ".join(f"({x:g},{y:.6g})" for x, y in points)


def gap_panel(bc, data, spec: dict, delta: float) -> list[str]:
    rows = _rows(bc, data, spec["file"], spec.get("where", {}))
    by_series: dict[str, dict[float, dict]] = {}
    for r in rows:                                                     # first row per (series, n): de-duplicates
        by_series.setdefault(r[spec["series"]], {}).setdefault(float(r["n"]), r)
    xs = sorted({x for s in by_series.values() for x in s})
    pos = {"ne": "at={(0.98,0.98)}, anchor=north east", "sw": "at={(0.02,0.02)}, anchor=south west",
           "se": "at={(0.98,0.02)}, anchor=south east", "nw": "at={(0.02,0.98)}, anchor=north west"}
    extra = f", legend style={{{pos[spec.get('legend', 'ne')]}}}" + (f", {spec['opts']}" if spec.get("opts") else "")
    out = [f"{BS}nextgroupplot[title={{{spec['panel']}}}, xtick={{{','.join(f'{x:g}' for x in xs)}}}{extra}]"]
    dropped = 0
    for i, (sval, pts) in enumerate(sorted(by_series.items(), key=lambda kv: float(kv[0]))):
        col, mark = _style(i)
        good = [(x, r) for x, r in sorted(pts.items()) if float(r["estimate"]) > 0]
        dropped += len(pts) - len(good)
        label = spec["label"].format(f"{float(sval):g}")
        line = _coords((x, float(r["estimate"])) for x, r in good)
        out.append(f"{BS}addplot[{col}, thick, no markers] coordinates {{{line}}};")
        out.append(f"{BS}addlegendentry{{{label}}}")
        kinds = {"sep": [], "mc": [], "other": []}
        for x, r in good:
            dec = r.get("decision", "")
            sep = dec in SEPARABLE if dec not in ("", "MC-LIMITED") else float(r["estimate"]) - 3 * _se(r) >= delta
            kinds["mc" if dec == "MC-LIMITED" else "sep" if sep else "other"].append((x, float(r["estimate"])))
        opts = {"sep": f"mark={mark}, mark options={{fill={col}}}",
                "other": f"mark={mark}, mark options={{fill=white}}", "mc": "mark=x, mark size=3pt"}
        for k, pts_k in kinds.items():
            if pts_k:
                out.append(f"{BS}addplot[{col}, only marks, {opts[k]}, forget plot] coordinates {{{_coords(pts_k)}}};")
    out.append(f"{BS}addplot[black, dashed, forget plot] coordinates {{({min(xs):g},{delta}) ({max(xs):g},{delta})}};")
    if dropped:
        out.append(f"% {dropped} non-positive estimate(s) not drawn on the log axis")
    return out


def fig_gap(bc, data, cfg: dict, delta: float) -> list[str]:
    panels = cfg["panels"]
    cols = 2
    lines = ["% generated by paper/tools/make_figures.py from the pinned result files; do not edit",
             f"{BS}begin{{tikzpicture}}",
             f"{BS}begin{{groupplot}}[group style={{group size={cols} by {math.ceil(len(panels) / cols)}, "
             "horizontal sep=1.6cm, vertical sep=2.2cm}, width=0.48\\textwidth, height=0.36\\textwidth, xmode=log, "
             "ymode=log, log ticks with fixed point, xlabel={context length $n$}, ylabel={gap (nats)}, "
             "legend style={font=\\scriptsize}, title style={font=\\small}, tick label style={font=\\scriptsize}]"]
    for p in panels:
        lines += gap_panel(bc, data, p, delta)
    lines += [f"{BS}end{{groupplot}}", f"{BS}end{{tikzpicture}}"]
    return lines


def _share(bc, data, s: dict, delta: float) -> dict[int, float]:
    rows = _rows(bc, data, s["file"], s.get("where", {}))
    if s["kind"] == "frac":                                           # per-cell share of draws (1A / F1 decision files)
        seen, by_k = set(), {}
        for r in rows:
            key = tuple(r[k] for k in ("r", "n", "K"))
            if key not in seen:
                seen.add(key)
                by_k.setdefault(int(float(r["K"])), []).append(float(r["frac_lo_ge_delta"]))
    elif s["kind"] == "rows_est":                                     # per-draw rows with estimate, se, se_mc (batch 5)
        by_k = {}
        for r in rows:
            lo = float(r["estimate"]) - 3.0 * math.hypot(float(r["se"]), float(r.get("se_mc") or 0.0))
            by_k.setdefault(int(float(r["K"])), []).append(float(lo >= delta))
    else:                                                             # per-draw rows (F3 / F2 row files)
        by_k = {}
        for r in rows:
            by_k.setdefault(int(float(r["K"])), []).append(float(float(r["mean"]) - 3.0 * float(r["se"]) >= delta))
    return {k: 100.0 * sum(v) / len(v) for k, v in sorted(by_k.items())}


def fig_library(bc, data, cfg: dict, delta: float) -> list[str]:
    lines = ["% generated by paper/tools/make_figures.py from the pinned result files; do not edit",
             f"{BS}begin{{tikzpicture}}",
             f"{BS}begin{{groupplot}}[group style={{group size=2 by 1, horizontal sep=1.8cm}}, width=0.48\\textwidth, "
             "height=0.38\\textwidth, xmode=log, log basis x=2, xlabel={library size $K$}, "
             "legend style={font=\\scriptsize, at={(0.98,0.98)}, anchor=north east}, title style={font=\\small}, "
             "tick label style={font=\\scriptsize}]",
             f"{BS}nextgroupplot[title={{separable (cell, library) pairs}}, ylabel={{per cent}}, ymin=0, ymax=105, "
             "legend style={at={(0.5,-0.3)}, anchor=north, legend columns=2}]"]
    for i, s in enumerate(cfg["share"]):
        col, mark = _style(i)
        pts = _coords(_share(bc, data, s, delta).items())
        lines.append(f"{BS}addplot[{col}, thick, mark={mark}] coordinates {{{pts}}};")
        lines.append(f"{BS}addlegendentry{{{s['label']}}}")
    lines.append(f"{BS}nextgroupplot[title={{long-context limit}}, ylabel={{nats}}, ymode=log]")
    ks = []
    for i, s in enumerate(cfg["limit"]):
        col, mark = _style(i)
        d = json.loads(_raw(bc, data, s["file"]))
        for part in s["json"].split("."):
            d = d[part]
        pts = sorted((int(k), v["mean"]) for k, v in d.items() if v["mean"] > 0)
        ks += [k for k, _ in pts]
        lines.append(f"{BS}addplot[{col}, thick, dashed, mark={mark}] coordinates {{{_coords(pts)}}};")
        lines.append(f"{BS}addlegendentry{{{s['label']}}}")
    lines.append(f"{BS}addplot[black, dashed, forget plot] coordinates {{({min(ks)},{delta}) ({max(ks)},{delta})}};")
    lines += [f"{BS}end{{groupplot}}", f"{BS}end{{tikzpicture}}"]
    return lines


def _json_at(bc, data, spec: dict) -> float:
    d = json.loads(_raw(bc, data, spec["file"]))
    for k in spec["json_keys"]:
        d = d[k]
    return float(d)


def fig_cumulative(bc, data, cfg: dict) -> list[str]:
    """Cumulative gap (kind = cum rows) against n, one panel per declared panel, with its budget as a dashed line."""
    panels = cfg["panels"]
    lines = ["% generated by paper/tools/make_figures.py from the pinned result files; do not edit",
             f"{BS}begin{{tikzpicture}}",
             f"{BS}begin{{groupplot}}[group style={{group size={len(panels)} by 1, horizontal sep=1.0cm}}, "
             "width=0.345\\textwidth, height=0.32\\textwidth, xmode=log, log ticks with fixed point, ymin=0, "
             "xlabel={context length $n$}, legend style={font=\\scriptsize}, title style={font=\\small}, "
             "tick label style={font=\\scriptsize}]"]
    pos = {"se": "at={(0.98,0.02)}, anchor=south east", "nw": "at={(0.02,0.98)}, anchor=north west"}
    for k, p in enumerate(panels):
        rows = _rows(bc, data, p["file"], p["where"])
        budget = _json_at(bc, data, p["budget"])
        ylab = ", ylabel={cumulative gap (nats)}" if k == 0 else ""
        lines.append(f"{BS}nextgroupplot[title={{{p['panel']}}}, ymax={1.15 * budget:.3f}, "
                     f"legend style={{{pos[p.get('legend', 'se')]}}}{ylab}"
                     + (f", {p['opts']}" if p.get("opts") else "") + "]")
        for i, sval in enumerate(p["order"]):
            col, _ = _style(i)
            pts = sorted((int(r["n"]), float(r["estimate"])) for r in rows
                         if r[p["series"]] == sval and int(r["n"]) >= 1)
            lines.append(f"{BS}addplot[{col}, thick, no markers] coordinates {{{_coords(pts)}}};")
            lines.append(f"{BS}addlegendentry{{{p['legend_labels'][sval]}}}")
        xs = [int(r["n"]) for r in rows if int(r["n"]) >= 1]
        lines.append(f"{BS}addplot[black, dashed, forget plot] coordinates {{({min(xs)},{budget:.4f}) "
                     f"({max(xs)},{budget:.4f})}};")
    lines += [f"{BS}end{{groupplot}}", f"{BS}end{{tikzpicture}}"]
    return lines


def delta_panel(bc, data, spec: dict, delta: float, grid: list[float]) -> list[str]:
    """Largest separable n against the margin: n*(d) = max{n : estimate - 3 SE >= d} per series (MC-limited cells
    excluded); a series stops at the first d where no cell qualifies (n* is non-increasing in d)."""
    rows = [r for r in _rows(bc, data, spec["file"], spec.get("where", {})) if r.get("decision", "") != "MC-LIMITED"]
    by_series: dict[str, dict[float, float]] = {}
    for r in rows:                                                     # first row per (series, n), as in gap_panel
        by_series.setdefault(r[spec["series"]], {}).setdefault(float(r["n"]), float(r["estimate"]) - 3 * _se(r))
    ns = sorted({n for s in by_series.values() for n in s})
    pos = {"ne": "at={(0.98,0.98)}, anchor=north east", "sw": "at={(0.02,0.02)}, anchor=south west"}
    extra = f", legend style={{{pos[spec.get('legend', 'ne')]}}}" + (f", {spec['opts']}" if spec.get("opts") else "")
    out = [f"{BS}nextgroupplot[title={{{spec['panel']}}}, ytick={{{','.join(f'{n:g}' for n in ns)}}}{extra}]"]
    for i, (sval, lo) in enumerate(sorted(by_series.items(), key=lambda kv: float(kv[0]))):
        col, _ = _style(i)
        pts = []
        for d in grid:
            ok = [n for n, b in lo.items() if b >= d]
            if not ok:
                break
            pts.append((d, max(ok)))
        if pts:
            out.append(f"{BS}addplot[{col}, thick, const plot, no markers] coordinates {{{_coords(pts)}}};")
            out.append(f"{BS}addlegendentry{{{spec['label'].format(f'{float(sval):g}')}}}")
    out.append(f"{BS}addplot[black, dashed, forget plot] coordinates {{({delta},{min(ns):g}) ({delta},{max(ns):g})}};")
    return out


def fig_delta(bc, data, cfg: dict, delta: float) -> list[str]:
    panels = cfg["panels"]
    lo_d, hi_d, k = cfg["range"][0], cfg["range"][1], 240
    grid = [lo_d * (hi_d / lo_d) ** (i / (k - 1)) for i in range(k)]
    lines = ["% generated by paper/tools/make_figures.py from the pinned map files; do not edit (post hoc, Appendix B)",
             f"{BS}begin{{tikzpicture}}",
             f"{BS}begin{{groupplot}}[group style={{group size=2 by {math.ceil(len(panels) / 2)}, horizontal sep=1.6cm, "
             "vertical sep=2.2cm}, width=0.47\\textwidth, height=0.3\\textwidth, xmode=log, ymode=log, "
             f"xmin={lo_d:g}, xmax={hi_d:g}, xtick={{{','.join(f'{x:g}' for x in cfg['xticks'])}}}, "
             "log ticks with fixed point, xlabel={margin $\\delta$ (nats)}, ylabel={largest separable $n$}, "
             "legend style={font=\\scriptsize}, title style={font=\\small}, tick label style={font=\\scriptsize}]"]
    for p in panels:
        lines += delta_panel(bc, data, p, delta, grid)
    lines += [f"{BS}end{{groupplot}}", f"{BS}end{{tikzpicture}}"]
    return lines


def main() -> int:
    bc = _bc()
    data = yaml.safe_load((ROOT / "paper" / "numbers.yaml").read_text(encoding="utf-8"))
    cfg = data["figures"]
    delta = float(bc.extract(_raw(bc, data, cfg["delta"]["file"]), cfg["delta"]["x"]))
    gen = ROOT / "paper" / "generated"
    gen.mkdir(exist_ok=True)
    (gen / "fig_gap.tex").write_text("\n".join(fig_gap(bc, data, cfg["gap"], delta)) + "\n", encoding="utf-8")
    lib = fig_library(bc, data, cfg["library"], delta)
    (gen / "fig_library.tex").write_text("\n".join(lib) + "\n", encoding="utf-8")
    if "cumulative" in cfg:
        cum = fig_cumulative(bc, data, cfg["cumulative"])
        (gen / "fig_cumulative.tex").write_text("\n".join(cum) + "\n", encoding="utf-8")
    if "delta_curves" in cfg:
        dc = fig_delta(bc, data, cfg["delta_curves"], delta)
        (gen / "fig_delta.tex").write_text("\n".join(dc) + "\n", encoding="utf-8")
    print(f"figures: fig_gap ({len(cfg['gap']['panels'])} panels), fig_library "
          f"({len(cfg['library']['share'])} share series, {len(cfg['library']['limit'])} limit series"
          f"{', PROVISIONAL' if cfg['library'].get('provisional') else ''}); delta {delta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
