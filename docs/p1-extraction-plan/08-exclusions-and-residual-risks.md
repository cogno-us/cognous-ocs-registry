# 8. Explicit exclusions and residual risks

Status: planning only. Exclusions are stated as customer capability that is not available, and are tabulated in [02](02-v1-capability-profile.md); they are not automatically permanent. This document consolidates the residual risks and the evidence limits of the plan itself, and documents Route A's existing behaviour and residual risk as the approved scope requires.

## Evidence limits of this plan

- **No repository test was run** and no source was changed (read-only probes only: pydantic coercion on `ActionClass`, construction of a `LocalExecutionPolicy` with an empty set, and `timedelta`/`datetime` limits). Every status of a test is read from recorded documents. Lane findings are source readings at the exact pins.
- The inventory baseline is PR #227, **merged** at `be1994a9`; provenance, the one manifest disposition change since the first analysed head, and the seven errata are in [03](03-field-extraction-register.md).
- Control Plane and Runtime behaviour was re-read at `7a4bcd40` and `c5e97e87`. The claim-carried binding design is a source reading, not a tested result. Unverified pieces: the contents of the Control Plane `tools/adversarial_mutations.py`, the qualification-repo workflows beyond the Runtime caller workflows, whether S03/S05 evidence pins a repository head or only the evaluator blob, the registry `docs/r08-preparation/08` bodies, and the rest of `verify.py` beyond line 200 in the binding lane.
- Two lanes disagreed on whether `LocalExecutionPolicy` accepts an empty set; checked directly at the pin: it **does** (see [04](04-component-ownership-and-adapter-matrix.md)).
- Not read: Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index and Action Manifest, so how downstream components handle new receipt keys is UNVERIFIED.
- Line numbers hold only at the pins. Required-check lists cannot be read from the clones ([06](06-pr-and-sprint-execution-plan.md) appendix).

## Route A: existing behaviour and residual risk (excluded from the V1 guarantee)

Route A is the adapter route. It is **not** protected by the V1 registry-mediated effect-time guarantee, V1 does not claim it is, and this plan changes no Route A file and weakens no Route A control.

**What exists today.** The policy is host-supplied and held as a plain attribute (`PinnedControlPlaneExecutor`, `control_plane_adapter.py:225-230`; only a `None` check). *Check 1:* `observe` evaluates `policy.check(op)` (`:100-106`), catching only `PermissionError` to record `local_refusal`; the trusted institution and domain binding (`_check_trusted_context`, `:87-92`) runs first. *Check 2:* `apply` reaches `LocalDestinationExecutor.execute_snapshot`, which evaluates `policy.check` again (`safe_executor.py:890`) after Control Plane revalidation and records `policy_denial` / `local_policy_rejected` on refusal. *No third check:* `commit()` opens `BEGIN IMMEDIATE` (`safe_executor.py:772`) and reads no grant, claim, selection or epoch; `reconcile()` and `observe_historical()` never call `check`. The Control Plane itself states there is no authority reread after validation and that the freshness deadline "narrows ... does not close" the window (`bounded.py:1784`, `:1791-1792`).

**Residual risk (adapter present or absent).**

1. A selection revoked, expired, superseded or epoch-advanced after the host built the policy is not seen at all; the last check precedes the commit with no shared lock.
2. The narrowing adapter is optional: nothing in the Runtime forces a host to call it, and "adapter available" must not be read as "narrowing enforced".
3. The executors do not type-check the policy: any object with `.check()` is accepted, so a duck-typed policy bypasses the allow-lists entirely (the `type(...) is LocalExecutionPolicy` gate exists only in the S04 consumer and the new adapter).
4. `executor.policy` is a reassignable attribute; reassignment after construction is outside the model.
5. `local_refusal` and `policy_denial` text cannot distinguish a caller-policy restriction from a registry narrowing.
6. A malformed `max_amount` ceiling raises `ValueError`, which Route A `observe` does not catch, so it escapes without `local_refusal` (existing, characterized and untouched).
7. A host that builds a Route A executor for a scope that has a `required` registry requirement is outside the guarantee; the Runtime cannot prevent it (host contract and gate refusal only).
8. A registry set that omits a deployed value refuses everything (fail closed, but outage-like).

