#!/usr/bin/env python3
import json, sys, collections
from pathlib import Path
REG = Path(sys.argv[1]); D = REG / "docs" / "family-migration" / "g0"
L = json.load(open(D / "current-candidate-ledger.json")); C = json.load(open(D / "historical-crosswalk.json"))
R = {r["rule_id"]: r for r in L["records"]}; G = {g["group_id"]: g for g in L["rule_groups"]}
repos = json.load(open(D / "evidence/worker-D/repositories.json"))
VERIFY = Path(sys.argv[2]).read_text().strip() if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else "PENDING (filled after the verification run)"
HOLDS = "G0: AUTHORIZED. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD."
cn = C["counts"]; ln = L["counts"]
def esc(t): return str(t).replace("|", "\\|").replace("\n", " ")
def tbl(head, rows): return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows])

# ---------------- source-baseline.md
bl = L["baseline_pins"]
rows = [[n, sha] for n, sha in bl.items()]
other = [[r["name"], r["head"], r.get("relevant", ""), r["clone"][:40]] for r in repos]
(D / "source-baseline.md").write_text(f"""# G0 source baseline (2026-10-27)

Non-authorizing, builder-side, read-only inventory. {HOLDS}

## 1. Current main of every examined repository

Resolved from each repository's default branch on 2026-10-27 before any worker started; historical commits are never used as current.

{tbl(["Repository", "Exact main SHA"], rows)}

Registry baseline for this PR: `317eb76acb2847c534c3ce7c2180b89b4aef987d` (merge of PR #49, the approved static migration plan v1.0). The G0 branch is cut from that commit.

Repositories inspected by Worker D (anonymous shallow clones, one at a time; SHAs recorded by the worker from the clone):

{tbl(["Repository", "HEAD at clone", "Relevant", "Clone"], other)}

Renames resolve to the same HEAD as the primary repositories: `cognous-agent-control-plane` = Control Plane, `cognous-agent-replay-bundle` = Replay Bundle, `moltbot-safe` = Runtime. `cognous-evidence-registry` and `cognous-evidence-attestation` were judged not relevant from README and a literal grep only; they were **not audited**.

## 2. Historical pins used only for the S02 old-to-current crosswalk

| Component | S02 pin | Current main |
|---|---|---|
| Runtime | `ec728da6dc301a664b331ac8986afd6e850a1273` | `{bl['cogno-us/cognous-execution-runtime']}` |
| Control Plane | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | `{bl['cogno-us/cognous-control-plane']}` |

Source churn since the S02 pins (git diff --name-status): Control Plane `src/` 5 files (3 new: `authorization_pin_export.py`, `canonical_policy_binding.py`, `policy_binding.py`; 2 modified: `local_authority_effect.py`, `runtime_authority.py`); Runtime `engine/` + `host/` 9 files (new: `authorization_pin.py`, `authorization_pin_format.py`, `registry_f1a_narrowing.py`, `registry_selection_authority.py`, `host/authorization_pin/*`; modified: `local_authority_effect.py`, `atomic_local_control_plane_executor.py`). `bounded.py` is byte-identical to the S02 pin.

## 3. Pins deliberately NOT moved

- V09 candidate manifest `docs/v09/candidate-manifest.json` is unchanged (candidate pins: Registry baseline `1a4de326…`, Control Plane `d66ae07f…`, Runtime `b5605f52…`, Stack Qualification `bb9b0890…`). The Runtime main has since advanced to `0dde0ef7…` (merge of Runtime PR #150, the F3 acceptance record); that is recorded here as the current main and does not amend the V09 candidate.
- Constitution: pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (ADOPTION.md). The Constitution repository main is `a4dd1111…`; it is **not adopted**. Tier numbering is inverted between the pin and that HEAD (the pin has Tier 1 as critical); every tier in this G0 package uses the pin meaning (decision AD-15).
- Pinned reusable workflow SHAs in `.github/workflows/` are unchanged.

## 4. Method and limits

Four read-only workers (A Registry, B Runtime, C Control Plane, D other repositories and cross-component delta) inspected non-overlapping source in read-only checkouts; the lead reconciled. Workers cited test names but **executed no tests**. Not-read areas are listed in each `evidence/worker-*/notes.md`. In short: test bodies, golden vectors, most of `bounded.py` outside the consumers of policy values, hub docs/scenarios/fixtures, replay-bundle and evidence-pack validators, ODES RFCs, and most of Stack Qualification were grepped or sampled, not read.
""")

# ---------------- family-eligibility-matrix.md
def part_rows(f):
    out = []
    for p in f["parts"]:
        ids = p["record_ids"]
        out.append([f["family"], p["part"], p["disposition"], ", ".join(i[3:] for i in ids), p["note"] + (f" (Lead override: {p['lead_override_reason']})" if p.get("lead_override_reason") else "")])
    return out
