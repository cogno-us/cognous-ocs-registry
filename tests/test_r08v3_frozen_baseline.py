"""M2 PR-1: frozen-baseline protection (BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v3/frozen_baseline_manifest.json` records the sha256 of every frozen file at the baseline commit: the r08-v1/r08-v2 implementation
(`registry_successor/*` other than the new `v3_*` modules, adapters, contract, consumer, records, conformance), the `baseline/` Runtime and Control Plane
snapshot, the v2 contract documents, all v1/v2 test vectors and goldens, the historical G0/G1 evidence, and the V09 candidate. The manifest was produced
with `git show <baseline>:<path> | sha256sum` for each file. This test fails if any of them changes or disappears, and proves that no frozen module
imports an `r08-v3` module (a new contract version must not reinterpret previously valid signed records).
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v3" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]


def test_manifest_shape():
    assert len(MANIFEST["baseline_commit"]) == 40 and len(FILES) > 100
    for needed in ("registry_successor/verify.py", "registry_successor/families.py", "registry_successor/v2_f1ab.py", "registry_successor/v2_policy_identity.py",
                   "registry_successor/decision.py", "registry_successor/record.py", "docs/r08-v2-contract.md", "docs/v09/candidate-manifest.json"):
        assert needed in FILES, needed
    assert any(p.startswith("baseline/") for p in FILES) and any(p.startswith("docs/family-migration/g0/") for p in FILES)
    assert any(p.startswith("tests/vectors/") for p in FILES) and any(p.startswith("tests/golden/") for p in FILES)
    assert not any("/v3_" in p or p.startswith("tests/vectors/r08v3/") for p in FILES)


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def test_no_frozen_module_imports_an_r08_v3_module():
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert "v3_f1abc" not in text and "v3_families" not in text and "v3_verify" not in text and "v3_decision" not in text, path


def test_v3_modules_are_new_files_only():
    present = {p.name for p in (ROOT / "registry_successor").glob("v3_*.py")}
    assert present == {"v3_f1abc.py", "v3_families.py", "v3_record.py", "v3_selection.py", "v3_verify.py", "v3_policy_identity.py", "v3_decision.py"}
    for name in present:
        assert "registry_successor/" + name not in FILES


def test_frozen_entry_points_still_refuse_r08_v3():
    """A new contract version must not reinterpret previously valid signed records or open the old dispatch."""
    from registry_successor import families, selection, record, v2_selection, decision
    for version in ("r08-v3", "R08-V3"):
        sel = families.table_for_contract_version(version)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
        assert families.lookup_for(version, "f1abc-local-execution-limits") is None
        assert families.compose_for(version, {}, None).code == "contract_unsupported"
    assert families.lookup_v2("f1abc-local-execution-limits") is None and families.lookup("f1abc-local-execution-limits") is None
    assert "f1abc-local-execution-limits" not in families.FAMILIES_V2 and "f1abc-local-execution-limits" not in families.FAMILIES


def test_v2_identity_table_and_codes_unchanged():
    from registry_successor import v2_codes, v2_policy_identity as pid, common as c
    assert len(c.CODES) == 46 and len(v2_codes.CODES_V2) == 48 and len(v2_codes.CODES_V2_REV2) == 51
    assert set(pid.IDENTITY_FAMILIES) == {"f1a-local-execution-allowlist", "f1ab-local-execution-allowlist", "f4-control-plane-age-bounds",
                                          "f5-action-class-age-bounds"}
    assert pid.REGISTERED_CONTRACT_VERSIONS == ("r08-v2",)
