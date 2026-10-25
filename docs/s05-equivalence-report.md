# S05 equivalence report (bounded, builder-authored, Copilot-reviewed)

Plan OCS-REG-PLAN v1.1 (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`), Constitution pin `1c2e920f…`. Authorization: [decision record](decisions/2026-10-24-s05-authorization.md). Method and frozen inputs: [s05-comparison-spec.md](s05-comparison-spec.md). Raw evidence: `docs/s05-results/` (`differential-raw.json`, `pytest-output.txt`). Revision identities of every subject file are in the raw file (`identities`): base `4839747f…`, baseline `safe_executor.py` blob `2fc880da…` (sha256 `940e7819…5b68`), S03 validator `afee88b3…`, S04 consumer `bf382d00…`; expectations blob `37a68275…` and oracle blob `503851c4…` were committed before the harness and are pinned by it. The S03 validator, S04 consumer, `baseline/`, the plan and the Constitution are unchanged by this PR. Config: CPython 3.13.17, pytest 8.3.5, Linux.

## Result

S05 PASS — bounded differential equivalence demonstrated for the tested, representable LocalExecutionPolicy profile. Copilot-reviewed; not formally independently qualified.

(The Copilot disposition is recorded in `docs/sprint-status.md` at closeout.)

## Case counts (PASS / FAIL / SKIP)

| Group | Cases | Pass | Fail | Skip |
|---|---|---|---|---|
| G1 exhaustive (64 caller × 27 registry policies; 27 operations) | 1,728 pairs, 46,656 comparisons | all | 0 | 0 |
| G2 per-field, three values (56 pairs × 3 fields; 4 operations) | 168 pairs, 672 comparisons | all | 0 | 0 |
| Refusal R01–R34 | 34 | 34 | 0 | 0 |
| Representation E01–E20 × 3 fields | 60 | 60 | 0 | 0 |
| Representable boundaries B01–B05 × 3 fields | 15 | 15 | 0 | 0 |
| End to end through `LocalDestinationExecutor` | 11 | 11 | 0 | 0 |
| Pin PIN-1..3, limitations LIM-1..3 | 6 | 6 | 0 | 0 |

Harness: 16 tests; full suite 347 passed. Scratch mutations (not committed): union instead of intersection, registry-only instead of intersection, pin check removed — all caught (7, 5 and 4 harness failures).

## A–G findings

- **A equivalent permissions.** For every pair, the historical policy built directly from the effective sets, the registry-backed policy and the independent oracle gave identical first-failing-check results (admit, adapter, action, unit), which also confirms check ordering.
- **B non-widening.** No operation refused by the caller-constructed policy was admitted after the overlay in any case; the caller policy object was never mutated.
- **C refusal.** All 34 refusal recipes returned the frozen disposition and reason, returned the caller's own policy object, and left behavior equal to the historical caller policy. One recipe (a caller subclass with a replaced `check`) is refused as `caller_policy_invalid`; its behavior is not compared because its own check is replaced.
- **D negative and boundary.** Empty intersections, disallowed values, wrong versions, source mismatch, manifest substitution and invalid selection are covered by G1/G2 and R01–R34. Representable boundaries (256 entries, 128-character entries) are accepted and behave identically.
- **E representation.** Classes E01–E19 (empty allow-list, U+200B, U+2028, NUL, lone surrogate, unassigned and private-use code points, whitespace, tab, newline, NBSP, DEL, control characters, `*` and `a*b`, entry over 128 characters, list over 256 entries, and the others in the frozen file) are accepted by the historical constructor but refused by S03 and by the consumer. Under refusal the caller policy governs, so behavior equals historical; these are **unsupported representations, not inequivalences**. Narrowing a caller policy that lists such a value (when a representable record is applied) is the designed intersection result. E20 (empty-string entry) is rejected by the historical constructor too. **Observation:** the lone-surrogate class (E05) cannot be evaluated through the baseline at all, because `snapshot_envelope` fails with `UnicodeEncodeError` before `check()`; both paths fail identically. It is recorded in the raw results as `not_exercisable`, not counted as an equivalence demonstration for that class.
- **F trust limitations.** Unchanged and reproduced: the consumer verifies installed source bytes on disk, not the loaded code object (LIM-1: a replaced in-process `check` is not detected); S03 alone does not authenticate (LIM-2); `record_source` is unverified provenance (LIM-3). Trusted-host profile only; no claim against a compromised interpreter, host administrator or trusted selection configuration.
- **Pin.** No hidden reliance on a self-selected pin: the harness supplies the pin only through `TrustConfig`; PIN-1 accepts the committed fixtures only with the frozen candidate digest, PIN-2 refuses an altered pin, PIN-3 shows the API offers no derivation path. Synthetic scenarios compute their own pin as the operator stand-in; R09/R14/R24/R31 cover substitution against an unchanged pin. The candidate digest is still not an approved pin.
- **G evidence.** Failures during development are preserved in the PR history: G2 first failed because the harness fixture passed unsorted entries (a harness bug, fixed; S03 requires sorted entries) and E05 first failed as above. No expected outcome in the frozen files was changed.

## Behavioral differences

None found for the tested representable profile. Designed narrowing (intersection) and unsupported-representation refusals are classified separately above and are not inequivalences.

## Not claimed

Universal equivalence; coverage of the other `LocalExecutionPolicy` fields; independent certification; production readiness; complete OCS qualification. The builder wrote both oracle and harness (the oracle is frozen and imports no code under test); Copilot review is code review, not independent qualification.

## Proposed S06 scope (not started)

Cleanup only: reconcile S03 stricter-than-constructor rules with the constructor or document them as policy; decide on the E05 surrogate handling at the baseline boundary; fold the S04 limitations and this report's limits into one trust-limitations page; remove or archive duplicated fixture helpers across S03/S04/S05 tests.
