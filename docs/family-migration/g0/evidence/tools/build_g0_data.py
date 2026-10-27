#!/usr/bin/env python3
"""Assemble G0 machine-readable deliverables from worker outputs + mechanical crosswalk. Usage: build_g0_data.py <g0-out> <registry-checkout>"""
import json, sys, collections
from pathlib import Path
OUT = Path(sys.argv[1]); REG = Path(sys.argv[2]); DEST = REG / "docs" / "family-migration" / "g0"
DEST.mkdir(parents=True, exist_ok=True)
J = lambda p: json.load(open(p))

BASE = {
 "cogno-us/cognous-ocs-registry": "317eb76acb2847c534c3ce7c2180b89b4aef987d",
 "cogno-us/cognous-control-plane": "d66ae07fa240510efdcc11ed4b3e1189dcefc822",
 "cogno-us/cognous-execution-runtime": "0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491",
 "cogno-us/cognous-stack-qualification": "bb9b08904192b5f50a49e00ed8de0cab80fd7c19",
}
# ---- candidates
recs = []
EMPTYABLE = ('dependencies','missing_negative_oracles','existing_tests','required_contract_change','registry_coverage','constitutional_constraints','non_widening','symbol','snippet')
for L in "ABCD":
    for x in J(OUT / L / "candidates.json"):
        x = dict(x); x["worker"] = L; x["repository"] = x["repository"] if "/" in x["repository"] else "cogno-us/" + x["repository"]; x["proposed_disposition_worker"] = x["proposed_disposition"]
        x["lead_review"] = None
        for k in EMPTYABLE:
            if x.get(k) in (None, "", []): x[k] = "NONE RECORDED (worker left the field empty)"; x.setdefault("empty_fields_normalized", []).append(k)
        recs.append(x)
byid = {r["rule_id"]: r for r in recs}
assert len(byid) == len(recs) == 116
# lead adjustments (logged)
byid["G0-C-037"]["proposed_disposition"] = "ELIGIBLE-NOT-MIGRATED"
byid["G0-C-037"]["lead_review"] = ("Worker proposed OUT-OF-SCOPE/low priority (Tier 3 supportable for this repository). Lead aligns the disposition with the approved "
    "wave M8 (F10) as ELIGIBLE-NOT-MIGRATED; tier stays 'Tier 2 minimum until reviewed' per S02 section 3; priority low; Architect to confirm tier.")

GROUPS = {
 "RG-F1A-ALLOW-SETS-FIVE": ("F1a/F1b", "The five allow-sets (actions, adapters, units, institutions, authority domains): Registry f1ab record, Runtime policy fields, effect-time containment guard, narrowing adapter", "ALREADY-GOVERNED", ["G0-A-001","G0-A-002","G0-B-009","G0-B-010","G0-B-012","G0-B-013"]),
 "RG-F1C-MAX-AMOUNT": ("F1c", "max_amount numeric ceiling (Registry: no slot; Runtime: caller-owned; action-manifest: per-action ceiling)", "ELIGIBLE-NOT-MIGRATED", ["G0-A-003","G0-B-007","G0-D-001"]),
 "RG-F1C-MAX-EFFECTS": ("F1c", "max_effects numeric ceiling (Registry: no slot; Runtime: caller-owned)", "ELIGIBLE-NOT-MIGRATED", ["G0-A-004","G0-B-008"]),
 "RG-F1D-TARGET-PREFIXES": ("F1d", "allowed_target_prefixes / allowed targets (Registry: no slot; Runtime: caller-owned; action-manifest: allowed_targets)", "ELIGIBLE-NOT-MIGRATED", ["G0-A-005","G0-B-006","G0-D-002"]),
 "RG-F1D-TARGET-MATCH": ("F1d", "target_match mode choice (segment|exact|legacy-prefix); the closed vocabulary itself is F2 and stays in code", "ELIGIBLE-NOT-MIGRATED", ["G0-A-006","G0-B-004"]),
 "RG-F9-TENANT-LENGTH": ("F9", "tenant_id length bound 128 (Runtime, Control Plane x5 sites, action-manifest)", "RETAIN-IN-CODE", ["G0-B-003","G0-C-035","G0-D-004"]),
 "RG-F4-OBSERVATION-POLICY": ("F4", "Destination observation age/tolerance (300/5 literal in acp run; required ctor field; importer-recorded copy)", "ELIGIBLE-NOT-MIGRATED", ["G0-C-001","G0-C-002","G0-D-011"]),
 "RG-F11-REDACTION-DEFAULTS": ("F11", "Redaction defaults (Control Plane RedactionConfig; action-manifest hint string; replay-bundle keyword defaults)", "ELIGIBLE-NOT-MIGRATED", ["G0-C-038","G0-D-007","G0-D-012"]),
 "RG-F6-ACTION-LISTS": ("F6", "Agent/action permission lists (Runtime permissions.json legacy; action-manifest authority_required and tools.allowed)", "UNRESOLVED", ["G0-B-014","G0-D-008"]),
 "RG-F7-DEDUPE": ("F7", "Dedupe/replay TTL (Runtime dedupe_ttl_seconds; Control Plane DedupeProfile)", "UNRESOLVED", ["G0-B-015","G0-C-022"]),
}
rg = {}
member_of = {}
for gid, (fam, summ, disp, ids) in GROUPS.items():
    for i in ids: assert i in byid and i not in member_of; member_of[i] = gid
    rg[gid] = {"group_id": gid, "family": fam, "summary": summ, "lead_disposition": disp, "record_ids": ids}
