# Stage 0.6 authorization gate (v2 freeze): design, threat model and limits

Code: `dynaicl/experiments/stage06_authorization.py` (verification, key handling, run lock), `dynaicl/experiments/stage06_probe.py`
(`gate_session`, `authorize_confirmatory`, `require_gate`), `scripts/stage06_issue_authorization.py` (issuer). Tests: V25-V28 and
`tests/test_stage06_gate.py`; 12 gate mutants in `dynaicl/validation/mutations_stage06_gate.py`.

## 1. What it protects against, and what it does not

**Purpose.** A confirmatory `run` or `analyze` must be impossible without an explicit, current, user-held authorization, on top of the
frozen manifest, configuration, seed and checkpoint requirements.

| Threat | Stopped? | How |
|---|---|---|
| accidental launch (wrong notebook cell, wrong config, stale command) | yes | no artifact, or an artifact for another freeze, config, seed set or mode, is REFUSED |
| automated or agent-initiated launch (this assistant, a scheduler, a script) | yes, **if the key is not available to it** | the artifact is HMAC-authenticated; nobody without the key can produce one. The key is typed or exported by the user at launch |
| a forged or edited artifact, including a hash-only one | yes | HMAC-SHA256 over a domain-separated canonical payload, compared in constant time |
| replay of an old artifact (after a new freeze, or after expiry) | yes | bound to the manifest and snapshot hashes, the issue time must not precede the freeze, validity is at most 72 h |
| a second confirmatory run in the same place | yes | run lock per checkpoint directory (one run id), results directory check |
| a pilot or test configuration used to authorize or to run confirmatory work | yes | modes and seed roles are checked; pilot and test configs take no authorization |
| a file swapped between the check and the use | yes | the artifact and the config are read once; later steps use the parsed copy |
| an attacker who can **edit and run arbitrary code** outside the frozen tree | **no** | they can run a modified runner that skips the gate. The manifest hash that the user supplies on the command line only protects the frozen tree itself |
| an attacker who holds the key | **no** | the key is the whole secret |
| a Python caller that constructs `VerifiedGate` by hand or calls `run_unit` directly | **no** (API guards only prevent accidents) | `run_units`, `analyze` and `write_results` refuse a confirmatory config without a `VerifiedGate`, but the class can be built by any Python caller |
| a second run started in a different checkpoint and results directory under a new run id | **no** | the lock is per directory; run ids are issued by the user, who is the authority |

A hash-only artifact (no secret) would be forgeable by anyone who can write files, including the agent. HMAC with a user-held key is the
smallest design that makes the artifact unforgeable for everyone but the key holder, and it needs only the standard library. An asymmetric
signature (for example Ed25519) would let verifiers hold only a public key, but it needs a vetted third-party dependency, which the
frozen environment deliberately avoids; the cost is that the runner and the issuer share the user's secret.

## 2. Artifact

A JSON document `{"payload": {...}, "hmac_sha256": "<64 hex>"}`. The signature is
`HMAC-SHA256(key, "dynaicl-stage06-authorization/v1\n" + canonical_json(payload))`.

Bound payload fields (all required, exact types): `schema`, `purpose` (`confirmatory_authorization`), `test_only`, `mode`
(`confirmatory`), `run_id` (8-64 characters of `A-Z a-z 0-9 . _ -`), `issued_utc`, `expires_utc`, `manifest_sha256`, `snapshot_sha256`
(the snapshot archive), `config_hash` (the canonical hash of the validated confirmatory configuration), `config_file_sha256`,
`prereg_sha256`, `amendment_sha256`, `seeds` (`evaluation`: both replicate seeds, `bootstrap`), `qualification_sha256` (optional: when set, it must
equal the qualification report actually used).

**Seeds** are compared by set equality with the configuration (a subset or a superset is REFUSED; the order of the two replicates is not significant).

**Stale** means: bound to any manifest, snapshot, configuration, pre-registration or amendment hash other than the current frozen state; or issued
before the current freeze (the manifest's `created_utc`); or past `expires_utc`; or not yet valid (issued in the future beyond a 5-minute skew); or with a
validity window longer than 72 h or not positive.

## 3. Behaviour

* **Outcomes.** Malformed input (empty, truncated, not an object, wrong keys or types) is `CORRUPT` (exit 4). Every policy failure is `REFUSED`
  (exit 3) and names the failing field. No partial output is written.
* **Where it is verified.** At start of every invocation (so on every resume), and again at completion, immediately before the analysis and results are written
  (the frozen files are re-hashed and the authorization is re-verified from the bytes held in memory). A run that outlives its expiry therefore fails at completion;
  the user issues a new artifact **with the same run id** and resumes: all units are already done, so only the analysis runs.
* **The key.** Read from `DYNAICL_STAGE06_AUTH_KEY` (then removed from the process environment so child processes do not inherit it) or a hidden interactive
  prompt. Never accepted on the command line, never printed, logged, checkpointed, written to results, or stored in the run lock.
* **Run lock.** `RUN_LOCK.json` in the checkpoint directory is created atomically (exclusive create) by the first invocation. Later invocations must carry the same
  run id (resume). A different run id is REFUSED. A results directory (named after the run id) that already exists for the confirmatory config hash refuses a
  second run or a repeated analysis.
* **Mode and seed isolation.** Pilot and test configurations never accept an authorization; the existing mode, frozen-config and seed-role checks still run
  first, so an authorization can never widen what the config may do.
* **No bypass.** There is no flag, environment variable or config key that disables the gate (tested with five environment variable names and three flags).
  `allow_test_only` exists only as an internal test parameter and is unreachable from the command line.

## 4. Issuer

`scripts/stage06_issue_authorization.py` recomputes the binding from the files, takes the key from the environment or a hidden prompt, and writes the artifact with
an exclusive create (it never overwrites). Key policy: a real artifact needs at least 24 characters and must not start with `TEST-ONLY-`; a `--test-only`
artifact needs a key starting with `TEST-ONLY-` and can never authorize a confirmatory run (the runner refuses test-only artifacts and test-only keys on the
production path). **The issuer was exercised only with test keys, in temporary directories. No real artifact exists, and V25 asserts that no artifact file
remains in the workspace.** The user runs it in Phase E with their own key.

Typical Phase E use (the user's own terminal):

```
export DYNAICL_STAGE06_AUTH_KEY='<your secret>'
python scripts/stage06_issue_authorization.py --manifest docs/FREEZE_MANIFEST_STAGE06_v2.json --snapshot dist/stage06_frozen_snapshot_v2.zip \
    --config config/stage06.yaml --run-id <id> --hours 24 --out <path>
python -m dynaicl.experiments.stage06_probe run --config config/stage06.yaml --manifest docs/FREEZE_MANIFEST_STAGE06_v2.json \
    --expected-manifest-sha256 <stored hash> --snapshot dist/stage06_frozen_snapshot_v2.zip --authorization <path> --checkpoint-dir <dir>
```
