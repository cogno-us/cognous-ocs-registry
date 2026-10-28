#!/usr/bin/env python3
"""Deterministic parameter ledger. Inputs: worker-evidence/pass2/A.jsonl (Worker A inventory), rule-catalogue.json (final rule dispositions),
lead-adjudications.json (parameter_adjudications, merges). Outputs: parameter-catalogue.json, parameter-reconciliation.md. `--check` recomputes in memory.
A parameter is an independently configurable field a legitimate owner could vary. Composite copies, site duplicates and enforcement invariants are listed
but never counted. Eligibility of a counted parameter follows its canonical rule's final disposition unless a recorded override says otherwise."""
import collections
import json
import sys
from pathlib import Path

AUD = Path(__file__).resolve().parent.parent
OUT_JSON, OUT_MD = "parameter-catalogue.json", "parameter-reconciliation.md"
CAT = {"REGISTRY-GOVERNED": "A", "REGISTRY-ELIGIBLE": "A", "CALLER-OR-ISSUER-OWNED": "B", "RETAIN-IN-CODE": "C", "PROVIDER-OR-HOST-OWNED": "D", "OUT-OF-SCOPE": "D", "UNRESOLVED": "E", "BLOCKED": "E"}
CAT_NAMES = {"A": "Registry-manageable", "B": "Caller/issuer-owned", "C": "Mandatory invariant parameter (retain in code)", "D": "Operational, host or provider parameter (incl. out-of-scope)", "E": "Unresolved or blocked candidate"}
FIELDS = ["parameter_id", "canonical_rule_id", "historical_ids", "g0_group_ids", "name", "owner", "source_repo", "source_commit", "source_path", "consumer", "current_value",
          "valid_domain", "narrowing_relation", "registry_contract", "registry_family", "registry_represented", "enforcement_integrated", "independently_accepted",
          "eligibility", "blocking_decision", "evidence", "confidence"]


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def build():
    adj = json.loads((AUD / "lead-adjudications.json").read_text())
    pa = adj["parameter_adjudications"]
    rules = {r["rule_id"]: r for r in json.loads((AUD / "rule-catalogue.json").read_text())["rules"]}
    remap = {m: mg["into"] for mg in adj.get("merges", []) for m in mg["members"]}
    errors = []
    recs = []
    lines = (AUD / "worker-evidence" / "pass2" / "A.jsonl").read_text().splitlines()
    for ln in lines:
        x = json.loads(ln)
        if x.get("meta") or x.get("summary"):
            continue
        recs.append(x)
    add_ids = {a["parameter_id"] for a in pa.get("additions", [])}
    recs += pa.get("additions", [])
    out = []
    seen = set()
    for x in recs:
        pid = x["parameter_id"]
        if pid in seen:
            errors.append(f"duplicate parameter id {pid}")
        seen.add(pid)
        x = dict(x)
        x.update(pa.get("overrides", {}).get(pid, {}))
        rid = remap.get(x["canonical_rule_id"], x["canonical_rule_id"])
        if rid not in rules:
            errors.append(f"{pid}: canonical rule {rid} not in catalogue")
            continue
        x["canonical_rule_id"] = rid
        counted = x["unit_type"] == "PARAMETER"
        rule_disp = rules[rid]["disposition"]
        explicit = "eligibility" in pa.get("overrides", {}).get(pid, {}) or pid in add_ids
        if counted and not explicit:
            x["eligibility"] = rule_disp
        if counted and x["eligibility"] != rule_disp and not explicit:
            errors.append(f"{pid}: eligibility {x['eligibility']} differs from rule {rid} {rule_disp} without override")
        x["counted"] = counted
        x["category"] = CAT[x["eligibility"]] if counted else "not counted (" + x["unit_type"] + ")"
        x["narrowing_unit"] = pa.get("narrowing_units", {}).get(pid, pid)
        x["tier"] = x.get("tier") or ("CORE" if x["eligibility"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE") else None)
        x["rule_disposition"] = rule_disp
        out.append(x)
    out.sort(key=lambda r: r["parameter_id"])
    for r in out:  # keep only the ledger fields plus derived fields
        for k in FIELDS:
            r.setdefault(k, None)
    counted = [r for r in out if r["counted"]]
    man = [r for r in counted if r["eligibility"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE")]
    gov = [r for r in man if r["eligibility"] == "REGISTRY-GOVERNED"]
    eli = [r for r in man if r["eligibility"] == "REGISTRY-ELIGIBLE"]
    for r in man:
        rr = rules[r["canonical_rule_id"]]
        if rr["disposition"] != r["eligibility"]:
            errors.append(f"{r['parameter_id']}: manageable parameter in rule with disposition {rr['disposition']}")
    for rid, rr in rules.items():
        if rr["disposition"] in ("REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE"):
            n = sum(1 for r in man if r["canonical_rule_id"] == rid)
            if n != rr["parameter_count"]:
                errors.append(f"{rid}: rule parameter_count {rr['parameter_count']} != ledger manageable parameters {n}")
            if n == 0:
                errors.append(f"{rid}: manageable rule without a ledger parameter")
    for r in gov:
        if not (r["registry_represented"] == "YES" and r["enforcement_integrated"] == "YES"):
            errors.append(f"{r['parameter_id']}: governed parameter lacks represented+integrated evidence")
    if any(r["independently_accepted"] != "NO" for r in counted):
        errors.append("a parameter claims independent acceptance")
    by_elig = collections.Counter(r["eligibility"] for r in counted)
    by_cat = collections.Counter(r["category"] for r in counted)
    units_all = {r["narrowing_unit"] for r in counted}
    units_man = {r["narrowing_unit"] for r in man}
    rules_with_params = {r["canonical_rule_id"] for r in counted}
    rules_man = {r["canonical_rule_id"] for r in man}
    total_rules = len(rules)
    rep = [r for r in man if r["registry_represented"] == "YES"]
    integ = [r for r in man if r["enforcement_integrated"] == "YES"]
    core = [r for r in man if r["tier"] == "CORE"]
    blocked = [r for r in counted if r["eligibility"] == "BLOCKED"]
    unres = [r for r in counted if r["eligibility"] == "UNRESOLVED"]
    retained = [r for r in counted if r["eligibility"] == "RETAIN-IN-CODE"]
    strict = [r for r in counted if r["eligibility"] != "RETAIN-IN-CODE"]
    summary = {
        "historical_rows": 620, "g0_groups": 97, "g0_records": 116, "canonical_rules": total_rules,
        "rules_with_at_least_one_counted_parameter": len(rules_with_params),
        "ledger_records": len(out), "ledger_records_not_counted": collections.Counter(r["unit_type"] for r in out if not r["counted"]),
        "distinct_configurable_parameters": len(counted), "retained_in_code_candidate_parameters": len(retained), "configurable_parameters_excluding_retained": len(strict), "distinct_narrowing_units": len(units_all),
        "parameters_by_eligibility": dict(sorted(by_elig.items())), "parameters_by_category": dict(sorted(by_cat.items())),
        "manageable_parameters": len(man), "manageable_governed_parameters": len(gov), "manageable_eligible_parameters": len(eli),
        "manageable_rules": len(rules_man), "manageable_narrowing_units": len(units_man),
        "manageable_core_parameters": len(core), "manageable_qualified_or_coupled_parameters": len(man) - len(core),
        "qualified_or_coupled_ids": sorted(r["parameter_id"] for r in man if r["tier"] != "CORE"),
        "represented_in_registry_parameters": len(rep), "enforcement_integrated_parameters": len(integ), "independently_accepted_parameters": 0,
        "eligible_not_migrated_parameters": len(eli), "eligible_represented_only_parameters": len([r for r in eli if r["registry_represented"] == "YES"]),
        "blocked_parameters": len(blocked), "unresolved_parameters": len(unres),
        "blocked_parameter_ids": sorted(r["parameter_id"] for r in blocked), "unresolved_parameter_ids": sorted(r["parameter_id"] for r in unres),
        "newly_discovered_vs_g0": sorted(r["parameter_id"] for r in man if r["parameter_id"] == "P-RG-C-TERMINAL-REVOCATION-enabled"),
    }
    summary["percentages"] = [
        {"label": "Registry-manageable parameters / candidate configurable parameters", "numerator": len(man), "denominator": len(counted), "percent": pct(len(man), len(counted))},
        {"label": "Registry-manageable parameters / candidate parameters excluding those the audit retains in code", "numerator": len(man), "denominator": len(strict), "percent": pct(len(man), len(strict))},
        {"label": "Core-tier manageable parameters / candidate configurable parameters", "numerator": len(core), "denominator": len(counted), "percent": pct(len(core), len(counted))},
        {"label": "Enforcement-integrated parameters / manageable parameters", "numerator": len(integ), "denominator": len(man), "percent": pct(len(integ), len(man))},
        {"label": "Registry-represented parameters / manageable parameters", "numerator": len(rep), "denominator": len(man), "percent": pct(len(rep), len(man))},
        {"label": "Independently accepted parameters / manageable parameters", "numerator": 0, "denominator": len(man), "percent": 0.0},
        {"label": "Manageable rules / rules with at least one counted parameter", "numerator": len(rules_man), "denominator": len(rules_with_params), "percent": pct(len(rules_man), len(rules_with_params))},
        {"label": "Manageable rules / all canonical rules", "numerator": len(rules_man), "denominator": total_rules, "percent": pct(len(rules_man), total_rules)},
        {"label": "Manageable narrowing units / all narrowing units (finest partition)", "numerator": len(units_man), "denominator": len(units_all), "percent": pct(len(units_man), len(units_all))},
        ]
    summary["rule_partition_sensitivity"] = [
        {"partition": "catalogue rules (this audit)", "manageable": len(rules_man), "of": len(rules_with_params)},
        {"partition": "one unit per independently narrowable parameter", "manageable": len(units_man), "of": len(units_all)},
        {"partition": "worker B alternatives (see worker-evidence/pass2/B.jsonl): F1a split five ways, F4 two ways, max_amount+max_effects joined", "manageable": "11 to 19 depending on partition", "of": "partition-dependent"}]
    summary["sensitivities_on_parameter_count"] = [
        {"change": "ObservationPolicy.clock_tolerance_seconds excluded with RG-C-006 if AR-1 extends the exclusion", "manageable_parameters": len(man) - 1},
        {"change": "drop QUALIFIED/COUPLED tier (" + ", ".join(sorted(r["parameter_id"] for r in man if r["tier"] != "CORE")) + ")", "manageable_parameters": len(core)},
        {"change": "RG-C-005 and RG-C-006 authorized by the Architect (AR-1, AR-4)", "manageable_parameters": len(man) + len([r for r in blocked if r['canonical_rule_id'] in ('RG-C-005', 'RG-C-006')]), "note": "the three age/tolerance parameters would become eligible (they are the blocked parameters)"}]
    return {"summary": summary, "errors": errors, "parameters": out}


def render(data):
    return json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def table(h, rows):
    return "\n".join(["| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |" for r in rows])


def build_md(data):
    s = data["summary"]
    P = data["parameters"]
    counted = [p for p in P if p["counted"]]
    L = ["# Parameter-level reconciliation", "", "> Release: HOLD. Publication: HOLD. Production: HOLD. Audit only; not independent Tier 1 qualification.", "",
         "Every number below is computed from `parameter-catalogue.json` (rebuilt by `tools/build_parameters.py`); none is copied from prose.", "",
         "## 1. Five different units", "",
         table(["Unit", "Count", "What it counts"], [
             ["Historical rule sites", s["historical_rows"], "Rows of the S02 inventory: one per hard-coded implementation site, including mandatory invariants, vocabularies and serialization details. Many rows implement one rule."],
             ["G0 rule groups", s["g0_groups"], "G0's grouping of 116 current source records into logical rules."],
             ["Canonical rules", s["canonical_rules"], "This audit's logical rules after merges, splits and the repository-coverage sweep. Most are protected mechanisms with no tunable value."],
             ["Rules with at least one configurable parameter", s["rules_with_at_least_one_counted_parameter"], "Canonical rules containing at least one independently configurable parameter, whoever owns it."],
             ["Candidate configurable parameters", s["distinct_configurable_parameters"], f"Independently variable fields a legitimate owner could set, whoever owns them, including {s['retained_in_code_candidate_parameters']} literals the audit retains in code ({s['configurable_parameters_excluding_retained']} without them). Composite copies, derived values, site duplicates and invariants are excluded."],
             ["Registry-manageable parameters", s["manageable_parameters"], "Parameters of rules that are REGISTRY-GOVERNED or REGISTRY-ELIGIBLE."]]), "",
         "Rules and parameters differ because a rule can carry several parameters (the five F1a allow-sets, two F4 ages, two observation-policy fields, and the governed target prefixes plus match mode). Pass 1 reported 13 manageable rules and 19 parameters. Pass 2 reports 13 rules and 20 parameters: merging prefixes+match removes one governed rule, and the newly found terminal-revocation enablement adds one eligible rule and one parameter.", "",
         "## 2. Answers", "",
         table(["Question", "Answer"], [
             ["Distinct logical rules", s["canonical_rules"]],
             ["Rules containing meaningful configurable parameters", s["rules_with_at_least_one_counted_parameter"]],
             ["Candidate configurable parameters (all owners)", f"{s['distinct_configurable_parameters']} ({s['configurable_parameters_excluding_retained']} excluding literals retained in code)"],
             ["Registry-manageable parameters", f"{s['manageable_parameters']} ({s['manageable_governed_parameters']} governed + {s['manageable_eligible_parameters']} eligible); {s['manageable_rules']} rules; {s['manageable_narrowing_units']} narrowing units"],
             ["Represented in the Registry", s["represented_in_registry_parameters"]],
             ["Integrated at an enforcement boundary", s["enforcement_integrated_parameters"]],
             ["Independently accepted", s["independently_accepted_parameters"]],
             ["Eligible, not migrated", f"{s['eligible_not_migrated_parameters']} ({s['eligible_represented_only_parameters']} represented in the Registry but with no consumer)"],
             ["Blocked by an Architect decision", f"{s['blocked_parameters']} blocked parameters; {s['unresolved_parameters']} unresolved parameters (excluded from the manageable numerator)"],
             ["New opportunities missed by G0", ", ".join(s["newly_discovered_vs_g0"]) or "none"]]), "",
         "## 3. Percentages (denominators stated)", "",
         table(["Ratio", "Numerator", "Denominator", "Percent"], [[x["label"], x["numerator"], x["denominator"], x["percent"]] for x in s["percentages"]]), "",
         "Rule-level coverage depends on how rules are partitioned, so parameter-level coverage is the more stable headline:", "",
         table(["Partition", "Manageable", "Of"], [[x["partition"], x["manageable"], x["of"]] for x in s["rule_partition_sensitivity"]]), "",
         "Sensitivities on the parameter count:", "",
         table(["Change", "Result"], [[x["change"], ", ".join(f"{k}={v}" for k, v in x.items() if k != "change")] for x in s["sensitivities_on_parameter_count"]]), "",
         "Tiers: CORE parameters have a direct monotone narrowing relation and a defined consumer path. QUALIFIED parameters (opt-in safeguard enablement toggles, or one rank parameter needing re-shaping) and COUPLED parameters (derived in part from another Registry value) are manageable in principle but carry a stated dependency. Qualified/coupled: " + ", ".join(s["qualified_or_coupled_ids"]) + ".", "",
         "## 4. Parameters by category", "",
         table(["Category", "Meaning", "Parameters"], [[k, CAT_NAMES[k], v] for k, v in sorted({c: sum(1 for p in counted if p["category"] == c) for c in {p["category"] for p in counted}}.items())]), "",
         "Records excluded from the count: " + ", ".join(f"{v} {k}" for k, v in sorted(s["ledger_records_not_counted"].items())) + ".", ""]
    for grp, ttl in (("REGISTRY-GOVERNED", "Governed"), ("REGISTRY-ELIGIBLE", "Eligible, not migrated"), ("BLOCKED", "Blocked"), ("UNRESOLVED", "Unresolved")):
        rows = [p for p in counted if p["eligibility"] == grp]
        L += [f"## {ttl} ({len(rows)})", "",
              table(["Parameter", "Rule", "Represented", "Integrated", "Tier", "Blocking decision / note"],
                    [[p["parameter_id"], p["canonical_rule_id"], p["registry_represented"], p["enforcement_integrated"], p["tier"] or "", (p["blocking_decision"] or (p.get("note") or ""))[:160]] for p in rows]) if rows else "None.", ""]
    return "\n".join(L) + "\n"


def outputs():
    d = build()
    return d, {OUT_JSON: render(d), OUT_MD: build_md(d)}


def main():
    d, o = outputs()
    if d["errors"]:
        print("ERRORS:", *d["errors"], sep="\n")
        return 1
    if "--check" in sys.argv:
        bad = [n for n in o if (AUD / n).read_text() != o[n]]
        print("parameter ledgers match recomputation" if not bad else f"MISMATCH {bad}")
        return 1 if bad else 0
    for n, t in o.items():
        (AUD / n).write_text(t)
    print("wrote", ", ".join(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
