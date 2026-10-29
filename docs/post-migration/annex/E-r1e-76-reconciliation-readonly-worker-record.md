# R1-E (Registry PR #76) reconciliation - read-only T0 inspection, 2026-10-29

Disposition: **B - supersede with a smaller addendum**, scheduled AFTER R6 acceptance (R1 consolidation), not parallel with R5.

## 1. Ergonomics facts at bea582b
- README (l.3, 11-13, 36, 45, 126-134): 0.1.0-draft, "merged" not selected, not in hub lock, non-authorizing; commands demo, validate, init, doctor, evidence render, dashboard, schema export, ci. HOLDS.
- pyproject.toml:30-35 `stack` = aam fa17081, acp 0a41faa97269..., arb 028f63d, agep a3ebbb9. Four components. HOLDS.
- Registry / EffectivePolicySnapshot / lifecycle: no reference in src/cognous_ocs/lock.py or doctor.py (grep). HOLDS.
- README l.145: "No control-plane passthrough layer exists; only the demo calls `acp run`". Only demo.py runs real `acp run` + `acp validate-run` (demo.py:403,425); validate uses aam/arb/agep only; doctor is local checks (+ manifest version lookup); render/dashboard are static readers.
- Pin ancestry (control-plane clone): `git merge-base --is-ancestor 0a41faa97269 main` = yes (ancestor of 739efe7). But `git ls-tree 0a41faa97269 src/agent_control_plane/ | grep registry|effective` = EMPTY; main has registry_effective_policy.py, registry_governed_{policy,lifecycle}.py, registry_*_governance.py, effective_configuration_binding.py. So the pinned acp has NO Registry-governed layer: any E2/E3 work forces a pin bump of the Control Plane (the addendum says "do not silently refresh pins", so it needs its own decision).

## 2. Supported APIs for E1-E3 on current mains
- Control Plane `agent_control_plane/__init__.py` (`__all__` at l.75): zero registry/EffectivePolicySnapshot/GovernedPolicyWorkflow/binding names (grep count 0). Governed layer is importable only as submodules (internal). `acp` CLI (cli.py) subcommands: run (cli_run), validate-run, validate-replay, redact-*, sign-replay, verify-signed-replay. No registry/inspect/doctor/binding command. 
- Exists as module-level (not exported): `registry_effective_policy.EffectivePolicySnapshot` with `.identity_digest`, `.family(slot)`, `resolve_effective_policy`, `build_snapshot`, `FAMILY_TABLE`, `SCHEMA_REVISIONS` (l.25,37,84-126); `effective_configuration_binding.classify()` returning BOUND/MISMATCH/INVALID/VERSION_UNSUPPORTED/LEGACY/UNBOUND_AFTER_CUTOFF (l.40-41, 193), `record_defect`, `digest_of`, `mint`; `registry_governed_policy.derive_policy` / `GovernedPolicyWorkflow`; `RegistrySelectionRefused`/`Refusal` (registry_governed_lifecycle l.57-65).
- Registry main: no pyproject/packaging, no CLI, no `__all__` outside registry_consumer (S04: apply_registry_overlay, TrustConfig, OverlayResult, CONSUMER_REASON_CODES). registry_successor/__init__ is docstring-only. Engine functions exist (engine.verify.verify_selection, selection.parse_selection_envelope, identity.effective_policy_digest, families.lookup_for/table_for_contract_version, v2_codes) but none is declared public/stable.
- Mapping to E2 needs: frozen contract versions = no list/inspect API (only per-module constants/table_for_contract_version); family presence = FamilyTable internals / GovernedFamilies; selector/scope mismatch = refusal codes inside verify/check_scope, no standalone read-only call; selection validity = verify_selection needs trust, verifier, now, record (an inspection call would need caller-supplied trust material); effective-policy digest = snapshot.identity_digest (needs live resolve with host profile); binding status = classify() needs a persisted runtime_authority + live member from a running workflow.
- NEW-API / STOP findings: (a) public export of governed layer or a read-only `inspect` entry on Control Plane = new component API (STOP per addendum s5); (b) a read-only Registry verifier/inspector with a stable schema = new Registry API; (c) E2 "missing effective-policy binding" and "trust/epoch errors" require reading persisted store/binding = touches persisted-binding semantics and the "Unsigned persistence store" limit (post-migration 00 l.45); (d) E3 "actual effective restrictions" requires disclosure policy decisions; (e) importing registry_* internals would violate R1 plan "use supported interfaces". Net: E2/E3 as written are NOT satisfiable from existing supported APIs; they are a new-API track. E4 (static render of operator outputs) and E5 (schemas) need no component change.

