# 04 Schema fitness matrix

Non-authorizing analysis. Compares each candidate family with the **current** S03 contract (`s03-v1`, record type `local-execution-allowlist`) and the S04 consumer. Nothing here changes either.

## 1. What S03 can express today [V, from `docs/s03-contract.md` and the schema file]

- One record type, one evaluator (`engine.safe_executor.LocalExecutionPolicy.check`), one fixed `supplies` list: `allowed_actions`, `allowed_adapters`, `allowed_units`. Unknown fields are refused, so any extra field is a new contract version, not an additive change.
- `data`: three non-empty, sorted, duplicate-free string lists (at most 256 entries, 1 to 128 characters, no C*/Z* characters, no `*`).
- Applicability: exact `runtime_source_blob_id`; no ranges, no consumer or profile selector.
- `non_authorizing: true`; digests give integrity, not authenticity (T2).
- Composition at the S04 consumer: `effective = caller ∩ registry` for the three fields; optional-overlay profile (a refusal leaves the caller policy unchanged, T7).
- No expiry, clock, tenant, selection, activation or signing field.

## 2. Fit codes

A represented directly. B representable with a bounded extension. C needs a new typed family-specific payload. D needs new applicability or selection semantics. E should never be configurable policy.

| Family / field group | Code | Why | Monotonic non-widening composition definable? |
|---|---|---|---|
| F1a allowed_units, adapters, actions | A | exactly S03 | Yes: intersection; shown by S05 differential tests for the bounded trusted-host profile (inactive); not a proof |
| F1b allowed_institutions, allowed_authority_domains | B | same type and check; needs a new contract version because `supplies` is fixed and unknown fields are refused | Yes: intersection |
| F1c max_amount, max_effects | C | numeric payload: type, range, binary64, bool-versus-int and NaN handling (W1-015); W8-091 origin | Yes, as minimum with a code hard cap, once the ceiling's classification is ruled |
| F1d allowed_target_prefixes, target_match | D | prefix semantics, not set membership; the match-mode vocabulary (F2) is code | Not established: [I] list intersection of prefixes is not the intersection of the sets of targets they admit; needs a defined containment relation and a mode order (`segment`, `exact`, `legacy-prefix`; `legacy-prefix` is security-weakening, W1-029). Do not define until ruled |
| F2 match-mode vocabulary, separators | E (proposed, pending D1: W1-029 is UNRESOLVED) | protected invariant in code | not applicable |
| F3 admission guards (W1-007/008) | E | admission guards | not applicable |
| F3 other resource bounds | C | single numeric ceilings | Yes, as minimum below a code hard cap; a floor is also needed so a value cannot disable a limit |
| F4 freshness bounds (destination observation ages; `max_status_age_seconds` belongs to F5) | C and D | numeric ages plus clocks, observation authority and consumer selection | Per scalar age ceiling: yes as minimum under a ruled direction. Across bounds, and for anything involving clock source or tolerance: not defined (see §4) |
| F5 per-class declarations, tightening fields | C and D | structured per-class payload; needs class selection | Per field, directional (§4); definable only for fields with a ruled stricter direction |
| F5 `allow_synthetic_resolver` and similar relaxing toggles | E (proposed, pending D1: W8-014 is UNRESOLVED) | relaxes an authentication requirement | Not applicable: registry data must not be able to relax |
| F6 agent permission allow-list | C | mapping agent to list; new evaluator and baseline | Yes per agent as intersection; absent-agent semantics needs a ruling (08) |
| F7 dedupe profile | C and D | multi-field, two components, capability dependency | Conditional; see §4 |
| F9 tenant id length | C (not recommended) | one number; no value | Yes, as minimum; low value |
| F10 trend thresholds | C | non-gating numbers | No authority semantics; composition not needed |
| F11 redaction defaults | C | sets of redaction categories | Union (more redaction), only where categories are compatible and never removing a protected redaction |
| M1 to M8 | E | mandatory in code | not applicable |
| G reason vocabularies | E as policy; separate reference-data record type possible | external commitments (CA12, CA21) | not applicable: a vocabulary record must not change refusal behavior |
| H lifecycle | E | mandatory transition logic stays in code | not applicable |
| J historical proposals | not representable as policy records | proposal status is not an S03 `status` | not applicable |

## 3. Semantic patterns

