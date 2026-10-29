"""Numbers audit of the manuscript text (task E4 / F2): fail on any number that does not come from a generated macro.

Rule: in paper/sections/*.tex, outside comments and outside the arguments of \\cite, \\ref, \\eqref, \\label, \\url, \\href,
\\input, \\includegraphics and \\begin/\\end, the text may contain no decimal number and no integer above 10. Every result
number must be a macro from paper/generated/numbers.tex (re-extracted from a pinned commit). Small structural integers
(n <= 3, "two replicates", d = 2) are allowed; years inside citations are inside \\cite and therefore ignored.
Also fails on any use of an undefined \\macro that looks like a number macro (defined in numbers.yaml but missing).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_ARGS = re.compile(r"\\(cite[tp]?|ref|eqref|label|url|href|input|include|includegraphics|begin|end|autoref|cref)"
                       r"(\[[^\]]*\])?\{[^}]*\}")
NUMBER = re.compile(r"(?<![A-Za-z\\])(\d+\.\d+|\.\d+|\d{2,})")


def scan(path: Path) -> list[str]:
    bad = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = re.sub(r"(?<!\\)%.*$", "", line)
        text = SKIP_ARGS.sub("", text)
        for m in NUMBER.finditer(text):
            tok = m.group(1)
            if "." not in tok and int(tok) <= 10:
                continue
            bad.append(f"{path.name}:{i}: bare number {tok!r}: {line.strip()[:100]}")
    return bad


def main() -> int:
    files = sorted((ROOT / "paper" / "sections").glob("*.tex"))
    if not files:
        print("FAIL: no section files found")
        return 1
    bad = [b for f in files for b in scan(f)]
    defined = set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}",
                             (ROOT / "paper" / "generated" / "numbers.tex").read_text(encoding="utf-8")))
    used = {m for f in files for m in re.findall(r"\\([A-Z][A-Za-z]+)", f.read_text(encoding="utf-8"))}
    import yaml
    declared = {n["macro"] for n in yaml.safe_load((ROOT / "paper" / "numbers.yaml").read_text(encoding="utf-8"))["numbers"]}
    for m in sorted((used & declared) - defined):
        bad.append(f"number macro \\{m} is used but was not generated")
    print("\n".join(bad) if bad else f"numbers audit: PASS ({len(files)} section files)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
