"""Integrity of the M2 proposal documents (docs/family-migration/m2): counts and holds only. No behaviour is tested."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
M2 = ROOT / "docs" / "family-migration" / "m2"
LEDGER = ROOT / "docs" / "family-migration" / "g0" / "current-candidate-ledger.json"


def test_five_documents_only():
    assert sorted(p.name for p in M2.iterdir()) == [
        "01-migration-backlog.md", "02-m2-successor-contract-proposal.md", "03-m2-implementation-blueprint.md",
        "04-m2-test-matrix.md", "05-blocking-architectural-decisions.md"]


def test_backlog_lists_every_eligible_group_once():
    ledger = json.loads(LEDGER.read_text())
    eligible = [g["group_id"] for g in ledger["rule_groups"] if g["lead_disposition"] == "ELIGIBLE-NOT-MIGRATED"]
    assert len(eligible) == 23
    text = (M2 / "01-migration-backlog.md").read_text()
    for gid in eligible:
        rows = [ln for ln in text.splitlines() if ln.split("|")[1:3] and ln.split("|")[1].strip().isdigit() and ln.split("|")[2].strip() == gid]
        assert len(rows) == 1, gid
    assert "0 of 23" in text


def test_contract_covers_only_the_two_ceilings_and_leaves_v2():
    text = (M2 / "02-m2-successor-contract-proposal.md").read_text()
    assert "max_amount" in text and "max_effects" in text and "r08-v3" in text
    assert "Frozen `r08-v2` is unchanged" in text


def test_test_matrix_has_required_scenarios():
    text = (M2 / "04-m2-test-matrix.md").read_text()
    for i in range(1, 15):
        assert "T%02d" % i in text or "T%02da" % i in text, i
    assert "independent qualification" in text


def test_holds_preserved():
    text = (M2 / "05-blocking-architectural-decisions.md").read_text()
    assert "M2 implementation: NOT YET AUTHORIZED" in text
    assert "Release/publication/production: HOLD" in text