Route A status is KNOWN_LIMIT (LIM-A1 in [07](07-independent-qualification-matrix.md)): characterized and reported, never a PASS. Any later expansion to Route A requires separate scope approval and independent qualification.

## Residual risks

| # | Risk | Effect | Where it is handled |
|---|---|---|---|
| 1 | No operational trust root, key ceremony or snapshot channel exists; the Ed25519 adapter uses synthetic keys | V1 proves "technically verifiable with synthetic keys", not authenticated operation; GAP-G3-07 stays open | Operator-gated; disclosed in every status report |
| 2 | No independent qualification lead designated (GAP-G4-13) | Tier 1 cannot close; the likely outcome is a truthful "NOT INDEPENDENTLY QUALIFIED" release candidate | [07](07-independent-qualification-matrix.md); escalate only if no lead can be secured |
| 3 | Route A is excluded from the effect-time guarantee (GAP-G3-03) | See the Route A section above | Approved scope; LIM-A1 |
| 4 | The claim-carried binding proves that the claim-authorized policy identity equals the Runtime-held current one at the lock, not that the effective sets were computed honestly or the evaluation was correct; `claim_commitment` is an unkeyed hash | A compromised gate or provisioning path is outside the guarantee | Runtime row as independent anchor; optional hardening H-1 (Architect, S4-0); disclosed |
| 5 | The Control Plane claim change moves both repository heads | Every artifact bound to `c5e97e87`/`7a4bcd40` is re-issued at a new tuple; if the Runtime merged without the Control Plane its successor tests would skip silently | `EXT-S4-4` first; Runtime PR fails its own check without the Control Plane pin; re-pin rule |
| 6 | New durable mutable Runtime state (activation, high-water, revocations, log) | Needs custody review; one trusted writer only; never seeded from a claim (the `provision_claim` seeding pattern must not apply) | DT-02; `EXT-S4-0`, `EXT-S4-2`; QG-16 |
| 7 | Database restore reverts high-water, revocations and the log together | Same class as the known limit (B14, D07, GAP-G1-02); no restore-safe epoch issuer exists | External floor, log-head and high-water digest checks, gate refuses required scopes until first sync; disclose, never claim restore safety (R13, NX-09) |
| 8 | An older trust snapshot is undetected today: `TrustSnapshot.version` is only checked `>= 1` | Revocation-source rollback undetected | `EXT-S1-6` snapshot-version floor |
| 9 | `revocation_ref` is validated but never consumed (`selection.py:87`); revocation rides on the operator-delivered snapshot | Latency is unbounded until the sync cadence is set (B-08, operator) | S1 ADR; snapshot-borne revocation plus bounded lifetime; the commit-time row is authoritative once written |
| 10 | Authoritative lineage always refuses (`selection.py:230-234`) | V1 depends on the consumer receiving exactly one selection per scope from a trusted channel | `EXT-S1-1`; single-selection delivery |
| 11 | Single-signer authority only; no quorum or separation of duties | Accepted for V1 unless decided otherwise | Architect/operator |
| 12 | No `qualification_ref` for evaluators (MC-05, X-04) | The V0.2 `unqualified_evaluator` gate has no counterpart in `r08-v1` | Owner: qualification repo; P6 gate |
| 13 | A registry set that omits a deployed institution, domain or adapter refuses everything | Fail closed, but an availability risk that looks like an outage | Operational runbook; S2 differential tests |
| 14 | F5 narrowing applied after approval issuance yields a wall of `runtime_authority_approval_mismatch` holds | Fail closed (R5), looks like an outage | Ordering (effective profile first), the read-only pre-flight `incompatible_approvals`, `EXT-S3-4` |
| 15 | Outage extensions: R6 is applied literally, so a registry-narrowed class is non-extendable and loses outage extension entirely; "extend up to the caller's ceiling" would be a different ruling needing a numeric ceiling field | Availability under outage for narrowed classes | `EXT-S3-5`; not reopened |
| 16 | The bundled CLI uses default ages; the 2x dispatch window remains unless `anchor_deadline_to_inputs` is set; clock tolerance (5 s) is not registry-governed | A customer may read "freshness is governed" more broadly than status and approval | Exclusions in [02](02-v1-capability-profile.md) |
| 17 | `AGE_MAX` and any host floor are proposals pending an owner survey; a larger legitimate in-use bound is refused (visible HOLD) on the registry path only; bounds of a few seconds can expire every check before dispatch | Availability | G-5; `EXT-S3-2`; tested at the boundary |
| 18 | All differential and boundary evidence is builder-authored; the S05 oracle, R08 spec and the QS13 amendment contaminate independence | An independent author who reads them is no longer blind | Author from contract, manifest and source; record what was read |
| 19 | Historical `PASS_RECORDED` cases are at the g8-r10 pins, not the current heads; 11 Runtime known-limit tests are undeclared (GAP-G4-07) | Existing evidence is weaker than counts suggest | QG-13; re-run at exact pins |
| 20 | Binding rulings R1 to R14 are recorded by the Architect; the transcription of earlier D1..D13 rulings into the P0 documents remains a builder transcription (UNVERIFIED) | Conditional gates may end BLOCKED | ADR ratification; Architect |
| 21 | Any head change invalidates evidence at the old tuple; the evaluator blob must never be edited | Re-pin of S01, all records and S05 | R14; zero-edit rule; re-pin rule |
| 22 | Concurrency and clock gates are probabilistic | One run is not evidence | Repetition and raw logs required (QG-08, QG-09) |
| 23 | Trusted-host threat model only (T1, T5); same-host file access, loaded-code integrity, hostile clock, non-SQLite or remote destinations are outside every gate | Guarantee is bounded to the synthetic emulator profile | Disclosed |
| 24 | Naming collisions: P0 prerequisites G1..G9 versus inventory `GAP-Gx-xx`; sprint labels S1..S6 versus historical S01..S06; selection `epoch` versus record-succession `epoch` (DT-03) | Mis-citation | `EXT-` prefix; DT-03 naming map in `EXT-S1-1` |
| 25 | Digest-profile hazard: the registry digest uses `ensure_ascii=True`, the Control Plane `commitment` uses `ensure_ascii=False`; they differ for non-ASCII tokens, which `valid_token` permits | A binding digest computed on one side may not verify on the other | One digest profile in `EXT-S4-0` with a non-ASCII vector; test in `EXT-S1-5` |
| 26 | Local Runtime tests skip when `agent_control_plane` is missing, so a green Runtime check can hide a skipped atomic suite; `PRAGMA synchronous` is unset for the new writers | Easy to mistake CI green for evidence; durability is untested | Every card requires a non-skipped run at an exact Control Plane pin; durability is a test (QG-16) |
| 27 | Port drift: `v2_verify.py` duplicates the `r08-v1` ten-layer logic; the v1 integrity scan relies on helper-name discipline; the registry has no in-tree CI and the S01 lock sources are absent | A v1 fix may not mirror; check results cannot be exact-head evidence until `EXT-S1-0` | Differential test in `EXT-S1-2`; `EXT-S1-0`; v1 is frozen |
| 28 | Several LD-02 granularity and vocabulary questions are open (class-level versus per-code reason strings, structured carrier, Control Plane vocabulary, and registry catch-all causes such as `selection_missing`) | Negative causes could collapse at the Control Plane or at commit | Injectivity test in `EXT-S1-5`; ratified in the S1-1 / S4-0 ADRs (Architect) |
| 29 | Multi-family identity: up to three selections per operation (F1, F4, F5); whether a claim carries a list of identities or one combined identity is an ADR point | Claim schema churn | `EXT-S1-1`, `EXT-S4-0` |
| 30 | F5 class names are unknown to the registry: a typo class is valid until the Control Plane adapter enforces it | A registry record may silently not apply | Unknown-class refusal at the Control Plane adapter (`EXT-S3-4`) |

## What would be a material surprise

A concrete customer scenario that requires central target scoping (F1d), central spend ceilings (`max_amount`) or Route A commit-time protection would justify extending the profile, each only through separate scope approval and independent qualification. Each has a ready extension path in the same typed-adapter architecture; none is currently justified by a scenario in the inventory.
