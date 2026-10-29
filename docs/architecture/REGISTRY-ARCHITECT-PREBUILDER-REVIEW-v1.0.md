# Architect pre-builder review — Registry 19 target (2026-10-28)

Status: REVIEW FINDINGS AND DECISION PROPOSALS, NON-AUTHORIZING. Applies to Registry PR #68 at initial head 8344c4bfbe33432d78f0fe8548f724058f66bacd; read with Engineering Constitution and ADOPTION.md @ 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b, Static Migration Plan v1.1 section 12, Engineering Plan v1.5 and adopted audit PR #60.

## 1. Read-only consistency findings

- Inventory reconciliation: five allow sets + two numeric ceilings + two linked target fields + two F4 scalars + one class freshness + one unreadable + one revocation assurance + one terminal revocation + one irreversible + one deadline anchoring + two observation fields = **19**. The two target fields constitute **one jointly narrowable unit**, not independently applicable policy levers.
- Audit: 19 manageable parameters across 12 canonical rules; do not equate 19 with 19/444 rules. Three audit BLOCKED fields are not authorized for migration. Last verified merged 13/19 integrated, six outstanding, zero independently accepted.
- Preserve historical r08-v1–r08-v5 envelopes, signature domains, frozen vectors and protected evaluators. A future unified successor does not license in-place rewrite.
- CI on initial PR head 8344c4b completed successfully (Registry tests run 40802425789). This checks repo CI, **not** architecture acceptance, independent Tier 1, or proof of cross-component contracts.

## 2. Explicit architectural choices, with preferred proposals

**D-01: Integration unit** — **Recommend** one host-bound immutable EffectivePolicySnapshot (typed field carriers + source and family identity), built from valid original host policy plus all required authenticated Registry restrictions. Do not introduce a generic executable rule language or standalone Registry authorizer. Final schema/ABI requires builder source reconciliation.

**D-02: Contract unit** — **Recommend** one candidate r08-v6 successor envelope, with a registered family catalogue and per-family schema revisions. Preserve cross-version cryptographic domain separation and exact historical reader isolation. Do not allocate r08-v6 or choose raw wire bytes until verified against all frozen source pins.

**D-03: Target scope** — **Recommend** only extant exact scope identifiers (consumer, tenant, institution, authority domain, operation) plus host action-class context. Agent/task identity remains an explicit *host mapping*, not a new cryptographic scope field. Broader inheritance, wildcard scoping or role resolution is a separate feature and is NOT part of the 19-parameter migration.

**D-04: Applicability** — **Recommend** host-declared required family set, canonicalized and included in the effective-policy identity. Any missing, withdrawn, invalid or mismatched mandatory family refuses. Do not silently activate partial family subsets. Deployment-wide exclusivity is still a separate durable host-control requirement: existing in-process activation ledger is advisory.

**D-05: Non-widening operators** — Reuse accepted set intersection, numeric min, false-to-true strengthening, closed-enum refusal and jointly validated target containment. Crucially, compare original host **validity before overlay** so Registry does not heal an invalid original host.

**D-06: Approval/persistence** — **Open, Architect decision required.** F4 constructor scalar values currently lack persistent decision/approval binding. ObservationPolicy also lacks an established equivalent commitment path. Options: (A) retain workflow-local F4 with documented restriction (not global reproducibility); (B) add backward-compatible persisted effective-configuration binding (requires F3 qualification); (C) alter approval preimage (approval invalidation). Do NOT choose B/C or assert full persistence without explicit decision.

**D-07: Temporal safety** — **Open.** Exact ObservationPolicy clock/range, 60/300 precedence, anchor_deadline_to_inputs, outage extension and age_ceilings interplay must be resolved from the current source and evidence; do not assume independent min composition is sufficient.

**D-08: Revocation/irreversibility** — **Open.** Requires holder inventory/assurance evidence; terminal-revocation control cannot invent revocation authority; irreversible flag may require dependent-state normalization. If existing evaluators cannot enforce the proposed changed values unchanged, report protected-evaluator decision instead of patching around it.

**D-09: Snapshot custody** — **Open.** A common immutable policy object is not equivalent to atomic multi-selector source snapshots. Durable high-water epochs, issuer trust and revocation visibility remain host obligations pending an implementation design.

**D-10: Test regime** — **Recommend** cheap per-change schema, frozen replay, imports, local negative and CI checks; one *coordinated* complete cross-component regression/mutation/security and independent Tier 1 qualification after final engineering freeze. A known failing intermediate CI or widening counterexample is never deferred to final testing.

## 3. Preconditions for builder implementation (NO implementation authorization by this document)

1. Reconcile exact source schema against audit parameter-catalogue.json, all merged r08-v1–v5 contract files, Control Plane #91, Registry #67 and current Runtime. No speculative wire field names as if accepted.
2. Produce an exact source-to-param crosswalk at current heads, including host ownership, shape, allowed range, rejected inputs, commitment path, selection source and expected refusal at all relevant boundaries.
3. Decide explicitly with Architect which architectural blockers D-06–D-09 are accepted assumptions, held scope or separately authorized contract changes.
4. Freeze the candidate successor record format, signing inputs, family dispatch, reader compatibility, reason vocabulary and cross-family identity in a **single review gate** before code migration.
5. Only then perform the integrated remaining-six implementation; leave historical held PRs and out-of-scope controls untouched.

## 4. Handoff guardrails

Do not open six incremental parameter-contract PR chains. One lead builder with independent short-lived workers owns (A) Registry schema/contracts, (B) CP effective profile and revocation, (C) CP observation/freshness, (D) compatibility/adversarial review. Avoid overlapping writes. Preserve merge permissions for Architect. Builder may revise documents and open draft PRs; must not merge, deploy, trigger paid tests or relax holds. At final review submit exact heads, decision ledger, field-to-consumer matrix, test failures (including negatives), coverage and remaining unresolved decisions in a concise consolidated report.

## 5. Known external gates

Ed25519 #26/#34 SECURITY-HELD. V09 separate. Held Registry #58/#59 and Control Plane #87 remain held. Constructor clock tolerance NOT authorized; distinct ObservationPolicy tolerance is within the 19. Release, publication and production HOLD. Independent qualification deferred, not waived.
