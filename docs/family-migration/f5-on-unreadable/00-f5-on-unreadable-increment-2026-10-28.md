# F5 increment: Registry-governed per-class `on_unreadable` (`P-RG-C-009-on_unreadable`, RG-C-009) (2026-10-28)

Status: **IMPLEMENTED IN OPEN, UNMERGED PRs; NOT ACCEPTED.** Builder-side, non-authorizing, documentation only. Independent Tier 1 qualification is DEFERRED to the integrated engineering freeze (not waived). V09 assurance separate. Ed25519 #26/#34 SECURITY-HELD. Release, Publication, Production HOLD.

## 1. Mandatory references
- Static Migration Plan v1.1 (`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`). Engineering Plan v1.5 (`docs/plans/PROJECT_PLAN-v1.5.md`). Independent Inventory Audit, PR #60, merge `6516446a4e551e50f2bb47c1d57fbf8ace27d7c5`. Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` with `ADOPTION.md` at the same revision.
- Accepted baseline: Control Plane #89 merge `5f11e0f9b10d05cf6970aac0e8023ecbdd448c42`; Registry docs #63 merge `47adfc8f0a07ec488030fe8d83fde6d84a1cd51c` (both verified as the current `main` heads on GitHub before and after this work).

## 2. Deliverables and exact pins
| Item | Where | Exact revision |
|---|---|---|
| A. Registry implementation (`r08-v5`) | Registry PR [#64](https://github.com/cogno-us/cognous-ocs-registry/pull/64), branch `f5-on-unreadable-r08-v5`, OPEN, UNMERGED | head `6c3e5e4037d34bd2b31371461bfc872c762026b9`, based on `47adfc8f` |
| B. Control Plane consumer | Control Plane PR [#90](https://github.com/cogno-us/cognous-control-plane/pull/90), branch `f5-on-unreadable-governed-consumption`, OPEN, UNMERGED | head `e5426dd943106b422d1c5dfcee0ba22e64a47c11`, based on `5f11e0f9` |
| C. Documentation / accounting | this PR (Registry), branch `f5-on-unreadable-accounting` | see the PR |
| D. Consolidation assessment | separate docs-only Registry PR, branch `consolidation-assessment-2026-10-28` | see the PR |
| Runtime change | **None** | n/a |
| Dependencies | Registry checkout at the A pin (CI step 2 of the Control Plane PR), PyNaCl from Registry `requirements-ed25519.lock.txt` (hash-locked) | pins in `tests/test_f5_class_unreadable_governance.py` (`PIN`) and `.github/workflows/tests.yml` |

Merge dependencies: A before B (B's CI checks out A's exact SHA; merge A with a merge commit so the SHA stays reachable, otherwise re-pin B). C and D are documentation and independent of the code PRs. Registry #58, #59 and Control Plane #87 are HELD and untouched.

## 3. Contract decision record (Phase 1)
Source: Control Plane `5f11e0f`, Registry `47adfc8`.

| # | Question | Finding (source evidence) |
|---|---|---|
| 1 | Accepted values | `ActionClass.on_unreadable: Literal["refuse","bounded_tolerance"]`, default `refuse` (`runtime_authority.py:132`). Closed vocabulary, no coercion. |
| 2 | Consuming evaluator branches | Exactly two reads in `bounded.py` (pinned by a test that counts them): `:2111` (irreversible and not `refuse` gives `action_class_invalid`) and `:2189` `_read_grant` (a cached positive may stand in for an unreadable grant status only for a non-irreversible `bounded_tolerance` class). The cached-purpose path (`reversibility.py` `judge_cached_purpose`, `bounded._cached_purpose`) does NOT read it. |
| 3 | Is `refuse` always no more permissive than `bounded_tolerance`? | On the only admitting branch (`:2189`) yes: `refuse` never admits a cached positive. Only the two-point order `refuse` < `bounded_tolerance` is used; no total order is assumed beyond it. |
| 4 | Does irreversibility change the domain? | **Yes.** For an irreversible class the only valid value is `refuse`; `bounded_tolerance` makes the class invalid (every action refuses). Hence the host-validity rule below. |
| 5 | Can the Registry narrow without widening other class attributes? | Yes. The composer sets `on_unreadable` only (profile dumped, one key set, re-validated); a test asserts everything else is byte-identical. |
| 6 | Can the value enter the effective profile before approval issuance? | Yes, at workflow construction. |
| 7 | Does the commitment bind it? | Yes. `approval_commitment` (`runtime_authority.py:236`) hashes `profile.model_dump()`, which contains every `ActionClass`. Equal composition gives an identical commitment; a narrowing gives a different one. |
| 8 | How do selection changes invalidate approvals and decisions? | Re-verification at construction, decision, execute entry and the commit gate must reproduce the bound effective map, Registry digest and effective-profile digest, else `selection_changed`. A decision persisted under one effective profile cannot execute under another (`authorization-critical inputs changed before effect`). An equal effective identity is accepted. |
| 9 | Is a new Registry contract version required? | **Yes.** The `r08-v2` F5 payload is exactly `class_status_max_age_seconds`; a second key is `field_unknown`, and `r08-v2` is frozen. Smallest successor: `r08-v5`, one family `f5-action-class-unreadable-policy`, payload exactly `class_on_unreadable`, version-specific signing domain and policy identity, new modules and table only. |
| 10 | Can class-age and unreadable coexist safely in one workflow? | Yes, as ONE workflow (optional age pair) with a bound identity tuple (both Registry digests plus the FINAL profile digest); either source failing, revoked, withdrawn or changed refuses at every boundary; no fallback to either family alone. Two independent workflows for one action are not supported. |

**Host-validity rule (Architect, 2026-10-28; implemented).** The ORIGINAL host profile is validated against the `bounded.py:2111` invariant before any selection source is read or Registry is called. The Registry may only reduce permissions in an already admissible host profile; it must not repair an invalid authority declaration or conceal a host defect (`host_class_invalid`). A Registry `refuse` composed into an irreversible-and-`bounded_tolerance` class would have made an always-refused class operational (a widening in effect); the Registry cannot see irreversibility, so the guard is consumer-side. `registry_would_heal_invalid_class` remains inside `derive_unreadable` as defence in depth.

**Rejected alternatives**
- *R2: one composite Registry family carrying class age and `on_unreadable`* (like `f1abcd`). Couples two independently governed parameters in one record and one lifecycle, and would have required reopening the frozen `r08-v2` F5 semantics or a second new version. Kept as an Architect option, not implemented.
- *Add `class_on_unreadable` to the `r08-v2` F5 payload.* Frozen; `field_unknown`.
- *`policy_binding` as the carrier (the R6 path).* Needs an activation authority that does not exist and forces `anchor_deadline_to_inputs` (excluded).
- *Patch or override inside the evaluator (read-time substitution).* Changes protected evaluator semantics and substitutes after the commitment was computed.
- *Let a Registry `refuse` repair an invalid irreversible/`bounded_tolerance` host class.* Widening in effect; refused by the host-validity rule.
- *Stack two governed subclasses for the joint case.* A second wrapper over an already gated destination is refused by design; the joint case is one workflow.

## 4. Consumer and Registry behaviour (summary; full text in the two PRs)
Registry: `v5_*` modules (seven), a separate table with one family, `ocs-reg/r08-v5/selection\n` signing domain, `ocs-reg/r08-v5/effective-policy\n` identity domain, `deny_all` never set, stricter-per-class composition, looser Registry value reported as `registry_value_not_narrowing:<classes>`, unknown Registry class refused `composition_record_invalid`, invalid caller refused `composition_caller_invalid`. Control Plane: `GovernedClassUnreadableWorkflow`; verification, composition, lifecycle and commit gate as in section 3; protected evaluator files unchanged (sha256-pinned by tests).

## 5. Lifecycle and effect boundary
Boundaries: construction; start of `decide`; start of `execute`; commit gate immediately before `destination.apply`, via the existing `_GatedDestination` wrapper and `DefinitiveDestinationRejection("registry_f5_unreadable_selection_invalid")` (destination not called; attempt recorded `failed`, which blocks automatic retry). Preserved Architect decisions, nothing new built: the residual delegated-apply window is accepted for bounded engineering only; stronger production atomicity is not established; the host owns authoritative `selection_source` custody with durable rollback and epoch protection (`registry-f4-selection-source-custody.md` applies unchanged); no Control Plane ratchet; no new destination transaction interface.

## 6. Tests, mutation and CI (PASS / FAIL / SKIP / NOT RUN kept distinct)
**Registry (PR #64).**
- New tests: family/composition 72, identity 25, signed decision path (real synthetic Ed25519) 59, frozen baseline and cross-version refusal 176 = 332 (158 frozen files pinned byte-identical against `47adfc8f`).
- Hash-locked environment (`requirements-s01`, `requirements-ed25519`, `requirements-ed25519-test-oracle` installed with `--require-hashes`; cryptography 50.0.1, PyNaCl 1.6.2, pytest 8.3.5): unchanged main `47adfc8` = **7145 passed / 2 skipped / 0 failed**; PR head `6c3e5e4` = **7477 passed / 2 skipped / 0 failed** (+332 = exactly the new tests). The two skips are the same on both sides (`tests/test_adapter_ed25519.py:624` and `:676`, large message / slow corpus).
- Earlier builder-environment runs (kept as historical evidence in `evidence/`): main 1 failed (`test_installed_cryptography_matches_the_test_only_lock`); an earlier branch run also failed the EXT-S1.5 identity-module boundary guard. **Reproduced and classified:** the cryptography failure is a builder-venv version mismatch; under the lockfile (cryptography 50.0.1) it PASSES on main and on the branch. The boundary guard (`test_module_boundaries_are_static_and_checked_from_source_text`) diffs `origin/main...HEAD` against an allowlist of `registry_successor/` files an earlier PR may touch, so any branch adding modules fails it wherever an `origin/main` ref exists (in CI the diff was empty at the earlier head). Resolved with a narrow allowlist change: exactly the seven new `v5_*.py` files, no existing module, no exclusion pattern, no assertion removed. The two v2-guard allowlists (`test_r08v2_family_dispatch.py`, `test_ext_s1_5_vectors.py`) were extended the same narrow way for the v5 modules, as the v4 PR did (`7cd8042`).
- CI at PR #64 exact head `6c3e5e4`: `pytest`, CodeQL, Analyze (python), Analyze (actions): all success (earlier head `1b0c0b5` also green).

**Control Plane (PR #90).**
- New module: 148 tests, all PASS at the exact Registry pin with `OCS_REQUIRE_REGISTRY_PIN=1`. Existing suites on the branch at their own pin: F4 73 pass, F5 class-age 111 pass (Registry `6f600ab`); evaluator suites (`test_runtime_authority`, `test_reversibility`, `test_bounded_authorization`) 152 pass.
- Full suite, CI-equivalent dependencies (`pip install -e ".[dev]"`; pytest 9.2.0, pytest-asyncio 1.4.1, pydantic 2.14.1; freezes in `evidence/`), unpinned default run: main `5f11e0f` **1359 passed / 99 skipped / 0 failed** on Python 3.11 and 3.12; PR branch **1359 passed / 100 skipped / 0 failed** on both (+1 skip = the new module NOT RUN without the pin, by design). Failure sets identical (empty). The earlier "35 async + 6 pin" local failures recorded in earlier increments came from a builder environment without pytest-asyncio; they do not occur in a CI-equivalent environment (this is a correction of how that earlier number should be read, not a change to earlier evidence).
- Mutation: 43 mutants on `registry_f5_class_unreadable_governance.py` (`evidence/mutation-harness-mut_u.py`). **Round 1** (raw: `mutation-cp-round1.log/.json`): 37 killed, 6 survived. Each survivor was investigated: M07 (unnamed-class host-value cross-check), M14 (`deny_all` set with kind `applied`), M39 (record class unknown to the host, adapter-side parse) were defence-in-depth guards behind the real Registry's own refusal and were killed by tests that stub the Registry result; M10 (host vocabulary check) by a direct unit test of the public function (the pydantic `Literal` prevents the state for a real profile); M18 (entry held-profile check) by asserting no selection-source read on a tampered profile; M31 (commit gate uses the execute-entry clock) by a test with a slightly skewed wall clock. One intermediate attempt for M31 was invalid (it failed on the real code too, so its "kill" was spurious) and was replaced. No test was weakened. **Round 2/3** re-runs of the survivors: all killed (`mutation-cp-round2.log`, `mutation-cp-round3.log`). **Final full 43-mutant re-run on the committed tests (Control Plane head `e5426dd`): 43 mutants, 43 killed, 0 survived, 0 pattern errors** (`evidence/mutation-cp-final.log`, `evidence/mutation-results-cp-final.json`). Equivalent or unreachable mutants: none claimed. The kill on each mutant is a failing test against the mutated source while the unmutated source passes all 148.
- CI at PR #90 exact head `e5426dd` (push and pull_request events): `test (3.11)`, `test (3.12)`, `manifest-validator-parity`, CodeQL, Analyze (python), Analyze (actions): all success; the step "Run the Registry-governed F5 on_unreadable tests (must not skip)" carries a junit gate (0 skipped, 0 failed, at least 148 tests) and concluded `success` on Python 3.11 and 3.12 in both event runs (read from the jobs API; job logs are not retrievable).

## 7. Parameter accounting (denominator 19, unchanged and adopted)
Merged basis: **12 integrated, 7 eligible-not-integrated, 0 independently accepted** (F1a-b, F1c, F1d governed by M1-M3; F4 status and approval ages merged as of Control Plane #88; F5 class status age merged as of #89).
`on_unreadable` (RG-C-009, F5, `f5-action-class-unreadable-policy`): represented (r08-v5, PR #64 open); enforcement integration implemented (Control Plane PR #90 open); independently accepted: no.
**If #64 and #90 merge: 13 integrated, 6 eligible-not-integrated, 0 independently accepted until formal qualification.** Open PRs are not counted; green builder CI is not acceptance.
Remaining six after `on_unreadable` (catalogue `P-` ids): `requires_revocation_assurance`, `reversibility`, `anchor_deadline_to_inputs`, terminal-revocation enablement, `ObservationPolicy.max_age_seconds`, `ObservationPolicy.clock_tolerance_seconds`. Excluded and unchanged: constructor clock tolerance (RG-C-006; AR-1/AR-2; Registry #58 held, NOT AUTHORIZED), identity/mandate ages (AR-4), funded merge authorities (unresolved).

## 8. `r08-v5` contract-version collision (Architect decision 2026-10-28)
Registry #58 (constructor clock tolerance F4T, head `1a67d539`, held) and Registry #64 both claim contract id `r08-v5` and both add `registry_successor/v5_*.py` and `docs/r08-v5-contract.md`. **Decision:** `r08-v5` is reserved for the authorized `on_unreadable` implementation. #58 must not later merge under the same contract version or filenames and is not modified here; if clock tolerance is later authorized it must be rebased on the then-current Registry baseline and assigned a distinct successor version (next free id: `r08-v6`) or explicitly reconciled by the Architect. The proposals are not combined into one composite record, and the historical #58 evidence is not rewritten. Recorded in `docs/family-migration/contract-version-allocation.md`.

## 9. Remaining technical limitations
1. Residual delegated-apply window (accepted for bounded engineering only; production atomicity unqualified).
2. `selection_source` rollback, epoch and revocation visibility are host custody duties; no Control Plane ratchet.
3. The value governs only the cached-grant branch; the cached-purpose path is unchanged (a protected-evaluator change would be needed to wire it; not authorized).
4. A profile carrying `policy_binding` is refused; Registry per-family digests are not persisted in the decision binding.
5. F4 constructor scalars cannot be combined with this workflow or the F5 workflows on the same action (F4 refuses runtime-authority profiles); see the consolidation assessment.
6. Registry class ids must satisfy the Registry token rule.
7. Builder-tested only; independent review not performed (deferred).

## 10. Decisions requiring Architect attention
- **D-1** Merge decisions for Registry #64, Control Plane #90 and the two documentation PRs, in the order A, B, C/D, with Registry #64 merged by merge commit (or an explicit re-pin decision).
- **D-2** Confirm the consumer-side host-validity rule (invalid irreversible/`bounded_tolerance` host is refused at construction, not hidden by a Registry value).
- **D-3** Confirm that the value governing only the cached-grant branch is acceptable (cached-purpose wiring not authorized).
- **D-4** Confirm the joint class-age + `on_unreadable` design (one workflow, one bound identity) versus the rejected composite-family option R2.
- **D-5** Confirm the `r08-v5` allocation and the `r08-v6` next-free rule for any future clock-tolerance work.
- **D-6** Decisions raised by the consolidation assessment (separate PR).
