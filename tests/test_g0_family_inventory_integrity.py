"""G0 inventory integrity (offline). Checks the consistency of the G0 package; adds no behavior and qualifies nothing.

Verifies: 620/620 historical rows accounted with unchanged classes, 32 unresolved rows individually tracked, every ledger record source-backed, every family F1-F11
dispositioned, no immutable control proposed for migration, historical evidence/frozen contract/V09 manifest/cited source blobs unchanged since the baseline commit
317eb76acb2847c534c3ce7c2180b89b4aef987d, and the holds preserved.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G0 = ROOT / "docs" / "family-migration" / "g0"
HOLDS = ("G0: CONDITIONAL ACCEPTANCE. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. "
         "Release: HOLD. Publication: HOLD. Production: HOLD.")
VOC = {"MIGRATED", "ALREADY-GOVERNED", "ELIGIBLE-NOT-MIGRATED", "RETAIN-IN-CODE", "OUT-OF-SCOPE", "UNRESOLVED", "BLOCKED"}
S02_CLASSES = {"MANDATORY-INVARIANT": 354, "SERIALIZATION-OR-EVIDENCE": 90, "INCIDENTAL-CONDITIONAL": 51, "REFUSAL-OR-REASON-VOCABULARY": 50,
               "CONFIGURABLE-CANDIDATE": 43, "UNRESOLVED": 32}
BASELINE = {"cogno-us/cognous-ocs-registry": "317eb76acb2847c534c3ce7c2180b89b4aef987d",
            "cogno-us/cognous-control-plane": "d66ae07fa240510efdcc11ed4b3e1189dcefc822",
            "cogno-us/cognous-execution-runtime": "0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491",
            "cogno-us/cognous-stack-qualification": "bb9b08904192b5f50a49e00ed8de0cab80fd7c19"}
PINNED_BLOBS = {
    "docs/s02-evidence/README.md": "86445b4868e07638915b085abd3afb7441ced89f",
    "docs/s02-evidence/W1.md": "2a224ac3c9cf367a841ead4a8679166a4477d425",
    "docs/s02-evidence/W2.md": "5ffbcec825b9fe56a3a6ab3fddd1fb78e877f264",
    "docs/s02-evidence/W3.md": "a1e610b430c04af7de395ddb32f9595ec17cee2e",
    "docs/s02-evidence/W4.md": "3412a9b06bda28a5439d2f07ad349d296f02ae60",
    "docs/s02-evidence/W5.md": "db7d52ab6602d0d4b05c670f575ecc35fdf3cbde",
    "docs/s02-evidence/W6.md": "c83557fb48a3c8b791e2ffe87c7b7cd513fca03e",
    "docs/s02-evidence/W7.md": "5ccb195c462883699aa1356e654469102a989702",
    "docs/s02-evidence/W8.md": "7318560eb6aba4d27b534081ac0bdea82786e6ee",
    "docs/s02-evidence/W9.md": "dcdb77402fe0072d43e497999a69f1a0ff9c460f",
    "docs/s02-inventory.md": "a76bc33b94eadd25b94af50045aa2387170956e2",
    "docs/s06-next-family-recommendation.md": "4fe993629ce4229009599c6b9d65865fd17d79f3",
    "docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.0.md": "bcc51873ec42ea5e6dfa6c89ced2cedf9cfed91f",
    "docs/v09/candidate-manifest.json": "f4804449432a8e61d4f5054d88830b34b9d9a039",
    "docs/r08-v2-contract.md": "ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f",
    "docs/r08-v2-contract-amendment-1.md": "081dae56b8fdd3736022900f8dc224eafcd96189",
    "docs/r08-v2-contract-amendment-2.md": "e082331d729a6b07b2210a4fd02a06bba3a393c6",
    "docs/r08-v2-contract-amendment-3.md": "c9bf1d39d60c4f15962855aa39e5d814052f2e77",
    "docs/r08-v2-contract-amendment-4.md": "71d639aa208ba1007d0946de69a8ed76a2cfe67c",
    "docs/s03-contract.md": "86a99ba48fff64e2144167fee76c36bbf2d84d86",
    "registry_successor/v2_f1ab.py": "2614bb4d613f0db6aae4413cc05c2f4897adb193",
    "registry_successor/families.py": "3b8e7452d7c6ee357602265634206873a49867d0",
    "registry_successor/v2_age_bounds.py": "3216d7e19663e6cd31c9f311e535b8a9445e31e7",
    "registry_successor/v2_policy_identity.py": "eea22798b729be849d6abd0847daa474872fe65a",
}
LEDGER = json.loads((G0 / "current-candidate-ledger.json").read_text())
CROSS = json.loads((G0 / "historical-crosswalk.json").read_text())
RECORDS = {r["rule_id"]: r for r in LEDGER["records"]}
ROWS = {m["id"]: m for m in CROSS["rows"]}


def blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def s02_rows_from_evidence():
    out = {}
    for f in sorted((ROOT / "docs" / "s02-evidence").glob("W*.md")):
        for line in f.read_text().splitlines():
            if re.match(r"\| W\d+-\d+", line):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                out[cells[0]] = cells[4]
    return out


def test_all_620_historical_rows_are_accounted_with_unchanged_classes():
    ev = s02_rows_from_evidence()
    assert len(ev) == 620 and set(ev) == set(ROWS) and len(CROSS["rows"]) == 620
    for rid, cls in ev.items():
        assert ROWS[rid]["historical"]["class"] == cls, rid
    counts = {}
    for cls in ev.values():
        counts[cls] = counts.get(cls, 0) + 1
    assert counts == S02_CLASSES
    for m in CROSS["rows"]:
        assert m["crosswalk_status"] in {"UNCHANGED", "MOVED", "CHANGED", "DELETED"} and m["references"] is not None
        assert m["old_source_sha"] and m["current_source_sha"]
    assert CROSS["counts"]["rows"] == 620


def test_the_75_candidate_and_unresolved_rows_have_worker_resolutions_and_32_unresolved_are_tracked():
    needing = {i for i, m in ROWS.items() if m["historical"]["class"] in {"CONFIGURABLE-CANDIDATE", "UNRESOLVED"}}
    assert len(needing) == 75
    assert all(ROWS[i]["g0_resolution"] for i in needing)
    unresolved = {i for i, m in ROWS.items() if m["historical"]["class"] == "UNRESOLVED"}
    assert len(unresolved) == 32
    for i in unresolved:
        t = ROWS[i]["unresolved_tracking"]
        assert t and t["g0_status"] == "UNRESOLVED-PRESERVED" and t["historical_classification_changed"] is False
        assert t["ratification_required"] is True and t["proposed_resolution"] and t["proposal_confidence"] in {"HIGH", "MEDIUM", "LOW"}
    assert all(not m["unresolved_tracking"] for i, m in ROWS.items() if i not in unresolved)


def test_every_ledger_record_is_source_backed_and_dispositioned():
    assert len(RECORDS) == len(LEDGER["records"]) == 116 and LEDGER["counts"]["records"] == 116
    for r in RECORDS.values():
        for key in ("repository", "file", "symbol", "lines", "snippet", "evaluator", "config_owner_and_source", "boundary", "registry_coverage", "constitutional_constraints",
                    "tier", "migration_eligibility", "required_contract_change", "non_widening", "existing_tests", "missing_negative_oracles", "dependencies",
                    "proposed_disposition", "rationale", "kind", "family"):
            assert r.get(key) not in (None, "", []), (r["rule_id"], key)
        assert re.fullmatch(r"[0-9a-f]{40}", r["source_sha"]), r["rule_id"]
        assert r["proposed_disposition"] in VOC and r["lead_disposition"] == r["proposed_disposition"]
        assert r["migration_eligibility"] in {"ELIGIBLE", "CONDITIONAL", "NOT_ELIGIBLE", "UNRESOLVED"}
        for s in r["s02_rows"]:
            assert s in ROWS, (r["rule_id"], s)
        if r["repository"] in BASELINE:
            assert r["source_sha"] == BASELINE[r["repository"]], r["rule_id"]
    assert LEDGER["baseline_pins"] == BASELINE


def test_crosswalk_and_ledger_link_each_other():
    for i, m in ROWS.items():
        for rid in m["linked_candidate_rule_ids"]:
            assert rid in RECORDS, (i, rid)
    for r in RECORDS.values():
        for s in r["s02_rows"]:
            assert r["rule_id"] in ROWS[s]["linked_candidate_rule_ids"] or ROWS[s]["historical"]["class"] not in {"CONFIGURABLE-CANDIDATE", "UNRESOLVED"}, (r["rule_id"], s)


def test_counts_are_recomputed_not_asserted():
    by = {}
    for r in RECORDS.values():
        by[r["proposed_disposition"]] = by.get(r["proposed_disposition"], 0) + 1
    assert by == LEDGER["counts"]["records_by_disposition"]
    groups = {}
    for g in LEDGER["rule_groups"]:
        assert g["lead_disposition"] in VOC and g["record_ids"] and all(i in RECORDS for i in g["record_ids"])
        groups[g["lead_disposition"]] = groups.get(g["lead_disposition"], 0) + 1
    assert groups == LEDGER["counts"]["groups_by_disposition"]
    assert sum(len(g["record_ids"]) for g in LEDGER["rule_groups"]) == 116
    assert LEDGER["counts"]["rule_groups"] == len(LEDGER["rule_groups"])


def test_every_family_has_a_disposition_and_every_record_is_placed():
    fams = {f["family"] for f in LEDGER["families"]}
    assert {"F1a", "F1b", "F1c", "F1d", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11"} <= fams
    placed = set()
    for f in LEDGER["families"]:
        assert f["parts"], f["family"]
        for p in f["parts"]:
            assert p["disposition"] in VOC and p["record_ids"]
            placed.update(p["record_ids"])
            ds = {RECORDS[i]["proposed_disposition"] for i in p["record_ids"]}
            assert p["disposition"] in ds or p.get("lead_override_reason"), (f["family"], p["part"])
    for r in RECORDS.values():
        if r["family"].startswith("NEW:"):
            continue
        assert r["rule_id"] in placed, r["rule_id"]
    assert {n["family"] for n in LEDGER["new_families"]} == {r["family"] for r in RECORDS.values() if r["family"].startswith("NEW:")}


def test_no_immutable_control_is_proposed_for_migration():
    for r in RECORDS.values():
        if r["kind"].startswith("IMMUTABLE_CONTROL"):
            assert r["proposed_disposition"] in {"RETAIN-IN-CODE", "ALREADY-GOVERNED", "OUT-OF-SCOPE"}, r["rule_id"]
        if r["proposed_disposition"] == "ELIGIBLE-NOT-MIGRATED":
            assert r["migration_eligibility"] in {"ELIGIBLE", "CONDITIONAL", "UNRESOLVED"}, r["rule_id"]
    assert not any(p["disposition"] == "MIGRATED" for f in LEDGER["families"] for p in f["parts"])


def test_historical_evidence_frozen_contracts_manifest_and_cited_sources_are_unchanged():
    for rel, sha in PINNED_BLOBS.items():
        assert blob(ROOT / rel) == sha, rel


def test_deliverables_exist_and_preserve_holds():
    for name in ("source-baseline.md", "historical-crosswalk.json", "current-candidate-ledger.json", "family-eligibility-matrix.md", "migration-backlog.md",
                 "unresolved-decisions.md", "g0-exit-report.md"):
        assert (G0 / name).is_file(), name
    for name in ("source-baseline.md", "family-eligibility-matrix.md", "migration-backlog.md", "unresolved-decisions.md", "g0-exit-report.md"):
        assert HOLDS in (G0 / name).read_text(), name
    backlog = (G0 / "migration-backlog.md").read_text()
    for w in range(1, 14):
        assert f"## M{w} " in backlog
    t = (G0 / "g0-exit-report.md").read_text()
    for banned in ("production ready", "security clearance", "certified"):
        assert banned not in t.lower().replace("not certified", "")


def test_sprint_status_has_a_separate_successor_entry_and_keeps_history():
    s = (ROOT / "docs" / "sprint-status.md").read_text()
    assert s.startswith("# Sprint status (the only live status document)\n\n## CURRENT STATUS (2026-10-27, post-merge)")
    assert "## SUCCESSOR PROGRAM STATUS (Registry family migration" in s and HOLDS in s
    assert "## HISTORICAL (as prepared, pre-merge" in s


def test_inventory_counts_are_preserved():
    assert len(ROWS) == 620 and len(RECORDS) == 116 and len(LEDGER["rule_groups"]) == 97
    cfg = {"ALREADY-GOVERNED", "ELIGIBLE-NOT-MIGRATED", "UNRESOLVED", "BLOCKED"}
    assert sum(1 for g in LEDGER["rule_groups"] if g["lead_disposition"] in cfg) == 33
    assert sum(1 for m in ROWS.values() if m["unresolved_tracking"]) == 32


def test_reclassification_proposals_stay_unratified():
    n = 0
    for w in "BCD":
        n += len(json.loads((G0 / "evidence" / f"worker-{w}" / "reclassification_proposals.json").read_text()))
    assert n == 20
    assert "unratified proposals" in (G0 / "unresolved-decisions.md").read_text()


def test_architect_decisions_are_recorded_accurately_and_others_stay_open():
    rows = {}
    for line in (G0 / "unresolved-decisions.md").read_text().splitlines():
        m = re.match(r"\| (AD-\d\d) \|", line)
        if m:
            rows[m.group(1)] = line
    assert len(rows) == 24
    assert "**ACCEPTED**" in rows["AD-01"]
    assert "**DIRECTION ACCEPTED; detailed scope pending.**" in rows["AD-02"]
    assert "**DIRECTION ACCEPTED; successor contract pending.**" in rows["AD-03"]
    for k, line in rows.items():
        if k not in {"AD-01", "AD-02", "AD-03"}:
            assert line.rstrip().endswith("| OPEN |"), k
    backlog = (G0 / "migration-backlog.md").read_text()
    assert "negative-oracle closure" in backlog and "approved successor contract/version" in backlog


def test_exit_report_records_verified_ci_and_does_not_claim_independence():
    t = (G0 / "g0-exit-report.md").read_text()
    assert "ad7c7896ee4f9af3cced6e91ce4cc33b6fe93b27" in t and "40593574612" in t and "40593568699" in t
    assert "Independent qualification | NOT PERFORMED" in t and "does not establish independent qualification" in t
    assert "NOT YET OBSERVED" not in t
    assert "ARCHITECT CONDITIONALLY ACCEPTED" in (ROOT / "docs" / "sprint-status.md").read_text()