mrows = [r for f in L["families"] for r in part_rows(f)]
newrows = [[n["family"], ", ".join(i[3:] for i in n["record_ids"]), "/".join(n["dispositions"]), "/".join(n["eligibility"])] for n in L["new_families"]]
fam_wave = [[f["family"], f["name"], f["plan_wave"]] for f in L["families"]]
rdisp = ln["records_by_disposition"]; gdisp = ln["groups_by_disposition"]
(D / "family-eligibility-matrix.md").write_text(f"""# G0 family eligibility matrix

Proposals only; none is ratified, none is implemented. Rows are source-backed by `current-candidate-ledger.json` (record ids `A-001` abbreviate `G0-A-001`). {HOLDS}

Disposition vocabulary: MIGRATED / ALREADY-GOVERNED / ELIGIBLE-NOT-MIGRATED / RETAIN-IN-CODE / OUT-OF-SCOPE / UNRESOLVED / BLOCKED. Nothing is MIGRATED under this program: no migration has been implemented.

## 1. Counts

{tbl(["Disposition", "Records (source sites)", "Rule groups (unique rules)"], [[k, rdisp.get(k, 0), gdisp.get(k, 0)] for k in ["ALREADY-GOVERNED", "ELIGIBLE-NOT-MIGRATED", "RETAIN-IN-CODE", "OUT-OF-SCOPE", "UNRESOLVED", "BLOCKED", "MIGRATED"]] + [["Total", ln["records"], ln["rule_groups"]]])}

A *record* is one source site found by one worker. A *rule group* merges records that describe the same rule across components (ten merges, 19 records absorbed). Records by eligibility: {ln['records_by_eligibility']}.

## 2. Families F1–F11 and their parts

{tbl(["Family", "Part", "Proposed disposition", "Records", "Evidence and note"], mrows)}

Plan wave per family: {"; ".join(f"{a} → {c}" for a, b, c in fam_wave)}.

## 3. Source-backed conflicts with Plan v1.0 premises

1. **M1 / F1b is already governed.** In r08-v2 the f1ab record carries all five sets (`allowed_actions, allowed_adapters, allowed_units, allowed_institutions, allowed_authority_domains`); institutions and authority domains are validated, narrowed by intersection and may be deny-all (`registry_successor/v2_f1ab.py`). "Carried unchanged" is true only of the frozen r08-v1/S04 overlay (`registry_consumer/consumer.py:42`). Runtime enforces the F-01 five-set subset at effect time. The gap is negative oracles, not mechanism.
2. **F4 and F5 are partly governed.** `FAMILIES_V2` already registers `f4` (status and approval ages) and `f5` (class→age map). Plan v1.0 states F4/F5 are not covered. Identity/mandate ages, clock tolerance, the observation policy and the other F5 profile fields are not covered.
3. **Registry carries no operator-configurable value** and no slot for `max_amount`, `max_effects`, `allowed_target_prefixes` or `target_match`; Amendment 3 records them as caller-owned residuals. The Runtime effect-time guard compares only the five sets.
4. **F6/F7 candidates named by S02 are legacy or provider facts** (Runtime `permissions.json`, `dedupe_ttl_seconds`). The live homes of F6-like values are the action-manifest `authority_required`/`tools.allowed` declarations (unresolved ownership).
5. **S02 omitted whole repositories.** Twenty NEW families were found (section 4); only the redaction defaults and the tenant bound were visible to S02 outside Runtime/Control Plane.

## 4. NEW source-backed families

{tbl(["Family", "Records", "Disposition", "Eligibility"], newrows)}

Only five NEW families carry a non-retain disposition: `NEW:dedupe-ttl` (UNRESOLVED), `NEW:effect-limits` (UNRESOLVED; W8-091), `NEW:audit-budget` (ELIGIBLE-NOT-MIGRATED, reference profile only), `NEW:claim-scanner-terms` (UNRESOLVED; outside effect/authority) and `NEW:consequence-tier-delay-ceilings` (BLOCKED; owner confirmation, proposed and unenforced).

## 5. Constitutional constraints applied

CA05 (no invented policy, default or floor), CA12 (floors protected), CA18 (policy versioned, authenticated, reviewed; invariants protected from config override), and the Constitution's statement that no particular rules engine, storage form or activation mechanism is required. Every eligible row is governed by plan section 7: configuration may only narrow, unknown/absent/corrupt input never adds permission, and a measurable baseline plus negative tests must exist before any increment.
""")

