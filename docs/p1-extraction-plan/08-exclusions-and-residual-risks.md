# 8. Explicit exclusions and residual risks

Status: planning only. Exclusions are stated as customer capability that is not available, and are tabulated in [02](02-v1-capability-profile.md); they are not automatically permanent. This document consolidates the residual risks from all five lanes and the evidence limits of the plan itself.

## Evidence limits of this plan

- **No repository test was run** and no source was changed (two read-only probes were executed: pydantic coercion on `ActionClass`, and construction of a `LocalExecutionPolicy` with an empty set). Every status of a test is read from recorded documents. Lane findings are source readings at the exact pins and are labelled as such.
- The inventory baseline is merged and accepted (qualification repo merge commit `be1994a961e4e40612d999972ede6547a3729887`); it is analytical evidence, not independent operational qualification. The seven errata found by the P1 source read are listed in [03](03-field-extraction-register.md) and change no disposition.
- Control Plane and Runtime behaviour was re-read at `7a4bcd40` and `c5e97e87`; P0 had only second-hand claims. The claim-carried binding for the commit-time check is a source reading, not a tested result.
- Two lanes disagreed on whether `LocalExecutionPolicy` accepts an empty set; this was checked directly at the pin and it **does** accept one (see [04](04-component-ownership-and-adapter-matrix.md), decision 4).
- Not read: Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index and Action Manifest, so how downstream components handle new receipt keys is UNVERIFIED.

## Residual risks

