# R08-PREP 10: Source revision reconciliation and review closure

Purpose: (1) keep the historical S01/S02 source baseline and the current component heads separate, with the contract-relevant differences between them (Architect LD-06 / R-09); (2) reconcile the ISS review's older plan text against merged v1.2 (R-08); (3) close the three Copilot findings on PR #18 with bounded evidence.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification. **No integration baseline is selected here.**

## 1. Sources and revisions examined

| Source | Revision |
|---|---|
| Runtime `cognous-execution-runtime`, HISTORICAL BASELINE (S01/S02 pin) | `ec728da6dc301a664b331ac8986afd6e850a1273` |
| Runtime, CURRENT CANDIDATE (default-branch head, re-fetched) | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` |
| Control Plane `cognous-control-plane`, HISTORICAL BASELINE (S01/S02 pin) | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` |
| Control Plane, CURRENT CANDIDATE (default-branch head, re-fetched) | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` |
| Registry `main` (merged R07 inventory and analysis) | `e3f5bbc32f957a10822a15a1b642e48c63d428e9` |
| Registry plan v1.2 (merged) | blob `32319775c6e2d9c3fff1e2171c8f4c9d096911d6` |
| ISS review base plan text | PR #16 head `100aa407` |
| Registry frozen baseline `baseline/execution-runtime/engine/safe_executor.py` | git blob `2fc880dae37eac76e5074533435740ce0684209d` |

Not inspected: tests were not executed; the effective-grant, freshness, executor and reason-vocabulary files were checked only by whole-tree `git diff --stat` (unchanged between pin and head, below), not re-read; Action Manifest, Governed Exchange and ODES sources; any Control Plane production resolver; the hub repository.

## 2. Source revision reconciliation (historical baseline vs current candidate)

The two heads were re-fetched for this document and are unchanged since the earlier lane work. [EXISTING]

| Component | Pin to head, whole tree | Result |
|---|---|---|
| Runtime | `git diff --stat ec728da6… c5e97e87…` | 3 files: `engine/local_authority_effect.py` (+52/-3 in the engine diff, 55 changed lines), `tests/test_atomic_approval_status_terminality.py` (+314), `tests/test_atomic_approval_terminality_flow.py` (+59). No other engine file changed, so `safe_executor.py`, `control_plane_adapter.py`, `atomic_local_control_plane_executor.py` and `effective_grant.py` are identical at both revisions |
| Control Plane | `git diff --stat 0a41faa9… 7a4bcd40…` | 2 files: `src/agent_control_plane/local_authority_effect.py` (+8/-2) and `tests/test_claim_journal_stage.py` (+165). `bounded.py`, `rule_revision.py`, `freshness.py`, `runtime_authority.py` and the reason-vocabulary schemas are identical at both revisions |

Contract-relevant differences [EXISTING, from the diffs read in full]:

1. **Runtime, terminal approval revocation (head only).** The head adds a retained revoked-approval set (`APPROVAL_REVOCATION_TABLE = "authority_approval_revocations_v1"`, `engine/local_authority_effect.py:39`), a helper `_approval_revoked`, a rejection of claim provisioning for a revoked `approval_ref`, a rewritten `set_approval_status` that makes `revoked` terminal under `BEGIN IMMEDIATE` (parity with `set_grant_status`), and an added `or self._approval_revoked(conn, expected.approval_ref)` term in the commit-time approval check (`_validate_claim_state`, approval block before line 746). At the pin, an approval revoked then set back to `active` would pass the commit-time `status` check. [EXISTING]
2. **Control Plane, claim-issuance journal (head only).** `_materialize_under_handoff` passes `stage="claim"`, the `decision`, and a `check_ref` into `workflow._resolve` and `_record_check` when a runtime-authority profile or an identity/freshness profile is configured, so the claim-stage resolution is journaled. It does not change the `current != decision.binding` refusal. [EXISTING]
3. **Not different:** the commit-time policy loop (`engine/local_authority_effect.py:746-758` at head; the same logic at the pin, where `_validate_claim_state` starts at line 627), the claim validity interval check (head line 707), trusted time taken after lock acquisition (head line 800), and every Control Plane `bounded.py` line cited in documents 03 and 04. Line numbers in this document are head numbers unless marked pin. [EXISTING]

Which statements in documents 01-09 rest on which revision:

| Statement | Basis |
|---|---|
| Control Plane `bounded.py` cites in 03 (decision/effect resolution, grant and policy checks) | Identical at pin and head |
| Runtime `safe_executor.py`, adapter, atomic executor and `effective_grant` cites in 03, 04, 05 | Identical at pin and head |
| `local_authority_effect.py` line cites in 03 section 3.4 and 04 findings 1-2 (`675-760`, `782`) | Head only; the file differs from the pin (item 1) |
| Terminal approval revocation (04 finding 4, 04 race table "withdrawn approval", 04 LD-06) | Head only; absent at the pin |
| Claim-journal stage (not cited in 03/04) | Head only (item 2) |

[PROPOSAL] Planning stance, following the Architect: preserve both baselines. Historical evidence stays attributed to the pins and is not invalidated. R10 selects a new exact-source integration candidate after reviewing the differences above; the registry migrates to neither revision automatically because `main` advanced. Nothing here selects the candidate. The registry's own frozen evaluator blob `2fc880da…` is byte-identical at the pin, at the Runtime head, and in `baseline/` (S01/S03 provenance and the lane check), so the evaluator semantics the S03/S04/S05 evidence used are not affected by the head differences. [EXISTING]

## 3. Plan text reconciliation (R-08)

The ISS review documents cite OCS v1.2 PR #16 head `100aa407`. The merged plan at `e3f5bbc3…` is the controlling text. A diff of PR #16 head against merged v1.2 shows the plan file changed (49 insertions, 35 deletions on the merge-base comparison recorded in document 08 R-08). [EXISTING]

[PROPOSAL] How to use that fact without relying on unread detail: the line-by-line differences were not enumerated for this document, so any ISS-review statement that quotes or paraphrases v1.2 section numbers, phase scope or gate wording is to be treated as unverified against the merged text until the R14 owners recheck it. This applies to the ISS review's mappings of the shared addendum, section 3.3 binding wording and the R08/R14/R15 sequencing. The merged plan's own text is what documents 01-09 cite directly (per-operation participation, section 3.2/3.4; R09/R10 tasks). Where an ISS statement and merged v1.2 differ, merged v1.2 controls. A read-only line-by-line diff remains a candidate task (document 08 section 7(d)). This section does not claim the differences are immaterial.

## 4. Copilot review closure (PR #18, review `5641463638`, head `f947485…`)

One review returned; no further review is requested. Corrections were committed at `46087f158a164e6bafc8365ba609c88d3fec0418` and the sections below are verified against that text and source.

### 4.1 Finding 1: epoch tie-break versus explicit supersession

| Item | Disposition |
|---|---|
| Finding | Doc 02 section 4.5 let the highest verified epoch govern, contradicting doc 01 section 3.3 (explicit supersession; overlapping effective selections refuse) |
| Disposition | **Accepted and corrected.** A higher epoch never authorizes supersession alone. A newer epoch takes effect only through an explicit, attributable, approved selection decision (doc 01 section 3.3 "Supersession"); two verified selections that would both be effective for one scope at one evaluation time refuse for both (`selection_epoch_conflict`). `min_epoch` only rejects epochs below the floor |
| Where corrected | `02-authentication-and-custody.md` section 4.5; consistent with `01-lifecycle-contract.md` section 3.3 (supersession row) |
| Bounded evidence | Doc-to-doc consistency check of the two sections at `46087f1`; `grep` shows no remaining "highest epoch governs" wording in 02 |
| Residual limit | The final conflict rule and the selection-scope key remain decision A-03; no source implements it |

### 4.2 Finding 2: Control Plane resolution versus Runtime revalidation

| Item | Disposition |
|---|---|
| Finding | Doc 03 said the Runtime does not validate grants, contradicting Route B |
| Disposition | **Accepted and corrected.** Responsibilities stay separate: the Control Plane resolves grants at decision time and again at effect time through the trusted resolver; in Route B the Runtime destination additionally enforces the stored authority state inside the commit transaction. Neither is a registry check |
| Where corrected | `03-consumer-integration-contract.md` section 3.3 |
| Bounded evidence | Control Plane `bounded.py` (identical at both pins): `_resolve_inputs` at 2239, grant validity at 2411 (`expires_at` / `not_before` against `now`), `execute()` re-resolution `stage="effect"` at 1685 and the `current != persisted.binding` refusal at 1690. Runtime `engine/local_authority_effect.py` (head): `_validate_claim_state` at 675, claim validity interval at 707 (`not_before <= now < expires_at`), authoritative grant row and validity at 724, approval block ending before 746, policy loop 746-758, `execute_claim_atomic` at 782 with `BEGIN IMMEDIATE` at 798 and trusted time after the lock at 800. At the pin the same checks exist with different line numbers (`_validate_claim_state` at 627, `execute_claim_atomic` at 733) except the terminal approval revocation term (section 2 item 1) |
| Residual limit | Route A (`PinnedControlPlaneExecutor`) has no destination-transaction grant read; the atomic read exists only for Route B in one SQLite database. Route choice is decision C-06 |

### 4.3 Finding 3: commit-time selection validity

| Item | Disposition |
|---|---|
| Finding | A selection can expire between evaluation and commit without changing epoch, digests or the policy row, so identity comparison does not enforce doc 01 section 3.4 |
| Disposition | **Accepted; recorded as an open binding gap, not solved.** Registered as LD-09 (doc 04 section 4.2 and race table; doc 06 QM-06; doc 08 register) |
| What exists today at the destination | [EXISTING] a trusted clock evaluated after lock acquisition (`_trusted_now`, lines 79-84, called at 800); a claim validity interval check (`claim.not_before <= now < claim.expires_at`, line 707); grant validity (line 724). The policy loop (746-758) compares `ref`, `version`, `status == "active"` and tenant only. **No lock-held validity or expiry check exists for a registry selection**, and the policy row carries no interval |
| Where documented | `04-effective-policy-consistency.md` sections 4.2, 5 and 7 (LD-09); `06-qualification-contract.md` QM-06; `08-decisions-and-dependencies.md` section 4.4 |
| Candidate closures (not adopted) | (a) a lock-held validity check against trusted time for the selection interval; (b) constrain the claim `expires_at` to the authenticated selection interval at issuance; (c) accept and state the limitation. Architect rulings C-03/LD-01 add that identity-only or evidence-only recording is insufficient to prove authorization at commit |
| Residual limit | The Architect's F1 limit stands: `LocalExecutionPolicy.check` runs before the claim outside the transaction (`atomic_local_control_plane_executor.py:69`, document 03 section 3.4), so even a closed expiry gap does not re-evaluate F1 restrictions atomically. The F1 authority-to-effect guarantee is UNQUALIFIED until an integration design shows re-evaluation within a supported atomic boundary or an independently defensible no-widening binding |

## 5. Constitutional and v1.2 mapping

Read in the pinned Constitution by other lanes: CA03, CA05, CA06, CA12, CA18, CA22. This document adds no new article reading. Plan v1.2: R09/R10 effect-boundary and revocation tasks; section 3.3 atomic effective-policy binding (A5, scope clarified); R17 qualification. Crosswalk A5 (no global atomicity), A10.

## 6. Decisions raised

| ID | Decision | Owner | Blocking consequence | Overlap |
|---|---|---|---|---|
| S-01 | Select the R10 integration candidate (exact Runtime and Control Plane revisions) after reviewing section 2 | Runtime / Control Plane integration owners; OCS Architect and operator for scope | R10 cannot start; no consumer binding can name a source revision | LD-06 |
| S-02 | Re-ground ISS-review statements against merged v1.2 (read-only diff) | GCR owner with OCS Architect | R14 crosswalk would rest on pre-merge text | R-08; G-01 |
| S-03 | Whether the destination or claim issuance enforces selection expiry (section 4.3 options a-c) | OCS Architect | Doc 01 section 3.4 unenforceable at commit | LD-09 |

## 7. Risks and unresolved constraints

- Terminal approval revocation exists only at the Runtime head; consumers of the S01 pin do not have it (LD-06).
- The Control Plane claim-journal change was read from the diff only; its behaviour was not tested.
- Line numbers in section 4.2 are head numbers; pin numbers were given only where checked.
- The plan diff in section 3 was summarised by size; line-level effects on the ISS review were not established.
- No test was run, and nothing here is [DEV-TESTED] for the head changes beyond the new upstream test files existing in the diff.
