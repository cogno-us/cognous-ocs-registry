# G0 minimum operational profile (ADOPTED for planning)

**Status: ADOPTED for planning by operator decision (relayed by the Architect directive of 2026-10-26); G0 APPROVED / CLOSED on merge of PR #40.** Earlier text below that says "proposal" or "proposed" records the pre-decision state and is kept for history. Recorded decisions and the schedule change: [Amendment 1](../decisions/2026-10-26-amendment-1-plan-v1.4-g0-schedule.md). The profile is frozen for planning only. It authorizes no implementation: S01-S09 and S03A are NOT AUTHORIZED until separately approved. Tier 1: NOT STARTED. Release, publication and production: HOLD. Nothing here is independently qualified and nothing proposed has been run.

Companions: [dependency crosswalk](g0-dependency-crosswalk.md), [acceptance matrix](g0-acceptance-matrix.md).

## 1. Verified baseline (2026-10-26)

| Item | Verified value |
|---|---|
| Plan v1.4 | Merged: PR #39, merge `4f0936426eee9f45918a7dc9ab76454409158668`; file `docs/plans/PROJECT_PLAN-v1.4.md` is on Registry main (12,724 bytes). Post-merge checks on that commit: `pytest`, `Analyze (python)`, `Analyze (actions)` all success. Plan text says its frozen baseline is `6a050f23` (PR #38); main has since moved by the #39 commits only. |
| Registry main | `4f0936426eee9f45918a7dc9ab76454409158668` |
| Control Plane main | `fff27ebf356007e1eb3bb24198efc7e3e3f0c5eb` (R6, #84) |
| Execution Runtime | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (read-only clone, fetched; `origin/main` equals it; the GitHub API for this repository is not enabled in this session, so this comes from `git fetch`). `engine/safe_executor.py` blob is `2fc880dae37eac76e5074533435740ce0684209d` at that head, matching the protected blob in plan section 5. |
| Stack Qualification main | `67dcaeffc955ef1b91388e0abd1ceff8eb87834c` (#231) |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; `ADOPTION.md` read at that exact commit (read-only fetch). Applied: a merge or passing check is not adoption or authorization; independence cannot be inferred from a second automated process; this proposal needs the operator's decision. Other articles applied by reference only, not re-audited |
| Adopted contracts | `r08-v2` (#25) and Amendment 1 (#32), TR-01, DR-CP-AGE-1, ADR-REG-S4-0 (#37, status ADOPTED, documentation only). All present on main; none modified by G0. |
| Protected code boundaries | `engine/safe_executor.py` unchanged; Control Plane `bounded.py` semantics unchanged; `r08-v2` and ADRs frozen; no edits in other repositories. |

## 2. Proposed scenario

**Profile label: `MSOP-F1a-C11`.** It is a label for one slice of existing scenarios, not a new scenario. Primary catalog scenario: **C11** (credential and permission boundaries; Stack Qualification `scenarios/catalog.json`; the only P1 catalog scenario mapped to F1a, registry dependency BENEFICIAL, evidence KNOWN_LIMIT_ASSERTED, not independently qualified; [crosswalk row](https://github.com/cogno-us/cognous-stack-qualification/blob/67dcaeffc955ef1b91388e0abd1ceff8eb87834c/docs/registry-v1-scope-assessment/02-canonical-scenario-crosswalk.md)). Related, reused only as assertion patterns, **not** as in-scope families: **D02** (binding substitution; crosswalk maps it to F1b,F1c; registry dependency UNNECESSARY), **C02** (unknown action and manifest mismatch; F1a; UNNECESSARY, P4), **C01** (missing grant; crosswalk maps it to F4,F5), **D03** (authority change; F4,F5; UNNECESSARY, used only for the generation/withdrawal path). C11 itself maps to F1a,F1b,F1c in the crosswalk; the profile covers only its F1a part. Gaps this would close if the sprints are implemented and qualified (none is closed today): GAP-G3-01, GAP-G3-02, GAP-G3-07, GAP-G2-01 ([gap register](https://github.com/cogno-us/cognous-stack-qualification/blob/67dcaeffc955ef1b91388e0abd1ceff8eb87834c/docs/registry-v1-scope-assessment/05-gap-register.md)).

Why this slice: it is the smallest scenario in which a registry value changes an enforcement outcome (a unit, adapter or action that the caller's policy allows is refused because the authenticated selection narrows it), and it exercises every mandatory plan v1.4 behaviour. F4/F5 freshness values do not affect it.

## 3. Specification (items 1-10 of the G0 directive)

Identifiers below are **proposed fixture names**, to be fixed at S06 predeclaration. Which existing `registry_records/` synthetic fixtures can be reused is UNVERIFIED; S06 pins it.

1. **Operation and ID.** One local execution claim for operation `op-allowed` (unit `u-read`, adapter `a-local`, action `act-list`) and one for `op-refused` (unit `u-write`, same adapter and action), both submitted through Runtime `execute_claim_atomic` (`engine/local_authority_effect.py`) against a local non-effecting emulator. Scenario IDs: C11 primary; D02, C02, C01, D03 related.
2. **Initial configuration.** Tenant `tenant-syn-1`, governed scope `scope-syn-1`, `participation=required`. Caller `LocalExecutionPolicy` allows units `{u-read, u-write}`, adapters `{a-local}`, actions `{act-list, act-copy}`. Signed selection at epoch 1 (`r08-v2`, family `f1ab`) narrows units to `{u-read}`. The `f1ab` payload requires **five** sets (`allowed_units`, `allowed_adapters`, `allowed_actions`, `allowed_institutions`, `allowed_authority_domains`; an absent key refuses `field_missing`, `docs/r08-v2-contract.md` section 2), so the fixture also carries institution and authority-domain sets equal to the caller's (no narrowing). Plan v1.4 names three fields; this is a deviation the operator is asked to accept in section 5. Synthetic Ed25519 issuer key. Approval at `policy_generation` 1 bound to the effective-policy digest.
3. **Success.** `op-allowed`: selection verified, binding matches the active row at the lock, effect committed in the emulator, receipt carries the binding and effective-policy digest, evidence appended in the same transaction.
4. **Refusal.** `op-refused`: the caller policy would allow it; the narrowed policy refuses it. The exact typed code is predeclared at S06 from the existing vocabulary (reasons 0.3, 172 codes); no new reason is invented.
5. **Approval-to-effect change.** Withdraw (or narrow again) after approval but before commit raises `policy_generation`; the claim is refused at the lock (AR-07), the old approval stays invalid, a fresh approval at the current generation succeeds (AR-11, AR-12).
6. **Withdrawal and revocation.** Withdrawal and selection or issuer-key revocation before the lock: REFUSE; after commit: no rollback, disclosed (AR-04); key revocation severs prior `activation_ref` (AR-17, AR-27). Ratchet and lineage replacement stay refused (AR-10, AR-22, AR-23).
7. **Retry and stale generation.** Claim carrying an older epoch or generation: REFUSE_STALE; carried ahead: HOLD with `store_state` unchanged (AR-05, AR-12, AR-21). Whether a repeated claim is already stopped by an existing single-use claim state is UNVERIFIED and is characterised at S06; duplicate-delivery protection beyond that is excluded (section 6).
8. **Restart, restore, missing anchor.** Restart recovers by authenticated replay and keeps the ratchet. Missing, unreadable or ahead-of-store anchor, older store or hash-chain break: store `unknown`, HOLD for every participation, no empty baseline (AR-08, AR-18, AR-26). The restore window between the last anchor update and the store head is **undetectable by construction** (ADR 3.6) and is disclosed, not tested away.
9. **Evidence.** `selection_log_v1` (closed 24-member entries including `reasons_registry_label` and `reasons_registry_sha256`), the companion `selection_evidence_v1` stream for refusals, receipt keys, effective-policy digest, exact source/manifest/lock pins, raw per-test output with explicit PASS/FAIL/SKIP/NOT RUN.
10. **Exclusions.** Section 6.

## 4. Candidate configuration manifest

| Key | Value | Origin / owner |
|---|---|---|
| Fields | `allowed_units`, `allowed_adapters`, `allowed_actions` narrowed; `allowed_institutions`, `allowed_authority_domains` carried unchanged (five-set `f1ab`, intersection) | `registry_successor/v2_f1ab.py` `compose_f1ab`; Runtime `LocalExecutionPolicy` (`engine/safe_executor.py:359-365`, unchanged) |
| Contract | `r08-v2` + Amendment 1, family `f1ab` | #25, #29, #32 |
| Identity | canonical effective-policy digest | #33; vectors `docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json` |
| Binding | `policy-binding/0.1`, `approval-commitment/0.2`, reasons 0.1/0.2/0.3 | Control Plane #84 (merged); claim-carried form is S02 |
| Activation and guard | ADR-REG-S4-0 | S04, S05 |
| Keys | synthetic Ed25519, `registry_adapters/ed25519_verifier.py` + `key_admission.py`, canonical base64 | #26, #34 (SECURITY-HELD) |
| Platform | Linux x86-64, CPython 3.11-3.13 | tested scope in `docs/adapters/ed25519.md` |
| Optional | F4/F5 integer-second age families (#31): **not included**; the scenario does not need them | plan section 2 |

## 5. Operator decision (recorded 2026-10-26)

Approved: `MSOP-F1a-C11` (F1a-only scope, scenario C11); the five-set `f1ab` payload with institutions and authority-domains unchanged (the earlier question (0) is resolved); a dedicated Runtime narrowing sprint S03A; EXT-S1-9 and the signing-domain repair in S01; deferral of F4/F5 and Control Plane EXT-S3-1..3; synthetic Ed25519 keys. Details: [Amendment 1](../decisions/2026-10-26-amendment-1-plan-v1.4-g0-schedule.md). Still open: naming an independent Tier 1 lead before the S06 oracle freeze; independent cryptographic review; the CCTV licence scope decision (acceptance matrix section 3).

Original question text, kept for history: approve, amend or reject the profile; accept the gaps as plan amendments; keep F4/F5 and EXT-S3-1..3 out; synthetic keys only; name a Tier 1 lead; decide the CCTV licence scope.

## 6. Explicit exclusions and the customer capability each removes

| Excluded | Capability not available |
|---|---|
| F4/F5 age and per-class values, other F1 sub-families (F1b, F1c), F6, F7 and other families | Central change control of freshness, per-class authority, other local-execution values, agent permissions and delivery policy; they stay code or host constants |
| Duplicate-effect / ambiguous-delivery protection (D04, C09, GAP-G1-01, GAP-G2-04) | No registry-governed retry or dedupe; the component default (OFF) stands and is a disclosed limit |
| More than one tenant or scope; other OS or CPython versions | No fleet or multi-institution rollout; no tested portability |
| Operational key ceremony, rotation, compromise drills | Synthetic keys are not operational trust; no production trust root |
| Publication, discovery, dashboards, GCR (R12 remainder, R14-R16) | No distribution service or cross-domain interoperability |
| Effecting or external workflows, cloud, paid calls | Emulator only |
| Route A rechecks at commit (D-12) | Route A is not re-verified at the commit boundary; status reports say so |
| Restore inside the anchor window | Undetectable by construction; disclosed |

None of these exclusions is a claim that the capability is unnecessary for a later release.
