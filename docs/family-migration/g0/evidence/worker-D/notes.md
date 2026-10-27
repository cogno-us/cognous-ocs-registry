# G0 Worker D notes (read-only; non-Registry/CP/Runtime repositories)

## Scope covered
Cloned shallow, one at a time, no failures: action-manifest, open-control-stack (hub), governance-evidence-pack, replay-bundle, governed-exchange, ODES, verifier, evidence-registry, evidence-attestation, institutional-governance. cognous-agent-control-plane, cognous-agent-replay-bundle and moltbot-safe are RENAMES: they resolve to the identical HEADs of control-plane (d66ae07f), replay-bundle (40012b8c) and the Runtime (0dde0ef7). Not re-inventoried (workers A/B/C). HEAD SHAs are in `repositories.json`. Constitution and stack-qualification were already checked out.

## Not read (do not infer anything)
- evidence-registry and evidence-attestation: README and a literal grep only; judged NOT RELEVANT, not audited.
- hub: docs/, examples/ (except one scenario for 60/300), fixtures/, scenarios/, collateral/, most of tools/ (mvp_*, scanner_tree_analysis, deployment_review, verify_candidate_archive), tests/.
- replay-bundle/evidence-pack: only constants/imports/freshness paths; validators and renderers not audited. ODES: src/ literal grep and contract constants only; RFCs, conformance, profiles not read.
- GAX: only transport.py constants and gax_ref.py header.
- stack-qualification (28k files): read workflow names, tools/v1_validation.py top, suites/_pins.py, the v1-2026-10-16-a freeze manifest and refreeze log. Not read: schemas/, scenarios/, comparators/, docs/, process/release-gate preregistration thresholds.
- No test was run; test names are from grep output only. Most candidates therefore say "NOT READ" for tests.

## Method
`git ls-files`, README heads, grep for `^[A-Z_]{4,} =`, MAX_/max_/ttl/seconds/default literals, schema minimum/maximum, then reading the hit. Candidate line ranges and snippets were taken mechanically from the files at the recorded SHAs.

## Surprises / findings that need an Architect decision
1. **Constitution tier numbering is inverted between the plan pin and the checkout.** The checkout HEAD is a4dd1111 (not the pin 1c2e920f). The pin (present as an object) says "Tier 1 critical ... Tier 3 routine"; HEAD says "Tier 1 routine; Tier 3 critical" (ENGINEERING_CONSTITUTION.md and ORCHESTRATION.md, 8+4 lines). All tiers in my files use the pin meaning (Tier 1 = authority/admission). Anyone reading the checkout at HEAD will misread tiers. HEAD also adds addenda/RISK_BASED_TESTING.md. The Constitution fixes: CA05 (no invented policy/default/floor), CA12 (floors protected), CA18 (policy versioned, authenticated, reviewed; invariants protected from config override), "no particular rules engine, storage or canonical kernel is constitutionally required". It leaves open: which values are configurable, the storage form, and the activation mechanism.
2. **Downstream importers pin exact producer revisions and do not know the current CP/Runtime.** Replay importers.py:81-96 and evidence-pack importer.py:95-100 accept CP 7a4bcd40 / Runtime c5e97e87 / Manifest fa170815; "any other runtime revision is refused as an unsupported combination". Current mains (CP d66ae07f, Runtime 0dde0ef7) appear in neither. Waves G3 will change producer revisions and therefore hit this (CD-03). Pin comments call themselves "alpha scaffolding ... removed at end-of-alpha (P5)".
3. **Hub component-lock and stack-qualification effective pins are the old generation** (CP 0a41faa9, Runtime ec728da6): 7 of 11 locked components have moved at their HEADs (CD-04, CD-12).
4. **Verifier lacks the reasons-0.3 registry** (only 0.1 and 0.2 vendored; default 0.1) while CP HEAD ships 0.3 with 8 more codes (CD-01). Content of 0.1/0.2 and both ODES schemas is byte-identical to the sources.
5. **Tenant id bound 128 appears in at least 8 places in 3 repositories** (CD-05); no disagreement, no shared source.
6. **60 vs 300 evidence (not a resolution).** CP cli_run.py:510 `ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5)`; CP bounded.py:1271 `status_max_age_seconds: int = 60`; one retained hub scenario has obligation `max_age_seconds: 300` and reconciliation `observation_max_age_seconds: 60` side by side. Suggests two concepts (evidence-age vs observation-age) but CP consumer code is worker C's. Also an unrelated 60 s admin-command window in the hub protected_destination.py:154.
7. **Two registry-record formats.** The hub has `ocs-registry-record/0` (tools/registry_records.py, step 2.1, OCS-DGR-ARCH/1.0.0) with its own rule table, dispositions and fail_closed-only missing treatment; the Registry repo has r08-v2. Relationship is not documented in what I read. Ask the Architect whether the hub profile is superseded.
8. **Action manifest is a second, live, authored home of F1c/F1d/F6 values** (effect_limits, target_policy, authority_required, tools.allowed). The CP re-declares its checks (no import), so a Registry narrowing needs both sides. Relevant to F6, whose baseline S06 said was outside the import.

## Candidate NEW families (not F1-F11), with evidence
- NEW:manifest-default-posture: `default_action` default `escalate` (G0-D-003). Recommend RETAIN-IN-CODE.
- NEW:destination-admission-rate-limit: 128/60 s, 64, 60 s command window (G0-D-017). Source says non-configurable by design.
- NEW:audit-budget: AUDIT_DEFAULTS with storage ceiling (G0-D-018): best example of narrow-only host value, but reference profile only.
- NEW:inventory-staleness: lifecycle_inventory.reconcile max_age (G0-D-023). Caller-supplied, non-authorizing; the only lifecycle/obsolescence-like threshold I found. No lifecycle threshold literal exists in these repos.
- NEW:claim-scanner-terms: scanner RULES term tables (G0-D-025); the hub names these as the first data-not-code partition. Outside effect/authority; Architect to decide scope.
- NEW:consequence-tier-delay-ceilings: T0 4h .. T4 30d, proposed, unenforced (G0-D-026), BLOCKED on owner confirmation.
- NEW:exchange-delivery-retry (G0-D-014) and NEW:qualification-harness-thresholds (G0-D-029, OUT-OF-SCOPE).
- Not found: action-manifest permission/effect limit literals beyond the above; evidence-pack size/retention limits (none beyond 8 MiB cap); replay-bundle limits beyond ingress/importer caps; exchange admission limits (none).

## S02 omissions attributable to uninspected repos
S02 surveyed only Runtime and CP files (W1-W9). Everything in G0-D-001..029 is therefore absent from S02 except the tenant bound (W1-027/W6-008) and the redaction defaults (W9-002 CP side). Specifically uninspected by S02: action-manifest (authored limits, defaults, 100000/32 budget, 4 MiB cap), replay-bundle (importer caps, redaction defaults copy, recorded-freshness re-check), evidence-pack, hub reference_profiles and tools, institutional-governance tier ceilings, verifier, ODES, GAX. No S02 row was mis-classified on this evidence, so `reclassification_proposals.json` is empty. No `s02_resolution.json` (no S02 rows assigned).

## Counts
29 candidates: 15 CONDITIONAL, 14 NOT_ELIGIBLE; dispositions 13 RETAIN-IN-CODE, 9 ELIGIBLE-NOT-MIGRATED, 3 UNRESOLVED, 3 OUT-OF-SCOPE, 1 BLOCKED. 32 immutable look-alikes. 12 contract-dependency records.
