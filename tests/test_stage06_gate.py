"""Stage 0.6 v2: authorization gate (V25), refusal taxonomy (V26), checkpoint fuzz (V27), seed roles (V28), their mutations, the
reproduction of the two v1 failures on the old snapshot, and the notebook scan. Test-only keys and temporary directories only."""

import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from dynaicl.config import stage06_seed_roles as SR
from dynaicl.validation import checks_stage06_gate as G
from dynaicl.validation.mutations import run_check_safely
from dynaicl.validation.mutations_stage06_gate import MUTATIONS_STAGE06_GATE, PRIMARY_DETECTORS
from tests._util import assert_check

ROOT = Path(__file__).resolve().parents[1]
V1_SNAPSHOT = ROOT / "dist" / "stage06_frozen_snapshot.zip"
skip_mut = pytest.mark.skipif(bool(os.environ.get("DYNAICL_MUTATION")), reason="session-wide mutation active")


@pytest.mark.parametrize("key", ["V25", "V26", "V27", "V28"])
def test_stage06_gate_checks(key):
    r = assert_check(G.ALL_CHECKS_STAGE06_GATE[key]())
    print(f"\n{r.name}: " + json.dumps({k: v for k, v in r.details.items() if k not in ("rows", "failures")}, default=str)[:400])


def test_mutation_plan_covers_every_gate_mutation():
    assert set(PRIMARY_DETECTORS) == set(MUTATIONS_STAGE06_GATE)


@skip_mut
@pytest.mark.parametrize("mutation", sorted(MUTATIONS_STAGE06_GATE))
def test_stage06_gate_mutation_killed_by_assertion_level_failure(mutation):
    key = PRIMARY_DETECTORS[mutation]
    with MUTATIONS_STAGE06_GATE[mutation]():
        res = run_check_safely(G.ALL_CHECKS_STAGE06_GATE[key])
    print(f"\n{mutation}: {key}={res['status']}")
    assert res["status"] == "FAIL", res


def test_seed_role_document_is_generated_from_the_table():
    roles = SR.load_roles(ROOT / "config" / "stage06_seed_manifest.yaml")
    assert (ROOT / "docs" / "STAGE06_SEED_ROLES.md").read_text(encoding="utf-8") == SR.render_markdown(roles)


# ------------------------------------------------------------------------------------------ v1 failures reproduced

CASE = r'''
import json, sys, tempfile
from pathlib import Path
from dynaicl.config.stage06_schema import load_stage06_config
from dynaicl.experiments import stage06_probe as P
cfg = load_stage06_config("config/stage06_test.yaml")
tmp = Path(tempfile.mkdtemp())
ck = P.checkpoint_root(tmp, cfg)
P.save_unit(ck, ("tier1",), {"passed": True, "details": {}}, {}, 0.1, cfg, None)
js = ck / "tier1.json"
js.write_text(js.read_text(encoding="utf-8")[: int(js.stat().st_size * 0.6)], encoding="utf-8")
def run(fn):
    try:
        fn()
        return "no error"
    except Exception as exc:
        return type(exc).__name__
print("truncated_unit_json:", run(lambda: P.load_unit(ck, ("tier1",), cfg, None)))
env = tmp / "env.json"
env.write_text(json.dumps({"environment": {"python": "0.0", "implementation": "x", "numpy": "0", "scipy": "0", "pyyaml": "0",
                                           "system": "x", "machine": "x"}}), encoding="utf-8")
manifest = {"environment_manifest": "env.json", "manifest_sha256": "0" * 64}
print("missing_qualification_path:", run(lambda: P.check_environment(manifest, tmp / "no_such_report.json", cfg, tmp)))
'''


def _run_case(tree: Path) -> dict:
    p = subprocess.run([sys.executable, "-c", CASE], cwd=tree, capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": str(tree)})
    return dict(line.split(": ", 1) for line in p.stdout.strip().splitlines() if ": " in line) | {"stderr": p.stderr[-300:]}


@pytest.mark.skipif(not V1_SNAPSHOT.exists(), reason="old (v1) snapshot not present")
def test_original_v1_failures_are_reproduced_on_the_old_snapshot_and_fixed_now(tmp_path):
    old = tmp_path / "old_v1_tree"
    with zipfile.ZipFile(V1_SNAPSHOT) as z:
        z.extractall(old)
    before, after = _run_case(old), _run_case(ROOT)
    print(f"\nv1 snapshot: {before}\nrevised tree: {after}")
    assert before["truncated_unit_json"] == "JSONDecodeError", before          # the original defect, reproduced
    assert before["missing_qualification_path"] == "FileNotFoundError", before   # the original defect, reproduced
    assert after["truncated_unit_json"] == "Corrupt", after                    # the fix changes the outcome
    assert after["missing_qualification_path"] == "Refusal", after


# ------------------------------------------------------------------------------------------ notebooks


def test_v2_notebooks_contain_no_confirmatory_path_seed_or_authorization_reference():
    roles = SR.load_roles(ROOT / "config" / "stage06_seed_manifest.yaml")
    seeds = [str(s) for k in ("confirmatory_evaluation", "confirmatory_bootstrap") for s in roles[k]["seeds"]]
    forbidden = seeds + ["config/stage06.yaml", "authorization", "AUTH_KEY", "RUN_CONFIRMATORY", "stage06_issue", "--authorization",
                         "confirmatory_evaluation", "confirmatory_bootstrap"]
    notebooks = sorted((ROOT / "colab").rglob("*_v2.ipynb"))
    for nb in notebooks:
        text = nb.read_text(encoding="utf-8")
        hits = [f for f in forbidden if re.search(re.escape(f), text, re.I if f.islower() else 0)]
        assert not hits, (nb.name, hits)
        assert 'MANIFEST_SHA' in text and 'FREEZE_MANIFEST_STAGE06_v2.json' in text
        code = "\n".join("".join(c["source"]) for c in json.loads(text)["cells"] if c["cell_type"] == "code")
        # looked up in the notebook's CODE (the raw JSON escapes its quotes): the extracted manifest must hash to MANIFEST_SHA at run time
        assert re.search(r"assert\s+sha\(\"/content/DynaICL/docs/FREEZE_MANIFEST_STAGE06_v2\.json\"\)\s*==\s*MANIFEST_SHA", code), nb.name
        assert " run --config" not in code and "analyze --config" not in code
