"""Frozen-baseline protection for `r08-v7` (BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v7/frozen_baseline_manifest.json` extends the r08-v6 manifest with the r08-v6 modules, contract, tests and vectors (sha256 from
`git show <baseline>:<path>`, baseline = the r08-v6 head `42a666328b974a7581013358bcf8bc7b9eac7761`; generator in
docs/family-migration/unified-engine/evidence/genman7.py). Nothing frozen, including the whole of r08-v1 .. r08-v6, may change, and no frozen module may
import the engine or an r08-v7 module. The three existing source-scan guards edited for allowlisting only are NOT in the manifest (as for r08-v6).
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v7" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]
V6_MODULES = {"v6_class_revocation_assurance.py", "v6_terminal_revocation.py", "v6_families.py", "v6_record.py", "v6_selection.py", "v6_verify.py",
              "v6_policy_identity.py", "v6_decision.py"}
V7_MODULES = {"v7_decision.py", "v7_families.py", "v7_policy_identity.py"}
ENGINE_MODULES = {"__init__.py", "profile.py", "profiles.py", "selection.py", "record.py", "verify.py", "decide.py", "identity.py", "families_irreversibility.py"}
ALLOWLIST_EDITED_GUARDS = {"tests/test_ext_s1_5_identity_module.py", "tests/test_ext_s1_5_vectors.py", "tests/test_r08v2_family_dispatch.py"}
BASELINE = "42a666328b974a7581013358bcf8bc7b9eac7761"


def test_manifest_shape():
    assert MANIFEST["baseline_commit"] == BASELINE and len(FILES) >= 193
    for needed in ["registry_successor/" + n for n in sorted(V6_MODULES)] + [
            "registry_successor/verify.py", "registry_successor/families.py", "registry_successor/v2_policy_identity.py", "registry_successor/v5_verify.py",
            "docs/r08-v5-contract.md", "docs/r08-v6-contract.md", "tests/r08v6_support.py", "tests/test_r08v6_decision_path.py", "tests/test_r08v6_frozen_baseline.py",
            "tests/test_r08v6_policy_identity.py", "tests/test_r08v6_revocation_assurance_family.py", "tests/test_r08v6_terminal_revocation_family.py",
            "tests/test_r08v6_lifecycle_boundaries.py", "tests/vectors/r08v6/identity_vectors.json", "tests/vectors/r08v6/signed_selection_vector.json",
            "tests/vectors/r08v6/frozen_baseline_manifest.json", "tests/vectors/r08v5/identity_vectors.json"]:
        assert needed in FILES, needed
    assert not any("v7_" in p or "r08v7" in p or "r08-v7" in p or "registry_successor/engine/" in p for p in FILES)
    assert not ALLOWLIST_EDITED_GUARDS & set(FILES)


def test_the_manifest_extends_the_r08_v6_manifest_without_changing_any_hash():
    old = json.loads((ROOT / "tests" / "vectors" / "r08v6" / "frozen_baseline_manifest.json").read_text())["files"]
    assert set(old) < set(FILES)
    assert all(FILES[p] == h for p, h in old.items())


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def test_no_frozen_module_imports_the_engine_or_an_r08_v7_module():
    names = tuple(sorted(m[:-3] for m in V7_MODULES)) + ("registry_successor.engine", "registry_successor import engine", "families_irreversibility")
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert not any(name in text for name in names), path


def test_v7_modules_are_new_files_only():
    present = {p.name for p in (ROOT / "registry_successor").glob("v7_*.py")}
    assert present == V7_MODULES
    assert {p.name for p in (ROOT / "registry_successor" / "engine").glob("*.py")} == ENGINE_MODULES
    assert {p.name for p in (ROOT / "registry_successor").glob("v6_*.py")} == V6_MODULES
    for name in present:
        assert "registry_successor/" + name not in FILES
    for name in ENGINE_MODULES:
        assert "registry_successor/engine/" + name not in FILES


def test_no_per_version_copy_of_the_engine_exists():
    """The engine is ONE package: there is no v7_verify / v7_record / v7_selection copy of the per-version orchestration."""
    for stale in ("v7_verify.py", "v7_record.py", "v7_selection.py"):
        assert not (ROOT / "registry_successor" / stale).exists()


def test_every_other_committed_registry_file_is_unchanged_from_the_baseline_except_the_allowlisted_guards():
    """A tripwire on the working tree (not only the manifest): `git diff --name-only <baseline>` may list only new v7 files, the new docs/vectors/tests and the
    three allowlist-edited guards. Skipped where no git metadata or baseline object is available."""
    import subprocess
    probe = subprocess.run(["git", "cat-file", "-e", BASELINE + "^{commit}"], cwd=ROOT, capture_output=True)
    if probe.returncode != 0:
        pytest.skip("baseline commit not present in this checkout")
    changed = subprocess.run(["git", "diff", "--name-only", "--diff-filter=MDRT", BASELINE, "--", "."], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert set(changed) <= ALLOWLIST_EDITED_GUARDS, sorted(set(changed) - ALLOWLIST_EDITED_GUARDS)
