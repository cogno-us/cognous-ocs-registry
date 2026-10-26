# Amendment 1 to static plan v1.4: G0 profile adoption and schedule change

- Date: 2026-10-26
- Amends: [plan v1.4](../plans/PROJECT_PLAN-v1.4.md) section 4 (execution schedule) only. The plan file is **not edited**; where this amendment and the plan differ on the rows named here, this amendment governs. Plan v1.4 sections 1-3 and 5-8, plans v1.1-v1.3, adopted ADRs and historical evidence are unchanged.
- Basis: operator decision "G0 PROFILE APPROVAL AND PLAN v1.4 AMENDMENT", relayed by the OCS Architect directive of 2026-10-26, approving the Architect's disposition on [PR #40](https://github.com/cogno-us/cognous-ocs-registry/pull/40#issuecomment-6425216049). The repository holds no separate operator-signed document; this record rests on that directive (UNVERIFIED beyond it).
- Authority boundary: this approves the **profile and the planning amendment**. It does **not** authorize implementation: S01-S09 and S03A are NOT AUTHORIZED until separately approved. Tier 1 NOT STARTED. Release, publication and production HOLD.

## 1. Operator decisions recorded

1. `MSOP-F1a-C11` is the minimum operational profile ([profile](../v1.4/g0-minimum-profile.md), status ADOPTED for planning, scenario C11, F1a-only scope).
2. The existing five-set `r08-v2` / `f1ab` payload is used, with `allowed_institutions` and `allowed_authority_domains` carried unchanged (no contract change).
3. A dedicated Runtime F1a narrowing mini-sprint is added (S03A).
4. EXT-S1-9 adversarial verifier tests are assigned to S01.
5. The `r08-v2` signing-domain mismatch is corrected within S01.
6. F4/F5 and Control Plane EXT-S3-1..3 are deferred unless a source-backed need is shown.
7. Synthetic Ed25519 keys for the non-production emulator.

Not approved: production key ceremony, operational trust roots, cloud deployment, paid calls, external effects, new registry rule families, additional tenants or scopes, publication, production. Independent cryptographic review and Tier 1 qualification remain separate gates.

## 2. Schedule as amended

Sequence: **G0 → S01 → S02 → S03 → S03A → S04 → S05 → S06 → S07 → S08 → S09.** S03A is an additional sprint; no existing sprint is renumbered.

| ID | Change | Owner and deliverable | Dependency |
|---|---|---|---|
| S01 | **Widened** | Registry: EXT-S1-6 withdrawal; snapshot-version floor; r08-v2 signing-domain correction; EXT-S1-9 builder-side adversarial verifier battery. Negative oracles are committed before the code changes. Frozen `r08-v2` wire contract preserved | G0 |
| S02 | Unchanged | Control Plane: EXT-S4-4 claim-carried binding | S01 (withdrawal paths), R6 #84 |
| S03 | Unchanged | Exact-head re-pin and compatibility tests | S02 |
| **S03A** | **New** | Runtime: F1a narrowing adapter | S03 |
| S04 | Depends on S03A, otherwise unchanged | Runtime durable selection state | S03A |
| S05 | Depends on S04, otherwise unchanged | Runtime atomic effect-time guard | S04 |
| S06-S09 | Unchanged scope, independence requirements and gates | | |

Effort: plan v1.4 estimated S01 at 2-3 working days before the battery and the signing repair were added; the Architect re-estimates S01 when authorizing it, and splits it rather than exceeding the plan's 5-day maximum. S03A is estimated 2-4 working days. The plan's total (18-33 days) therefore rises by the S03A estimate plus any S01 growth; this is not a delivery promise.

## 3. S01 mandatory signing tests

1. A valid v2 signature under the v2 domain (`b"ocs-reg/r08-v2/selection\n" + canonical_bytes(statement)`) succeeds.
2. A v1-signed v2 statement is rejected.
3. A v2-signed v1 statement is rejected.
4. Existing v1 signing and verification are unchanged (`SIGNING_DOMAIN` and v1 goldens untouched).
5. Tampered, stale, revoked and cross-scope statements refuse with the correct typed codes.

Reason for the repair: G0 found that `registry_successor/verify.py` `_authenticity` (line 440) builds the signed message with `selection.signing_input`, which hard-codes the `r08-v1` prefix (`selection.py:27`) for every contract version, contradicting `docs/r08-v2-contract.md` section 1. The change brings the code to the frozen contract; it must not alter the contract. The Ed25519 adapter and verifier hardening (#26, #34) stay SECURITY-HELD until a recorded independent result.

## 4. S03A requirements and acceptance

Objective: apply the authenticated, composed five-set `f1ab` policy to the Runtime's existing deterministic `LocalExecutionPolicy` boundary.

Requirements: no change to `engine/safe_executor.py` (protected blob `2fc880da`); no second execution authority; no generic policy interpreter; reuse the frozen `f1ab` composition semantics (`registry_successor/v2_f1ab.py` `compose_f1ab`); preserve policy provenance and effective-policy identity; never widen the caller's allowed sets; the digest identifies the exact policy actually enforced; missing, malformed, substituted or unsupported policy input is explicitly refused; claims without a binding keep their existing behaviour where the adopted contract permits.

Acceptance: a caller-allowed operation is refused when the authenticated selection narrows it; an operation inside the intersection succeeds; unsupported policy is never silently ignored; a digest mismatch prevents execution; positive, negative, boundary and differential tests pass; existing Runtime safety tests stay green. Nothing here has been implemented or run.

## 5. Effect on the G0 gaps

G0-GAP-1 → S03A. G0-GAP-2 → S01. G0-GAP-4 → S01. G0-GAP-3 (no independent Tier 1 lead) remains open as an operator action before the S06 oracle freeze (plan section 7). See the [crosswalk](../v1.4/g0-dependency-crosswalk.md).
