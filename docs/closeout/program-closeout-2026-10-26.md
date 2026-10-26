# Program closeout and reconciliation, 2026-10-26

Non-authorizing, builder-side, documentation only. It authorizes no work. It does not edit the static plans, frozen contracts or historical evidence. Release, publication and production: **HOLD**. Tier 1 independent qualification: **NOT STARTED** (no independent lead; GAP-G4-13 open).

Rule used throughout: a contract, reason code, merged ADR, green CI or an AI review is **not** evidence of implementation or qualification. Levels: **S** specified, **I** implemented, **D** developer-tested (builder tests, CI, AI/Copilot review), **Q** independently qualified. Nothing in this repository is at **Q**. Status words: COMPLETE, PARTIAL, NOT STARTED, BLOCKED, DEFERRED, NOT REQUIRED, UNVERIFIED.

## 1. Completion matrix

PR numbers are Registry PRs unless a repository is named. Merge SHAs are abbreviated; all PRs below are merged.

| Item | Planned deliverable | Status / level | Evidence | Missing work | Disposition |
|---|---|---|---|---|---|
| S01-S06 (plan v1.1) | Baseline import, inventory, minimal contract, overlay consumer, differential equivalence, consolidation | COMPLETE, S+I+D (bounded to three allow-lists) | #1 `6feb06ec`, #3 `15938729`, #5 `2d177fba`, #8 `0b76df2b`, #10 `e10e8077`, #12 `03b4db31`; [sprint-status](../sprint-status.md) | Nothing wired to the Runtime; 3 E05 SKIPs; no pin approved | Closed; history only |
| R08-PREP | Selection, lifecycle, activation, custody, effective-policy design | COMPLETE, S | #18 `1324bab1` | None | Closed |
| R08-S01 | `r08-v1` contract and selection-verification foundation | COMPLETE as a foundation, I+D | #19 `783ff59f` | No activation, key, verifier or Runtime wiring | Superseded by EXT line |
| P0 (v1.3) | V0.2 contract reconciliation | COMPLETE, S | #20 `ce00520f` (v1.3 adoption), #21 `d61ef729` | None | Closed |
| P1 plan (v1.3) | Extraction design and execution cards | COMPLETE, S | #22 `d2c472e4`; [p1-extraction-plan](../p1-extraction-plan/README.md) | Later work followed the EXT sequence only in part (see section 4) | Input to v1.4 |
| EXT-S1-0 | Registry CI | COMPLETE, I+D | #23 | CI is not qualification | Closed |
| EXT-S1-1 | Canonical V1 contract (D-01..D-31) | COMPLETE, S | #25; Amendment 1 #32 | None | Frozen |
| EXT-S1-2 | Family-dispatch foundation | COMPLETE, I+D | #27 | None | Closed |
| EXT-S1-3 | Five-set `f1ab` family | COMPLETE, I+D | #29 | None | Closed |
| EXT-S1-4 | F4/F5 integer-second age families | COMPLETE, I+D | #31; [spec](../ext-implementation/ext-s1-4-age-integer-slots.md) | Age-range characterisation is WIP in the Project, not in the repo | Closed |
| EXT-S1-5 | Effective-policy identity | COMPLETE, S+I+D | spec #30, #35; implementation #33 | Cross-repo consumption (Runtime, Control Plane) not done | Reuse vectors |
| EXT-S1-6 | Withdrawal / snapshot-floor behaviour | NOT STARTED | `trust_snapshot_version_stale` and `selection_withdrawn` are declared in `registry_successor/v2_codes.py` with no emitter; no withdrawal handling in `selection.py`, `verify.py`, `decision.py`; tests describe them as codes "with no behaviour" | All behaviour | Deferred input |
| EXT-S1-7 | Ed25519 `SignatureVerifier` adapter | COMPLETE as built, I+D; **SECURITY-HELD** | #26 `51469cbe` and core verifier hardening #34 `06b9ab95` | No independent cryptographic review; Linux x86-64 CPython 3.11-3.13 scope only; CCTV vector upstream licence confirmation not obtained | Hold stays; Q gate |
| EXT-S1-8 | Activation / high-water conformance kit | COMPLETE, I+D | #28 | No consumer under test (Runtime) | Reuse in S4-2/S4-3 |
| EXT-S1-9 | R09 adversarial battery with the real verifier ([card](../p1-extraction-plan/11-ext-pr-execution-cards.md)) | NOT STARTED | No PR | Whole battery (forged, replayed, rollback, stale snapshot and so on); partly depends on EXT-S1-6 | Reuse as acceptance battery in v1.4 |
| P1 follow-ups | M1, FU-1, FU-2, F4, canonical base64, #26 review fixes | COMPLETE, I+D | #36 `0fca88c6` | None | Closed |
| EXT-S2-G | CI check inventory | COMPLETE, S | #24; [inventory](../ext-implementation/ext-s2-g-check-inventory.md) | None | Input |
| EXT-S2-1, S2-2 | Runtime-side changes | NOT STARTED | Runtime read-only head `c5e97e87` unchanged by this program | All | v1.4 |
| EXT-S3-1..3 | Control Plane per plan | NOT STARTED | Control Plane main `fff27ebf`; no change other than R6 | All | v1.4 |
| EXT-S3-4 | Approval generation / ceilings | PARTIAL, I+D | Control Plane #84 (`policy-binding/0.1`, `approval-commitment/0.2`, reasons 0.1/0.2/0.3 immutable) | Plan's host-factory per-class minimum not delivered | v1.4 |
| EXT-S4-0 | Integration and authority contract | COMPLETE as a contract only, S | #37 `a3f2daff`; [ADR](../decisions/2026-10-26-adr-ext-s4-0-integration-contract.md) | Zero code; 27 acceptance rows AR-01..AR-27 unexecuted | Adopted; not implemented |
| EXT-S4-1 | (Registry-side step) | NOT REQUIRED | ADR sequencing | n/a | n/a |
| EXT-S4-4, S4-5, S4-2, S4-3 | Claim-carried binding; re-pin; Runtime destination and atomic guard; end-to-end emulator | NOT STARTED, DEFERRED | ADR sequence | All | Not authorized |
| EXT-S5 | Predeclaration, QG-01..QG-12 qualification gate runs, freeze, gap report (cards S5-1..last) | PARTIAL: preparation only | Stack Qualification #231 (successor assertion 172/164 with substitution negatives; pin file proposed) | Pin not approved; nothing to pin until S4 | Deferred |
| EXT-S6 | RC pin freeze, full exact-pin run, evidence retention, truthful status report | NOT STARTED | n/a | All | Deferred |
| Tier 1 independent qualification | Independent review and qualification | NOT STARTED | GAP-G4-13 | Lead, reviewers, scope | Operator decision |