# ---------------- migration-backlog.md
def ids(*gs): return ", ".join(gs)
T = "N/A: no implementation is proposed for this wave on current evidence."
M = [
 ("M1", "F1b allow-set completion (institutions, authority domains)", "ALREADY-GOVERNED; evidence gap", "A-002, B-010, B-012",
  dict(own="Registry owns the f1ab record (`registry_successor/v2_f1ab.py`, `families.py`); Runtime owns the policy fields and the effect-time guard (`registry_selection_authority.check_effect`).",
       contract="No change: existing r08-v2 `f1ab-local-execution-allowlist`. The plan premise ('carried unchanged') is contradicted by source.",
       eval="No change. `LocalExecutionPolicy.check` (protected evaluator) and the narrowing adapter already handle all five sets.",
       dep="None for source. Optional Runtime/Stack Qualification differential against the baseline `LocalExecutionPolicy` for the two sets (S05 equivalence was 3-set).",
       auth="Unchanged: Registry narrows; absence is `field_missing`; deny-all is an explicit `[]`.",
       proof="Existing: intersection ⊆ caller and ⊆ Registry. To add: exhaustive small-grid and subset property for the two sets; effect-time subset test on the two sets.",
       tests="Positive: narrowing of institutions. Negative: disjoint set → `applied_deny_all` naming the two fields; NFC/NFD and case-fold; decision-level selection crossing `scope.institution`/`scope.authority_domain`. Differential: five-set composed policy vs baseline policy. Missing today: all of these exist only for `allowed_units`.",
       indep="Tier 1 subject: independent qualification required before acceptance, as for V08. Builder tests are not independent.",
       prs="PR-1 Registry tests-only closure; PR-2 optional Stack Qualification differential; no contract PR.",
       block="AD-01 (reclassify M1 as evidence closure), AD-06 (equality vs subset for the two sets).")),
 ("M2", "F1c numeric ceilings (max_amount, max_effects)", "ELIGIBLE-NOT-MIGRATED (conditional)", "A-003, A-004, B-007, B-008, D-001",
  dict(own="Caller owns the ceilings today (Runtime `LocalExecutionPolicy`; action-manifest per-action ceiling). A Registry family would carry a narrowing ceiling only.",
       contract="New narrowing-only family (new family id under r08-v2, registered in both `FAMILIES_V2` and `IDENTITY_FAMILIES`) or r08-v3. The frozen contract states 'no max_amount slot'; Amendment 3 lists them as caller-owned residuals.",
       eval="Runtime guard extended to compare Registry ceiling ≥ effective ceiling inside the same atomic transaction; `safe_executor.py` evaluator unchanged.",
       dep="Runtime: adapter + guard + selection store identity. Control Plane: canonical policy binding / authorization-pin export carry a new family identity. Action-manifest authored ceilings stay caller data.",
       auth="effective = min(caller, Registry); absent/unknown/corrupt record → existing refusal/HOLD, never a higher value. Numeric domain must be fixed first (int or finite float ≥ 0, magnitude ≤ 2^53).",
       proof="Property: effective ≤ caller and ≤ Registry for all values incl. boundary equality, 2^53, float/int mix; guard refuses any effective value above the record.",
       tests="Positive: lower Registry ceiling applies. Negative: Registry above caller never raises; boundary equality; non-finite; NaN; bool-as-int. Differential: baseline policy with the ceiling set equal to the Registry value. Missing: no test names `test_amount_exactly_at_max_is_allowed` in the current Runtime tests (equivalents cited).",
       indep="Tier 1 (admission to an effect): independent qualification required.",
       prs="PR-1 contract decision record/amendment; PR-2 Registry family + vectors; PR-3 Runtime adapter/guard; PR-4 Control Plane binding; PR-5 Stack Qualification differential; independent review.",
       block="AD-03 (contract path), AD-07 (may the Registry ever carry these), numeric domain ruling.")),
 ("M3", "F1d target configuration", "ELIGIBLE-NOT-MIGRATED (conditional)", "A-005, A-006, B-004, B-006, D-002",
  dict(own="Caller owns prefixes and the mode choice. The mode vocabulary and separators (F2) stay in `safe_executor.py`.",
       contract="As M2. Prefix order relation (subset of prefixes vs prefix-extension) is non-trivial; mode narrowing order is not proven in source.",
       eval="Evaluator unchanged; only the effective policy values are narrowed. Segment-aware matching remains code.",
       dep="Runtime guard and Control Plane binding as M2. Action-manifest `allowed_targets`/`allow_any_target` are a second authored home.",
       auth="Narrowing only; an unknown mode or malformed prefix refuses; a record can never turn `exact` into `legacy-prefix`.",
       proof="Define a partial order on (mode, prefix set) and prove effective ≤ both operands, including dot-segment and separator edge cases.",
       tests="Existing S01 suite covers target modes and well-formedness (names `test_default_target_match_is_segment_aware_*` etc. NOT FOUND in the current Runtime tests; equivalents cited). Add disjoint/overlapping prefix negatives and mode-widening negatives.",
       indep="Tier 1: independent qualification required.",
       prs="After M2 contract decision: Registry family PR, Runtime PR, Control Plane PR, qualification PR.",
       block="AD-03, AD-07, order-relation ruling for prefixes and modes.")),
 ("M4", "F6 agent permissions", "OUT-OF-SCOPE (Runtime) / UNRESOLVED (action-manifest)", "B-014, D-008",
  dict(own="Runtime `permissions.json` is a legacy sample data file. The action-manifest `authority_required`/`tools.allowed` declarations are the live authored home.",
       contract=T, eval="Control Plane re-declares its own checks and does not import the manifest.", dep="Both sides would need to change for a Registry narrowing (CD-10).",
       auth=T, proof=T, tests=T, indep=T, prs=T, block="AD-10 (confirm F6 scope), AD-19 (are non-core repositories in scope).")),
 ("M5", "F7 dedupe/replay TTL", "OUT-OF-SCOPE / UNRESOLVED", "B-015, C-022",
  dict(own="Runtime TTL models a provider horizon; Control Plane `DedupeProfile` has three required ints with an invariant.", contract=T, eval=T, dep=T, auth=T, proof=T, tests=T, indep=T, prs=T,
       block="AD-13 (policy or provider fact).")),
 ("M6", "F3 budgets", "RETAIN-IN-CODE (floors); UNRESOLVED (residual)", "B-001..B-003, B-027, C-040, D-006, D-024",
  dict(own="Admission and parsing floors are mandatory and stay in code. The residual host-owned budgets (OpenShell timeout 1..30, CLI input cap, manifest cap, bounded-json defaults) have no authority effect.",
       contract=T, eval="Floors are in the protected evaluator path.", dep=T, auth="A budget may only be lowered, never raised above the floor.", proof=T, tests=T, indep=T, prs=T,
       block="AD-08 (floors stay floors), AD-09 (low-risk lowering candidates), scope: should the Registry carry resource budgets at all.")),
 ("M7", "F9 tenant-ID length", "RETAIN-IN-CODE", "B-003, C-035, C-036, D-004",
  dict(own="The 128 bound is repeated at 8 sites in 3 repositories with no shared source; the canonical binding additionally restricts the pattern.", contract=T, eval=T,
       dep="A narrowing config would desynchronize sites and could make valid tenants unrepresentable.", auth=T, proof=T, tests=T, indep=T, prs=T, block="AD-18.")),
 ("M8", "F10 diagnostic thresholds", "ELIGIBLE-NOT-MIGRATED (low priority)", "C-037",
  dict(own="Control Plane `reason_vocabulary` keyword defaults (5, 1); non-gating report.", contract="A Registry diagnostic profile with no authority semantics, if wanted.",
       eval="Report generator reads the value; no gate.", dep="Control Plane only.", auth="No authority semantics: a change alters a report, never an effect.",
       proof="A value change cannot alter any gate outcome (no consumer influences an authority decision).", tests="Positive/negative threshold behaviour; differential vs literal defaults. `test_rule_revision.py:118-120` (by name).",
       indep="Not required if Tier 3 is ratified; otherwise Tier 2 review.", prs="One Registry family PR + one Control Plane PR.", block="AD-23 (tier ruling).")),
 ("M9", "F8 demo lists", "OUT-OF-SCOPE / RETAIN-IN-CODE", "C-025..C-030",
  dict(own="Demo-only defaults; helpers that grant read/write authority; the legacy `PolicyGate` evaluator.", contract=T, eval=T, dep=T, auth="Demo grants confer authority and are not tunables.", proof=T, tests=T, indep=T, prs=T,
       block="AD-12 (retire or guard inert `policy_config.default_action` and demo helpers).")),
 ("M10", "F11 redaction defaults", "ELIGIBLE-NOT-MIGRATED (conditional)", "C-038, D-007, D-012",
  dict(own="Defaults in action-manifest (`[REDACTED]`), replay-bundle keyword defaults and the Control Plane `RedactionConfig`; the redaction mechanism and truncation stay in code.",
       contract="New narrowing-only family where narrowing means *more* redaction.", eval="Redaction mechanism (`redaction.py`) unchanged.", dep="Action-manifest, replay-bundle and Control Plane keep separate copies today (CD-06).",
       auth="A record may only add redaction; it can never turn payload redaction off.", proof="Effective redaction set ⊇ code default set for every input.", tests="Negative: attempt to disable payload redaction or fingerprint blanking must refuse.",
       indep="Confidentiality controls are treated as Tier 1 until reviewed (S02 section 3).", prs="Registry family PR, per-component consumer PRs.", block="AD-03, AD-19.")),
 ("M11", "F4 freshness", "PARTLY ALREADY-GOVERNED; remainder ELIGIBLE-NOT-MIGRATED", "A-007, A-009, C-001..C-006, C-019, C-020, B-016, D-011",
  dict(own="Registry f4 already carries `status_max_age_seconds` and `approval_max_age_seconds`. Control Plane constructor defaults (60/60/60/60/5), the observation policy (300/5 literal in `acp run`) and the Runtime recovery window (86400) are uncovered.",
       contract="Extend by a new family id or r08-v3; f4 is a closed two-int record.", eval="`bounded._fresh` and `_reconcile_observation` unchanged; values narrowed at construction.",
       dep="Mapping ruling: under a runtime-authority profile the class bound replaces the global status bound only for grant status (conflict and policy status keep the ctor bound). 60 and 300 govern different decisions; nothing relates them.",
       auth="min(host, Registry); a Registry age can only shorten the window; absent record keeps the host value.", proof="Property: accepted age ≤ min of both operands; clock tolerance cannot exceed the host value.",
       tests="Existing: `test_bounded_authorization.py`, `test_freshness.py` (by name). Add decision-time and effect-time differential, and the 60-vs-300 independence test.",
       indep="Tier 1: independent qualification required.", prs="Registry family PR, Control Plane PR, Runtime PR (recovery window), qualification PR.", block="AD-02, AD-03, AD-11.")),
 ("M12", "F5 authority-profile declarations", "PARTLY ALREADY-GOVERNED; remainder ELIGIBLE-NOT-MIGRATED", "A-008, C-008..C-011, C-021, C-031",
  dict(own="Registry f5 carries the class→age map; policy-binding/0.1 already carries host ceilings. `on_unreadable`, revocation assurance, reversibility and class declarations remain host profile values.",
       contract="New family id or r08-v3.", eval="`validate_extensions` (protected) unchanged.", dep="Trust anchors (producer keys, catalogue, signer sets) are never externalized.",
       auth="Only stricter directions: `refuse` over `bounded_tolerance`; longer assurance never allowed.", proof="Order relation per field (enum strictness order) with refusal on unknown values.",
       tests="`test_runtime_authority.py`, `test_reversibility.py` (by name). Add per-field narrowing negatives; note UNKNOWN_BEHAVIORS has one gate branch.", indep="Tier 1: independent qualification required.",
       prs="After M11 contract decision.", block="AD-02, AD-03.")),
 ("M13", "Delta and residual closure", "Closure item", "S02 §3a rows W8-041, W8-042, W8-068, W8-072; the 32 UNRESOLVED rows",
  dict(own="Lead and Architect.", contract="None.", eval="None.", dep="Importer pins, verifier reasons registry and hub component lock lag the current mains (AD-16, AD-17).",
       auth="None.", proof="None.", tests="Integrity tests of this G0 package.", indep="Not applicable.", prs="Per ratified resolution; no source changes in G0.",
       block="All AD entries; see `unresolved-decisions.md`.")),
]
out = ["# G0 migration backlog (proposal; M1–M13 sequence unchanged)\n",
       f"{HOLDS}\n",
       "This backlog maps eligible families onto the approved M1–M13 sequence. **Nothing here starts a wave.** The order is not redesigned; where source contradicts a plan premise the conflict is stated (family-eligibility-matrix.md section 3). Ten fields are given per wave: source ownership, Registry contract/version, evaluator integration, Control Plane/Runtime dependencies, authorization semantics, non-widening proof, tests (positive/negative/differential), independent qualification, proposed PR sequence, blocking decisions.\n",
       "## Recommended first implementation increment (after Architect authorization)\n",
       "**M1 re-scoped as negative-oracle closure for institutions and authority domains.** It needs no contract change, no source change in Runtime or Control Plane, and it builds the differential harness that M2, M3, M11 and M12 reuse. Everything else needs the contract-path decision AD-03 (new narrowing-only family id under r08-v2 vs r08-v3) first. This is a recommendation only; G1 is not authorized.\n",
       "## Summary\n", tbl(["Wave", "Family", "G0 finding", "Records"], [[m[0], m[1], m[2], m[3]] for m in M]), ""]