| Pattern | Rule proposed | Conditions and limits |
|---|---|---|
| Allow-lists | effective = intersection of caller and registry | Empty result means deny-all for that field, which S03 cannot express in a record (non-empty lists; S06 A) |
| Maximum ceilings | effective = minimum | Needs a code hard cap and a floor; registry value may only lower |
| Minimum assurance | effective = maximum | Requires an ordered assurance vocabulary; `ALLOWED_ASSURANCE_CLASSES` is a closed code set (W5-028 unresolved), so no registry-defined order |
| Required evidence | union only where categories are compatible | Union of incompatible categories is undefined; `EVIDENCE_KINDS` is a closed code set (W6-004 unresolved) |
| Freshness | needs explicit clock, timestamp, expiry, measurement semantics and observation authority | A registry record must not carry an observation or a clock reading; `now` is supplied by the evaluator's clock; the 60 and 300 bounds apply to different observed objects (03 §3) |
| Authority profiles | registry data must not issue grants or approvals | A profile may describe a class the host already governs; it cannot create holders, grants or resolvers |
| Reason vocabularies | versioned reference data | Never selects behavior; closed sets stay code (M7) |
| Lifecycle | mandatory logic stays in code | Registry may not alter a transition |
| ISS cognitive policies | do not assume OCS operators apply | No ISS architecture source was available; no mapping is asserted (08) |

**Architect ruling D4:** there is no universal monotonic direction, and composition is never inferred from numerical type alone. Each scalar needs explicit units, ordering, applicable floor or ceiling, direction of tightening, interaction with code-owned invariants and a deterministic unsupported-case outcome; the rows above are patterns to be instantiated per family, not defaults. No universal rules algebra is proposed. Each row above is a separate, local rule that a family chooses and an Architect rules on.

## 4. Where non-widening composition is not definable

1. **F1d target prefixes.** Not definable without a defined containment relation and a ruling on mode ordering.
2. **F7 dedupe profile.** The three values are ordered (`provider_horizon <= escalation_deadline < dedupe_ttl`) and span two components. If the stricter direction were: larger TTL, smaller deadline, smaller horizon, then a componentwise "stricter" meet of two valid triples (max TTL, min deadline, min horizon) preserves the ordering [I, shown by inequality: min h ≤ h_a ≤ d_a and min h ≤ h_b ≤ d_b, so min h ≤ min d; and min d < max TTL]. But that direction is an assumption: W3-063 is UNRESOLVED, a smaller TTL widens the duplicate window while an earlier deadline trades availability, and the horizon's direction was not established. Also the capability dependency (`dedupe-ttl/0.1`, destination TTL not below the profile TTL) is a cross-component required dependency, not a composition. A further hazard [V from `dedupe_mode`]: raising the effective profile TTL above the destination's declared TTL makes `dedupe_mode` fall from `destination_ttl` to a weaker mode, so a "stricter" meet can weaken behavior unless the destination capability is rechecked after composition. Verdict: **conditionally definable, not established.**
3. **F4 across bounds and clocks.** Ages are scalars, but composing a registry age with a caller's `clock_tolerance_seconds`, a lease timeout or `max_age_extension_seconds` has no single direction. `anchor_deadline_to_inputs` (`freshness.py`, default False) and `nonce` (W8-042) are booleans whose direction is domain-specific. Verdict: **not definable as one rule**; definable only per scalar once each direction is ruled.
4. **F5 class declarations.** `irreversible` is **not** independently composable when a host class declares `reversibility`: the pinned Control Plane `check_class_members` (`reversibility.py:125-143`, used by `ActionClass`) derives the boolean from the enum and rejects a conflict with `irreversible_flag_mismatch` (also S02 W8-059 [R]). Changing only the boolean to true for a `reversible_at_cost` class yields an invalid profile. A coupled composition rule is deferred; standalone `irreversible` changes are excluded for any class with a `reversibility` value, or with `reads_protected_data` true or `counterparty_observable` false (`check_class_members` derives the enum as `irreversible` when it is undeclared in those cases, so setting the flag false raises `irreversible_flag_mismatch`; when a `reversibility` is declared with those conditions, the host raises `protected_read_not_irreversible` or `unobservable_not_strict` instead) [V, `reversibility.py:129-160`, identical at `0a41faa9` and `7a4bcd40`]. Where none applies it is a free boolean. Per field, the plausible tightening directions are: `requires_revocation_assurance` false to true, `max_status_age_seconds` lowered, `on_unreadable` `bounded_tolerance` to `refuse` [I]. Adding a class changes the applicable set; whether that widens or narrows depends on selection semantics (D). Verdict: **per-field only; set-level not defined.**
5. **F6 absent agent.** Intersection per agent is definable; an agent absent from a record is either unconstrained (optional-overlay semantics) or denied (key-wise intersection). Both are internally consistent; they are different policies. Ruling needed.
6. **F11 union.** Defined only inside a closed, ordered category set owned by code.

## 5. Findings

- Strongest reuse: F1b. It is the only extension that needs no new evaluator, baseline or semantics.
- F1c, F3, F6, F11: typed payload (C) is enough, but each needs a ruling first (08 D1, D4, D6).
- F4, F5, F7: need D (selection and applicability) plus rulings; they are not first-increment candidates.
- G, H, M1 to M8, F2, relaxing toggles: never policy (E).
- Optional-overlay refusal (T7) is unsuitable for any family where a refusal must mean deny. Whether registry failure must deny is a property of the host's ACTIVATION profile (05 §4, 06 §2.8), not a field of the envelope or of any record: a record that cannot be loaded cannot say that its failure must deny.
