"""Frozen-baseline protection for the `r08-v8` preparation (APPROVED CANDIDATE; BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v8/frozen_baseline_manifest.json` extends the r08-v7 manifest (itself the r08-v6 manifest plus r08-v6) with every r08-v7 module, engine module, contract
document, test and vector that this change does not edit (sha256 from `git show <baseline>:<path>`, baseline = Registry main 67512a71546748cd888e4cf790485ea0bef9199a;
generator in docs/family-migration/final-three-prep/evidence/genman8.py). So r08-v1 .. r08-v7 are byte-identical to main. The three engine files that carry ADDITIVE edits
(`profile.py`, `identity.py`, `profiles.py`) are not hashed whole: the manifest records their baseline hash and the exact line-level edit, and the test reverses the edit
and recovers the baseline byte for byte, and pins that only the listed baseline lines were replaced. The two guard tests edited for allowlisting only are NOT in the manifest.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v8" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]
ADDITIVE = MANIFEST["additive_edits"]
BASELINE = "67512a71546748cd888e4cf790485ea0bef9199a"
V7_MODULES = {"v7_decision.py", "v7_families.py", "v7_policy_identity.py"}
V8_MODULES = {"v8_decision.py", "v8_families.py", "v8_policy_identity.py"}
V8_ENGINE_NEW = {"families_anchor.py", "families_observation.py"}
EDITED_ENGINE = {"registry_successor/engine/profile.py", "registry_successor/engine/identity.py", "registry_successor/engine/profiles.py"}
ALLOWLIST_EDITED_GUARDS = {"tests/test_r08v7_frozen_baseline.py", "tests/test_ext_s1_5_identity_module.py"}
FROZEN_ENGINE = {"__init__.py", "selection.py", "record.py", "verify.py", "decide.py", "families_irreversibility.py"}


def test_manifest_shape():
    assert MANIFEST["baseline_commit"] == BASELINE and len(FILES) >= 213
    for needed in ["registry_successor/" + n for n in sorted(V7_MODULES)] + ["registry_successor/engine/" + n for n in sorted(FROZEN_ENGINE)] + [
            "registry_successor/v6_decision.py", "registry_successor/verify.py", "registry_successor/families.py", "registry_successor/v2_policy_identity.py",
            "docs/r08-v6-contract.md", "docs/r08-v7-contract.md", "tests/r08v6_support.py", "tests/r08v7_support.py", "tests/test_r08v7_decision_path.py",
            "tests/test_r08v7_engine_differential.py", "tests/test_r08v7_engine_profile.py", "tests/test_r08v7_irreversibility_family.py",
            "tests/test_r08v7_lifecycle_boundaries.py", "tests/test_r08v7_policy_identity.py", "tests/vectors/r08v7/identity_vectors.json",
            "tests/vectors/r08v7/signed_selection_vector.json", "tests/vectors/r08v7/frozen_baseline_manifest.json", "tests/vectors/r08v6/frozen_baseline_manifest.json"]:
        assert needed in FILES, needed
    assert not (EDITED_ENGINE | ALLOWLIST_EDITED_GUARDS) & set(FILES)
    assert not any("v8_" in p or "r08v8" in p or "r08-v8" in p or "families_anchor" in p or "families_observation" in p for p in FILES)
    assert set(ADDITIVE) == EDITED_ENGINE


def test_the_manifest_extends_the_r08_v7_manifest_without_changing_any_hash():
    old = json.loads((ROOT / "tests" / "vectors" / "r08v7" / "frozen_baseline_manifest.json").read_text())["files"]
    assert set(old) < set(FILES)
    assert all(FILES[p] == h for p, h in old.items())


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def _revert(path):
    spec = ADDITIVE[path]
    current = (ROOT / path).read_text(encoding="utf-8").splitlines(keepends=True)
    for op in sorted(spec["ops"], key=lambda o: o["current_lines"][0], reverse=True):
        j1, j2 = op["current_lines"]
        assert "".join(current[j1:j2]) == op["current_text"], (path, op["current_lines"])
        current[j1:j2] = op["baseline_text"].splitlines(keepends=True)
    return "".join(current).encode("utf-8")


@pytest.mark.parametrize("path", sorted(EDITED_ENGINE))
def test_the_additive_edit_reverses_to_the_baseline_byte_for_byte(path):
    assert hashlib.sha256(_revert(path)).hexdigest() == ADDITIVE[path]["baseline_sha256"]


def test_the_additive_edits_are_pure_insertions_apart_from_the_pinned_comment_and_kind_lines():
    """No baseline code line is deleted or rewritten except the pinned ones: the `KINDS` tuple (a new member appended), one comment line in profile.py and the
    module docstring header line of profiles.py (text appended). identity.py is a pure insertion."""
    assert {o["tag"] for o in ADDITIVE["registry_successor/engine/identity.py"]["ops"]} == {"insert"}
    replaced = {p: [o["baseline_text"] for o in spec["ops"] if o["tag"] != "insert"] for p, spec in ADDITIVE.items()}
    assert replaced["registry_successor/engine/identity.py"] == []
    assert replaced["registry_successor/engine/profile.py"] == [
        'KINDS = ("classmap-enum", "scalar-enum")\n',
        "    kind: str  # classmap-enum (map of class -> value) | scalar-enum (one scalar value)\n"]
    assert len(replaced["registry_successor/engine/profiles.py"]) == 1
    assert replaced["registry_successor/engine/profiles.py"][0].startswith('"""The two shipped contract profiles (docs/r08-v7-contract.md section 3).')
    assert all(o["tag"] in ("insert", "replace") for spec in ADDITIVE.values() for o in spec["ops"])