LBL = [("own", "Source ownership"), ("contract", "Registry contract / version"), ("eval", "Evaluator integration"), ("dep", "Control Plane / Runtime dependencies"), ("auth", "Authorization semantics"),
       ("proof", "Non-widening proof"), ("tests", "Tests (positive / negative / differential)"), ("indep", "Independent qualification"), ("prs", "Proposed PR sequence"), ("block", "Blocking decisions")]
for m in M:
    out.append(f"## {m[0]} — {m[1]}\n\nG0 finding: **{m[2]}**. Records: {m[3]}.\n")
    for k, lab in LBL: out.append(f"- **{lab}:** {m[4][k]}")
    out.append("")
(D / "migration-backlog.md").write_text("\n".join(out))

# ---------------- unresolved-decisions.md
AD = [
 ("AD-01", "Reclassify M1: F1b is ALREADY-GOVERNED in f1ab; confirm M1 becomes negative-oracle closure.", "A finding 2"),
 ("AD-02", "Reconcile Plan v1.0 'F4/F5 not covered' with the registered `f4`/`f5` families; map M11/M12 to the remainder.", "A finding 4"),
 ("AD-03", "Contract path for every new Registry-carried field: new family id under r08-v2 (hand edits to `FAMILIES_V2` and `IDENTITY_FAMILIES`) or r08-v3.", "A decision 5"),
 ("AD-04", "Add a single-source test tying `FAMILIES_V2` to `IDENTITY_FAMILIES` (no test asserts their key sets are equal today).", "A decision 3"),
 ("AD-05", "Ratify or replace the constant `MAX_SNAPSHOT_NODES = 1048576`, labelled PROPOSED in source.", "A decision 4"),
 ("AD-06", "For institutions and authority domains: equality ('carried unchanged') or subset (what Runtime enforces)?", "A/B"),
 ("AD-07", "May the Registry ever carry `max_amount`, `max_effects`, `allowed_target_prefixes`, `target_match`, given Amendment 3 records them as caller-owned residuals?", "A/B/C"),
 ("AD-08", "Confirm F3 limits stay floors (at most host-owned lowering).", "B"),
 ("AD-09", "Recovery window 86400 s and OpenShell timeout are the only low-risk resource candidates; confirm eligibility.", "B"),
 ("AD-10", "Confirm F6 (Runtime permissions) and F7 (Runtime TTL) as OUT-OF-SCOPE.", "B"),
 ("AD-11", "Mapping of the Registry F4 status scalar onto conflict/policy status when a runtime-authority profile exists.", "C surprise 5"),
 ("AD-12", "Retire or guard inert `policy_config.default_action`, `authority_records_from_policy_config` and demo helpers.", "C"),
 ("AD-13", "Is `DedupeProfile` policy or a provider fact?", "C"),
 ("AD-14", "Relationship of the hub's `ocs-registry-record/0` format to Registry r08-v2.", "D"),
 ("AD-15", "Constitution checkout HEAD `a4dd1111` inverts tier numbering relative to pin `1c2e920f`; confirm the pin remains authoritative.", "D"),
 ("AD-16", "Replay-bundle and evidence-pack importers accept only Control Plane `7a4bcd40` / Runtime `c5e97e87` / manifest `fa170815`; current mains are refused. Wave G3 changes will hit this.", "D"),
 ("AD-17", "The verifier vendors reasons 0.1/0.2 only; the Control Plane ships 0.3 (eight more codes).", "D"),
 ("AD-18", "Tenant-id bound 128 appears in 8 places across 3 repositories with no shared source.", "C/D"),
 ("AD-19", "Are hub, exchange, replay-bundle and action-manifest reference values in scope for the migration program?", "D"),
 ("AD-20", "Consequence-tier delay ceilings (T0 4h … T4 30d) are proposed and unenforced; owner confirmation needed (BLOCKED).", "D"),
 ("AD-21", "Claim-scanner term tables: in scope of the Registry?", "D"),
 ("AD-22", "Origin of the effect cap (W8-091): minimum of three declared integers; who owns each?", "C"),
 ("AD-23", "F10 tier: Tier 3 supportable (worker) vs Tier 2 minimum (S02 section 3).", "C"),
 ("AD-24", "Several test names cited by S02 are NOT FOUND in current Runtime tests; confirm the cited equivalents.", "B"),
]
unr = [m for m in C["rows"] if m["unresolved_tracking"]]
urows = [[m["id"], m["historical"]["loc"], m["historical"]["construct"][:70], m["unresolved_tracking"]["proposal_confidence"], m["unresolved_tracking"]["worker_still_configurable"],
          ", ".join(i[3:] for i in m["unresolved_tracking"]["linked_candidate_rule_ids"]) or "none", m["unresolved_tracking"]["proposed_resolution"][:230]] for m in unr]
