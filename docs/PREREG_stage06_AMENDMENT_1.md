# Stage 0.6 pre-registration: Amendment 1 (operational changes only)

Date: 2026-10-11. Freeze label: **v2**. Applies to: `docs/PREREG_stage06.md` (v1 freeze, byte-identical, NOT edited).
Approved by the user in the message "Authorization-Gate Change and Re-Freeze".

## 1. What this amendment does NOT change

The estimands, the long-context region, the primary family, the inference procedure, the decision rules (GO / STOP / REVISE / BLOCKED),
delta, alpha, the bootstrap schedule, N = 4000 per replicate, the noise levels (q = 0.755, 2.56, 6.5 and the q = 0 control), the scales, the
horizons, the comparator, Tier-1 and Tier-2, the critical checks, and **all seed values** are exactly as in `docs/PREREG_stage06.md`.
Evidence: the SHA-256 of `docs/PREREG_stage06.md` and of `config/stage06.yaml` (the confirmatory configuration, hence its config hash) are
identical in the v1 and v2 freezes (see `docs/STAGE06_CHANGE_REPORT_v1_to_v2.md`). The statistical code (`stage06_analysis.py`) is unchanged.

## 2. Operational changes (each maps to an approved item)

1. **Authorization gate (approved item 1).** A confirmatory `run` or `analyze` additionally needs an authorization artifact: an HMAC-SHA256
   authenticated JSON document, keyed by a secret that only the user holds and supplies at launch, binding the manifest hash, the snapshot
   archive hash, the confirmatory config hash and file hash, the pre-registration and this amendment's hashes, the exact seed set
   (both replicate seeds and the bootstrap seed, by set equality), the execution mode, a run id, an issue time and an expiry of at most 72 h,
   and a schema version. It is verified at start, on every resume and at completion. One run id per checkpoint directory (a run lock);
   pilot and test configurations take no authorization. Design, threat model and limits: `docs/STAGE06_AUTHORIZATION_GATE.md`. This supplements
   section 11 of the pre-registration.
2. **Refusal handling (approved item 2).** Outcome taxonomy: `REFUSED` (exit 3) for policy and guard failures and `CORRUPT` (exit 4) for integrity
   failures of data the runner reads, each naming the path and the reason. This replaces the uncaught tracebacks that the v1 runner produced for a
   truncated unit JSON and a missing qualification path.
3. **Seed-role clarification (approved item 3).** `config/stage06_seed_manifest.yaml` is the single seed-role table. The v1 role `pilot` is split into
   `pilot_evaluation` (62001, 62101) and `pilot_bootstrap` (62999), with allowed and forbidden uses per role. Seed values are unchanged.
   `docs/STAGE06_SEED_ROLES.md` is generated from it and tested against it.
4. **Notebook and bundle (approved item 3).** The pilot notebook contains no confirmatory cell and no confirmatory seed or authorization path;
   hash order is documented in `docs/STAGE06_CHANGE_REPORT_v1_to_v2.md`.
5. **Versioned freeze evidence.** Mutation matrix, environment manifest, tested-file record and validation report carry a `_v2` suffix so
   that the v1 evidence is preserved untouched.

## 3. Consequences for earlier artifacts

The v1 snapshot, manifest, Phase D qualification and Phase D pilot outputs are bound to the v1 snapshot. They are preserved, obsolete for v2, and
are not reused. Disclosure-log history is append-only; corrections are dated errata (E1 onwards).
