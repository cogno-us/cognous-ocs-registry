"""Integrity of the independent Registry eligibility audit (offline). Adds no behavior and qualifies nothing.

Checks that the audit ledgers are internally consistent and reproducible: 620/620 historical rows reconciled with unchanged classes, every row mapped to exactly
one canonical rule with exactly one disposition, every G0 source record mapped once, M2/M3 members counted once, no retained mandatory control mapped into an eligible
or governed rule, ledgers equal to a fresh recomputation, frozen G0/S02 evidence byte-identical to the pinned baseline, cross-check disagreements all dispositioned,
and the holds preserved. It does NOT establish that any classification is correct; classification correctness is evidenced in the audit directory.
"""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUD = ROOT / "docs" / "audit" / "registry-eligibility-2026-10-28"
G0 = ROOT / "docs" / "family-migration" / "g0"
VOC = {"REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "RETAIN-IN-CODE", "CALLER-OR-ISSUER-OWNED", "PROVIDER-OR-HOST-OWNED", "OUT-OF-SCOPE", "UNRESOLVED", "BLOCKED"}
S02_CLASSES = {"MANDATORY-INVARIANT": 354, "SERIALIZATION-OR-EVIDENCE": 90, "INCIDENTAL-CONDITIONAL": 51, "REFUSAL-OR-REASON-VOCABULARY": 50,
               "CONFIGURABLE-CANDIDATE": 43, "UNRESOLVED": 32}
NINE_MEMBER_PARAMETERS = 9  # five f1ab allow-sets + max_amount + max_effects + allowed_target_prefixes + target_match


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RECONCILE = _load(AUD / "tools" / "reconcile.py", "audit_reconcile")
RENDER = _load(AUD / "tools" / "render_reports.py", "audit_render")
CROSS = json.loads((G0 / "historical-crosswalk.json").read_text())
LEDGER = json.loads((G0 / "current-candidate-ledger.json").read_text())
ROWS = json.loads((AUD / "crosswalk.json").read_text())["rows"]
RULES = json.loads((AUD / "rule-catalogue.json").read_text())["rules"]
REC = json.loads((AUD / "reconciliation.json").read_text())
SUMMARY = REC["summary"]
BY_RULE = {r["rule_id"]: r for r in RULES}
ADJ = json.loads((AUD / "lead-adjudications.json").read_text())


def test_620_rows_exactly_once_with_unchanged_ids_and_classes():
    ids = [r["id"] for r in ROWS]
    assert len(ids) == 620 and len(set(ids)) == 620
    frozen = {r["id"]: r["historical"]["class"] for r in CROSS["rows"]}
    assert set(ids) == set(frozen)
    assert all(r["historical_class"] == frozen[r["id"]] for r in ROWS)
    assert dict(collections.Counter(r["historical_class"] for r in ROWS)) == S02_CLASSES


def test_every_row_maps_to_one_rule_and_every_rule_has_one_valid_disposition():
    assert all(r["canonical_rule_id"] in BY_RULE for r in ROWS)
    assert all(r["disposition"] in VOC and r["worker_disposition"] in VOC for r in ROWS)
    assert len(BY_RULE) == len(RULES) == SUMMARY["canonical_rules_total"]
    assert all(r["disposition"] in VOC for r in RULES)
    assert sum(SUMMARY["canonical_rules_by_disposition"].values()) == len(RULES)
    assert sum(SUMMARY["rows_by_final_disposition"].values()) == 620
    for rule in RULES:  # a rule's historical rows are exactly the rows pointing at it
        assert sorted(rule["historical_source_ids"]) == sorted(r["id"] for r in ROWS if r["canonical_rule_id"] == rule["rule_id"])


def test_row_disposition_follows_rule_unless_explained():
    for r in ROWS:
        rule = BY_RULE[r["canonical_rule_id"]]
        if r["disposition"] != rule["disposition"]:
            assert r["id"] in ADJ["row_disposition_overrides"], r["id"]
        if r["disposition"] != r["worker_disposition"]:
            assert r["disposition_differs_from_worker"] is True


def test_no_retained_control_is_mapped_into_an_eligible_or_governed_rule():
    manageable = {"REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED"}
    for r in ROWS:
        if r["worker_disposition"] == "RETAIN-IN-CODE" and BY_RULE[r["canonical_rule_id"]]["disposition"] in manageable:
            assert r["disposition"] == "RETAIN-IN-CODE" and r["id"] in ADJ["row_disposition_overrides"], r["id"]
    assert REC["errors"] == []


def test_every_g0_record_and_group_is_mapped_exactly_once():
    record_ids = {x["rule_id"] for x in LEDGER["records"]}
    assert len(record_ids) == 116 and set(REC["g0_record_crosswalk"]) == record_ids
    placed = [x for rule in RULES for x in rule["g0_record_ids"]]
    assert sorted(placed) == sorted(record_ids)
    assert len(REC["g0_group_crosswalk"]) == 97
    assert {x["g0_group_id"] for x in REC["g0_group_crosswalk"]} == {g["group_id"] for g in LEDGER["rule_groups"]}
    assert all(x["audit_rule_id"] in BY_RULE for x in REC["g0_group_crosswalk"])


def test_m2_m3_members_are_counted_once_and_nothing_is_independently_accepted():
    governed = [r for r in RULES if r["disposition"] == "REGISTRY-GOVERNED"]
    assert sum(r["parameter_count"] for r in governed) == NINE_MEMBER_PARAMETERS == SUMMARY["registry_governed_parameters"]
    for r in governed:
        assert r["implementation_layers"] == {"registry_represented": "YES", "enforcement_integrated": "YES", "independently_accepted": "NO"}
        assert r["migration_status"] == "IMPLEMENTED"
    assert SUMMARY["migration_state"]["independently_accepted"] == 0
    names = {r["rule_id"] for r in governed}
    assert {"RG-F1A-ALLOW-SETS-FIVE", "RG-F1C-MAX-AMOUNT", "RG-F1C-MAX-EFFECTS", "RG-F1D-TARGET-PREFIXES", "RG-F1D-TARGET-MATCH"} == names
    for r in RULES:  # represented-only rules are never counted as governed
        if r["disposition"] == "REGISTRY-ELIGIBLE":
            assert r["implementation_layers"]["enforcement_integrated"] == "NO"


def test_eligible_rules_carry_a_narrowing_relation_and_evidence():
    for r in RULES:
        if r["disposition"] in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED"):
            assert r["proposed_narrowing_semantics"], r["rule_id"]
            assert r["evidence_references"] and r["current_source_locations"], r["rule_id"]
            assert r["configurable"] == "YES" and r["registry_appropriate"] == "YES", r["rule_id"]
            assert r["parameter_count"] >= 1, r["rule_id"]


def test_ledgers_equal_a_fresh_recomputation_from_the_evidence():
    out = RECONCILE.build()
    assert out["errors"] == []
    fresh = RECONCILE.render(out)
    for name in RECONCILE.OUTPUT_NAMES:
        assert (AUD / name).read_text() == fresh[name], name
    reports = RENDER.build_reports()
    for name in RENDER.REPORTS:
        assert (AUD / name).read_text() == reports[name], name


def test_worker_evidence_is_complete_for_every_shard():
    for shard in RECONCILE.HIST_SHARDS + ["H1", "H2"]:
        inp = [json.loads(x) for x in (AUD / "worker-evidence" / "shards" / f"{shard}.jsonl").read_text().splitlines()]
        out = [json.loads(x) for x in (AUD / "worker-evidence" / f"{shard}.jsonl").read_text().splitlines()]
        key = "group" if shard.startswith("H") else "id"
        want = [x["group"]["group_id"] if key == "group" else x["id"] for x in inp]
        got = [x["group_id"] if key == "group" else x["id"] for x in out]
        assert want == got, shard
    for name in ("I1", "I2", "I3"):
        assert {"repos", "candidate_sites", "coverage_limits"} <= set(json.loads((AUD / "worker-evidence" / f"{name}.json").read_text()))


def test_every_cross_check_disagreement_is_dispositioned():
    resolutions = {x["item"]: x for x in ADJ.get("cross_check_resolutions", [])}
    for name in sorted((AUD / "worker-evidence").glob("J*.jsonl")):
        for line in name.read_text().splitlines():
            x = json.loads(line)
            key = x.get("rule_id") or x["id"]
            verdict = x.get("claim_verdict") or x.get("verdict")
            if verdict in ("FALSIFIED", "DOWNGRADE", "UPGRADE", "SPLIT", "MERGE"):
                assert key in resolutions, f"{name.name}:{key} cross-check disagreement not dispositioned"
            if x.get("claim_verdict") is None and x.get("verdict") is None:  # J1 blind re-audit: compare to the final row disposition
                final = next(r for r in ROWS if r["id"] == x["id"])["disposition"]
                if x["disposition"] != final:
                    assert x["id"] in resolutions, f"{name.name}:{x['id']} blind re-audit disagrees with final {final} and is not dispositioned"


def test_frozen_g0_and_s02_evidence_is_byte_identical_to_the_pinned_baseline():
    pins = json.loads((AUD / "frozen-blob-pins.json").read_text())["blobs"]
    assert len(pins) == 38
    for rel, blob in pins.items():
        data = (ROOT / rel).read_bytes()
        assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == blob, rel


def test_holds_and_non_authorization_are_preserved():
    readme = (AUD / "README.md").read_text()
    for needle in ("Release: HOLD", "Publication: HOLD", "Production: HOLD", "NOT independent Tier 1 qualification", "does not modify"):
        assert needle in readme, needle
    for name in RENDER.REPORTS:
        assert "HOLD" in (AUD / name).read_text()