def test_the_inserted_identity_lines_are_exactly_the_scalar_int_branch():
    (op,) = ADDITIVE["registry_successor/engine/identity.py"]["ops"]
    assert op["current_text"].splitlines()[0].strip().startswith('elif row.kind == "scalar-int":')
    assert "pid._type_refusal(field, value)" in op["current_text"] and "scalar-enum" not in op["current_text"].replace("# scalar-enum", "")


def test_no_frozen_module_imports_the_engine_a_v7_or_a_v8_module():
    names = tuple(sorted(m[:-3] for m in V7_MODULES | V8_MODULES)) + ("registry_successor.engine", "registry_successor import engine", "families_irreversibility",
                                                                       "families_anchor", "families_observation")
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")) and not path.startswith("registry_successor/engine/") \
                and not path.startswith(tuple("registry_successor/" + m for m in sorted(V7_MODULES))):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert not any(name in text for name in names), path


def test_new_files_only_the_v8_modules_the_two_engine_family_modules_and_nothing_else_is_added():
    assert {p.name for p in (ROOT / "registry_successor").glob("v8_*.py")} == V8_MODULES
    assert {p.name for p in (ROOT / "registry_successor").glob("v7_*.py")} == V7_MODULES
    engine = {p.name for p in (ROOT / "registry_successor" / "engine").glob("*.py")}
    assert engine == FROZEN_ENGINE | {"profile.py", "profiles.py", "identity.py"} | V8_ENGINE_NEW
    for name in V8_MODULES:
        assert "registry_successor/" + name not in FILES
    for stale in ("v8_verify.py", "v8_record.py", "v8_selection.py"):
        assert not (ROOT / "registry_successor" / stale).exists()


def test_every_other_committed_file_is_unchanged_from_main_except_the_allowlisted_edits():
    """A tripwire on the working tree: `git diff --name-only <main>` may list only the three additive engine edits and the two allowlist-edited guards (new files are not
    reported by --diff-filter=MDRT). Skipped where no git metadata or the baseline object is available."""
    import subprocess
    probe = subprocess.run(["git", "cat-file", "-e", BASELINE + "^{commit}"], cwd=ROOT, capture_output=True)
    if probe.returncode != 0:
        pytest.skip("baseline commit not present in this checkout")
    changed = subprocess.run(["git", "diff", "--name-only", "--diff-filter=MDRT", BASELINE, "--", "."], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert set(changed) <= EDITED_ENGINE | ALLOWLIST_EDITED_GUARDS, sorted(set(changed) - (EDITED_ENGINE | ALLOWLIST_EDITED_GUARDS))
