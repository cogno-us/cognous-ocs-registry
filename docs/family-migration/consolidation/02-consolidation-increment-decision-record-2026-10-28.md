# Architectural consolidation increment: decision record, evidence and status

Status: documentation only; non-authorizing; append-only. 2026-10-28. Governing documents: Static Migration Plan v1.1, Engineering Plan v1.5, adopted audit (PR #60, merge `6516446a4e551e50f2bb47c1d57fbf8ace27d7c5`), consolidation assessment (PR #65, merge `75266cd40400832aee4a798e4d62aba239425b17`), Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ADOPTION.md` at the same revision). This is builder evidence; it is not independent qualification (deferred, not waived).

## Baselines and heads
| Item | Value |
|---|---|
| Registry `main` | `75266cd40400832aee4a798e4d62aba239425b17` (`r08-v5` merge #64 `94e8652725ec34e29fc9b91ed132bb8b5a4b381a`; accounting #66 `2c04c11f7d98548619b68b36064d07e9be878249`) |
| Control Plane `main` (base) | `ae47a040ecfa7d22fb2d98932318d4770f1d3709` (#90) |
| Control Plane consolidation PR | #91, head `592cc610d8474967affb2589d9c02e173c1d3402` |
| Registry PR | none opened: shared orchestration is DOCUMENT-ONLY (not safe, see 01) |
| Registry documentation PR | this PR |

## Adopted decisions and how each was met
| # | Architect decision | Outcome |
|---|---|---|
| 1 | Shared governed-workflow lifecycle skeleton | `registry_governed_lifecycle.GovernedLifecycle`; F4, F5 class age and F5 on_unreadable re-based on it |
| 2 | Family validation and composition stay specialized | Derivations, composers, host validators, refusal codes and exception classes unchanged |
| 3 | Validate the original host before narrowing | Existing `host_class_defect` first; composed workflow refuses `host_class_invalid` before any source read; final validator re-checks it (defence in depth) |
| 4 | Validate the final composed configuration | `final_composition_defect`: no widening, only governed fields differ, extension limit cannot grow, host invariants |
| 5 | Bind one final effective policy to existing identities | Profile-bearing fields: existing `approval_commitment`/`catalogue_digest` over the FINAL profile. F4 scalars: explicit in-workflow bound identity only (see unresolved decision U-1) |
| 6 | Registry selections mandatory where configured | Every declared family verified at every boundary; no optional overlay, no fallback |
| 7 | Fail-closed at existing lifecycle boundaries | Construction, decision, execute entry, commit gate; held state checked first and again last |
| 8 | No generic policy interpreter | None added; the composed workflow calls the existing family derivations |
| 9 | No new authorization or trust authority | None; the ledger only refuses |
| 10 | Protected evaluator algorithms unchanged | `bounded.py`, `runtime_authority.py`, `freshness.py`, `policy_binding.py`, `rule_revision.py`, `reversibility.py` byte-identical (sha256-pinned in tests) |
| 11 | `r08-v5` stays allocated; `r08-v6` not introduced | Ledger updated (append-only) |

## Results by work package
- **A. Lifecycle:** behaviour preserved. Existing suites F4 73, F5 class age 111, on_unreadable 148 pass unchanged apart from the sha256 pins of the two rewritten consumers (updated, reason recorded in the test) and one allowlist entry for the new module in the on_unreadable "only these modules mention the field" guard. One hardening: held state re-checked after the sources ran.
- **B. Composition:** `GovernedPolicyWorkflow` composes F4 ages, F5 class age and F5 on_unreadable (any non-empty subset). Achieved: explicit applicability, all-or-nothing, deterministic, no widening, no post-approval substitution for profile-bearing fields, lifecycle revalidation of every declared family, full refusal when any family becomes invalid. Blocked precisely: persisted-decision/approval binding of the F4 scalars (U-1).
- **C. Deployment applicability:** NOT achieved at deployment scope. The Control Plane has no supported activation boundary (the only `src/` construction site is `cli_run.py`, a plain workflow; no composition root, no activation record, no (tenant, action) index; `activation_sequence` RESERVED). A local advisory `GovernedActivationLedger` was added; it cannot claim exclusivity. Missing contract and minimal proposal: `docs/governed-workflow-consolidation.md` in Control Plane #91 (U-2).
- **D. Registry contract consolidation:** DOCUMENT-ONLY (01). v3/v4 are hash-frozen (`frozen_baseline_manifest.json`, `test_r08v4/v5_frozen_baseline.py`), parity-tested and allowlist-guarded; any shared implementation belongs to a future contract version. `r08-v6` not introduced.
- **E. Tests:** composition module 89 tests (real synthetic Ed25519): each family alone, all combinations, missing/failing mandatory family, revocation/withdrawal/expiry at decision, effect entry and commit gate per family, changed selection between entry and dispatch, partial outage, scope mismatch, approval and decision identity (host-profile approval, rebuilt workflow, restart), original-host invalidity (nothing read), final-composition invalidity, no-widening, F4-scalar gap characterisation, held-state edits, cached-purpose exclusion, failed-attempt semantics, ledger, frozen-Registry compatibility, protected pins.

## Evidence (raw files in `evidence/`)
- Targeted suites, pinned Registry (F4/F5-age pin `6f600ab…`, r08-v5 pin `6c3e5e4…`): 73 + 111 + 148 + 89 = 421 passed, 0 skipped (`targeted-suites-final.txt`).
- Full Control Plane suite, CI-equivalent venvs (freezes included), unchanged main `ae47a04` vs branch: Python 3.11 and 3.12: main 1359 passed / 100 skipped / 0 failed; branch 1359 passed / 101 skipped / 0 failed (`cp-full-*.log`). The extra skip is the pin-gated composition module outside its dedicated CI step.
- Mutation of the new guards (51 mutants, harness `mut_c.py`): round 1 46 killed, 5 survived (`mutation-cp-consolidation-round1.log`); round 2 re-ran those and the six killed only by sibling suites: 10 of 11 killed by the composition tests alone (`...round2.log`); final run at the PR head: 51 mutants, 50 killed, 1 survivor (P11, equivalent as argued below), 0 pattern errors (`final/mutation-cp-consolidation-final.log`). Equivalent: **P11** (final host-invariant re-check): for any final profile that passes the unchanged-field comparison and the widening checks, `irreversible` equals the host's and `on_unreadable` is at most the host's; the original host is already validated (P12, P13 killed), so the final profile cannot violate the invariant. It is kept as defence in depth.
- CI: Control Plane #91 `test (3.11)`, `test (3.12)`, `manifest-validator-parity` at the exact head `592cc61`: all success (push and pull_request runs), plus CodeQL and both Analyze jobs.

## Unresolved Architect decisions
- **U-1 (F4 scalars):** options A accept (scalars are execute-time freshness inputs bound per workflow instance; builder recommendation), B add a scalar member to the persisted decision binding, C add the scalars to the approval preimage (invalidates existing approvals). B and C are authority-semantic and need F3 requalification.
- **U-2 (deployment exclusivity):** where the one-governed-configuration-per-(tenant, action, authority scope) control lives (host `BoundedRecordStore` record, deployment configuration, or a future activation log, EXT-S4).
- **U-3 (Registry shared orchestration):** only with a future contract version; decide together with the allocation policy (DEC-5).
- **U-4:** cached-purpose path not governed by `on_unreadable` (protected evaluator); unchanged.

## Accounting (denominator 19, unchanged)
13 integrated, 6 remaining, 0 independently accepted. This increment migrates no parameter. Builder CI and mutation results are not independent acceptance.

## Standing holds
Registry #58/#59 and Control Plane #87 held; constructor clock tolerance and further migrations NOT AUTHORIZED; independent Tier 1 DEFERRED, NOT WAIVED; V09 SEPARATE; Ed25519 #26/#34 SECURITY-HELD; Release, Publication, Production HOLD; no automatic merges.