rc = []
for Lt in "BCD":
    for x in json.load(open(D / f"evidence/worker-{Lt}/reclassification_proposals.json")): rc.append([Lt, x["id"], x["old_class"], x["proposed_class"][:90]])
(D / "unresolved-decisions.md").write_text(f"""# G0 unresolved items and Architect decisions

{HOLDS}

## 1. The 32 historical UNRESOLVED rows (individually tracked)

All 32 keep their historical classification **UNRESOLVED** in `historical-crosswalk.json` (`unresolved_tracking.g0_status = UNRESOLVED-PRESERVED`). The proposal column is a worker's source-quoted proposal with a confidence; it is not a resolution until the Architect ratifies it.

{tbl(["Row", "Historical location", "Construct", "Confidence", "Still configurable?", "Candidates", "Proposed resolution (truncated; full text in the crosswalk)"], urows)}

Decisive evidence summary: W6-042 (a missing `ObservationPolicy` always produces a hold) is an immutable control by source; W4-014/W4-015 are inert (no consumer); W8-091 stays open on source (see AD-22). On the workers' own assessment 16 of the 32 rows remain `still_configurable = UNRESOLVED`: W1-029, W1-056, W1-058, W1-073, W2-025, W2-036, W2-038, W2-067, W2-077, W2-082, W3-024, W3-063, W5-012, W5-023, W8-091, W9-007; the other 16 are assessed NO (not a configurable rule) but are still not reclassified.

## 2. Architect decisions required

{tbl(["Id", "Decision", "Source"], [list(a) for a in AD])}

## 3. Reclassification proposals (NOT applied)

Workers proposed {len(rc)} reclassifications. They are recorded here and in `evidence/worker-*/reclassification_proposals.json`; the historical classes in the crosswalk are unchanged.

{tbl(["Worker", "Row", "Historical class", "Proposed"], rc)}

## 4. Coverage limits that bear on these decisions

Test bodies were not read and no test was executed. Evidence-registry and evidence-attestation were not audited. Worker D read slices of Stack Qualification only. Hub docs, scenarios and fixtures, replay-bundle and evidence-pack validators, and ODES RFCs were not read. W3-063 and W1-029 were resolved by Worker B.
""")

