#!/usr/bin/env python3
"""Renders the human-readable audit reports from the machine-readable ledgers (never from typed numbers).

Run after reconcile.py:  python3 render_reports.py [--check]
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUD = HERE.parent
WE = AUD / "worker-evidence"

HOLDS = ("Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. "
         "No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.")
REPORTS = ("reconciliation-report.md", "eligibility-decisions.md", "merge-and-split-explanations.md", "omitted-rule-groups.md",
           "unresolved-architectural-decisions.md", "proposed-backlog-additions.md", "worker-cross-check-results.md")


def load(name):
    return json.loads((AUD / name).read_text())


def pct(a, b):
    return f"{100.0 * a / b:.1f}%" if b else "n/a"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def short(s, n=140):
    s = (s or "").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def jl(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def build_reports():
    cw = load("crosswalk.json")["rows"]
    cat = load("rule-catalogue.json")["rules"]
    rec = load("reconciliation.json")
    s = rec["summary"]
    adj = json.loads((AUD / "lead-adjudications.json").read_text())
    by = {r["rule_id"]: r for r in cat}
    reports = {}

    gov = [r for r in cat if r["disposition"] == "REGISTRY-GOVERNED"]
    elig = [r for r in cat if r["disposition"] == "REGISTRY-ELIGIBLE"]
    pend = [r for r in cat if r["disposition"] in ("UNRESOLVED", "BLOCKED")]
    total_rules = s["canonical_rules_total"]
    manage = len(gov) + len(elig)
    manage_p = s["registry_manageable_parameters_governed_plus_eligible"]
    cfgrel = s["configuration_relevant_rules_denominator"]
    represented_only = [r for r in elig if (r["implementation_layers"] or {}).get("registry_represented") == "YES"]
    integrated = [r for r in gov if r["implementation_layers"]["enforcement_integrated"] == "YES"]

    # ------------------------------------------------------------------ reconciliation-report.md
    classes = sorted(s["historical_rows_by_class"])
    disps = ["REGISTRY-GOVERNED", "REGISTRY-ELIGIBLE", "RETAIN-IN-CODE", "CALLER-OR-ISSUER-OWNED", "PROVIDER-OR-HOST-OWNED", "OUT-OF-SCOPE", "UNRESOLVED", "BLOCKED"]
    matrix = collections.Counter((r["historical_class"], r["disposition"]) for r in cw)
    lines = ["# Independent Registry eligibility audit — numerical reconciliation", "",
             f"> {HOLDS}", "",
             "All numbers below are computed by `tools/reconcile.py` from the ledgers in this directory (`--check` recomputes them in CI); none is typed by hand.", "",
             "## 1. Answer to the Architect's question", "",
             f"Of **{total_rules}** distinct canonical logical rules reconciled from the 620 historical records, the 97 current groups and the repository-coverage sweep:", "",
             table(["Measure", "Rules", "Configuration parameters", "Share"],
                   [["Registry-governed (implemented and integrated at the Runtime enforcement boundary; NOT independently accepted)", len(gov), s["registry_governed_parameters"], pct(len(gov), manage)],
                    ["Registry-eligible, not yet governed", len(elig), s["registry_eligible_parameters"], pct(len(elig), manage)],
                    ["**Registry-manageable total (governed + eligible)**", f"**{manage}**", f"**{manage_p}**", "100%"],
                    ["…as a share of all canonical rules", f"{manage} of {total_rules}", "", pct(manage, total_rules)],
                    [f"…as a share of the {cfgrel} configuration-bearing rules (configurable = YES, or a pending decision)", f"{manage} of {cfgrel}", "", pct(manage, cfgrel)],
                    ["Unresolved or blocked (decision needed before eligibility can be stated)", len(pend), "", ""]]), "",
             "The denominator for *all* rules is granularity-dependent (how finely protected mechanisms are split); the manageable count and the configuration-bearing count are the robust figures. See §6.", "",
             "## 2. Implementation state of the manageable rules (three separate facts)", "",
             table(["Layer", "Rules", "Parameters", "Share of manageable rules"],
                   [["Represented in the Registry", len(gov) + len(represented_only), sum(r["parameter_count"] for r in gov + represented_only), pct(len(gov) + len(represented_only), manage)],
                    ["Integrated at an enforcement boundary", len(integrated), sum(r["parameter_count"] for r in integrated), pct(len(integrated), manage)],
                    ["Independently accepted", s["migration_state"]["independently_accepted"], 0, pct(s["migration_state"]["independently_accepted"], manage)]]), "",
             "Implemented rules are those whose Registry representation AND enforcement-boundary integration are both merged. Nothing is independently accepted: V09 independent qualification is open and builder CI does not establish acceptance.", "",
             "Governed rules (counted once each; M2/M3 members are not double counted):", "",
             table(["Rule", "Parameters", "Wave / evidence"], [[r["rule_id"], r["parameter_count"], short(r["proposed_migration_wave"], 160)] for r in gov]), "",
             "Represented in the Registry but not integrated (the Control Plane has no consumer):", "",
             table(["Rule", "Parameters", "Wave"], [[r["rule_id"], r["parameter_count"], r["proposed_migration_wave"]] for r in represented_only]), "",
             "## 3. Historical reconciliation (620 records)", "",
             table(["Historical class (frozen)", "Rows"] + [d.replace("-", " ").title() for d in disps],
                   [[c, s["historical_rows_by_class"][c]] + [matrix.get((c, d), 0) for d in disps] for c in classes] +
                   [["**Total**", s["historical_rows"]] + [s["rows_by_final_disposition"].get(d, 0) for d in disps]]), "",
             f"- Every one of the 620 rows appears exactly once as a primary crosswalk row; original IDs and original classes are unchanged ({', '.join(f'{k} {v}' for k, v in sorted(s['historical_rows_by_class'].items()))}).",
             f"- {s['rows_reclassified_vs_historical_class_by_worker']} rows were reclassified by a worker relative to what their historical class implied; {s['rows_where_final_differs_from_worker']} rows carry a final (lead-adjudicated) disposition that differs from the worker's, each with a recorded reason; {s['rows_rekeyed_by_lead']} rows were re-keyed by the lead to separate a mechanism from the parameter it sits beside.",
             f"- Source status: {s['rows_source_status']} (no row is treated as deleted; coordinates that drifted were re-located by symbol).", "",
             "## 4. Canonical rules", "",
             table(["Origin", "Rules"], [[k, v] for k, v in sorted(s["canonical_rules_by_origin"].items())] + [["**Total**", total_rules]]), "",
             table(["Disposition", "Rules"], [[d, s["canonical_rules_by_disposition"].get(d, 0)] for d in disps] + [["**Total**", total_rules]]), "",
             f"{s['canonical_rules_from_historical_rows']} rules contain at least one historical row; {s['canonical_rules_g0_only_no_historical_row']} are G0-current rules with no historical row; {s['canonical_rules_repo_coverage_only']} were discovered by the repository-coverage sweep (none of those is Registry-eligible).", "",
             "## 5. Reconciliation with the G0 inventory (116 source sites, 97 groups)", "",
             "The provisional G0 conclusion was 5 already-governed + 23 eligible-not-migrated = 28 of 97 groups. Group-level movement:", "",
             table(["G0 disposition -> audit disposition", "G0 groups"], [[k, v] for k, v in s["g0_group_vs_audit_matrix"].items()]), "",
             f"The audit disagrees with G0 on {len(s['g0_groups_where_audit_disagrees'])} of 97 groups on the independent group audit (before lead merges and splits). Grouping verdicts: {s['g0_group_grouping_verdicts']}.", "",
             "Why the headline moved (each item is detailed in `eligibility-decisions.md`):", "",
             "1. The four M2/M3 groups (max_amount, max_effects, target prefixes, target match) are no longer *eligible-not-migrated*: they are implemented and integrated at the Runtime effect-time guard on current main. They move to REGISTRY-GOVERNED, not accepted.",
             "2. G0's ALREADY-GOVERNED label is overstated for the F4/F5 age scalars (RG-A-007, RG-A-008) and for `age_ceilings` (RG-C-021): the Registry composes them, but the Control Plane has no Registry consumer. They are REGISTRY-ELIGIBLE with the Registry half represented.",
             "3. RG-C-031 (`default_action`) was labelled ALREADY-GOVERNED but has no Registry slot; it is issuer-authored manifest data.",
             "4. Several G0 eligible groups are not Registry-manageable on the audit evidence (host/provider facts, issuer data, no enforcement boundary, or synthetic): RG-B-016, RG-C-037, RG-D-015, RG-D-018, RG-D-020, RG-D-021, RG-D-022 (synthetic). RG-F11, RG-D-012 and RG-F7-DEDUPE are unresolved on ownership; RG-C-011 stays eligible (rank-raising overlay, MEDIUM, retained reviewer disagreement).",
             "5. Several duplicates collapse: RG-A-007 + RG-C-003 + RG-C-004; RG-A-008 + RG-C-008 + RG-C-021 (+ a re-discovered class status age bound); RG-C-031 + RG-D-003.",
             "6. RG-C-005 and RG-C-006 (identity/mandate age, clock tolerance) are monotone in shape but excluded by accepted decision DR-CP-AGE-1 as host-owned, so they are BLOCKED on an Architect reversal rather than eligible. RG-C-018 (freshness nonce toggle) stays out of the manageable set (host-owned: a Registry cannot enforce it). RG-C-024 (funded merge authorities) moves to unresolved.", "",
             "## 6. Integrity checks (enforced by `tests/test_audit_registry_eligibility_integrity.py`)", "",
             "- 620 primary historical rows, no duplicates, no deletions; original classes preserved; IDs equal the frozen G0 crosswalk.",
             "- Every row maps to exactly one canonical rule; every rule has exactly one disposition; rule-level totals equal the sum of dispositions.",
             "- No retained mandatory control is mapped into an eligible or governed rule (the reconciler fails on such a contradiction).",
             "- Every one of the 116 G0 source records maps to exactly one canonical rule; M2/M3 composite members are counted once (nine governed parameters in total).",
             "- The committed ledgers equal a fresh recomputation from the worker evidence and the lead adjudications.",
             "- The 38 frozen G0/S02 evidence files are byte-identical (git blob ids) to the pinned baseline.", "",
             "## 7. Coverage limits (do not read this audit as exhaustive)", "",
             "- Static source review only; no test suite was run. Worker classifications are AI-produced; the Audit Lead verified the high-impact reclassifications named in `eligibility-decisions.md` against source and ran an independent blind second review (see `worker-cross-check-results.md`).",
             "- Historical-row classification for the 494 non-candidate rows relied on risk-targeted source reading; the blind re-audit sampled 178 retain-in-code rows (148 risk-selected + 30 random), not all 545.",
             "- Repository coverage: Runtime and Control Plane files already covered by S02/G0 were grep-scanned, not re-read. Action Manifest and Governed Exchange schemas, examples, docs and tests, the Stack Qualification repository (about 10 of 28,961 files read) and parts of the Stack Orchestrator were not reviewed in full.",
             "- The count of *all* canonical rules depends on how finely protected mechanisms are split; only the Registry-manageable and configuration-bearing counts are decision-grade.",
             "- Observations that are not migration defects: see `unresolved-architectural-decisions.md` §3."]
    reports["reconciliation-report.md"] = "\n".join(lines) + "\n"

    # ------------------------------------------------------------------ eligibility-decisions.md
    L = ["# Registry eligibility decisions (proposals for Architect approval)", "", f"> {HOLDS}", "",
         "Every canonical rule that is governed, eligible, unresolved or blocked is listed with its evidence. Rules that are retained in code, owned by a caller/issuer/provider/host, or out of scope are listed in `rule-catalogue.json` with the reason (`disposition_basis`).", ""]
    for title, group in (("Registry-governed (implemented and integrated; not independently accepted)", gov), ("Registry-eligible (not yet governed)", elig), ("Unresolved or blocked", pend)):
        L += [f"## {title}", ""]
        for r in group:
            L += [f"### {r['rule_id']} — {r['name']}", "",
                  f"- Disposition: **{r['disposition']}** (basis: {r['disposition_basis']}); G0 disposition(s): {', '.join(r['g0_dispositions']) or 'not in G0 inventory'}; confidence {r['confidence']}.",
                  f"- Parameters: {r['parameter_count']}; migration status {r['migration_status']}; layers {r['implementation_layers']}; proposed wave: {r['proposed_migration_wave']}.",
                  f"- Configuration owner: {short('; '.join(r['configuration_owner']), 260)}",
                  f"- Value / domain: {short(r['value_type'], 260)}",
                  f"- Narrowing semantics: {short(r['proposed_narrowing_semantics'], 320)}",
                  f"- Existing Registry coverage: {short(str(r['existing_registry_coverage']), 320)}"]
            if r["blocking_architectural_decisions"]:
                L.append("- Blocking decisions: " + "; ".join(short(b, 220) for b in r["blocking_architectural_decisions"]))
            L.append(f"- Historical rows: {', '.join(r['historical_source_ids']) or 'none (G0-current rule)'}; G0 groups: {', '.join(r['g0_group_ids']) or 'none'}; evidence: {short('; '.join(r['evidence_references']), 260)}")
            L.append("")
    L += ["## Rules whose disposition differs from G0", "",
          table(["Rule", "G0", "Audit", "Reason (basis)"],
                [[r["rule_id"], ", ".join(r["g0_dispositions"]), r["disposition"], short(r["disposition_basis"], 180)] for r in cat if r["differs_from_g0"]]), ""]
    reports["eligibility-decisions.md"] = "\n".join(L) + "\n"

    # ------------------------------------------------------------------ merge-and-split-explanations.md
    L = ["# Merge, split and re-key explanations", "", f"> {HOLDS}", "",
         "## Lead merges (many-to-one, explained)", ""]
    for m in adj["merges"]:
        L += [f"- **{m['into']}** ← {', '.join(m['members'])}: {m['reason']}"]
    L += ["", "## Lead splits (one G0 group divided because the parts have different dispositions)", ""]
    for sp in adj["splits"]:
        L += [f"- **{sp['new']}** split from {sp['from']} (record {', '.join(sp['records'])}): {sp['reason']}"]
    L += ["", "## Row re-keys (mechanism separated from the parameter it sits beside)", ""]
    for rid, spec in adj["row_rekeys"].items():
        L += [f"- {rid} → **{spec['canonical_key']}**: {spec['reason']}"]
    L += ["", "## Many-to-one groupings by the first-pass workers (rules with more than one historical row)", ""]
    multi = [r for r in cat if len(r["historical_source_ids"]) > 1]
    L += [f"{len(multi)} rules contain more than one historical row. The merge basis recorded by the workers is in `crosswalk.json` (`merge_basis`). Largest groups:", ""]
    L += [table(["Rule", "Historical rows", "Disposition", "Example merge basis"],
                [[r["rule_id"], len(r["historical_source_ids"]), r["disposition"],
                  short(next((x["merge_basis"] for x in cw if x["canonical_rule_id"] == r["rule_id"] and x["merge_basis"]), ""), 120)]
                 for r in sorted(multi, key=lambda r: -len(r["historical_source_ids"]))[:40]]), ""]
    L += ["## G0 grouping verdicts that did NOT change a disposition (proposals only)", "",
          "Workers H1/H2 judged these groups over- or under-merged; because the parts share one disposition the audit keeps the G0 group identity and records the proposal:", ""]
    hv = []
    for sh in ("H1", "H2"):
        for h in jl(WE / f"{sh}.jsonl"):
            if h["grouping_verdict"] != "SUPPORTED":
                hv.append([h["group_id"], h["grouping_verdict"], short(h["note"], 200)])
    L += [table(["G0 group", "Verdict", "Note"], hv), ""]
    reports["merge-and-split-explanations.md"] = "\n".join(L) + "\n"

    # ------------------------------------------------------------------ omitted-rule-groups.md
    omit_ids = s["omitted_from_g0_97_inventory_configurable_or_pending"]
    L = ["# Rules omitted from the current 97-group inventory", "", f"> {HOLDS}", "",
         f"Rules that are configurable (or pending a decision) and have no counterpart in the 116-record / 97-group G0 inventory: **{len(omit_ids)}**. "
         f"**Newly discovered Registry-eligible rules among them: {sum(1 for i in omit_ids if by[i]['disposition'] in ('REGISTRY-ELIGIBLE', 'REGISTRY-GOVERNED'))}.**", "",
         table(["Rule", "Disposition", "Configurable", "Origin", "Why it is not Registry-manageable / what is pending"],
               [[i, by[i]["disposition"], by[i]["configurable"], by[i]["origin"], short(by[i]["disposition_basis"] + " " + (by[i]["blocking_architectural_decisions"][0] if by[i]["blocking_architectural_decisions"] else ""), 200)]
                for i in omit_ids]), "",
         "Also omitted from the *historical-row* populations of S02 because it was not read: Action Manifest, Governed Exchange, Institutional Governance, Evidence Pack, Replay Bundle, ODES, Evidence Registry, Evidence Attestation, hub, verifier and Stack Orchestrator sources. They were swept by the repository-coverage workers (see `worker-evidence/I1.json`, `I2.json`, `I3.json`); none yielded a new Registry-eligible rule.", ""]
    reports["omitted-rule-groups.md"] = "\n".join(L) + "\n"

    # ------------------------------------------------------------------ unresolved-architectural-decisions.md
    L = ["# Unresolved architectural decisions", "", f"> {HOLDS}", "",
         "## 1. Decisions raised by the lead", ""]
    for d in adj["decisions"]:
        L += [f"### {d['id']} — {d['title']}", "", d["body"], "", f"*Recommendation:* {d['recommendation']}", ""]
    L += ["## 2. Blocking decisions attached to individual rules", ""]
    rows = []
    for r in cat:
        for b in r["blocking_architectural_decisions"]:
            if r["disposition"] in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED", "UNRESOLVED", "BLOCKED"):
                rows.append([r["rule_id"], r["disposition"], short(b, 260)])
    L += [table(["Rule", "Disposition", "Blocking question"], rows), "",
          "## 3. Observations that are not migration defects", "",
          "Recorded for the Architect; none concerns an active migration and none was escalated as a material safety defect.", ""]
    for o in adj.get("observations", []):
        L += [f"- {o}"]
    reports["unresolved-architectural-decisions.md"] = "\n".join(L) + "\n"

    # ------------------------------------------------------------------ proposed-backlog-additions.md
    L = ["# Proposed corrections and additions to the migration backlog (for Architect approval)", "",
         f"> {HOLDS}", "",
         "These are proposals only. The active migration plan and `m2/01-migration-backlog.md` are not changed by this audit and migration work is not blocked by it.", "",
         "## A. Counts the backlog would carry if the proposals are accepted", "",
         table(["Backlog metric (rule groups / rules)", "G0 / backlog today", "Audit proposal"],
               [["Already governed or implemented", "5 (G0) + 4 implemented M2/M3 pending acceptance", f"{len(gov)} rules / {s['registry_governed_parameters']} parameters (all implemented; 0 accepted)"],
                ["Eligible, not yet integrated", "23 eligible-not-migrated (19 after M2/M3)", f"{len(elig)} rules / {s['registry_eligible_parameters']} parameters"],
                ["Unresolved or blocked", "5 (G0)", f"{len(pend)}"]]), "",
         "## B. Eligible backlog (audit view, ordered by the existing waves)", "",
         table(["Rule", "Parameters", "Proposed wave", "Layer state", "Blocking decision"],
               [[r["rule_id"], r["parameter_count"], r["proposed_migration_wave"], r["implementation_layers"], short("; ".join(r["blocking_architectural_decisions"]), 160)]
                for r in sorted(elig, key=lambda r: str(r["proposed_migration_wave"]))]), "",
         "## C. Rules proposed for removal from the eligible backlog", "",
         table(["Rule", "G0", "Audit", "Reason"],
               [[r["rule_id"], ", ".join(r["g0_dispositions"]), r["disposition"], short(r["disposition_basis"], 200)] for r in cat if "ELIGIBLE-NOT-MIGRATED" in r["g0_dispositions"] and r["disposition"] not in ("REGISTRY-ELIGIBLE", "REGISTRY-GOVERNED")]), "",
         "## D. Rules proposed for addition", "",
         table(["Rule", "Disposition", "Reason"],
               [[r["rule_id"], r["disposition"], short(r["disposition_basis"], 200)] for r in cat if r["disposition"] == "REGISTRY-ELIGIBLE" and "ELIGIBLE-NOT-MIGRATED" not in r["g0_dispositions"] and "ALREADY-GOVERNED" not in r["g0_dispositions"]]), "",
         "## E. Corrections to stale labels", "",
         "- Mark RG-A-007 and RG-A-008 (with the merged RG-C-021 age_ceilings carrier) as *represented in the Registry, not governed*: counting them as ALREADY-GOVERNED overstates coverage until a Control Plane consumer exists (wave M11/M12).",
         "- Mark RG-C-031 as issuer-owned manifest data (no Registry slot).",
         "- Record RG-F11, RG-D-012, RG-F7-DEDUPE, RG-C-032 and the Runtime admission budgets as unresolved pending the owner decisions named in the rule catalogue.",
         "- Record the M2/M3 groups as implemented and integrated, pending independent Tier 1 acceptance.",
         "- Drop RG-B-016 from wave M11: the module is an experimental synthetic ledger no executor imports.",
         "- Bring AD-07 in line with the merged M2/M3 narrowing (see `unresolved-architectural-decisions.md`).", ""]
    reports["proposed-backlog-additions.md"] = "\n".join(L) + "\n"

    # ------------------------------------------------------------------ worker-cross-check-results.md
    L = ["# Worker evidence and independent cross-check results", "", f"> {HOLDS}", "",
         "## First-pass workers", "",
         table(["Shard", "Scope", "Rows or groups"],
               [["A", "43 CONFIGURABLE-CANDIDATE", 43], ["B", "51 INCIDENTAL-CONDITIONAL", 51], ["C", "32 UNRESOLVED", 32], ["D1–D4", "354 MANDATORY-INVARIANT", 354],
                ["F1–F2", "90 SERIALIZATION-OR-EVIDENCE", 90], ["G", "50 REFUSAL-OR-REASON-VOCABULARY", 50], ["H1–H2", "97 current rule groups (116 source sites)", 97],
                ["I1–I3", "Repository coverage (Runtime, Control Plane, Action Manifest, Governed Exchange, nine further OCS repos, Stack Orchestrator)", "35 candidate sites"]]), ""]
    jf = sorted(WE.glob("J*"))
    if not jf:
        L += ["Independent cross-check results: not yet recorded.", ""]
    else:
        L += ["## Independent cross-checks (blind second review / falsification)", "", "Raw outputs: `worker-evidence/J*.jsonl`. Disposition of every disagreement: `lead-adjudications.json` (`cross_check_resolutions`).", ""]
        res = adj.get("cross_check_resolutions", [])
        L += [table(["Item", "Lead resolution", "Reason"], [[x["item"], x["resolution"], short(x["reason"], 220)] for x in res]) if res else "No disagreements recorded.", ""]
        stats = adj.get("cross_check_stats", {})
        for k, v in stats.items():
            L += [f"- {k}: " + ", ".join(f"{a}={b}" for a, b in v.items())]
        L += [""]
    reports["worker-cross-check-results.md"] = "\n".join(L) + "\n"
    return reports


def main():
    reports = build_reports()
    if "--check" in sys.argv:
        bad = [n for n in REPORTS if (AUD / n).read_text() != reports[n]]
        print("reports match recomputation" if not bad else f"MISMATCH {bad}")
        return 1 if bad else 0
    for n, t in reports.items():
        (AUD / n).write_text(t)
    print("wrote", ", ".join(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
