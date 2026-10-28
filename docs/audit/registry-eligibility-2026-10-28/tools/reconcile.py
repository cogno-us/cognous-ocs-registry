#!/usr/bin/env python3
"""Deterministic reconciliation for the independent Registry eligibility audit (read-only on all inputs).

Inputs : worker-evidence/*.jsonl|json (raw worker outputs), lead-adjudications.json (explicit lead decisions),
         docs/family-migration/g0/{historical-crosswalk,current-candidate-ledger}.json (frozen G0 evidence, never modified).
Outputs: crosswalk.json, rule-catalogue.json, source-site-map.json, reconciliation.json (all totals are computed here, never typed).
Usage  : python3 reconcile.py [--check]   (--check recomputes in memory and fails if the committed outputs differ)
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUD = HERE.parent
ROOT = AUD.parents[2]
WE = AUD / "worker-evidence"
G0 = ROOT / "docs" / "family-migration" / "g0"
M2_BACKLOG = ROOT / "docs" / "family-migration" / "m2" / "01-migration-backlog.md"

HIST_SHARDS = ["A", "B", "C", "D1", "D2", "D3", "D4", "F1", "F2", "G"]
DISPOSITIONS = ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "RETAIN-IN-CODE", "CALLER-OR-ISSUER-OWNED", "PROVIDER-OR-HOST-OWNED",
                "OUT-OF-SCOPE", "UNRESOLVED", "BLOCKED")
S02_CLASSES = {"MANDATORY-INVARIANT": 354, "SERIALIZATION-OR-EVIDENCE": 90, "REFUSAL-OR-REASON-VOCABULARY": 50,
               "INCIDENTAL-CONDITIONAL": 51, "CONFIGURABLE-CANDIDATE": 43, "UNRESOLVED": 32}
G0_COUNTS = {"records": 116, "groups": 97}
OUTPUT_NAMES = ("crosswalk.json", "rule-catalogue.json", "source-site-map.json", "reconciliation.json")


def jl(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def dump(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def load_inputs():
    cw = json.loads((G0 / "historical-crosswalk.json").read_text())
    led = json.loads((G0 / "current-candidate-ledger.json").read_text())
    adj = json.loads((AUD / "lead-adjudications.json").read_text())
    worker = {}
    for s in HIST_SHARDS:
        for r in jl(WE / f"{s}.jsonl"):
            r["_shard"] = s
            worker[r["id"]] = r
    hgroups = {}
    for s in ("H1", "H2"):
        for h in jl(WE / f"{s}.jsonl"):
            h["_shard"] = s
            hgroups[h["group_id"]] = h
    icov = {n: json.loads((WE / f"{n}.json").read_text()) for n in ("I1", "I2", "I3", "I4") if (WE / f"{n}.json").exists()}
    return cw, led, adj, worker, hgroups, icov


def parse_waves():
    """group name -> wave, from the (read-only) M2 backlog table of the 23 G0 eligible groups."""
    waves = {}
    for line in M2_BACKLOG.read_text().splitlines():
        m = re.match(r"\|\s*\d+\s*\|\s*(RG-[A-Z0-9-]+)\s*\|", line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            waves[m.group(1)] = cells[-1]
    return waves


def normalize_disposition(base, impl, integrated):
    """Taxonomy rule: GOVERNED = implemented AND integrated at the enforcement boundary; represented-only stays ELIGIBLE."""
    if base in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED"):
        return "REGISTRY-GOVERNED" if (impl == "IMPLEMENTED" and integrated == "YES") else "REGISTRY-ELIGIBLE"
    return base


def humanize(key):
    return key.split(":", 1)[-1].replace("-", " ").replace("/", " / ")


def build():
    cw, led, adj, worker, hgroups, icov = load_inputs()
    errors = []
    cw_rows = {r["id"]: r for r in cw["rows"]}
    waves = parse_waves()
    ledger_rec = {r["rule_id"]: r for r in led["records"]}
    g0_group = {g["group_id"]: g for g in led["rule_groups"]}
    rec_to_group = {rid: g["group_id"] for g in led["rule_groups"] for rid in g["record_ids"]}

    # ---- input integrity -------------------------------------------------------------------------------------------------
    if sorted(cw_rows) != sorted(worker):
        errors.append("worker rows do not cover exactly the 620 frozen historical ids")
    for rid, r in worker.items():
        if r["orig_class"] != cw_rows[rid]["historical"]["class"]:
            errors.append(f"{rid}: original class changed")
        if r["disposition"] not in DISPOSITIONS:
            errors.append(f"{rid}: bad disposition {r['disposition']}")

    # ---- canonical key assignment (workers' keys + explicit lead re-keys) --------------------------------------------------
    row_key = {rid: worker[rid]["canonical_rule_key"] for rid in worker}
    for rid, spec in adj.get("row_rekeys", {}).items():
        if rid not in row_key:
            errors.append(f"rekey for unknown row {rid}")
        row_key[rid] = spec["canonical_key"]
    merge_into = {}
    for m in adj.get("merges", []):
        for mem in m["members"]:
            merge_into[mem] = m["into"]
    def resolve(k):
        return merge_into.get(k, k)
    row_rule = {rid: resolve(k) for rid, k in row_key.items()}

    # ---- rule skeletons ------------------------------------------------------------------------------------------------------
    rules = {}
    def rule(rid):
        if rid not in rules:
            rules[rid] = {"rule_id": rid, "historical_ids": [], "g0_group_ids": [], "g0_record_ids": [], "member_keys": [], "sites": [],
                          "origin": None, "coverage_sites": []}
        return rules[rid]
    for rid, k in row_rule.items():
        r = rule(k)
        r["historical_ids"].append(rid)
        r["origin"] = "HISTORICAL"
    # G0 groups -> rules (merged members are absorbed, split records are re-homed below)
    split_of = {}
    for sp in adj.get("splits", []):
        for rec in sp["records"]:
            split_of[rec] = sp["new"]
    for gid, g in g0_group.items():
        target = resolve(gid)
        r = rule(target)
        r["g0_group_ids"].append(gid)
        r["member_keys"].append(gid)
        for rec in g["record_ids"]:
            dest = rule(split_of[rec]) if rec in split_of else r
            dest["g0_record_ids"].append(rec)
            if rec in split_of and dest["origin"] is None:
                dest["origin"] = "LEAD-SPLIT"
        if r["origin"] is None:
            r["origin"] = "G0-CURRENT-ONLY"
        elif r["origin"] == "HISTORICAL":
            r["origin"] = "HISTORICAL+G0"
    for rid, r in rules.items():
        if rid.startswith("LR-") and r["origin"] == "HISTORICAL":
            r["origin"] = "HISTORICAL"
        if rid in adj.get("rule_overrides", {}) and "name" in adj["rule_overrides"][rid]:
            r["name_override"] = adj["rule_overrides"][rid]["name"]
    for m in adj.get("merges", []):
        rule(m["into"])["name_override"] = m["name"]
    # newly discovered sites from repository coverage workers
    for wid, cov in icov.items():
        for s in cov["candidate_sites"]:
            key = s["key"]
            r = rule(key)
            r["coverage_sites"].append({**s, "worker": wid})
            if r["origin"] is None:
                r["origin"] = "REPO-COVERAGE"
    for sp in adj.get("splits", []):
        r = rule(sp["new"])
        r["origin"] = "LEAD-SPLIT"
        r["name_override"] = sp["name"]
        r["split_from"] = sp["from"]

    # ---- dispositions ---------------------------------------------------------------------------------------------------------
    for rid, r in sorted(rules.items()):
        rows = [worker[x] for x in r["historical_ids"]]
        audits = [hgroups[g] for g in r["g0_group_ids"] if g in hgroups]
        r["_audits"] = audits
        r["_rows"] = rows
        cand = None
        why = None
        if rid in adj.get("split_dispositions", {}):
            cand, why = adj["split_dispositions"][rid]["disposition"], "LEAD-SPLIT: " + adj["split_dispositions"][rid]["reason"]
        elif rid in adj.get("rule_overrides", {}) and "disposition" in adj["rule_overrides"][rid]:
            cand, why = adj["rule_overrides"][rid]["disposition"], "LEAD-OVERRIDE: " + adj["rule_overrides"][rid]["reason"]
        elif audits:
            disps = {normalize_disposition(a["audit_disposition"], a["implementation_status"], a["enforcement_boundary_integrated"]) for a in audits}
            if len(disps) != 1:
                errors.append(f"{rid}: merged group audits disagree {sorted(disps)}")
            cand, why = sorted(disps)[0], "H-WORKER GROUP AUDIT"
        elif rows or r["coverage_sites"]:
            vals = {x["disposition"] for x in rows} | {x["preliminary_disposition"] for x in r["coverage_sites"]}
            if len(vals) != 1:
                errors.append(f"{rid}: unadjudicated disagreement {sorted(vals)}")
            cand, why = sorted(vals)[0], "UNANIMOUS WORKER ROWS" if rows else "REPO-COVERAGE WORKER"
        else:
            errors.append(f"{rid}: no basis for a disposition")
        r["disposition"] = cand
        r["disposition_basis"] = why

    # ---- row-level reconciliation (a row inherits its rule's disposition; contradictions must be explicit) ---------------------
    crosswalk = []
    contradictions = []
    for rid in sorted(worker):
        w = worker[rid]
        h = cw_rows[rid]
        rl = rules[row_rule[rid]]
        row_disp = rl["disposition"]
        spec = adj.get("row_disposition_overrides", {}).get(rid)
        if spec:
            row_disp = spec["disposition"]
        elif w["disposition"] != row_disp:
            sevl = {"REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED"}
            if w["disposition"] == "RETAIN-IN-CODE" and row_disp in sevl:
                contradictions.append(f"{rid}: worker RETAIN-IN-CODE but rule {rl['rule_id']} is {row_disp} (needs re-key or override)")
        crosswalk.append({
            "id": rid, "repository": h["repository"], "worker_shard": w["_shard"],
            "historical_class": h["historical"]["class"], "historical_tier": h["historical"].get("tier"),
            "historical_loc": h["historical"].get("loc"), "historical_construct": h["historical"].get("construct"),
            "crosswalk_status_g0": h["crosswalk_status"],
            "g0_record_links": h.get("linked_candidate_rule_ids") or [],
            "source_status": w["source_status"], "current_locations": w["current_locations"],
            "worker_disposition": w["disposition"], "disposition": row_disp,
            "disposition_differs_from_worker": row_disp != w["disposition"],
            "canonical_rule_id": rl["rule_id"], "worker_canonical_key": w["canonical_rule_key"],
            "rekeyed_by_lead": rid in adj.get("row_rekeys", {}),
            "merge_basis": w["merge_basis"], "configurable": w["configurable"], "registry_appropriate": w["registry_appropriate"],
            "config_owner": w["config_owner"], "controls": w["controls"], "widening_risk": w["widening_risk"],
            "narrowing_relation": w["narrowing_relation"], "existing_registry_coverage": w["existing_registry_coverage"],
            "child_params": w["child_params"], "confidence": w["confidence"], "evidence": w["evidence"],
            "blocking_decision": w["blocking_decision"], "worker_note": w["note"],
            "reclassified_vs_historical_class": bool(w["reclassified_vs_historical"]),
            "lead_adjudication": (adj.get("row_rekeys", {}).get(rid) or spec or {}).get("reason"),
        })
    errors.extend(contradictions)

    # ---- rule catalogue -------------------------------------------------------------------------------------------------------
    catalogue = []
    for rid, r in sorted(rules.items()):
        rows, audits = r["_rows"], r["_audits"]
        recs = [ledger_rec[x] for x in r["g0_record_ids"] if x in ledger_rec]
        cfgs = {x["configurable"] for x in rows} | ({a["configurable"] for a in audits}) | {x["configurable"] for x in r["coverage_sites"]}
        apps = {x["registry_appropriate"] for x in rows} | ({a["registry_appropriate"] for a in audits})
        def agg(vs):
            vs = {v for v in vs if v}
            if "YES" in vs:
                return "YES"
            if "UNKNOWN" in vs or not vs:
                return "UNKNOWN" if vs else "NO"
            return "NO"
        disp = r["disposition"]
        spec = adj.get("rule_attributes", {}).get(rid, {})
        configurable = spec.get("configurable") or (agg(cfgs) if disp in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED", "UNRESOLVED", "BLOCKED") else (
            "YES" if "YES" in cfgs else ("UNKNOWN" if "UNKNOWN" in cfgs else "NO")))
        registry_app = spec.get("registry_appropriate") or ("YES" if disp in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED") else (
            "UNKNOWN" if disp in ("UNRESOLVED", "BLOCKED") else "NO"))
        impl = spec.get("implementation_status")
        if impl is None:
            if audits:
                impl = sorted({a["implementation_status"] for a in audits})[0] if len({a["implementation_status"] for a in audits}) == 1 else "NOT-STARTED"
            else:
                impl = "NOT-STARTED" if disp in ("REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED") else ("IMPLEMENTED" if disp == "REGISTRY-GOVERNED" else "N/A")
        if disp == "REGISTRY-ELIGIBLE" and impl == "IMPLEMENTED":
            layers = {"registry_represented": "YES", "enforcement_integrated": "NO", "independently_accepted": "NO"}
        elif disp == "REGISTRY-GOVERNED":
            layers = {"registry_represented": "YES", "enforcement_integrated": "YES", "independently_accepted": "NO"}
        elif disp == "REGISTRY-ELIGIBLE":
            layers = {"registry_represented": "NO", "enforcement_integrated": "NO", "independently_accepted": "NO"}
        else:
            layers = None
        if layers and "layers" in spec:
            layers = spec["layers"]
        mig_status = "N/A"
        if disp == "REGISTRY-GOVERNED":
            mig_status = "IMPLEMENTED"
        elif disp in ("REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED"):
            mig_status = "NOT-STARTED" if impl != "IMPLEMENTED" else "NOT-STARTED"
        g0_disp = sorted({g0_group[g]["lead_disposition"] for g in r["g0_group_ids"]})
        blocks = []
        for src in [a.get("blocking_decision") for a in audits] + [x["blocking_decision"] for x in rows]:
            if src and src not in blocks:
                blocks.append(src)
        blocks = [b for b in spec.get("blocking", [])] + [b for b in blocks if b not in spec.get("blocking", [])]
        sites = []
        seen = set()
        for x in rows:
            for loc in x["current_locations"]:
                k = (loc.get("repo"), loc.get("file"), str(loc.get("lines")))
                if k not in seen:
                    seen.add(k)
                    sites.append({"repo": loc.get("repo"), "sha": loc.get("sha"), "file": loc.get("file"), "lines": loc.get("lines"),
                                  "symbol": loc.get("symbol"), "via": "historical-row:" + x["id"]})
        for rec in recs:
            k = (rec["repository"], rec["file"], str(rec["lines"]))
            if k not in seen:
                seen.add(k)
                sites.append({"repo": rec["repository"], "sha": rec["source_sha"], "file": rec["file"], "lines": rec["lines"], "symbol": rec["symbol"],
                              "via": "g0-record:" + rec["rule_id"]})
        for cs in r["coverage_sites"]:
            sites.append({"repo": cs["repo"], "sha": cs["sha"], "file": cs["file"], "lines": cs["lines"], "symbol": None, "via": "coverage-worker:" + cs["worker"]})
        for a in audits:
            for mc in a.get("missing_consumer_paths") or []:
                sites.append({"repo": mc.get("repo"), "sha": None, "file": mc.get("file"), "lines": mc.get("lines"), "symbol": None,
                              "via": "missing-consumer-path:" + a["group_id"], "note": mc.get("note")})
        first_rec = recs[0] if recs else None
        name = r.get("name_override") or (g0_group[r["g0_group_ids"][0]]["summary"] if r["g0_group_ids"] and r["g0_group_ids"][0] in g0_group
                                          and not r["rule_id"].startswith("LR-") else humanize(rid))
        if r["rule_id"].startswith("RG-") and not r.get("name_override") and r["g0_group_ids"]:
            name = g0_group[r["g0_group_ids"][0]]["summary"]
        components = sorted({s["repo"] for s in sites if s.get("repo")} | {x["repository"] for x in [cw_rows[i] for i in r["historical_ids"]]})
        owners = sorted({x["config_owner"] for x in rows if x.get("config_owner")} | {x["config_owner"] for x in r["coverage_sites"] if x.get("config_owner")} |
                        {x for x in [a.get("config_owner") for a in audits] if x} | ({first_rec["config_owner_and_source"]} if first_rec else set()))
        wave = None
        for g in r["g0_group_ids"]:
            wave = wave or waves.get(g)
        if disp == "REGISTRY-ELIGIBLE" and impl != "IMPLEMENTED":
            wave = spec.get("migration_wave") or wave or "PROPOSED-UNASSIGNED"
        if disp == "REGISTRY-GOVERNED":
            wave = spec.get("migration_wave") or wave or "COMPLETED-IMPLEMENTED"
        evidence = sorted({x["evidence"] for x in rows if x.get("evidence")} | {a["evidence"] for a in audits if a.get("evidence")} |
                          {x["evidence"] for x in r["coverage_sites"] if x.get("evidence")})
        confs = [x["confidence"] for x in rows] + [a["confidence"] for a in audits] + [x["confidence"] for x in r["coverage_sites"]]
        order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        confidence = min(confs, key=lambda c: order.get(c, 0)) if confs else "MEDIUM"
        gv = sorted({a["grouping_verdict"] for a in audits})
        entry = {
            "rule_id": rid, "name": name, "origin": r["origin"], "kind": ("PARAMETER" if disp in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE") else "RULE"),
            "historical_source_ids": sorted(r["historical_ids"]), "g0_group_ids": sorted(r["g0_group_ids"]), "g0_record_ids": sorted(r["g0_record_ids"]),
            "split_from": r.get("split_from"), "current_source_locations": sites, "component_owner": components, "configuration_owner": owners,
            "value_type": spec.get("value_type") or (first_rec["value_summary"][:240] if first_rec and disp in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED") else None),
            "valid_domain": spec.get("valid_domain"),
            "existing_behavior": spec.get("existing_behavior") or (first_rec["evaluator"][:240] if first_rec and disp in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED") else None),
            "proposed_narrowing_semantics": spec.get("narrowing") or (first_rec["non_widening"][:300] if first_rec and disp in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE") else None),
            "not_applicable_reason": (None if disp in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED") else
                                      f"{disp}: value/domain/narrowing attributes are not defined because the rule is not Registry-manageable"),
            "existing_registry_coverage": spec.get("coverage") or sorted({x["existing_registry_coverage"] for x in rows})[:3] or None,
            "disposition": disp, "disposition_basis": r["disposition_basis"], "configurable": configurable, "registry_appropriate": registry_app,
            "migration_status": mig_status, "implementation_layers": layers, "migration_eligibility": "ELIGIBLE" if disp in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED") else
            ("PENDING-DECISION" if disp in ("UNRESOLVED", "BLOCKED") else "NOT-ELIGIBLE"),
            "proposed_migration_wave": wave, "blocking_architectural_decisions": blocks, "evidence_references": evidence[:12], "confidence": confidence,
            "g0_dispositions": g0_disp, "differs_from_g0": bool(g0_disp) and not all(_g0_equiv(d, disp) for d in g0_disp),
            "grouping_verdicts": gv, "parameter_count": int(spec.get("parameters", 1)) if disp in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE") else 0,
            "in_g0_inventory": bool(r["g0_group_ids"] or r["g0_record_ids"]),
        }
        catalogue.append(entry)

    # ---- source-site map ------------------------------------------------------------------------------------------------------
    site_map = []
    for e in catalogue:
        for s in e["current_source_locations"]:
            site_map.append({"rule_id": e["rule_id"], **s})
    for rec in led["records"]:
        site_map.append({"rule_id": resolve(rec_to_group[rec["rule_id"]]) if rec["rule_id"] not in split_of else split_of[rec["rule_id"]],
                         "repo": rec["repository"], "sha": rec["source_sha"], "file": rec["file"], "lines": rec["lines"], "symbol": rec["symbol"],
                         "via": "g0-record:" + rec["rule_id"] + ":frozen-inventory"})

    # ---- reconciliation totals --------------------------------------------------------------------------------------------------
    by_disp = collections.Counter(e["disposition"] for e in catalogue)
    row_disp = collections.Counter(r["disposition"] for r in crosswalk)
    hist_class = collections.Counter(r["historical_class"] for r in crosswalk)
    row_to_rule = collections.defaultdict(list)
    for r in crosswalk:
        row_to_rule[r["canonical_rule_id"]].append(r["id"])
    gov = [e for e in catalogue if e["disposition"] == "REGISTRY-GOVERNED"]
    elig = [e for e in catalogue if e["disposition"] == "REGISTRY-ELIGIBLE"]
    represented_only = [e for e in elig if (e["implementation_layers"] or {}).get("registry_represented") == "YES"]
    cfg_relevant = [e for e in catalogue if e["configurable"] in ("YES", "UNKNOWN") or e["disposition"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED")]
    omitted = [e for e in catalogue if not e["in_g0_inventory"] and e["origin"] != "LEAD-SPLIT" and (
        e["disposition"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "UNRESOLVED", "BLOCKED") or e["configurable"] == "YES")]
    g0_groups_audit = collections.Counter(
        normalize_disposition(h["audit_disposition"], h["implementation_status"], h["enforcement_boundary_integrated"]) for h in hgroups.values())
    summary = {
        "historical_rows": len(crosswalk), "historical_rows_by_class": dict(sorted(hist_class.items())), "expected_s02_class_totals": S02_CLASSES,
        "rows_by_final_disposition": dict(sorted(row_disp.items())),
        "rows_by_worker_disposition": dict(sorted(collections.Counter(r["worker_disposition"] for r in crosswalk).items())),
        "rows_where_final_differs_from_worker": sum(1 for r in crosswalk if r["disposition_differs_from_worker"]),
        "rows_rekeyed_by_lead": sum(1 for r in crosswalk if r["rekeyed_by_lead"]),
        "rows_source_status": dict(collections.Counter(r["source_status"] for r in crosswalk)),
        "rows_reclassified_vs_historical_class_by_worker": sum(1 for r in crosswalk if r["reclassified_vs_historical_class"]),
        "canonical_rules_total": len(catalogue), "canonical_rules_by_origin": dict(sorted(collections.Counter(e["origin"] for e in catalogue).items())),
        "canonical_rules_by_disposition": dict(sorted(by_disp.items())),
        "canonical_rules_from_historical_rows": sum(1 for e in catalogue if e["historical_source_ids"]),
        "canonical_rules_g0_only_no_historical_row": sum(1 for e in catalogue if not e["historical_source_ids"] and e["in_g0_inventory"]),
        "canonical_rules_repo_coverage_only": sum(1 for e in catalogue if e["origin"] == "REPO-COVERAGE"),
        "registry_governed_rules": len(gov), "registry_governed_parameters": sum(e["parameter_count"] for e in gov),
        "registry_eligible_rules": len(elig), "registry_eligible_parameters": sum(e["parameter_count"] for e in elig),
        "registry_eligible_represented_in_registry_not_integrated": len(represented_only),
        "registry_manageable_rules_governed_plus_eligible": len(gov) + len(elig),
        "registry_manageable_parameters_governed_plus_eligible": sum(e["parameter_count"] for e in gov + elig),
        "rules_flagged_configurable_pass1_definition": len(cfg_relevant),  # superseded as a denominator by parameter-catalogue.json (rules with >=1 counted parameter)
        "unresolved_or_blocked_rules": by_disp.get("UNRESOLVED", 0) + by_disp.get("BLOCKED", 0),
        "retain_in_code_rules": by_disp.get("RETAIN-IN-CODE", 0), "caller_or_issuer_owned_rules": by_disp.get("CALLER-OR-ISSUER-OWNED", 0),
        "provider_or_host_owned_rules": by_disp.get("PROVIDER-OR-HOST-OWNED", 0), "out_of_scope_rules": by_disp.get("OUT-OF-SCOPE", 0),
        "omitted_from_g0_97_inventory_configurable_or_pending": [e["rule_id"] for e in omitted],
        "g0_groups_audited": len(hgroups), "pass1_group_audit_dispositions_before_lead_adjudication": dict(sorted(g0_groups_audit.items())),
        "pass1_groups_flagged_disagree_before_lead_adjudication": sorted(h["group_id"] for h in hgroups.values() if not h["agrees_with_g0"]),
        "g0_group_grouping_verdicts": dict(sorted(collections.Counter(h["grouping_verdict"] for h in hgroups.values()).items())),
        "g0_provisional_28_of_97": {"already_governed": 5, "eligible_not_migrated": 23, "sum": 28, "groups": 97},
        "migration_state": {"governed_implemented": len(gov), "governed_integrated_at_enforcement_boundary": sum(1 for e in gov if e["implementation_layers"]["enforcement_integrated"] == "YES"),
                            "independently_accepted": sum(1 for e in gov + elig if (e["implementation_layers"] or {}).get("independently_accepted") == "YES")},
        "g0_record_count_check": len(led["records"]), "g0_group_count_check": len(led["rule_groups"]),
    }
    g0_group_crosswalk = []
    for gid, g in sorted(g0_group.items()):
        tgt = resolve(gid)
        g0_group_crosswalk.append({"g0_group_id": gid, "g0_disposition": g["lead_disposition"], "audit_rule_id": tgt, "audit_disposition": rules[tgt]["disposition"],
                                   "records_split_out": sorted(x for x in g["record_ids"] if x in split_of)})
    g0_record_crosswalk = {rec["rule_id"]: (split_of.get(rec["rule_id"]) or resolve(rec_to_group[rec["rule_id"]])) for rec in led["records"]}
    g0_equiv = {"ALREADY-GOVERNED": "REGISTRY-GOVERNED", "ELIGIBLE-NOT-MIGRATED": "REGISTRY-ELIGIBLE", "RETAIN": "RETAIN-IN-CODE"}
    summary["g0_groups_where_final_audit_differs"] = sorted(x["g0_group_id"] for x in g0_group_crosswalk if g0_equiv.get(x["g0_disposition"], x["g0_disposition"]) != x["audit_disposition"])
    summary["g0_group_final_audit_dispositions"] = dict(sorted(collections.Counter(x["audit_disposition"] for x in g0_group_crosswalk).items()))
    summary["g0_group_vs_audit_matrix"] = {f"{a} -> {b}": n for (a, b), n in sorted(collections.Counter(
        (x["g0_disposition"], x["audit_disposition"]) for x in g0_group_crosswalk).items())}
    return {"crosswalk": crosswalk, "catalogue": catalogue, "sites": site_map, "summary": summary, "errors": errors, "row_to_rule": row_to_rule,
            "g0_group_crosswalk": g0_group_crosswalk, "g0_record_crosswalk": g0_record_crosswalk}


def _g0_equiv(g0, new):
    m = {"ALREADY-GOVERNED": "REGISTRY-GOVERNED", "ELIGIBLE-NOT-MIGRATED": "REGISTRY-ELIGIBLE"}
    return m.get(g0, g0) == new


def render(out):
    return {"crosswalk.json": dump({"schema": "registry-eligibility-audit-crosswalk/1", "rows": out["crosswalk"]}),
            "rule-catalogue.json": dump({"schema": "registry-eligibility-audit-rule-catalogue/1", "rules": out["catalogue"]}),
            "source-site-map.json": dump({"schema": "registry-eligibility-audit-source-site-map/1", "sites": out["sites"]}),
            "reconciliation.json": dump({"schema": "registry-eligibility-audit-reconciliation/1", "summary": out["summary"], "errors": out["errors"],
                                        "g0_group_crosswalk": out["g0_group_crosswalk"], "g0_record_crosswalk": out["g0_record_crosswalk"]})}


def main():
    out = build()
    texts = render(out)
    if "--check" in sys.argv:
        bad = [n for n in OUTPUT_NAMES if (AUD / n).read_text() != texts[n]]
        print("outputs match recomputation" if not bad and not out["errors"] else f"MISMATCH {bad} errors={out['errors'][:5]}")
        return 1 if bad or out["errors"] else 0
    for n in OUTPUT_NAMES:
        (AUD / n).write_text(texts[n])
    print(json.dumps(out["summary"], indent=1)[:6000])
    if out["errors"]:
        print("ERRORS:", len(out["errors"]))
        for e in out["errors"][:60]:
            print(" -", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
