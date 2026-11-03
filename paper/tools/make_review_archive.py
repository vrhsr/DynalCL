"""Export the anonymised review archive: no git history, every file listed in a SHA-256 manifest, identifying strings
scrubbed, and a scan that fails if any identifying string remains.

Contents (declared in paper/review_archive.yaml):
  pinned/<commit>/<path> : every evidence blob named in claims.yaml or numbers.yaml, read with `git show` at its commit
  code/<path>            : code, specifications and disclosure logs at `code_ref`
  paper/<path>           : the manuscript sources at the paper commit (HEAD)
  MANIFEST.json, SHA256SUMS, README.md
The paper builds from the archive without git: `python paper/build.py --archive` (build_claims.git_blob then reads
pinned/<commit>/<path>). Scrubbing changes some files' bytes (never a number the paper extracts; the build checks this);
MANIFEST.json records the SHA-256 of each file both before and after scrubbing.

    python paper/tools/make_review_archive.py --out ../review-archive [--zip]
"""

from __future__ import annotations

import argparse
import fnmatch
import gzip
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# Generic rules (no personal data here; personal identifiers come from the identifiers file, which is never exported).
# Order matters: whole paths before the names inside them. Third-party URLs are left alone (the personal handle rule
# covers the authors' own); third-party e-mail addresses listed under `keep_emails` (licence attributions) are kept.
GENERIC = [
    (r"git\+https://github\.com/[^\s\"',]+", "anon-vcs-requirement"),         # pip VCS lines name private repositories
    (r"(?<![A-Za-z])[A-Za-z]:(\\\\|\\|/)+Users(\\\\|\\|/)+[A-Za-z0-9_.-]+", "ANON-HOME"),
    (r"/home/[A-Za-z0-9_.-]+", "/home/anon-user"),
]
# e-mail addresses; top-level domains listed so that matrix products such as x@self.weight are not touched
EMAIL = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.(com|org|net|edu|gov|io|ai|in|uk|de|fr|ch|ca|au)\b"
ANON = ("anon-", "ANON-", "/home/anon-user")


def git(*args: str) -> bytes:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if out.returncode != 0:
        raise SystemExit(f"FAIL: git {' '.join(args)}: {out.stderr.decode(errors='replace').strip()}")
    return out.stdout


def load_rules(path: Path) -> list[tuple[re.Pattern, str]]:
    rules = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            pat, rep = (s.strip() for s in line.split("=>", 1))
            rules.append((re.compile(pat, re.IGNORECASE), rep))
    return rules


def scrub(raw: bytes, rules) -> tuple[bytes, int]:
    """Apply the rules to text (gzip members are scrubbed inside and re-compressed deterministically)."""
    if raw[:2] == b"\x1f\x8b":
        inner, n = scrub(gzip.decompress(raw), rules)
        return (gzip.compress(inner, mtime=0) if n else raw), n
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw, 0                                                  # binary: left as is, still scanned
    n = 0
    for pat, rep in rules:
        new, k = pat.subn(rep, text)
        n += k if new != text else 0                                   # kept matches (keep_emails) are not counted
        text = new
    return text.encode("utf-8"), n


def scan_text(raw: bytes) -> str:
    if raw[:2] == b"\x1f\x8b":
        return scan_text(gzip.decompress(raw))
    return raw.decode("utf-8", errors="replace")


def pinned_pairs() -> set[tuple[str, str]]:
    claims = yaml.safe_load((ROOT / "paper" / "claims.yaml").read_text(encoding="utf-8"))
    numbers = yaml.safe_load((ROOT / "paper" / "numbers.yaml").read_text(encoding="utf-8"))
    pairs = {(c["source"]["ref"], c["source"]["path"]) for c in claims["claims"] if c["source"]["ref"] != "none"}
    pairs |= {(numbers["refs"][f["ref"]], f["path"]) for f in numbers["files"].values()}
    return pairs


