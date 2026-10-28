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
PARAMS = _load(AUD / "tools" / "build_parameters.py", "audit_params")
CROSS = json.loads((G0 / "historical-crosswalk.json").read_text())
LEDGER = json.loads((G0 / "current-candidate-ledger.json").read_text())
ROWS = json.loads((AUD / "crosswalk.json").read_text())["rows"]
RULES = json.loads((AUD / "rule-catalogue.json").read_text())["rules"]
REC = json.loads((AUD / "reconciliation.json").read_text())
SUMMARY = REC["summary"]
BY_RULE = {r["rule_id"]: r for r in RULES}
ADJ = json.loads((AUD / "lead-adjudications.json").read_text())
PCAT = json.loads((AUD / "parameter-catalogue.json").read_text())
PSUM = PCAT["summary"]
PARAMETERS = PCAT["parameters"]
COUNTED = [p for p in PARAMETERS if p["counted"]]
MANAGEABLE = [p for p in COUNTED if p["eligibility"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE")]


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
    assert {"RG-F1A-ALLOW-SETS-FIVE", "RG-F1C-MAX-AMOUNT", "RG-F1C-MAX-EFFECTS", "LR-F1D-TARGET-POLICY"} == names
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
    pdata, pout = PARAMS.outputs()
    assert pdata["errors"] == []
    for name in pout:
        assert (AUD / name).read_text() == pout[name], name


def test_worker_evidence_is_complete_for_every_shard():
    for shard in RECONCILE.HIST_SHARDS + ["H1", "H2"]:
        inp = [json.loads(x) for x in (AUD / "worker-evidence" / "shards" / f"{shard}.jsonl").read_text().splitlines()]
        out = [json.loads(x) for x in (AUD / "worker-evidence" / f"{shard}.jsonl").read_text().splitlines()]
        key = "group" if shard.startswith("H") else "id"
        want = [x["group"]["group_id"] if key == "group" else x["id"] for x in inp]
        got = [x["group_id"] if key == "group" else x["id"] for x in out]
        assert want == got, shard
    for name in ("I1", "I2", "I3", "I4"):
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


# ---- pass 2: parameter-level integrity ------------------------------------------------------------------------------------------------

def test_every_parameter_has_one_stable_identity_and_one_canonical_rule():
    ids = [p["parameter_id"] for p in PARAMETERS]
    assert len(ids) == len(set(ids)) > 0
    assert all(p["canonical_rule_id"] in BY_RULE for p in PARAMETERS)
    assert all(p["eligibility"] in VOC for p in COUNTED)
    for field in PARAMS.FIELDS:
        assert all(field in p for p in PARAMETERS), field


def test_composites_duplicates_and_invariants_are_never_counted():
    assert {p["unit_type"] for p in COUNTED} == {"PARAMETER"}
    assert all(p["unit_type"] in ("COMPOSITE_MEMBER", "SITE_DUPLICATE", "INVARIANT_NOT_PARAMETER") for p in PARAMETERS if not p["counted"])
    assert len(COUNTED) == PSUM["distinct_configurable_parameters"]
    assert sum(PSUM["parameters_by_eligibility"].values()) == len(COUNTED)


def test_manageable_parameters_and_manageable_rules_reconcile():
    assert all(BY_RULE[p["canonical_rule_id"]]["disposition"] == p["eligibility"] for p in MANAGEABLE)
    man_rules = [r for r in RULES if r["disposition"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE")]
    assert sum(r["parameter_count"] for r in man_rules) == len(MANAGEABLE) == PSUM["manageable_parameters"]
    assert {p["canonical_rule_id"] for p in MANAGEABLE} == {r["rule_id"] for r in man_rules} and len(man_rules) == PSUM["manageable_rules"]
    assert PSUM["canonical_rules"] == len(RULES) == SUMMARY["canonical_rules_total"]
    assert PSUM["manageable_governed_parameters"] == SUMMARY["registry_governed_parameters"]
    assert PSUM["manageable_eligible_parameters"] == SUMMARY["registry_eligible_parameters"]


def test_nine_f1abcd_members_are_counted_once_and_layers_are_evidence_backed():
    governed = [p for p in MANAGEABLE if p["eligibility"] == "REGISTRY-GOVERNED"]
    assert len(governed) == 9 and len({p["parameter_id"] for p in governed}) == 9
    assert {p["narrowing_unit"] for p in governed if p["canonical_rule_id"] == "LR-F1D-TARGET-POLICY"} == {"NU-F1D-TARGET-SCOPE"}
    assert all(p["registry_represented"] == "YES" and p["enforcement_integrated"] == "YES" for p in governed)
    for p in MANAGEABLE:
        assert p["independently_accepted"] == "NO"
        if p["eligibility"] == "REGISTRY-ELIGIBLE":
            assert p["enforcement_integrated"] == "NO", p["parameter_id"]
        assert p["evidence"] and p["source_path"], p["parameter_id"]
    assert PSUM["independently_accepted_parameters"] == 0


def test_blocked_and_unresolved_are_excluded_from_the_manageable_numerator_but_reported():
    assert not {p["parameter_id"] for p in MANAGEABLE} & (set(PSUM["blocked_parameter_ids"]) | set(PSUM["unresolved_parameter_ids"]))
    assert PSUM["blocked_parameters"] == len(PSUM["blocked_parameter_ids"]) == sum(1 for p in COUNTED if p["eligibility"] == "BLOCKED")
    assert PSUM["unresolved_parameters"] == len(PSUM["unresolved_parameter_ids"]) == sum(1 for p in COUNTED if p["eligibility"] == "UNRESOLVED")


def test_every_percentage_is_recomputed_from_counts_with_an_explicit_denominator():
    for x in PSUM["percentages"]:
        assert x["denominator"] and x["label"]
        assert x["percent"] == round(100.0 * x["numerator"] / x["denominator"], 1), x["label"]
    labels = {x["label"]: x for x in PSUM["percentages"]}
    assert labels["Registry-manageable parameters / candidate configurable parameters"]["numerator"] == len(MANAGEABLE)
    assert labels["Registry-manageable parameters / candidate configurable parameters"]["denominator"] == len(COUNTED)
    assert labels["Manageable rules / all canonical rules"]["denominator"] == len(RULES)


def test_pass2_worker_outputs_are_retained_and_h_challenges_are_answered():
    for name in ("A.jsonl", "B.jsonl", "C.json", "D.jsonl", "E.jsonl", "F.json", "G.jsonl", "H.json"):
        assert (AUD / "worker-evidence" / "pass2" / name).exists(), name
    answered = {x["id"] for x in ADJ.get("pass2_h_resolutions", [])}
    h = json.loads((AUD / "worker-evidence" / "pass2" / "H.json").read_text())
    assert all(c["id"] in answered for c in h["challenges"]), [c["id"] for c in h["challenges"] if c["id"] not in answered]
