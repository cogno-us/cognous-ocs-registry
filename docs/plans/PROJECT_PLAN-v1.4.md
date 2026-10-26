# OCS Registry — Static Engineering Plan v1.4
Date: 2026-10-26
Status: **OPERATOR-APPROVED; effective upon merge of the adoption PR**. Approval authorizes **G0 planning/profile freeze only**; it does **not** authorize implementation S01–S09, qualification execution, release, publication, production, cloud, paid calls, or real-world effects.
Program authority: Cognous operator. Plan custodian: OCS Architect. Implementation: separately authorized bounded component builders.

## 1. Purpose and source authority
Deliver one demonstrable and independently assessed Registry → Control Plane → Execution Runtime governance workflow, rather than an open-ended registry expansion. The original S01–S06 and v1.3 closeout remain historical, not retrospectively reclassified.

Frozen planning baseline: Registry main `6a050f2350a59f998a606183817d5ece2bc2a321` (closeout PR #38); [closeout ledger](../closeout/program-closeout-2026-10-26.md) and [planning inputs](../closeout/v1.4-planning-inputs.md). Plan v1.3: [retained adopted file](PROJECT_PLAN-v1.3-DRAFT.md), blob `c20c981ac19c64cc7f8c15ad27a8a2ee5e681c95`, adoption PR #20. Preserved v1.1/v1.2 plans remain authoritative for their historical increments. Engineering Constitution pinned at [1c2e920f](https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md); check ADOPTION.md and applicable CA01, CA02, CA04, CA07, CA09–CA12, CA14, CA16, CA18–CA20, CA23.

Frozen adopted contracts: `r08-v2` and Amendment 1, TR-01, DR-CP-AGE-1, and [ADR-REG-S4-0](../decisions/2026-10-26-adr-ext-s4-0-integration-contract.md), which adopts AD-1..AD-5 alternative A and the eight immutable reasons-0.3 names. Do not redesign or modify their historical records. A contradiction requires a narrowly scoped ADR and operator escalation if material.

## 2. Success criterion and candidate profile
**Target capability:** authenticated Registry selection fixes a typed effective-policy identity; Control Plane binds it to an approval/claim; Runtime enforces the currently applicable activation and approval atomically at effect commit, retaining replayable positive and negative evidence and refusing changed/unknown authority.

**Candidate** (NOT frozen until G0 operator decision): F1a `allowed_units`, `allowed_adapters`, `allowed_actions`; one synthetic tenant and governed scope; local safe emulator; Linux x86-64, CPython 3.11–3.13; synthetic Ed25519 keys (not operational trust or ceremony). Existing Registry F4/F5 integer-second families may be reused only if required by the adopted scenario and its owning consumer is ready; their presence does not automatically expand active scope.

Required demonstration: one allowed and one refused operation; tampered/unapproved/expired selection refused; approval binding substitution refused; withdrawal/revocation between approval and effect refused; ratchet and lineage downgrade refused; replay and stale generation refused; restart/restore or missing anchor fails closed; unchanged no-binding claims remain byte-identical. Preserve the full ADR AR-01..AR-27 obligations for the applicable path, explicitly marking any unsupported test BLOCKED/NOT RUN, never silently dropping them.

**Exclusions:** multi-tenant/multi-scope generalization, other operating systems, new rule families, shared ISS/GCR authority, broad 15-repository migration, generalized policy interpreter, automatic latest selection, external effecting/production workflows, broader dynamic activation, unsupported character extensions, and operational key ceremony. Unsupported customer capabilities must be named in the G0 record.

## 3. Gate G0 — profile and dependency freeze (ONLY authorized work)
Owner: Architect with scenario inventory/qualification input; operator approves scope. Duration target 1–2 working days. One documentation-only PR.
- Reconcile v1.3 P2–P6 and R07–R18 obligations against EXT cards; classify SATISFIED / REQUIRED / DEFERRED / NOT APPLICABLE / UNVERIFIED, with owner, exact source and rationale; do not re-run the earlier Inventory Worker audit.
- Select the smallest actual customer/security scenario and predeclare its scenario IDs, supported F1a fields, consumer owners, inputs, signed-selection/effective-policy pins, authority states, safe effect emulator, refusal/evidence expectations and exclusions.
- Decide whether F4/F5 or Control Plane EXT-S3-1..3/per-class minimum are required by that scenario based on existing R6 implementation and exact source inspection. Do not rebuild helpers merely to complete old sprint labels.
- Identify the ownership of cryptographic assurance, independent Tier 1 oracle/lead, CCTV vector licensing and emulator trust limitations. No claim of independent qualification.
- Publish an exact candidate configuration manifest, acceptance matrix, negative outcomes and dependency crosswalk. Operator approval of the profile is required to leave G0.
**STOP after G0 PR; no S01 without explicit operator implementation authorization.**

## 4. Bounded mini-sprints (planned, NOT authorized)
Each row is one primary deliverable and normally one PR, with one exact owner, acceptance test pins, adverse conditions and a PASS/BLOCKED exit. Target 1–3 days; 5-day planned maximum; split rather than sprawl.

| ID | Owner and bounded deliverable | Dependency | Exit / acceptance | Estimate (working days) |
|---|---|---|---|---|
| S01 | Registry: EXT-S1-6 withdrawal and snapshot-version floor; preserve `r08-v2` | G0 | Valid withdrawal, stale snapshot, replay and invalid transition typed refusals; existing verifier tests pass | 2–3 |
| S02 | Control Plane: EXT-S4-4 successor claim-carried binding under claim commitment; no-binding path byte-identical; no `bounded.py` semantic change | S01 if G0 requires withdrawal paths; R6 #84 | AR-01/06/20, substitution negatives, unchanged old claims | 2–3 |
| S03 | Cross-repo qualification: EXT-S4-5 exact-head re-pin and S2-1/S3-1 regression; no source semantics edit | S02 | Recorded Registry/CP/Runtime heads and reproducible pass/fail/skip evidence | 1 |
| S04 | Runtime: first part of EXT-S4-2, durable governed-scope state, lineage, ratchet, revocation/high-water/generation, closed 24-member log and external-anchor restore fence | S03 | Transactional replay consistency; rollback, rebaseline, lineage/ratchet and log corruption fail closed | 3–5 |
| S05 | Runtime: second part of EXT-S4-2, typed selection guard in `execute_claim_atomic`; existing `engine/safe_executor.py` unchanged | S04 | Commit-time admission/refusal, changed-condition race, expiry, key revoke, retries, failure evidence; existing Runtime safety invariants pass | 3–5 |
| S06 | Existing stack-qualification/emulator: EXT-S4-3 end-to-end integration | S05 | Applicable AR-01..AR-27 and existing golden/conformance vectors with raw evidence, allowed/refused, restart/replay, honest SKIP/NOT RUN | 2–4 |
| S07 | Independent security assessment: verifier/canonical-base64 and Runtime atomic/recovery paths | S06 candidate; independent reviewer | Findings resolved or gate BLOCKED; EXT-S1-7/#34 SECURITY-HELD until genuine independent review; no AI-as-independent claim | 3–5 |
| S08 | Independent Tier 1 scenario qualification: frozen exact-pin batteries and distinct oracle | S07 security gate; named lead | Qualified/failed/incomplete independent verdict; preserve adverse cases and pin/evidence custody | 3–5 |
| S09 | Evidence freeze, handover and truthful candidate status (not release) | S08 | Stable exact source/profile/test pins, unresolved risk register, documented operational exclusions | 1–2 |

Estimated bounded work: 18–33 working days including G0, excluding independent reviewer waiting/availability; not a promised delivery date. Work may proceed concurrently only for disjoint read-only inventories and test planning. Shared authority state, source pins, claim schema and transaction code changes remain serialized.

EXT-S4-1: NOT REQUIRED. S02 → S03 → S04 → S05 → S06 preserves the adopted EXT-S4 dependency direction while splitting Runtime's large unit into two reviewable increments. EXT-S1-9 adversarial cases and EXT-S1-8 kit are reused within acceptance/independent testing, not silently discarded. EXT-S2-1/2 and EXT-S3-1..3 obligations enter the G0 crosswalk; add only necessary bounded prerequisites through a **separate operator-approved plan amendment** if the minimum profile cannot otherwise run. EXT-S5/EXT-S6 obligations map to S07–S09; no automatic equivalence or qualification transfer.

## 5. Mandatory engineering and security constraints
- Registry stores authenticated typed governed parameters, not grants, scripts, an arbitrary evaluator or effect authority. Code owns mandatory admission and safety invariants.
- Record publication, issuer selection approval and consumer activation are separate. No `latest` default. No registry-issued OCS effect authority.
- Mandatory/optional participation, explicit positive fallback basis and all typed missing/unknown/refusal classes follow ADR-S4-0. Never turn unknown authority or evidence into permissive fallback.
- `scope_required` ratchet never clears; governed-scope `selection_id` replacement prohibited in V1. Generation and high-water never restart to resurrect approvals.
- Consumer-owned state, 24-member logged preimage including `reasons_registry_label` and `reasons_registry_sha256`, authenticated recovery and external-anchor limitation per ADR. No false operational custody claims.
- Atomic verification occurs inside Runtime's established SQLite `BEGIN IMMEDIATE` effect path; no second authority or network call under the transaction; preserve `engine/safe_executor.py` (historical protected blob `2fc880da`).
- Fail-closed REFUSE / REFUSE_STALE / HOLD mapping and immutable reasons-0.3 vocabulary; do not silently invent new reasons.
- Source, manifest, dependency, lockfile and reason-registry exact pins retained; no write/merge to other components without authorization.
- Tests must include positive, invalid, substituted, missing, stale, restore, after-approval revocation and failure-evidence controls; explicit failing/skipped cases. Builder test or Copilot/AI review is never independent Tier 1 qualification.
- No paid calls, production/external effects, cloud deployment, operational credential/key ceremony, releases, tags, publication or production without separately authorized scope.

## 6. Sprint protocol and change control
Each instruction and PR cites this exact adopted plan/head, the pinned Constitution, applicable ADRs, sprint ID/authorization, files/owner, source baseline, test commands, expected oracles and exclusions. Builder performs build → test → fix → retest → commit. Routine repair within an authorized sprint is allowed; new scope, architecture or family is not. A material new issue blocks only an approved scenario or mandatory security invariant; otherwise DEFER with owner and impact.

Static plan is immutable after adoption; any material change requires operator-approved versioned successor or documented bounded amendment. `docs/sprint-status.md` is the sole live status and retains progress by sprint, pinned heads, PASS/BLOCKED and gate evidence. Decisions belong in dated `docs/decisions/`; qualification artifacts live in existing Stack Qualification infrastructure. No inferred automatic advancement or independent qualification. Preserve v1.3 and all earlier plans.

## 7. Decision rights and final gates
- **Operator** adopts G0 minimum scenario/profile; approves material new implementation scope, spending, production/release/publication and architectural boundary changes.
- **Architect and component owners** decide technical mappings, named functions, bounded test plumbing and review disposition inside authorized scope; cannot self-authorize new sprints or certify their own work.
- **Independent security reviewer** decides whether cryptographic and effect-boundary security findings are resolved; remains separate from builder.
- **Independent Tier 1 lead** declares qualification with an independent oracle; appoint before S07, preferably before S06 oracle freeze.
- **No automatic release** after S09. Operator separately authorizes release, publication and production.

## 8. Current program state
Existing contract and developer-tested Registry functionality: preserved as in merged closeout. No Registry → Control Plane → Runtime end-to-end workflow exists. EXT-S4 code implementation NOT AUTHORIZED; Tier 1 NOT STARTED; Ed25519 adapter SECURITY-HELD; RELEASE / PUBLICATION / PRODUCTION: HOLD. Next action after adoption: bounded G0-only preparation and operator profile decision.