P0-P6 mapping: P0 COMPLETE; P1 PARTIAL (S1 mostly done, S2-S4 not); P2-P6 NOT STARTED. UNVERIFIED: whether any P2-P6 item beyond the EXT cards was planned for implementation by name in v1.3; I did not re-derive that per phase. Missing evidence: a line-by-line P2-P6 read against v1.3.

## 2. Accepted architectural baseline

Specified (S) and adopted, not executable end to end: the `r08-v2` canonical contract and Amendment 1 (#25, #32); TR-01 activation and epoch ownership; DR-CP-AGE-1; and the EXT-S4-0 contract (consumer-owned durable activation state in the Runtime SQLite DB under the commit's `BEGIN IMMEDIATE`, hash-chained log with a closed 24-member entry schema, durable `scope_required` ratchet, lineage replacement prohibited, recovery baseline by replay, AD-1..AD-5 alternative A, eight reasons-0.3 names ratified).

## 3. Outstanding implementation boundaries

Everything the EXT-S4-0 ADR places in the Runtime (durable state, atomic guard, REFUSE/REFUSE_STALE/HOLD at the consumer boundary), claim-carried binding, EXT-S1-6, withdrawal and the snapshot floor, EXT-S2 and EXT-S3-1..3, the stack re-pin, and an end-to-end flow. **No Registry → Control Plane → Runtime flow exists today.**

## 4. Drift from the approved plan

- v1.3 is still named `...-DRAFT.md`; adoption is evidenced by PR #20 and the file's own status line, with no separate adoption record file.
- `docs/sprint-status.md` was stale (R08-S01 shown as the current action after merge); corrected in this PR, history kept.
- Control Plane delivered an R6 reconstruction (#84) rather than EXT-S3-1..3 as planned; EXT-S3-4 is only partly met.
- EXT-S1-7 and #34 merged under SECURITY-HELD labels; the hold is not lifted by the merge.
- EXT-S4-0 consolidated N-7/N-8/N-9 and added contract elements (ratchet, label/digest custody, closed log schema) that the original cards did not enumerate.
- Registry-side withdrawal (A1) and the snapshot floor remain unimplemented although their reason codes exist.

## 5. Qualification status

All work is BUILDER-TESTED and AI-REVIEWED. NOT INDEPENDENTLY SECURITY-ASSESSED. NOT TIER 1 QUALIFIED. Ed25519 scope is Linux x86-64 CPython 3.11-3.13. Copilot/AI review is technical review, not qualification. Stack Qualification holds only preparation (#231) and no approved pin.

## 6. Verified pins (2026-10-26)

| Repository | Pin |
|---|---|
| Registry main | `a3f2daff5c5873e13bdfdbf1adce329f8f129187`; post-merge `Registry tests` run 40372915409 completed with success; Analyze checks succeeded |
| Control Plane main | `fff27ebf356007e1eb3bb24198efc7e3e3f0c5eb` (R6, #84) |
| Execution Runtime (read-only clone head) | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`; imported S01 baseline remains `ec728da6dc301a664b331ac8986afd6e850a1273` (not the same commit) |
| Stack Qualification main | `67dcaeffc955ef1b91388e0abd1ceff8eb87834c` (#231) |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` |
| Plan v1.3 | blob `c20c981ac19c64cc7f8c15ad27a8a2ee5e681c95` at the time of inspection |

## 7. Open PRs and dispositions (recommendations only; no action taken)

Open at inspection: Registry #7 (pytest bump), Stack Qualification #224, #222, #198; no open Control Plane PRs. None belongs to this increment; leave them to their owners (#7 and #198 are routine dependency bumps). This closeout PR is the only open item of the increment and awaits the Architect.

## 8. Closeout limitations

Built from repository contents and PR metadata, one bounded inspection for EXT-S1-6, no re-run of historical suites, no line-by-line P2-P6 audit, no cross-repository code audit of Runtime or Control Plane beyond the pins above. Anything not listed as verified is UNVERIFIED.