| # | Risk | Effect | Where it is handled |
|---|---|---|---|
| 1 | No operational trust root, key ceremony or snapshot channel exists; the Ed25519 adapter uses synthetic keys | V1 proves "technically verifiable with synthetic keys", not authenticated operation; GAP-G3-07 stays open | Operator-gated (OB-02); disclosed in every status report |
| 2 | No independent qualification lead designated (GAP-G4-13) | Tier 1 cannot close; the likely outcome is a truthful "NOT INDEPENDENTLY QUALIFIED" release candidate | [07](07-independent-qualification-matrix.md); escalate only if no lead can be secured |
| 3 | Route A cannot be closed at the commit boundary (GAP-G3-03) | A registry-selected policy on Route A is only checked before the commit | **Decided: V1 is atomic Route B only** (operator); disclosed in every status report |
| 4 | Authority-to-effect consistency stays UNQUALIFIED after S2; the claim-carried guard proves selection identity was current under the lock, not that evaluation was correct | Do not claim a transaction-time guarantee before S4 and S5 | [02](02-v1-capability-profile.md) wording |
| 5 | Claim-carried binding spans two repositories | `EXT-S4-4` (Control Plane claim change, successor profile) is **mandatory**; both repositories re-pin (`EXT-S4-5`) and any evidence at the old tuple is superseded | **Ruled** (B-lite rejected); sequenced in [06](06-pr-and-sprint-execution-plan.md) |
| 6 | New durable mutable Runtime state (high-water, revoked set, activation log) | Needs its own custody review; one trusted writer only; never seeded from a claim (the `provision_claim` seeding pattern must not apply) | DT-02; `EXT-S4-0`, `EXT-S4-2` |
| 7 | Database restore reverts high-water and revoked sets together | Same class as the known limit (B14, D07, GAP-G1-02); the Control Plane has no restore-safe epoch issuer | External `min_epochs` floor, re-sync before serving, fail closed until re-baselined; disclose, never claim restore safety |
| 8 | An older trust snapshot is currently undetected: `TrustSnapshot.version` is only checked `>= 1` | Revocation-source rollback undetected | `EXT-S1-6` snapshot-version floor |
| 9 | `revocation_ref` is validated but never consumed (`selection.py:87`); revocation rides on the operator-delivered snapshot | Latency is unbounded until the sync cadence is set (B-08, operator) | S1 ADR; snapshot-borne revocation plus bounded lifetime |
| 10 | Authoritative lineage always refuses (`selection.py:230-234`) | V1 depends on the consumer receiving exactly one selection per scope from a trusted channel | `EXT-S1-1`; single-selection delivery |
| 11 | Single-signer authority only; no quorum or separation of duties | Accepted for V1 unless decided otherwise | Architect/operator |
| 12 | No `qualification_ref` for evaluators (MC-05, X-04) | The V0.2 `unqualified_evaluator` gate has no counterpart in `r08-v1` | Owner: qualification repo; P6 gate |
| 13 | A misconfigured registry set that omits a deployed institution, domain or adapter refuses everything | Fail closed, but an availability risk that looks like an outage | Operational runbook; S2 differential tests |
| 14 | F5 narrowing applied after approval issuance yields a wall of `runtime_authority_approval_mismatch` holds | Fail closed, looks like an outage | F5 is serialized behind F4 (W8-014 ruled); approvals issued against the effective profile |
| 15 | A signed outage extension could lift a registry-narrowed age bound by up to `max_age_extension_seconds` | **Ruled: outage extensions cannot widen registry limits**; the ruling must be implemented and tested (`EXT-S3-4`, QG-04) | Architect ruling |
| 16 | The bundled CLI uses default ages; the 2x dispatch window remains unless `anchor_deadline_to_inputs` is set; clock tolerance (5 s) is not registry-governed | A customer may read "freshness is governed" more broadly than status and approval | Exclusions in [02](02-v1-capability-profile.md) |
| 17 | The age floor is a code floor of at least 1 on strict integer seconds; there is no universal five-second floor; too high a deployment value refuses legitimate short-lived resolvers | Availability | Control Plane owner sets it; tested at the boundary |
| 18 | All differential and boundary evidence is builder-authored; the S05 oracle, R08 spec and the QS13 amendment contaminate independence | An independent author who reads them is no longer blind | Author from contract, manifest and source; record what was read |
| 19 | Historical `PASS_RECORDED` cases are at the g8-r10 pins, not at the current heads; 11 Runtime known-limit tests are undeclared (GAP-G4-07) | Existing evidence is weaker than counts suggest | QG-13; re-run at exact pins |
| 20 | D4, MC-06 G2/G3, W8-014 are now ruled ([10](10-architect-rulings-and-repin.md)); D6 plus the numeric encoding stay unmade because `max_amount` is deferred; the earlier D1 to D13 transcription remains UNVERIFIED | `max_amount` cannot proceed until separately authorized | Deferred with the field |
| 21 | Any head change invalidates evidence at the old tuple; the evaluator blob must never be edited | Re-pin of S01, all records and S05 | R10-F-03; zero-edit rule |
| 22 | Concurrency and clock gates are probabilistic | One run is not evidence | Repetition and raw logs required (QG-08, QG-09) |
| 23 | Trusted-host threat model only (T1, T5); same-host file access, loaded-code integrity, non-SQLite or remote destinations are outside every gate | Guarantee is bounded to the synthetic emulator profile | Disclosed |
| 24 | Naming collisions: P0 prerequisites G1..G9 versus inventory `GAP-Gx-xx`; sprint labels S1..S6 versus historical S01..S06; selection `epoch` versus record-succession `epoch` (DT-03) | Mis-citation | `EXT-` prefix; DT-03 naming map in `EXT-S1-1` |

## Deferred functionality (documented, never a release blocker)

| Item | Status | What is needed to reopen it |
|---|---|---|
| `max_amount` (RT-F1c-01) | DEFERRED by operator decision (Option B); no task, no reserved slot in V1 | Separate authorization; D6 ruling that the caller's value stays authoritative; numeric encoding (`{unit, scale, value}` rounded down to binary64); single-unit rule; QG-02 activated |
| F1d target scope, F6 permissions, F7 dedupe/TTL, F3 operational timeouts, F8 tool lists, F11 redaction, remaining F4/F5 rows | Outside the V1 profile | Separate authorization, ruling of the open decision named in the manifest, and a gate |
| Management UI (ENABLED/DISABLED) | Not built; the readiness mapping and acceptance criteria are fixed in [04](04-component-ownership-and-adapter-matrix.md); a toggle is a request for a signed, versioned selection or withdrawal, never a write | Ergonomics integration after V1, under the same required-policy and code-owned-invariant rules |
| Route A commit-time protection | Outside V1 (atomic Route B only) | Operator decision and a redesign not covered by this plan |

## What would be a material surprise

A concrete customer scenario that requires central target scoping (F1d), central spend ceilings (`max_amount`) or Route A commit-time protection would justify extending the profile. Each has a ready extension path in the same typed-adapter architecture; none is currently justified by a scenario in the inventory.