for r in recs:
    gid = member_of.get(r["rule_id"], "RG-" + r["rule_id"][3:])
    r["rule_group"] = gid
    if gid not in rg:
        rg[gid] = {"group_id": gid, "family": r["family"], "summary": r["value_summary"][:160], "lead_disposition": r["proposed_disposition"], "record_ids": [r["rule_id"]]}
    r["related_rule_ids"] = [i for i in rg[gid]["record_ids"] if i != r["rule_id"]]
    r["lead_disposition"] = r["proposed_disposition"]
    r["disposition_status"] = "PROPOSED - not ratified; Architect decision required before any increment"
groups = list(rg.values())

# ---- families
def fp(part, disp, ids, note, override=None):
    return {"part": part, "disposition": disp, "record_ids": ids, "note": note, **({"lead_override_reason": override} if override else {})}
FAMILIES = [
 {"family": "F1a", "name": "Allow-sets: actions, adapters, units (3 of the 5 f1ab sets)", "plan_wave": "(migrated before this program: r08-v2 f1ab)", "parts": [
   fp("actions/adapters/units in f1ab", "ALREADY-GOVERNED", ["G0-A-001","G0-B-009","G0-B-012","G0-B-013"], "Registry r08-v2 f1ab narrows (intersection) with explicit [] deny-all; Runtime effect-time guard enforces F-01 subset on all five sets."),
   fp("frozen r08-v1/S04 file overlay (three keys, non-empty lists)", "OUT-OF-SCOPE", ["G0-A-015"], "Frozen historical overlay; unchanged by this program.")]},
 {"family": "F1b", "name": "Allow-sets: institutions, authority domains", "plan_wave": "M1", "parts": [
   fp("institutions/authority domains in f1ab", "ALREADY-GOVERNED", ["G0-A-002","G0-B-010","G0-B-012"], "Source conflict with Plan v1.0 M1 ('carried unchanged'): in r08-v2 f1ab both sets are validated, narrowed and may be deny-all like the other three (v2_f1ab.py F1AB_FIELDS). 'Carried unchanged' holds only for the frozen r08-v1/S04 overlay. Gap is evidence, not mechanism: decision-level narrowing/deny-all/exhaustive-grid negative oracles exist only for allowed_units.")]},
 {"family": "F1c", "name": "Numeric ceilings: max_amount, max_effects", "plan_wave": "M2", "parts": [
   fp("max_amount", "ELIGIBLE-NOT-MIGRATED", ["G0-A-003","G0-B-007","G0-D-001"], "No Registry slot (contract: 'no max_amount slot'; Amendment 3: caller-owned). Needs a new narrowing-only family or contract version; Runtime guard compares nothing for it today."),
   fp("max_effects", "ELIGIBLE-NOT-MIGRATED", ["G0-A-004","G0-B-008"], "Same as max_amount. Runtime ledger consumes max_effects from the provisioned claim (G0-B-017, retained).")]},
 {"family": "F1d", "name": "Target configuration: allowed_target_prefixes, target_match selection", "plan_wave": "M3", "parts": [
   fp("allowed_target_prefixes", "ELIGIBLE-NOT-MIGRATED", ["G0-A-005","G0-B-006","G0-D-002"], "No Registry slot; order relation (subset of prefixes vs extension semantics) is non-trivial."),
   fp("target_match mode choice", "ELIGIBLE-NOT-MIGRATED", ["G0-A-006","G0-B-004"], "Choice among three closed modes; narrowing order between modes must be defined (exact narrower than segment narrower than legacy-prefix is not proven in source).")]},
 {"family": "F2", "name": "Target-match vocabulary and separators", "plan_wave": "(stays in code)", "parts": [
   fp("mode vocabulary, separators, well-formedness", "RETAIN-IN-CODE", ["G0-B-005","G0-B-011"], "Evaluator semantics (safe_executor.py); W1-029 stays UNRESOLVED as a row, with a proposal that the closed vocabulary is IMMUTABLE_CONTROL.")]},
 {"family": "F3", "name": "Size/depth/timeout budgets", "plan_wave": "M6", "parts": [
   fp("admission and parsing floors", "RETAIN-IN-CODE", ["G0-A-010","G0-A-011","G0-A-013","G0-B-001","G0-B-002","G0-B-017","G0-B-023","G0-B-026","G0-B-028","G0-B-030","G0-D-005","G0-D-009","G0-D-010","G0-D-013","G0-D-016","G0-D-019","G0-D-028"], "Mandatory floors / fail-closed admission bounds; no config path may lower or raise them."),
   fp("host-owned lowering of non-admission resource budgets (OpenShell timeout, CLI input cap, manifest file cap, bounded-json defaults)", "UNRESOLVED", ["G0-B-027","G0-C-040","G0-D-006","G0-D-024"], "Workers proposed RETAIN-IN-CODE (conditional). Whether the Registry should carry resource budgets at all is a scope decision; none changes an authority decision.", "Lead keeps UNRESOLVED because the question is scope (Registry carrying resource budgets), not value-level eligibility."),
   fp("run-record caps supplied by the lease author", "OUT-OF-SCOPE", ["G0-D-026"], "Caller/author-supplied data in a hub reference profile.")]},
 {"family": "F4", "name": "Observation / status / approval freshness bounds", "plan_wave": "M11", "parts": [
   fp("status_max_age_seconds / approval_max_age_seconds scalars in Registry f4", "ALREADY-GOVERNED", ["G0-A-007","G0-A-009"], "r08-v2 f4 carries two ints (1..2147483647, min(caller, registry)); contradicts Plan v1.0 'F4 not covered'."),
   fp("identity/mandate ages and clock tolerance (Control Plane ctor defaults)", "ELIGIBLE-NOT-MIGRATED", ["G0-C-003","G0-C-004","G0-C-005","G0-C-006"], "Not carried by f4. Mapping decision needed: under a runtime-authority profile the class bound replaces the global status bound only for grant status; conflict and policy status keep the ctor bound."),
   fp("destination observation policy (300 s / 5 s)", "ELIGIBLE-NOT-MIGRATED", ["G0-C-001","G0-C-002","G0-D-011"], "Distinct concept from the 60 s authority-input bound; no code relates the two (60 vs 300 analysis in the exit report)."),
   fp("freshness profile: extension limit and anchor", "ELIGIBLE-NOT-MIGRATED", ["G0-C-019","G0-C-020"], "Opt-in profile members; extension 0 refuses all; anchor toggles deadline anchoring."),
   fp("freshness profile: liveness mechanics (lease, reaper, nonce)", "RETAIN-IN-CODE", ["G0-C-016","G0-C-017","G0-C-018","G0-C-007"], "Liveness/safeguard mechanics; nonce toggle is a safeguard; selection rule is evaluator semantics."),
   fp("Registry snapshot / selection validity windows (signed data)", "RETAIN-IN-CODE", ["G0-A-012"], "valid_from/valid_until are authenticated data inside records, not configuration."),
   fp("Runtime recovery freshness window (86400 s)", "ELIGIBLE-NOT-MIGRATED", ["G0-B-016"], "Inline literal at recovery_resolution.py; narrow-only lowering candidate. Tier conflict: worker rated it Tier 3, S02 section 3 tiers freshness bounds (F4) as Tier 1 (ruling needed)."),
   fp("freshness values in other repositories (hub, exchange, resolver assurance, federated governance)", "ELIGIBLE-NOT-MIGRATED", ["G0-D-015","G0-D-020","G0-D-021","G0-D-022"], "Scope confirmation required: these live in non-core repositories and reference profiles.")]},
 {"family": "F5", "name": "Per-action-class authority declarations", "plan_wave": "M12", "parts": [
   fp("class age map in Registry f5", "ALREADY-GOVERNED", ["G0-A-008","G0-C-021","G0-C-031"], "r08-v2 f5 carries class->age; policy-binding/0.1 ceilings and approval-generation binding already host-configured."),
   fp("unreadable behaviour, revocation assurance, reversibility, class declarations", "ELIGIBLE-NOT-MIGRATED", ["G0-C-008","G0-C-009","G0-C-010","G0-C-011"], "Host profile values; only narrowing directions can be Registry-governed; three-value UNKNOWN_BEHAVIORS has one gate branch."),
   fp("host trust configuration (producer keys, catalogue, signer sets, holder inventory)", "RETAIN-IN-CODE", ["G0-C-013","G0-C-014","G0-C-023","G0-C-032"], "Trust anchors and authority roots are never externalized."),
   fp("evidence criteria thresholds", "RETAIN-IN-CODE", ["G0-C-012"], "Arrive inside the issuer-approved authority context (CALLER_SUPPLIED), not host config."),
   fp("operation-identity labels", "OUT-OF-SCOPE", ["G0-C-015"], "Labels recorded on attempt rows; no policy effect.")]},
 {"family": "F6", "name": "Agent permission allow-list", "plan_wave": "M4", "parts": [
   fp("Runtime permissions.py/permissions.json", "OUT-OF-SCOPE", ["G0-B-014"], "Legacy/synthetic data file; not on the governed effect path."),
   fp("action-manifest authority_required and per-tool allow lists", "UNRESOLVED", ["G0-D-008"], "Live authored home of F6-like values; ownership and narrowing order undecided.")]},
 {"family": "F7", "name": "Dedupe / replay-window defaults", "plan_wave": "M5", "parts": [
   fp("Runtime dedupe_ttl_seconds", "OUT-OF-SCOPE", ["G0-B-015"], "Models provider dedupe horizon (provider fact), validated per destination."),
   fp("Control Plane DedupeProfile", "UNRESOLVED", ["G0-C-022"], "Policy versus provider fact undecided (worker C question).")]},
 {"family": "F8", "name": "Demo policy tool lists", "plan_wave": "M9", "parts": [
   fp("demo defaults and config file schema", "OUT-OF-SCOPE", ["G0-C-025","G0-C-027"], "Demo-only / inert (policy_config.default_action has no consumer)."),
   fp("authority-granting helpers and legacy PolicyGate evaluator", "RETAIN-IN-CODE", ["G0-C-026","G0-C-028","G0-C-029","G0-C-030"], "Demo grants confer authority (read/write); evaluator is protected semantics.")]},
 {"family": "F9", "name": "Tenant id length bound", "plan_wave": "M7", "parts": [
   fp("tenant_id <= 128 (Runtime admission, Control Plane sites)", "RETAIN-IN-CODE", ["G0-B-003","G0-C-035","G0-C-036"], "Identifier-shape admission bound repeated in 8 places across 3 repositories with no shared source; canonical binding restricts further. Narrowing config would desynchronize sites."),
   fp("action-manifest tenant bound", "UNRESOLVED", ["G0-D-004"], "Worker D rated CONDITIONAL; cross-repository single-source question undecided.")]},
 {"family": "F10", "name": "Diagnostic trend thresholds", "plan_wave": "M8", "parts": [
   fp("trend report keyword defaults (5, 1)", "ELIGIBLE-NOT-MIGRATED", ["G0-C-037"], "Non-gating diagnostic; no consumer influences an authority decision. Low priority.", "Worker proposed OUT-OF-SCOPE; lead aligns to approved wave M8.")]},
 {"family": "F11", "name": "Redaction defaults", "plan_wave": "M10", "parts": [
   fp("default values in action-manifest and replay-bundle", "ELIGIBLE-NOT-MIGRATED", ["G0-D-007","G0-D-012"], "Conditional: defaults only; confidentiality may only be tightened."),
   fp("Control Plane RedactionConfig, redaction mechanism, truncation", "RETAIN-IN-CODE", ["G0-C-038","G0-C-039","G0-C-041"], "Confidentiality controls stay code-enforced; configuration may only widen redaction.")]},
]
newfam = collections.OrderedDict()
for r in recs:
    if r["family"].startswith("NEW:"): newfam.setdefault(r["family"], []).append(r["rule_id"])
