# Architect authorization record and contract freeze: final three Registry parameters (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. **Not independently qualified.** Independent Tier 1 qualification: DEFERRED, NOT WAIVED. Accounting is unchanged until enforcement implementations merge: **16/19 integrated, 3 remaining, 0 independently accepted.**

Governance baseline for this work package (OCS-REG-FINAL3): `cogno-us/cognous-engineering-constitution` `230c0aff1c2d1e054652cfc1be175147260b8aae` (Constitution, Orchestration, Compliance Addendum, Testing Policy v1.0, Adoption). Verified at start of session: constitution `main` is `c6d84b1ce6ac4fef37ec4b038e20ffddc317abd6`; the only change after the baseline is `LICENSE` and a README link, so there is no policy amendment to apply. Existing project-specific adoption records that pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` are NOT silently changed by this record (ADOPTION.md: a newly published text does not silently amend existing frozen adoptions); this work package follows the revision the Architect named.

Pinned bases at the start of this work package (live, re-verified): Registry `main` `b3eb7fe2b2a676580c293d21df688323fd2f0620` (docs-only since `67512a7`: #74 added two plan documents); Control Plane `main` `b7eb11aaeed9c766ecaae7d22955093f7f7cd1aa`. Inputs: Registry #75 `326c6467c7d38789404b893d7530bd5bf005e867`, Registry #77 (draft) `4df3a656cd82ef109169c52c3444e8ed8cf2ec4f`, Control Plane #94 `061a986563768f2f8f9f6c0861647a3c5b1935be`.

## 1. Decisions authorized by the Architect (directive "ARCHITECT AUTHORIZATION AND BUILDER DIRECTIVE", 2026-10-29)

| Id | Decision |
|---|---|
| D-06 | Option B: backward-compatible persisted effective-configuration binding. |
| D-07 | Option A: minimum protected-evaluator correction, file `src/agent_control_plane/runtime_authority.py` ONLY. |
| AR-1 | `ObservationPolicy.clock_tolerance_seconds` is distinct from the held constructor tolerance; the constructor exclusion does not automatically extend to it. |
| D-C5 | `r08-v8` is the successor carrying the three families. |

NOT granted (unchanged): merging, other protected evaluators, edits to frozen r08-v1..v7, new trust roots, revocation-authority changes, paid testing, deployment/publication, waiver of independent qualification. Standing holds: Registry #58/#59 HELD; Control Plane #87 HELD; constructor clock tolerance NOT AUTHORIZED; Ed25519 #26/#34 HELD; V09 SEPARATE; independent Tier 1 DEFERRED, NOT WAIVED; publication/release/production HOLD.

## 2. Sub-decisions resolved by the Lead Builder inside that authorization

The Architect approved the options and made #75 the starting point. The following were left open in #75. Each is resolved here by the minimum-sufficient, fail-closed reading (CA02, CA05). None widens authority; each is listed so the Architect can overrule it in the single consolidated review.

| Id | Resolution | Reason |
|---|---|---|
| D-06.B carriage | **C2**: a named member `effective_configuration` inside the already-persisted opaque `binding.runtime_authority` dict. No typed field, no JSON-schema file change, no `approval_commitment` or `catalogue_digest` change, no protected-evaluator edit. | Directive: avoid changing the approval preimage when the approved mechanism suffices; no schema alteration. Verified: fail CLOSED for legacy readers (a one-key-larger dict makes bindings unequal); a typed field would fail OPEN. |
| D-06.1/.2 member set | The directive list (host and final effective profile identity, F4 constructor scalars, ObservationPolicy effective values or explicit absence, declared mandatory family set with contract and family schema revisions and effective-policy digests, governing scope) **plus** the other constructor scalars `identity_max_age_seconds`, `mandate_max_age_seconds` and the CONSTRUCTOR `clock_tolerance_seconds`, bound **for equality only**. | Acceptance: "no unbound configuration in newly governed decisions". The constructor tolerance is bound only so drift refuses; there is NO Registry family for it and it is NOT narrowable: the hold "Constructor clock tolerance: NOT AUTHORIZED" is untouched. |
| D-06.3 | `evaluated_at` excluded (non-deterministic); `selection_id` / `selection_epoch` excluded (an equal replacement selection is accepted today; its effect is carried by the effective-policy digest). | Directive: no evaluation time in a restart-surviving digest. |
| D-06.4 | **Always on** for decisions minted by the Registry-governed lifecycle (no off switch, no default-off mode). The plain `BoundedAuthorizationWorkflow` mints nothing new (it has no governed configuration to bind). | An off switch is a path to unbound new decisions and to a hidden legacy fallback. |
| D-06.5 legacy | An explicit host-supplied finite integer `legacy_cutoff` (default 0 = no legacy decision is accepted). See section 5 for the evaluation and its limit. | Directive: no default or wildcard authorizes legacy fallback. |
| D-06.6 refusal | Reuse the registered `authorization_binding_changed` (durable `EffectTimeRefusal`). No new durable reason code. | A new durable code needs `runtime-authority-reasons/0.4` and a protected edit; not authorized. |
| D-06.7 | Characterization tests whose expected outcome the binding legitimately changes (for example `test_i04`, and the `test_z04` guard if it must accommodate the new lifecycle code) get documented successor tests; the originals stay in git history and are cited. | CA04 binding of Archetype B; no oracle edited merely to pass. |
| D-C1 | Admit Registry tolerance 0 (source `ge=0`). | Source-backed. |
| D-C2 | The numeric token range of the two int families is the EXISTING Registry constant (`AGE_MAX == MAX_INT == 2147483647`, already used by the F4 age families), reused as a structural canonical-encoding range, **not as a host bound**. | No invented limit: an existing source constant. |
| D-C3 | A host value outside that range, or a missing host policy, refuses the whole caller (no narrowing, no fallback). The host itself is not bounded by the Registry. | Fail closed (CA05). |
| D-C6 | Family ids and members as in draft #77: `f5-anchor-deadline-to-inputs-policy` (`anchor_deadline_to_inputs`: `anchor`/`no_change`), `f5-observation-max-age-policy` (`observation_max_age_seconds`), `f5-observation-clock-tolerance-policy` (`observation_clock_tolerance_seconds`; the `observation_` prefix prevents any alias with the constructor `clock_tolerance_seconds`, and that name is refused). | AR-1. |
| D-60/300 | No ordering between the 60-second authority-input default and the 300-second CLI literal is required or introduced. | Directive. |
| D-C4 | Moot: D-07 Option A is authorized, so the "accepted residual" alternative is not taken. | |

## 3. Frozen r08-v8 contract (single version, independent families)

One contract version `r08-v8` carries three independent families; sharing a version does NOT imply atomic selection or activation. Domains `ocs-reg/r08-v8/selection\n` and `ocs-reg/r08-v8/effective-policy\n`; family schema revision 1 each. It does NOT re-register `f5-action-class-irreversibility-policy` (that stays r08-v7); r08-v1..v7 behaviour, signing domains, canonicalization and committed evidence are unchanged. Engine edits are additive only (`scalar-int` identity kind, `V8` profile; `V8` not in `PROFILES`). Typed domains: anchor `anchor|no_change` (never a JSON boolean; a Registry value can never assert false; composition = `anchor` if either side is `anchor`); max age strict int 1..2147483647; tolerance strict int 0..2147483647; effective = `min(caller, registry)`; any out-of-domain, bool, float, subclass or alias input refuses. Reason vocabulary: no new code (an AST scan pins the emitted set against `CODES_V2_REV2`). The contract text is `docs/r08-v8-contract.md` in Registry PR #77; the single writer of Registry contracts in this work package is Worker C.

## 4. Frozen D-06 binding contract (`effective-configuration-binding/0.1`)

Carried as `binding.runtime_authority["effective_configuration"] = {"version": "effective-configuration-binding/0.1", "digest": "sha256:<64 hex>", "members": {...}}`.

Digest = the existing canonical `commitment()` (sorted-key canonical JSON) over: `domain` `cognous.control-plane.effective-configuration-binding`; `version`; `scope` (consumer, tenant, action, institution, authority_domain); `host_profile_digest`; `effective_profile_digest` (equals `catalogue_digest` for profile-bearing workflows, else null); `f4_scalars` {status_max_age_seconds, approval_max_age_seconds} (live values even when the F4 family is not declared); `other_scalars` {clock_tolerance_seconds, identity_max_age_seconds, mandate_max_age_seconds}; `observation_policy` = {max_age_seconds, clock_tolerance_seconds} effective values or an explicit JSON null; `families` = declared families in fixed order, each {slot, family_id, contract_version, family_schema_revision, effective_policy_digest} (an undeclared family is ABSENT, so the declared set is part of identity). All values are validated before hashing (exact `int`, never bool, 0..2147483647; exact `str`; digests `sha256:` + 64 lowercase hex, not all-zero); otherwise the workflow refuses.

Rules (all fail closed, none removes a refusal another check produced):
1. A new authorized governed decision mints the member (a hold persists no binding, as today).
2. Execute and pin-export claim recompute the live member and compare. Absent member: legacy classification only (section 5). Present member that is invalid, of unknown `version`, with `digest` not equal to the recomputation of its own `members`, or unequal to the live value: refuse `authorization_binding_changed`.
3. The member is a refusal-only equality check. It is never an approval input, never widens a bound, grants no authority.
4. Restart: nothing is held in memory; the persisted member says what the decision ran under, the live process says what runs now.
5. There is no "re-bind". A changed configuration needs a new decision.
6. `approval_commitment`, `catalogue_digest`, `RuntimeAuthorityProfile`, the published schemas and the reason vocabulary are unchanged. Existing approvals stay valid under their original semantics.

## 5. Evaluation of `legacy_cutoff` (directive section 5)

What it is: the number of rows in the append-only `decisions` list at activation, supplied by the host as an explicit integer. A decision without the member and with index below the cutoff executes under exactly the previous semantics (the member is omitted from the live side before the equality, nothing else is ignored) and is reported as `legacy`. Without a cutoff, at or past it, or when the member is stripped, it refuses.

Does it have source-backed durable provenance? **No.** It is host configuration. Available persistence is an unsigned local JSON store (existing tests rewrite persisted digests in place), with no signed floor and no durable ratchet (EXT-S4 anti-rollback is not implemented). A durable floor row would live in the same unsigned store and would add a persisted-schema change, so it would not create the trust boundary either. **Limitation, stated and retained as a hold:** the binding guards configuration DRIFT, restart/rebuild mix-ups, partial upgrades and buggy writers; it does not defend against a party who can rewrite the store, and it provides NO anti-rollback guarantee (rolling back to an older configuration whose digest equals an older persisted binding revives that old decision, now visibly). Anti-rollback and a signed decision store remain a separate held item and no guarantee is claimed here. No new authority root is invented.

## 6. D-07 exact change

`src/agent_control_plane/runtime_authority.py`: make the purpose-observation / cached-purpose deadline-anchoring block unconditional on `PolicyBinding` presence (the line `if binding is not None:` immediately before the block that registers `collector` deadlines). The inner `collector is not None and cl is not None` test already limits it to workflows with `anchor_deadline_to_inputs=True`. Pure `min` added to the deadline; no commitment, persisted-schema or reason-code change; strictly more restrictive. Predecessor evidence: CP #94 (`061a986`) is preserved unchanged; the three `*residual*` characterization tests are superseded by documented successor tests in the D-07 PR, citing the original results. If any other protected evaluator file must change, STOP and request separate authorization.

## 7. AR-1 and the extreme-tolerance overflow

Existing host domains (no upper bound): `max_age_seconds` int > 0, `clock_tolerance_seconds` int >= 0; checks at `bounded.py` future (`observed_at > reference + tolerance`) then stale (`age > max_age`), both strict `>`. Registry may only narrow. A missing host `ObservationPolicy` remains the hold `observation_policy_missing`. The extreme-tolerance `OverflowError` is a pre-existing host fragility in protected `bounded.py`, **not** introduced or fixed here: see `04-defect-record-extreme-tolerance-overflow-2026-10-29.md`. No policy ceiling is silently introduced.

## 8. PR structure, dependency-safe merge order (no automatic merge)

| # | PR | Content | Depends on |
|---|---|---|---|
| 1 | Registry #75 | decisions, annexes, this freeze, F3 expectations, defect record | none |
| 2 | Registry #77 | `r08-v8` implementation (merge of current main, no history rewrite) | #75 |
| 3 | CP #94 | test-only predecessor evidence, UNCHANGED | none |
| 4 | CP D-07 PR | the `runtime_authority.py` correction + successor tests (stacked on #94) | #94 |
| 5 | CP D-06 PR | persisted binding (non-protected files only) | none |
| 6 | CP consumers PR | three family consumers on the composed workflow, pinned to Registry #77 head | #77, D-06, D-07 |

Each PR carries a CI Scope Declaration (risk tier T3, exact head and dependencies, tests executed, evidence reused, tests omitted and why, original and new failures, remaining qualification obligations). F3-A (binding) and F3-B (temporal) independent qualification is PENDING and specified in `03-f3-qualification-expectations-F3A-F3B-2026-10-29.md` before any persisted-binding or protected-evaluator change is made. The builder does not qualify its own work. Accounting changes only when enforcement implementations actually merge, and "independently accepted" only on recorded independent evidence.
