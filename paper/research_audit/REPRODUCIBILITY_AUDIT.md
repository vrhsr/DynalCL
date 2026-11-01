# Reproducibility audit (Phase 4)

## 1. The reader's path (VERIFIED, 2026-10-31)

`git clone --branch paper-draft https://github.com/vrhsr/DynalCL` (fresh, into the session scratchpad), then
`python paper/build.py`: claims **PASS (41 verified, 0 pending)**, `numbers.tex: 63 macros; PASS`, numbers audit **PASS (15
section files)**, both PDFs built; total 2 min 57 s including the clone. A plain clone fetches every branch head, so all pinned
result commits are present. Requirements met by this laptop: Python 3.13 with pyyaml; git; MiKTeX pdflatex/bibtex.

Same build in the `paper-revision` worktree: PASS in 39 s.

## 2. From results branches to numbers

Every macro and claim reads its file with `git show <commit>:<path>` at a pinned commit and records its sha256 in
`paper/CLAIMS.md` / `generated/numbers.tex` (VERIFIED by reading the tools). A reader can therefore check any number without
re-running anything. Re-running a map needs box-scale CPU (wall times REPORTED in the disclosure log: 1A 2 h 07 min (S9); F3
10 079 s and F2 10 832 s at 16 workers (S33, S38)) and the seed-role table.

## 3. Gaps

| Gap | Effect | Fix |
|---|---|---|
| Large row files stay on the box (1A `map_rows.csv` 5.9 MB, S9); F3/F2 row files are on the branches | The 1A per-draw table uses the per-cell summary, not rows | Acceptable; say so in the data statement |
| Stage 0 mutation-matrix archive not retained (Colab recycled) | Known-scale mutation detection cannot be shown | Already not claimed |
| Sensitivity batch 4 not returned | AB11 unsupported | Wait for the branch |
| No archived DOI (Zenodo / Software Heritage) | Required for a camera-ready artefact | At acceptance, archive the paper-revision tag and result branches |
| Double-blind review | The public repo (`vrhsr/DynalCL`), the box path (`/home/rama_11187/...`) in disclosure logs, and git authorship identify the authors | Anonymised mirror for review (e.g. an anonymising service), strip the paper of the repo URL until acceptance |
| Environment | Map runs used Python 3.13.5, numpy 2.2.2, scipy 1.15.1 on Linux (REPORTED provenance); the paper build needs only pyyaml + LaTeX | State both in the reproducibility section |
| Test suites | Full Stage 0 slow tests, Stage 1 torch tests and `test_f2_references.py` exceed the local budget | Run on the box before submission (one CPU batch) |
| LLM involvement | The repository records that analyses, code and text were produced in Claude Code sessions (CLAUDE.md, disclosure logs) | Venue LLM-use and authorship policies must be checked and an LLM-use statement written (TMLR policy UNVERIFIED in this audit) |