NEWFAMS = [{"family": f, "record_ids": ids, "dispositions": sorted({byid[i]["proposed_disposition"] for i in ids}),
            "eligibility": sorted({byid[i]["migration_eligibility"] for i in ids})} for f, ids in newfam.items()]
# vocabulary check
VOC = {"MIGRATED","ALREADY-GOVERNED","ELIGIBLE-NOT-MIGRATED","RETAIN-IN-CODE","OUT-OF-SCOPE","UNRESOLVED","BLOCKED"}
for f in FAMILIES:
    for p in f["parts"]:
        assert p["disposition"] in VOC
        for i in p["record_ids"]: assert i in byid, i
        if "lead_override_reason" not in p:
            assert p["disposition"] in {byid[i]["proposed_disposition"] for i in p["record_ids"]}, (f["family"], p["part"])
for r in recs: assert r["proposed_disposition"] in VOC
inparts = collections.Counter(i for f in FAMILIES for p in f["parts"] for i in p["record_ids"])
unplaced = [i for i, r in byid.items() if not r["family"].startswith("NEW:") and i not in inparts]
print("records in F-families but not placed in any part:", unplaced)
# ---- counts
def cnt(it): return dict(sorted(collections.Counter(it).items()))
rec_disp = cnt(r["proposed_disposition"] for r in recs); grp_disp = cnt(g["lead_disposition"] for g in groups)
counts = {"records": len(recs), "rule_groups": len(groups), "records_by_eligibility": cnt(r["migration_eligibility"] for r in recs), "records_by_disposition": rec_disp,
          "groups_by_disposition": grp_disp, "records_by_worker": cnt(r["worker"] for r in recs), "new_families": len(NEWFAMS),
          "new_families_with_non_retain_disposition": [n["family"] for n in NEWFAMS if set(n["dispositions"]) - {"RETAIN-IN-CODE", "OUT-OF-SCOPE"}]}
