"""V09 post-merge record consistency (offline): merge SHA, current status block, and the two independent assignments.

Adds no behavior and qualifies nothing. Checks that the post-merge record, the sprint status and the assignments agree with the V09 manifest pins and
never designate or claim an independent assessor.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V09 = ROOT / "docs" / "v09"
MANIFEST = json.loads((V09 / "candidate-manifest.json").read_text())
MERGE = "b695f67d944286c76100ddab36818f926958297f"
PINS = {c["id"]: c["main_commit"] for c in MANIFEST["components"]}
ASSIGN = {"v07": V09 / "independent-v07-security-review-assignment.md", "v08": V09 / "independent-v08-tier1-assignment.md"}


def current_block():
    s = (ROOT / "docs" / "sprint-status.md").read_text()
    assert s.startswith("# Sprint status (the only live status document)\n\n## CURRENT STATUS (2026-10-27, post-merge)")
    return s.split("\n---\n")[0]


def test_sprint_status_records_the_v09_merge_and_holds_first():
    b = current_block()
    assert MERGE in b and "pull/47" in b and "NOT formally accepted" in b
    for needle in ("V01–V08: bounded engineering implementation merged.", "V09: freeze-candidate package merged; formal acceptance held.",
                   "Independent V07 security review: OPEN.", "Independent V08 Tier 1: NOT STARTED.", "Ed25519 #26/#34: SECURITY-HELD.",
                   "Release: HOLD.", "Publication: HOLD.", "Production: HOLD."):
        assert needle in b, needle
    for pin in PINS.values():
        assert pin in b


def test_history_is_preserved_and_superseded_blocks_are_marked():
    s = (ROOT / "docs" / "sprint-status.md").read_text()
    assert "## HISTORICAL (as prepared, pre-merge" in s
    for kept in ("V09 FREEZE-CANDIDATE PREPARED, NOT ACCEPTED", "Next planned increment V01", "G0 APPROVED / CLOSED", "S06", "R08-S01"):
        assert kept in s, kept


def test_post_merge_record_names_the_merge_and_the_historical_prs():
    t = (V09 / "post-merge-record.md").read_text()
    assert MERGE in t
    for needle in ("7b72de9ac7e4898c0f9bdad3e9b337775cc9c543", "1a9b6a933986a51e2cf8d2e5e79679538305e2c2", "bb9b08904192b5f50a49e00ed8de0cab80fd7c19", "open, unmerged", "closed as superseded"):
        assert needle in t, needle


def test_assignments_use_the_manifest_pins_and_the_required_sections():
    for name, path in ASSIGN.items():
        t = path.read_text()
        for cid in ("control_plane", "runtime", "stack_qualification"):
            assert PINS[cid] in t, (name, cid)
        assert MERGE in t and "1c2e920f4e58e07a52e8e2408a506cf7dbc1292b" in t
        for needle in ("Reviewer role required", "Exact", "Scope", "Contracts", "Oracle freeze", "Known limitations", "Mandatory failure reporting", "PASS", "BLOCK", "INCONCLUSIVE"):
            assert needle in t, (name, needle)


def test_assignments_never_designate_or_claim_an_independent_assessor():
    for name, path in ASSIGN.items():
        t = path.read_text()
        assert "No reviewer is designated" in t, name
        assert "AI" in t and "do not qualify" in t.lower() or "independence cannot be inferred" in t.lower(), name
        assert not re.search(r"\b(designated reviewer|reviewer:)\s*[A-Z][a-z]+ [A-Z][a-z]+", t)
        assert "INDEPENDENTLY QUALIFIED" not in t


def test_v08_assignment_requires_real_os_identities_and_main_sha_pins():
    t = ASSIGN["v08"].read_text()
    assert "real, distinct, non-root OS identities" in t
    assert "did **not** run at the Runtime merge SHA" in t