## 3. Conflicts with R1 plan / P1 / R1-START
- Ordering: R1 plan s3 R2-R4 consolidate verification, identity plumbing and "divergent EffectivePolicySnapshot construction" (R4). Building E-work on those modules in parallel with R5 targets surfaces R2-R4 may reshape; R1 plan s2 keeps public entry points but internals move. Plan mandatory order (l.12) has freeze then qualification; the addendum's parallel-with-R5 is a plan amendment not covered by R1 plan; post-migration/03 l.29 treats R1-E as non-dispatchable.
- Freeze/candidate: R1 plan s8 index is Registry/component SHAs; addendum s6 adds Ergonomics SHA to R7 and P1 manifests and (s2) "include it in the qualification candidate" - enlarges the T4 Tier 1 candidate with a new repo (CLI + subprocess runner + dependency pins). Not consistent with "later alteration = new candidate". P1 (l.5, 28, 49-51) already expects a P2 harness and per-run manifest; presentation-only reuse is compatible, freeze inclusion is optional and should be an Architect decision.
- Authority: non-goals s4 and deliverables E2-E6 do not contradict (read-only, no sign/activate/revoke). Residual risks: E2 "never an invented verdict" vs naming "expired/withdrawn/invalid" classes locally; E3 disclosure of effective restrictions; E4 "expected vs actual decision" display could read as a verdict. Not an authority conflict, but needs a wording guard.
- Governance pin: addendum cites constitution 1c2e920; R1-START records use dcdbe3b (adds only LICENSE, prompt-engineering addendum, README, assignment schema vs 230c0af); adoption records still 1c2e920/230c0af; decision D7 open (04 l.13).

## 4. Outdated assumptions
- Control Plane 0a41faa97269: ancestor of main but predates the entire Registry-governed layer; "newer Control Plane EffectivePolicySnapshot" is now on main (not exported).
- "Prerequisite: 19/19 integrated, D-06/D-07/AR-1 approved": 19/19 implementation integrated, 0 independently accepted (00 l.32); D-07 correction on main via #97; D-06 binding present. R1 plan l.14 said not presumed resolved - now resolved on main, but Architect confirmation of R0 entry still pending (03 l.23). R1 baseline not yet accepted (R1-START in progress).
- Parent PR #73 / downstream #74 merged: fine. Addendum is open/unmerged proposed (00 l.39).
- Hub lock reconciliation: Ergonomics README says pins equal hub lock (l.126-134), but Ergonomics itself is not in the hub lock; the hub lock must also be re-read at its current head (not done here).
- Registry main is now 2815643 (closeout #78); addendum text predates #76-#78 state.

## 5. Disposition B - proposed outline of the smaller addendum (<=1 page)
Remove: E2 and E3 as commands (registry doctor/inspect on live Registry state), the "parallel with R5" ordering, the mandatory Ergonomics SHA in R7 and in the qualification candidate, the 1c2e920 governance pin (cite the adopted revision per D7), any reading of persisted bindings, the "trust/epoch errors" and "expired/withdrawn" diagnosis classes unless a component emits them.
Keep: non-goals (s4), read-only/one-way dependency, UNVERIFIED-never-PASS, redaction, byte-for-byte display, offline tests.
Outline:
1. Scope: presentation-only static rendering of sanitized, operator-produced P1 outputs (E4) plus schema/tests/docs (E5, E6); pin inventory (E1) as a report.
2. Prerequisites: Architect accepts R6; R7 freeze exists; Control Plane/Registry public output contract for P1 reports defined by the P1 P2 harness (not by Ergonomics); Ergonomics pin bump decision for acp (0a41faa lacks governed layer).
3. Interfaces that exist today: JSON/report artifacts produced by P1 harness; acp run/validate-run, aam/arb/agep CLIs; Ergonomics dashboard/evidence render/schemas. No registry_* imports.
4. Deferred/new-track (separate decision): Control Plane read-only snapshot/binding-status export, Registry inspection API (would be E2/E3).
5. STOP: new component API, altered refusal semantics, persisted-binding change, new external access, any PASS shown without component verification.
6. Ordering: after R6/R7; Ergonomics not in the Tier 1 candidate by default (P1 evaluator manifest only), decided by Architect.
Before vs after R1 consolidation: AFTER - interfaces and APIs move in R2-R4; consuming or defining them earlier risks rework and enlarges the baseline/freeze scope.

## Unverified
Hub component-lock.json current contents; Ergonomics tests/CI results (not run); doctor's exact component calls (read only partially); full Registry engine public surface beyond listed defs; whether D-06/D-07/AR-1 approvals are recorded as Architect decisions (only code state checked).