ledger = {"schema": "g0-candidate-ledger/1", "status": "PROPOSED; non-authorizing; dispositions require Architect ratification; no migration implemented",
          "baseline_pins": BASE, "disposition_vocabulary": sorted(VOC), "counts": counts, "records": recs, "rule_groups": groups, "families": FAMILIES, "new_families": NEWFAMS}
json.dump(ledger, open(DEST / "current-candidate-ledger.json", "w"), indent=1, sort_keys=False); print(json.dumps(counts, indent=1))

# ---- crosswalk
mech = {x["id"]: x for x in J(OUT / "crosswalk_mech.json")}
res = {}
for L in "BC":
    for x in J(OUT / L / "s02_resolution.json"): res[x["id"]] = (L, x)
CHANGED_NOTE = ("Lead reviewed the cited diff hunks old->current. Additive evolution (successor claim profile, authorization pin, approval-revocation table, policy-binding/0.1, "
                "typed selection-refusal evidence). Historical class retained; no reclassification proposed; not a configurable rule.")
rows = []
for rid, m in mech.items():
    st = m["mechanical_status"]
    xs = {"UNCHANGED": "UNCHANGED", "UNCHANGED_SHIFTED": "MOVED", "FILE_UNCHANGED_COORDINATE_UNMAPPED": "MOVED", "CHANGED": "CHANGED"}[st]
    m["crosswalk_status"] = xs
    m["coordinate_note"] = ("historical coordinate is cumulative per docs/s02-evidence/README.md errata; source file blob is identical at both pins; current per-file line range not mechanically mapped unless supplied by a worker resolution"
                            if st == "FILE_UNCHANGED_COORDINATE_UNMAPPED" else None)
    m["semantic_status"] = "CHANGED-ADDITIVE-CLASS-RETAINED" if st == "CHANGED" else "UNCHANGED-CONTENT"
    m["semantic_review"] = CHANGED_NOTE if st == "CHANGED" else None
    m["linked_candidate_rule_ids"] = sorted(r["rule_id"] for r in recs if rid in r["s02_rows"]) if True else []
    if rid in res:
        L, x = res[rid]
        m["g0_resolution"] = {"worker": L, "worker_status": x["current_status"], "current_file": x["current_file"], "current_lines": x["current_lines"], "evidence_snippet": x["evidence_snippet"],
                              "still_configurable": x["still_configurable"], "notes": x["notes"], "candidate_rule_ids": x["candidate_rule_ids"]}
        m["linked_candidate_rule_ids"] = sorted(set(m["linked_candidate_rule_ids"]) | set(x["candidate_rule_ids"]))
        if x["current_status"] == "MOVED" and xs == "UNCHANGED": m["crosswalk_status"] = "MOVED"
        m["worker_mechanical_agreement"] = (x["current_status"] == "UNCHANGED") == (m["crosswalk_status"] == "UNCHANGED")
    m["unresolved_tracking"] = None
    rows.append(m)
