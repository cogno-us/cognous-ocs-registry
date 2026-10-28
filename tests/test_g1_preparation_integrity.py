"""G1 preparation integrity (offline, documentation only). Adds no behavior and qualifies nothing; builder tests are not independent.

Checks that the frozen G0 files are unchanged, the retained G0 counts still reconcile, the M1 gap register is complete and assigned, no oracle claims an
author or independence, and the standing holds are preserved.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G0 = ROOT / "docs" / "family-migration" / "g0"
G1 = ROOT / "docs" / "family-migration" / "g1-preparation"
HOLDS = ("G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. "
         "Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.")
G0_MERGE = "7208eb6f53f12677f138fe0c64ec48a2e58292b5"
FROZEN_G0_BLOBS = {
    "current-candidate-ledger.json": "c0db3c1736872ff37438073090c6782c8cbde79f",
    "historical-crosswalk.json": "1f146f3d86235b3d1a4351cb5eff7b4c173509a1",
    "source-baseline.md": "288f1bc261f44e1ef6a5207e532f80bba5ad293f",
    "family-eligibility-matrix.md": "c0fbedf9ad7eb87e584b6d450cd37f35db9ef817",
    "migration-backlog.md": "a688ebdc1667121e6378a063d20adbb8403f1a72",
    "unresolved-decisions.md": "b2b4ddb05630d6ff8b649169656d5af79c63d0e5",
    "g0-exit-report.md": "531eb6753db56fa7b8d1fc72f3b65f4c1f2b6f7c",
}
DOCS = ["README.md", "g0-freeze-record.md", "g0-erratum.md", "m1-existing-contract-crosswalk.md", "m1-negative-oracle-coverage-matrix.md", "independent-oracle-specification.md",
        "component-pins-and-test-baselines.md", "test-budget-and-execution-boundaries.md", "successor-contract-strategy.md", "open-decisions-and-prerequisites.md",
        "g1-authorization-recommendation.md"]


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def test_frozen_g0_files_are_byte_identical_to_the_merge_commit():
    for name, sha in FROZEN_G0_BLOBS.items():
        assert blob(G0 / name) == sha, name


def test_retained_g0_counts_reconcile():
    ledger = json.loads((G0 / "current-candidate-ledger.json").read_text())
    cross = json.loads((G0 / "historical-crosswalk.json").read_text())
    assert len(cross["rows"]) == 620 and len(ledger["records"]) == 116 and len(ledger["rule_groups"]) == 97
    d = {}
    for g in ledger["rule_groups"]:
        d[g["lead_disposition"]] = d.get(g["lead_disposition"], 0) + 1
    assert d == {"ALREADY-GOVERNED": 5, "ELIGIBLE-NOT-MIGRATED": 23, "RETAIN-IN-CODE": 56, "OUT-OF-SCOPE": 8, "UNRESOLVED": 4, "BLOCKED": 1}
    assert sum(d[k] for k in ("ALREADY-GOVERNED", "ELIGIBLE-NOT-MIGRATED", "UNRESOLVED", "BLOCKED")) == 33
    assert sum(1 for m in cross["rows"] if m["unresolved_tracking"]) == 32
    n = sum(len(json.loads((G0 / "evidence" / f"worker-{w}" / "reclassification_proposals.json").read_text())) for w in "BCD")
    assert n == 20


def test_all_deliverables_exist_and_preserve_the_holds():
    for name in DOCS:
        t = (G1 / name).read_text()
        assert HOLDS in t or name == "README.md" and HOLDS in t, name
    assert (G1 / "m1-oracle-register.json").is_file()
    for w in "EF":
        for f in ("topics.json", "test_inventory.json", "notes.md"):
            assert (G1 / "evidence" / f"worker-{w}" / f).is_file()


def test_freeze_record_names_the_merge_and_the_decision_history():
    t = (G1 / "g0-freeze-record.md").read_text()
    assert G0_MERGE in t and "e6c57f6980aa71581499b5fcdbc38a647ebbe304" in t and "not an independent security qualification" in t
    ids = set(re.findall(r"^\| (AD-\d\d) \|", t, re.M))
    assert ids == {f"AD-{i:02d}" for i in range(1, 25)}
    for name, sha in FROZEN_G0_BLOBS.items():
        assert sha in t, name


def test_gap_register_is_complete_assigned_and_claims_no_independence():
    reg = json.loads((G1 / "m1-oracle-register.json").read_text())
    oracles = reg["oracles"]
    assert reg["gap_total"] == len(oracles) == 65
    gaps = set()
    for w in "EF":
        for topic in json.loads((G1 / "evidence" / f"worker-{w}" / "topics.json").read_text()):
            gaps.update(g["gap_id"] for g in topic["gaps"])
    assert len(gaps) == 65 and {o["gap_id"] for o in oracles} == gaps
    assert len({o["oracle_id"] for o in oracles}) == 65
    sev = {}
    for o in oracles:
        assert o["work_package"] in {f"OW-{i}" for i in range(1, 10)} and o["status"] == "PROPOSED"
        assert o["authored_by"] is None and o["independent_author_designated"] is False
        assert o["basis"] in {"SPECIFICATION", "SPECIFICATION-PENDING-RULING", "CHARACTERISATION"}
        if o["basis"] == "SPECIFICATION-PENDING-RULING":
            assert o["depends_on_decision"]
        sev[o["severity"]] = sev.get(o["severity"], 0) + 1
    assert sev == {"HIGH": 11, "MEDIUM": 37, "LOW": 17}


def test_every_m1_topic_is_covered_and_none_is_full():
    for w in "EF":
        topics = json.loads((G1 / "evidence" / f"worker-{w}" / "topics.json").read_text())
        assert [t["topic_no"] for t in topics] == list(range(1, 13))
        assert all(t["coverage_for_two_sets"] != "FULL" for t in topics)


def test_g1_is_not_authorized_and_nothing_claims_independent_qualification():
    rec = (G1 / "g1-authorization-recommendation.md").read_text()
    assert "authorizes nothing" in rec
    spec = (G1 / "independent-oracle-specification.md").read_text()
    assert "nothing here is independent" in spec
    for name in DOCS:
        t = (G1 / name).read_text().lower()
        for banned in ("independently qualified", "production ready", "security clearance"):
            assert banned not in t, (name, banned)
    status = (ROOT / "docs" / "sprint-status.md").read_text()
    # Updated by the G1 readiness change: the successor section now records the merge of PR #51 and the readiness submission.
    assert "G1 PREPARATION MERGED, G1 READINESS SUBMITTED, G1 NOT AUTHORIZED" in status
    assert "G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED." in status


def test_sprint_status_keeps_the_v09_block_first_and_history():
    s = (ROOT / "docs" / "sprint-status.md").read_text()
    assert s.startswith("# Sprint status (the only live status document)\n\n## CURRENT STATUS (2026-10-27, post-merge)")
    assert "## HISTORICAL (superseded by the 2026-10-28 successor status above)" in s and "## HISTORICAL (as prepared, pre-merge" in s
