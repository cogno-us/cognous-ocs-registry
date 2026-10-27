"""V09 freeze-candidate integrity: pins, frozen contract bytes, gate honesty and status consistency (offline).

Plan: v1.5 (V09: exact pins, limitations, operational exclusions, truthful readiness; not a release). These tests read only files in this
repository. They add no behavior and qualify nothing; a failure means the candidate package is inconsistent with its own manifest or a frozen
artifact changed. The cross-repository checks live in tools/verify_v09_candidate.py (git objects of the four clones).
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V09 = ROOT / "docs" / "v09"
MANIFEST = json.loads((V09 / "candidate-manifest.json").read_text())
HEX40 = re.compile(r"^[0-9a-f]{40}$")
CONSTITUTION = "1c2e920f4e58e07a52e8e2408a506cf7dbc1292b"
PROTECTED = "2fc880dae37eac76e5074533435740ce0684209d"


def blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def comp(cid):
    return next(c for c in MANIFEST["components"] if c["id"] == cid)


def test_manifest_has_exactly_the_four_components_with_full_shas():
    assert MANIFEST["schema"] == "ocs-v09-candidate-manifest/1"
    assert [c["id"] for c in MANIFEST["components"]] == ["registry", "control_plane", "runtime", "stack_qualification"]
    for c in MANIFEST["components"]:
        assert HEX40.match(c["main_commit"]) and HEX40.match(c["main_tree"]), c["id"]
        assert len(c["merge_parents"]) == 2 and all(HEX40.match(p) for p in c["merge_parents"] if c["id"] != "registry") or c["id"] == "registry"
        for path, blob in c["blobs_git_sha1"].items():
            assert HEX40.match(blob), (c["id"], path)
    for q in MANIFEST["qualified_commit_equivalence"]:
        assert HEX40.match(q["qualified_commit"])


def test_no_moving_reference_is_used_as_a_pin():
    for c in MANIFEST["components"]:
        assert c["main_commit"] not in ("main", "HEAD") and HEX40.match(c["main_commit"])
    text = json.dumps(MANIFEST["components"])
    assert "refs/heads" not in text


def test_candidate_is_declared_not_a_release_and_holds_are_recorded():
    assert "NOT A RELEASE" in MANIFEST["status"] and "NOT ACCEPTED" in MANIFEST["status"]
    h = MANIFEST["holds"]
    assert h["release"] == h["publication"] == h["production"] == "HOLD"
    assert h["independent_V08_tier1"] == "NOT STARTED"
    assert h["independent_V07_security_review"] == "OPEN"
    assert h["Ed25519_26_34"] == "SECURITY-HELD"
    assert h["V09"].startswith("CANDIDATE PREPARATION AUTHORIZED") and "ACCEPTANCE NOT YET AUTHORIZED" in h["V09"]


def test_constitution_pin_matches_the_plan_and_is_the_immutable_revision():
    assert MANIFEST["constitution"]["pinned_commit"] == CONSTITUTION
    assert CONSTITUTION in (ROOT / "docs" / "plans" / "PROJECT_PLAN-v1.5.md").read_text()


def test_registry_resident_frozen_files_match_the_manifest_blobs():
    checked = 0
    for path, want in comp("registry")["blobs_git_sha1"].items():
        f = ROOT / path
        assert f.is_file(), path
        assert blob_sha1(f) == want, f"{path} changed since the candidate baseline"
        checked += 1
    assert checked >= 10


def test_protected_safe_executor_is_unchanged_and_equal_in_runtime():
    assert blob_sha1(ROOT / "baseline" / "execution-runtime" / "engine" / "safe_executor.py") == PROTECTED
    assert comp("registry")["blobs_git_sha1"]["baseline/execution-runtime/engine/safe_executor.py"] == PROTECTED
    assert comp("runtime")["blobs_git_sha1"]["engine/safe_executor.py"] == PROTECTED


def test_every_manifest_commit_is_named_in_inventory_and_sprint_status():
    inv = (V09 / "component-inventory.md").read_text()
    status = (ROOT / "docs" / "sprint-status.md").read_text()
    for c in MANIFEST["components"]:
        assert c["main_commit"] in inv, c["id"]
        assert c["main_commit"] in status, c["id"]


def test_gate_matrix_never_marks_an_independent_gate_as_passed():
    rows = [l for l in (V09 / "gate-matrix.md").read_text().splitlines() if l.startswith("| ") and not l.startswith("| Gate") and not l.startswith("|---")]
    assert len(rows) >= 10
    by = {r.split("|")[1].strip(): r.split("|")[3].strip() for r in rows}
    for gate, status in by.items():
        assert not status.startswith("INDEPENDENTLY QUALIFIED"), gate
    v07 = next(s for g, s in by.items() if g.startswith("V07"))
    v08 = next(s for g, s in by.items() if g.startswith("V08 independent"))
    ed = next(s for g, s in by.items() if g.startswith("Ed25519"))
    v09 = next(s for g, s in by.items() if g.startswith("V09"))
    assert "NOT RUN" in v07 and "OPEN" in v07
    assert "NOT STARTED" in v08
    assert "SECURITY-HELD" in ed
    assert "NOT AUTHORIZED" in v09 and "NOT RUN" in v09


def test_readiness_report_does_not_claim_release_readiness():
    text = (V09 / "readiness-report.md").read_text()
    assert "READY FOR INDEPENDENT QUALIFICATION" in text
    for m in re.finditer(r"RELEASE READY", text):
        before = text[max(0, m.start() - 12):m.start()].replace("*", "").lower()
        assert before.endswith("not "), "RELEASE READY must only appear negated"
    assert "BLOCKED" not in text.split("## Classification")[1].split("##")[0]


def test_historical_failures_are_preserved_not_replaced():
    ev = (V09 / "evidence-index.md").read_text()
    for needle in ("A08 BREACH", "F-A1 BREACH", "7b72de9ac7e4898c0f9bdad3e9b337775cc9c543", "40537445066", "INCONCLUSIVE", "process exception"):
        assert needle.lower() in ev.lower(), needle
    assert "not rewritten as 30 PASS" in ev


def test_sprint_status_records_current_state_and_keeps_history():
    s = (ROOT / "docs" / "sprint-status.md").read_text()
    head = s.split("*The sections below are preserved.")[0]
    for needle in ("V09: CANDIDATE PREPARATION AUTHORIZED; ACCEPTANCE NOT YET AUTHORIZED", "Independent V07 security review: OPEN", "Independent V08 Tier 1: NOT STARTED",
                   "Ed25519 #26/#34: SECURITY-HELD", "Release: HOLD", "Publication: HOLD", "Production: HOLD", "Next authorized action"):
        assert needle in head, needle
    # history is kept and the superseded statements are marked
    for kept in ("Next planned increment V01", "G0 APPROVED / CLOSED", "S06", "R08-S01"):
        assert kept in s, kept
    assert s.count("HISTORICAL") >= 3


def test_exclusion_register_covers_the_required_topics():
    t = (V09 / "limitations-and-exclusions.md").read_text()
    for needle in ("Production deployment", "trust-root custody", "External-anchor custody", "Ed25519", "Independent Tier 1", "Real-world authority", "revocation propagation",
                   "OS privilege isolation", "deployment environments", "Distribution, licensing"):
        assert needle.lower() in t.lower(), needle