def tree_files(ref: str, paths: list[str]) -> list[str]:
    return [p for p in git("ls-tree", "-r", "--name-only", ref, "--", *paths).decode("utf-8").splitlines() if p]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="new, empty or missing directory for the archive")
    ap.add_argument("--zip", action="store_true", help="also write <out>.zip (deterministic)")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load((ROOT / "paper" / "review_archive.yaml").read_text(encoding="utf-8"))
    personal = load_rules(ROOT / cfg["identifiers"])
    keep = {e.lower() for e in cfg.get("keep_emails", [])}
    email = re.compile(EMAIL, re.IGNORECASE)
    rules = [(re.compile(p, re.IGNORECASE), r) for p, r in GENERIC] + personal
    rules.append((email, lambda m: m.group(0) if m.group(0).lower() in keep else "anon-email"))
    never = [re.compile(p) for p in cfg["never"]]
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"FAIL: {out} is not empty")
    if git("status", "--porcelain", "--", "paper").strip():
        raise SystemExit("FAIL: paper/ has uncommitted changes; the archive is built from committed files only")
    paper_ref = git("rev-parse", "HEAD").decode().strip()

    plan: list[tuple[str, str, str]] = []                          # (archive path, ref, repository path)
    plan += [(f"pinned/{ref}/{path}", ref, path) for ref, path in sorted(pinned_pairs())]
    code_ref = cfg["code_ref"]
    docs = [p for p in tree_files(code_ref, ["docs"]) if any(fnmatch.fnmatch(p, g) for g in cfg["docs_globs"])]
    plan += [(f"code/{p}", code_ref, p) for p in tree_files(code_ref, cfg["code_paths"]) + docs]
    plan += [(p, paper_ref, p) for p in tree_files(paper_ref, cfg["paper_paths"])]
    blocked = [a for a, _, _ in plan if any(r.search(a) for r in never)]
    if blocked:
        raise SystemExit(f"FAIL: never-export rule matched: {blocked}")

    manifest = []
    for apath, ref, path in plan:
        raw = git("show", f"{ref}:{path}")
        clean, n = scrub(raw, rules)
        dest = out / apath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(clean)
        manifest.append({"path": apath, "sha256": hashlib.sha256(clean).hexdigest(), "bytes": len(clean),
                         "source_commit": ref, "source_path": path,
                         "source_sha256": hashlib.sha256(raw).hexdigest(), "replacements": n})

    readme = README.format(n=len(manifest), code_ref=code_ref, paper_ref=paper_ref,
                           scrubbed=sum(1 for m in manifest if m["replacements"]))
    (out / "README.md").write_text(readme, encoding="utf-8", newline="\n")   # LF on every platform (sha256sum -c)
    meta = {"schema": "review-archive/v1", "paper_commit": paper_ref, "code_commit": code_ref, "files": manifest}
    (out / "MANIFEST.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    sums = [f"{m['sha256']}  {m['path']}" for m in manifest]
    sums.append(f"{hashlib.sha256((out / 'README.md').read_bytes()).hexdigest()}  README.md")
    sums.sort(key=lambda s: s.split("  ", 1)[1])
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")

    rc = scan(out, [p for p, _ in personal] + [re.compile(p, re.IGNORECASE) for p, _ in GENERIC] + [email], keep)
    if rc:
        return rc
    total, n_rep = sum(m["bytes"] for m in manifest), sum(m["replacements"] for m in manifest)
    print(f"archive: {len(manifest)} files, {total / 1e6:.1f} MB, {n_rep} replacements "
          f"in {sum(1 for m in manifest if m['replacements'])} files; scan PASS -> {out}")
    if args.zip:
        z = out.with_suffix(".zip")
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(p for p in out.rglob("*") if p.is_file()):
                info = zipfile.ZipInfo(f.relative_to(out).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, f.read_bytes())
        print(f"zip: {z} ({z.stat().st_size / 1e6:.1f} MB), sha256 {hashlib.sha256(z.read_bytes()).hexdigest()}")
    return 0


def scan(out: Path, patterns: list[re.Pattern], keep: set[str]) -> int:
    """Fail on any identifying string in any file name or content (gzip members decompressed)."""
    hits = []
    for f in sorted(p for p in out.rglob("*") if p.is_file()):
        rel = f.relative_to(out).as_posix()
        text = scan_text(f.read_bytes())
        for pat in patterns:
            for where in (rel, text):
                for m in pat.finditer(where):
                    if not m.group(0).startswith(ANON) and m.group(0).lower() not in keep:
                        hits.append(f"{rel}: {pat.pattern!r} matched {m.group(0)[:40]!r}")
                        break
    if hits:
        print("scan FAILED: identifying strings remain\n  " + "\n  ".join(hits[:50]))
        return 1
    return 0


README = """# Review archive (anonymised)

Supplementary material for the anonymous TMLR submission "Where Bayesian References Disagree: Separability Maps for
In-Context Learning of Linear Dynamical Systems". It holds {n} files, listed with their SHA-256 in `SHA256SUMS` and
`MANIFEST.json`, and no version-control history. The full history and an archival DOI will accompany the camera-ready
version.

* `paper/`: the manuscript sources at the paper commit ({paper_ref}). `python paper/build.py --archive` re-extracts
  every number in the paper from `pinned/` (claims table, number macros, tables, figures, a numbers audit) and builds
  the PDF if `pdflatex` is available; it needs Python 3 with PyYAML.
* `pinned/<commit>/<path>`: each evidence file named in `paper/claims.yaml` or `paper/numbers.yaml`, exactly as it is at
  that commit (commit identifiers are kept so that the claims table can be checked against them).
* `code/`: the reference predictors, map and analysis code, tests, configurations, specifications, pre-registrations
  and the append-only disclosure logs, at the code commit ({code_ref}). Freeze manifests list hashes of the frozen
  files; files that needed anonymisation (below) no longer match them byte for byte. Tests that need stored run
  outputs are not runnable from this archive alone.

Anonymisation: names, user names, e-mail addresses, home and workspace paths and repository URLs were replaced by
`anon-...` tokens in {scrubbed} files; `MANIFEST.json` gives, for every file, the SHA-256 before and after and the
number of replacements. No number used by the paper was changed (the archive build re-extracts and checks them all).

Verify: `sha256sum -c SHA256SUMS` (or any SHA-256 tool), then `python paper/build.py --archive`.
"""


if __name__ == "__main__":
    raise SystemExit(main())
