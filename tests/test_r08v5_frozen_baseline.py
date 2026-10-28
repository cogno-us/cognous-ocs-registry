"""M11 PR-1: frozen-baseline protection for `r08-v5` (BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v5/frozen_baseline_manifest.json` extends the r08-v4 manifest with the merged r08-v4 modules, contract, tests and vectors (sha256 from
`git show <baseline>:<path>`). Nothing frozen, including r08-v1/v2/v3/v4, may change, and no frozen module may import an r08-v5 module.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v5" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]
V5_MODULES = {"v5_f4t.py", "v5_families.py", "v5_record.py", "v5_selection.py", "v5_verify.py", "v5_policy_identity.py", "v5_decision.py"}


def test_manifest_shape():
    assert len(MANIFEST["baseline_commit"]) == 40 and len(FILES) > 150
    for needed in ("registry_successor/verify.py", "registry_successor/v2_age_bounds.py", "registry_successor/v4_f1abcd.py", "registry_successor/v4_verify.py",
                   "registry_successor/v4_policy_identity.py", "docs/r08-v2-contract.md", "docs/r08-v4-contract.md", "tests/vectors/r08v4/identity_vectors.json",
                   "tests/test_r08v4_decision_path.py"):
        assert needed in FILES, needed
    assert not any("/v5_" in p or "r08v5" in p or "r08-v5" in p for p in FILES)


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def test_no_frozen_module_imports_an_r08_v5_module():
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert "v5_f4t" not in text and "v5_families" not in text and "v5_verify" not in text and "v5_decision" not in text, path


def test_v5_modules_are_new_files_only():
    present = {p.name for p in (ROOT / "registry_successor").glob("v5_*.py")}
    assert present == V5_MODULES
    for name in present:
        assert "registry_successor/" + name not in FILES


def test_frozen_entry_points_still_refuse_r08_v5():
    from registry_successor import families, v3_families, v4_families
    for version in ("r08-v5", "R08-V5"):
        sel = families.table_for_contract_version(version)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
        assert families.lookup_for(version, "f4t-control-plane-clock-tolerance") is None
        assert not v3_families.table_for_contract_version_v3(version).ok and not v4_families.table_for_contract_version_v4(version).ok
    for table in (families.FAMILIES, families.FAMILIES_V2, v3_families.FAMILIES_V3, v4_families.FAMILIES_V4):
        assert "f4t-control-plane-clock-tolerance" not in table
