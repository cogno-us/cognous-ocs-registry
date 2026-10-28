"""M3 PR-1: frozen-baseline protection for `r08-v4` (BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v4/frozen_baseline_manifest.json` extends the r08-v3 manifest with the merged r08-v3 modules, contract, tests and vectors (sha256 from
`git show <baseline>:<path>`). Nothing frozen, including r08-v1/v2/v3, may change, and no frozen module may import an r08-v4 module.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v4" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]
V4_MODULES = {"v4_f1abcd.py", "v4_families.py", "v4_record.py", "v4_selection.py", "v4_verify.py", "v4_policy_identity.py", "v4_decision.py"}


def test_manifest_shape():
    assert len(MANIFEST["baseline_commit"]) == 40 and len(FILES) > 140
    for needed in ("registry_successor/verify.py", "registry_successor/v3_f1abc.py", "registry_successor/v3_verify.py", "registry_successor/v3_policy_identity.py",
                   "docs/r08-v2-contract.md", "docs/r08-v3-contract.md", "tests/vectors/r08v3/identity_vectors.json", "tests/test_r08v3_decision_path.py"):
        assert needed in FILES, needed
    assert not any("v4_" in p or "r08v4" in p or "r08-v4" in p for p in FILES)


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def test_no_frozen_module_imports_an_r08_v4_module():
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert "v4_f1abcd" not in text and "v4_families" not in text and "v4_verify" not in text and "v4_decision" not in text, path


def test_v4_modules_are_new_files_only():
    present = {p.name for p in (ROOT / "registry_successor").glob("v4_*.py")}
    assert present == V4_MODULES
    for name in present:
        assert "registry_successor/" + name not in FILES


def test_frozen_entry_points_still_refuse_r08_v4():
    from registry_successor import families, v3_families
    for version in ("r08-v4", "R08-V4"):
        sel = families.table_for_contract_version(version)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
        assert families.lookup_for(version, "f1abcd-local-execution-limits") is None
        assert not v3_families.table_for_contract_version_v3(version).ok
    assert "f1abcd-local-execution-limits" not in families.FAMILIES_V2 and "f1abcd-local-execution-limits" not in families.FAMILIES
    assert v3_families.lookup_v3("f1abcd-local-execution-limits") is None
