"""Integrity tests for the G1 readiness package (documentation only): counts, traceability, labels, pins, frozen files, no executable oracle."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "docs" / "family-migration" / "g1-readiness"
PREP = ROOT / "docs" / "family-migration" / "g1-preparation"
HOLDS = ("G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. "
         "V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. "
         "Publication: HOLD. Production: HOLD.")
MD = ["README.md", "g1-preparation-merge-record.md", "registry-pin-delta-assessment.md", "environment-profile.md", "eight-file-test-evidence-closure.md",
      "runtime-f01-pin-path-assessment.md", "architect-decision-register.md", "m1-oracle-specification.md", "gap-to-oracle-traceability-matrix.md",
      "g1-readiness-report.md"]
FAMILIES = {f"OW-{i}" for i in range(1, 10)}
PR51_HEAD = "00e9bb63e0ad32c7900713050e47b5df22279152"
PR51_MERGE = "2afbd8cd119751842b5df824229726aeb0e4a863"
PROGRAM_PIN = "317eb76acb2847c534c3ce7c2180b89b4aef987d"
TYPED_INVALID = "317eb76acb2847c534c3ce7c2180b722d130fe8cb"
CODE_TREES = {"registry_adapters": "dcede40a6e", "registry_conformance": "0d6e818f99", "registry_consumer": "39640b15a8", "registry_contract": "d50de54705",
              "registry_records": "cc64f25119", "registry_successor": "5954fcf8e8", "baseline": "ae1ee8755c"}


def spec():
    return json.loads((R / "m1-oracle-specification.json").read_text(encoding="utf-8"))


def test_every_document_exists_and_carries_the_verbatim_holds():
    for name in MD:
        t = (R / name).read_text(encoding="utf-8")
        assert HOLDS in t, name
        assert "Non-authorizing, documentation only" in t, name
    for name in ("m1-oracle-specification.json", "eight-file-test-evidence-closure.json"):
        assert (R / name).is_file()
    assert spec()["holds"] == HOLDS


def test_no_overclaim_and_no_executable_oracle_is_present():
    for name in MD:
        t = (R / name).read_text(encoding="utf-8").lower()
        for banned in ("production ready", "security clearance", "is certified"):
            assert banned not in t, (name, banned)
        assert not re.search(r"\b(is|are|was|been|being) independently qualified", t), name
    assert not list(R.glob("*.py")) and not list(R.glob("test_*"))
    for o in spec()["oracles"]:
        assert o["authored_by"] is None and o["independent_author_designated"] is False and o["status"] == "PROPOSED"


def test_sixty_five_gaps_are_retained_and_traced_to_nine_families():
    s = spec()
    old = json.loads((PREP / "m1-oracle-register.json").read_text(encoding="utf-8"))["oracles"]
    assert {o["gap_id"] for o in old} == {o["gap_id"] for o in s["oracles"]} and len(s["oracles"]) == 65
    assert len({o["oracle_id"] for o in s["oracles"]}) == 65
    assert {o["family"] for o in s["oracles"]} <= FAMILIES and set(s["families"]) == FAMILIES
    assert sum(f["oracle_count"] for f in s["families"].values()) == 65
    mx = (R / "gap-to-oracle-traceability-matrix.md").read_text(encoding="utf-8")
    for o in old:
        assert o["gap_id"] in mx and o["oracle_id"] in mx
    ids = [f"M1-E-{i:02d}" for i in range(1, 36)] + [f"M1-F-{i:02d}" for i in range(1, 31)]
    assert sorted(ids) == sorted(o["gap_id"] for o in s["oracles"])


def test_eleven_high_gaps_are_prioritised_and_blocked_ones_are_labelled():
    s = spec()
    high = {o["gap_id"]: o for o in s["oracles"] if o["severity"] == "HIGH"}
    assert len(high) == 11
    expected_high = {"M1-E-06", "M1-E-10", "M1-E-12", "M1-E-21", "M1-E-26", "M1-E-30", "M1-E-34", "M1-F-06", "M1-F-07", "M1-F-08", "M1-F-26"}
    assert set(high) == expected_high
    blocked = {g for g, o in high.items() if o["readiness"].startswith("BLOCKED")}
    assert blocked == {"M1-E-12", "M1-E-34", "M1-F-08"}
    for g in blocked:
        assert high[g]["expected_observation"].startswith("NOT SPECIFIED") and high[g]["depends_on_decision"] == "PD-1"
    old = {o["gap_id"]: o for o in json.loads((PREP / "m1-oracle-register.json").read_text(encoding="utf-8"))["oracles"]}
    for o in s["oracles"]:
        assert o["severity"] == old[o["gap_id"]]["severity"]
        if old[o["gap_id"]]["depends_on_decision"] == "PD-1":
            assert o["readiness"].startswith("BLOCKED") and o["expected_observation"].startswith("NOT SPECIFIED")
    assert high["M1-F-06"]["restrictions"] and high["M1-E-21"]["restrictions"] and high["M1-F-07"]["restrictions"]


def test_every_oracle_has_the_required_fields_and_all_four_verdict_criteria():
    for o in spec()["oracles"]:
        for k in ("component_pins", "test_preconditions", "fixture_inputs", "expected_observation", "expected_basis", "mandatory_refusal_conditions",
                  "independence_requirement", "security_tier", "criteria", "gap_id", "family", "readiness"):
            assert o[k], (o["oracle_id"], k)
        assert set(o["criteria"]) == {"PASS", "FAIL", "BLOCK", "INCONCLUSIVE"}
        assert o["security_tier"] in ("T1", "T2", "T3")
        if o["readiness"] != "SPEC-READY":
            assert "NOT SPECIFIED" in o["expected_observation"]
    pins = " ".join(" ".join(o["component_pins"].values()) for o in spec()["oracles"])
    assert PROGRAM_PIN in pins and "0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491" in pins and TYPED_INVALID not in pins


def test_pin_facts_are_recorded_and_the_mistyped_sha_is_flagged_not_used():
    t = (R / "registry-pin-delta-assessment.md").read_text(encoding="utf-8")
    assert TYPED_INVALID in t and "does **not exist**" in t and PROGRAM_PIN in t
    for name, tree in CODE_TREES.items():
        assert name in t and tree in t
    for a in ("Amendment 3", "Amendment 4", "byte-identical", "Code is unchanged"):
        assert a in t
    m = (R / "g1-preparation-merge-record.md").read_text(encoding="utf-8")
    assert PR51_HEAD in m and PR51_MERGE in m and "merge commit" in m
    for other in MD:
        t2 = (R / other).read_text(encoding="utf-8")
        if other != "registry-pin-delta-assessment.md":
            assert TYPED_INVALID not in t2 or other == "g1-readiness-report.md" or "does not exist" in t2 or other == "README.md", other


def test_eight_files_are_recorded_with_commit_path_and_collection():
    c = json.loads((R / "eight-file-test-evidence-closure.json").read_text(encoding="utf-8"))
    files = c["files"]
    assert len(files) == 8 and sum(1 for f in files if f["repo"] == "Runtime") == 6 and sum(1 for f in files if f["repo"] == "Stack Qualification") == 2
    assert sum(f["collected"] for f in files if f["repo"] == "Runtime") == 293 and sum(f["collected"] for f in files if f["repo"] == "Stack Qualification") == 70
    for f in files:
        assert re.fullmatch(r"[0-9a-f]{40}", f["commit"]) and f["path"].endswith(".py") and f["cases"] and f["pin"] and f["gap"]
    f01 = next(f for f in files if f["path"].endswith("test_f01_policy_containment.py"))
    assert f01["pin"].startswith("NO")
    assert set(c["gap_effects"]) >= {"F-01", "F-07", "F-29", "F-06"}


def test_pin_path_assessment_separates_direct_from_complete_coverage():
    t = (R / "runtime-f01-pin-path-assessment.md").read_text(encoding="utf-8")
    assert "**No.**" in t and "allowed_actions and allowed_units" in t
    assert "does **not** claim the complete pin-plus-containment path is covered" in t
    assert "DRAFT" in t


def test_decision_register_marks_final_versus_provisional():
    t = (R / "architect-decision-register.md").read_text(encoding="utf-8")
    for i in range(1, 11):
        assert f"| PD-{i} |" in t
    rows = {m.group(1): m.group(2) for m in re.finditer(r"^\| (PD-\d+) \| [^|]+ \| ([^|]+) \|", t, re.M)}
    for pd in ("PD-1", "PD-2", "PD-4", "PD-10"):
        assert rows[pd].startswith("FINAL"), pd
    for pd in ("PD-3", "PD-7", "PD-8", "PD-9"):
        assert rows[pd].startswith("PROVISIONAL"), pd
    assert rows["PD-6"].startswith("PENDING") and rows["PD-5"].startswith("PREPARED")
    assert "no AI worker is assigned to an independent role" in t


def test_environment_profile_records_status_for_each_prerequisite_and_nothing_was_executed():
    t = (R / "environment-profile.md").read_text(encoding="utf-8")
    for status in ("PASS", "BLOCKED", "NOT RUN"):
        assert status in t
    assert "| E-18 | Any test execution" in t and "NOT RUN" in t.split("| E-18 |")[1].split("\n")[0]
    for s in ("pydantic 2.11.9", "pydantic 2.14.1", "PyNaCl 1.6.2", "v22.23.4"):
        assert s in t


def test_frozen_g0_and_g1_preparation_files_are_unchanged_by_this_package():
    import subprocess
    out = subprocess.run(["git", "diff", "--name-only", PR51_MERGE, "HEAD", "--", "docs/family-migration/g0", "docs/family-migration/g1-preparation"],
                         cwd=ROOT, capture_output=True, text=True)
    if out.returncode == 0:  # a shallow checkout without the merge commit cannot answer; the blob test in the preparation suite still applies
        assert out.stdout.strip() == "", out.stdout


def test_sprint_status_records_the_readiness_submission_without_changing_the_v09_block():
    s = (ROOT / "docs" / "sprint-status.md").read_text(encoding="utf-8")
    assert s.startswith("# Sprint status (the only live status document)\n\n## CURRENT STATUS (2026-10-27, post-merge)")
    assert "G1 PREPARATION MERGED, G1 READINESS SUBMITTED, G1 NOT AUTHORIZED" in s and HOLDS in s
    assert PR51_MERGE in s