# ---------------- g0-exit-report.md
gd = ln["groups_by_disposition"]; rd = ln["records_by_disposition"]
cfg_groups = gd.get("ALREADY-GOVERNED", 0) + gd.get("ELIGIBLE-NOT-MIGRATED", 0) + gd.get("UNRESOLVED", 0) + gd.get("BLOCKED", 0)
cfg_records = rd.get("ALREADY-GOVERNED", 0) + rd.get("ELIGIBLE-NOT-MIGRATED", 0) + rd.get("UNRESOLVED", 0) + rd.get("BLOCKED", 0)
(D / "g0-exit-report.md").write_text(f"""# G0 exit report — Registry family migration inventory reconciliation

Builder-side, non-authorizing. This report recommends; the Architect decides. {HOLDS}

## 1. Result

**Recommendation: G0 PASS (inventory complete) with 24 named Architect decisions; G1 remains blocked on AD-01 and AD-03.** The recommendation depends on the verification in section 7. PASS here means the inventory is complete and source-backed within the stated limits; it does not mean any family is approved, qualified or ready.

## 2. Historical reconciliation (S02, 620 rows)

{tbl(["Item", "Count"], [["Rows reconciled", cn["rows"]]] + [[k, v] for k, v in cn["by_historical_class"].items()] + [["Crosswalk status: UNCHANGED", cn["by_crosswalk_status"]["UNCHANGED"]], ["Crosswalk status: MOVED (line coordinates shifted; 31 of these are cumulative W8 coordinates with an unchanged file)", cn["by_crosswalk_status"]["MOVED"]], ["Crosswalk status: CHANGED (additive; class retained)", cn["by_crosswalk_status"]["CHANGED"]], ["Crosswalk status: DELETED", 0], ["Rows resolved by workers (43 candidates + 32 unresolved)", cn["worker_resolved_rows"]], ["UNRESOLVED rows individually tracked", cn["unresolved_tracked"]]])}

Historical ids and classifications are copied unchanged. No row was silently reclassified: the 20 worker reclassification proposals are listed in `unresolved-decisions.md` and not applied. The four S02 §3a rows are dispositioned: W8-041 → G0-C-017 (RETAIN-IN-CODE; liveness reaper interval), W8-042 → G0-C-018 (RETAIN-IN-CODE; safeguard toggle), W8-068 → G0-C-014 (RETAIN-IN-CODE; host trust data), W8-072 → G0-C-015 (OUT-OF-SCOPE; labels).

## 3. Current candidate counts

Definitions: a *record* is one source site; a *rule group* is a unique rule (ten merges across components). Dispositions are proposals.

{tbl(["Measure", "Rule groups", "Records"], [["Current configurable candidates (ALREADY-GOVERNED + ELIGIBLE-NOT-MIGRATED + UNRESOLVED + BLOCKED)", cfg_groups, cfg_records], ["Already Registry-governed", gd.get("ALREADY-GOVERNED", 0), rd.get("ALREADY-GOVERNED", 0)], ["Eligible, not migrated", gd.get("ELIGIBLE-NOT-MIGRATED", 0), rd.get("ELIGIBLE-NOT-MIGRATED", 0)], ["Retained in code", gd.get("RETAIN-IN-CODE", 0), rd.get("RETAIN-IN-CODE", 0)], ["Out of scope", gd.get("OUT-OF-SCOPE", 0), rd.get("OUT-OF-SCOPE", 0)], ["Unresolved", gd.get("UNRESOLVED", 0), rd.get("UNRESOLVED", 0)], ["Blocked", gd.get("BLOCKED", 0), rd.get("BLOCKED", 0)], ["Total", ln["rule_groups"], ln["records"]]])}

Records by eligibility: {ln['records_by_eligibility']}. New families discovered: {ln['new_families']} (five with a non-retain disposition). 

## 4. The 60-versus-300 relationship

The 60 s value governs the age of **authority-input reads** (grant status, identity, mandate, approval, conflict, policy): `BoundedAuthorizationWorkflow.__init__` defaults (`bounded.py:1271-1275`), `_fresh` at decision and effect time. The 300 s value (with 5 s tolerance) governs the age of the **destination observation** used before first dispatch, after dispatch and in `reconcile()` (`cli_run.py:510`; `ObservationPolicy.max_age_seconds` has no default). Nothing in code compares or orders them; an observation may be older than an authority input is allowed to be. Two distinct 5 s clock tolerances exist. The Registry f4 record carries only the 60-type status and approval scalars. Lead spot-check: `cli_run.py:510` and `bounded.py:1271-1275` read as stated; `bounded.py` is byte-identical to the S02 pin. A hub scenario placing 300 and 60 side by side is consistent with two concepts but is not evidence about the Control Plane.

## 5. Security-boundary check (Phase 5)

No record whose kind is IMMUTABLE_CONTROL is proposed ELIGIBLE-NOT-MIGRATED (checked by the integrity test). Constitutional safeguards, authentication/provenance, grant/approval authority, atomic effect/evidence transactions, revocation enforcement, fail-closed validation, mandatory floors, serialization integrity, replay/rollback protection, the closed refusal vocabulary and `engine/safe_executor.py` evaluator semantics all appear only as RETAIN-IN-CODE. Every eligible row is monotone narrowing: Registry configuration may only narrow, unknown/absent/corrupt input never adds permission. `immutable_controls_seen.json` (A 26, B 25, C 44, D 32) lists what was deliberately left alone. Notable: the effect-time guard compares only the five allow-sets with a Registry record; `max_amount`, `max_effects`, `allowed_target_prefixes` and `target_match` are never compared.

## 6. Findings that need attention outside the migration program

Downstream importers pin older producer revisions (AD-16); the verifier lacks reasons 0.3 (AD-17); the hub component lock and Stack Qualification effective pins are the old generation (7 of 11 locked components moved); the Constitution checkout is ahead of the pin with inverted tier numbering (AD-15); `remove_authoritative_state` deletes grant rows without a retained-revocation record while approvals gained `authority_approval_revocations_v1` (G0-B-029; an authority-surface question, not a config value).

## 7. Verification

{VERIFY}

Lead spot-checks (executed by the lead against the checkouts): f1ab field set; zero Registry code hits for `max_amount|max_effects|allowed_target_prefixes|target_match`; Runtime `tenant_id` 128 bound; Control Plane `cli_run.py:510` and `bounded.py:1271-1275`; `bounded.py` identical to the S02 pin; Control Plane and Runtime churn since the S02 pins (file lists in `source-baseline.md`). Worker claims not spot-checked are labelled worker findings in the ledger.

## 8. Limits

AI workers and CI are not independent assessors. Dispositions are proposals. Test bodies were not read and no component test suite was executed. The inventory is as complete as the grep-plus-read method allows; it is not proven exhaustive. Not read: see `source-baseline.md` section 4 and each worker's `notes.md`.

## 9. Holds unchanged

{HOLDS} The V09 candidate manifest and all historical evidence files are unchanged; no component source was changed; no workflow pin moved.
""")
print("docs written")