rowmap = {m["id"]: m for m in rows}
raw = {r["id"]: r for r in J(OUT / "s02_rows_raw.json")}
for rid, (L, x) in res.items():
    if x["historical_class"] == "UNRESOLVED":
        p = x["proposed_resolution_for_unresolved"]
        rowmap[rid]["unresolved_tracking"] = {"historical_class": "UNRESOLVED", "g0_status": "UNRESOLVED-PRESERVED", "historical_classification_changed": False, "proposed_resolution": p["text"],
            "proposal_evidence": p["evidence"], "proposal_confidence": p["confidence"], "worker_still_configurable": x["still_configurable"],
            "linked_candidate_rule_ids": x["candidate_rule_ids"], "ratification_required": True,
            "note": "Proposal only. The historical row stays UNRESOLVED until the Architect ratifies a resolution."}
for r in raw.values(): assert rowmap[r["id"]]["historical"]["class"] == r["cls"]
xcounts = {"rows": len(rows), "by_historical_class": cnt(m["historical"]["class"] for m in rows), "by_crosswalk_status": cnt(m["crosswalk_status"] for m in rows),
           "by_semantic_status": cnt(m["semantic_status"] for m in rows), "by_mechanical_status": cnt(m["mechanical_status"] for m in rows), "unresolved_tracked": sum(1 for m in rows if m["unresolved_tracking"]),
           "worker_resolved_rows": len(res), "worker_mechanical_disagreements": [m["id"] for m in rows if m.get("worker_mechanical_agreement") is False]}
cw = {"schema": "g0-historical-crosswalk/1", "status": "historical classifications copied unchanged; no silent reclassification; rows are not migration tasks",
      "old_pins": {"runtime": "ec728da6dc301a664b331ac8986afd6e850a1273", "control_plane": "0a41faa972699f7ec3063967a14cd9bdd3e67d27"},
      "current_pins": {"runtime": BASE["cogno-us/cognous-execution-runtime"], "control_plane": BASE["cogno-us/cognous-control-plane"]},
      "method": "Per-worker abbreviation table + git diff -U0 hunk mapping (tools/build_crosswalk.py); lead review of the 14 CHANGED rows; worker resolutions for the 75 CONFIGURABLE-CANDIDATE and UNRESOLVED rows",
      "counts": xcounts, "rows": rows}
json.dump(cw, open(DEST / "historical-crosswalk.json", "w"), indent=1); print(json.dumps(xcounts, indent=1))
