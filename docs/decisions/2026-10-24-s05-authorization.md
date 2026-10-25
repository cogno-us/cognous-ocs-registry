# Operator decision record — S05 authorization and standing Copilot review designation (2026-10-24)

- Decision date: 2026-10-24 (as issued by the operator). GitHub recording time: this file's first commit in the S05 PR; the decision was issued before it was recorded, and no retrospective approval date is claimed.
- Authority: Cognous operator (André de Lima), per OCS-REG-PLAN v1.1 change control.
- Source: the operator's instruction document "TASK: Confirm S04 closeout and execute S05 behavioral-equivalence assessment", attached to the Claude Code S05 builder session on 2026-10-24 (attachment `c79ba102-attachment.txt`; section "OPERATOR DECISION — EFFECTIVE IMMEDIATELY" and the sections that follow). This file is a builder transcription, not independently countersigned.
- Plan: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`, unchanged). The plan heading "S05 ... PLANNED; NOT AUTHORIZED" is static plan text; authorization is carried by this decision, as for S02 to S04.
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md

## Verbatim operator decision

> 1. Confirm S04 has closed successfully. PR #8 implementation and PR #9 closeout were reported merged. Verify exact GitHub state and status records before proceeding.
>
> 2. Accept S04 as PASS, bounded, Copilot-reviewed and not independently qualified, subject to the verified closeout evidence.
>
> 3. AUTHORIZE S05 — Behavioral Equivalence, as defined in OCS-REG-PLAN v1.1.
>
> 4. Designate GitHub Copilot (copilot-pull-request-reviewer[bot]) as the standing independent technical reviewer for S05 and subsequent authorized development sprints.
>
> 5. This is an operator-approved exception to the normal requirement for a separately designated independent technical reviewer. Copilot review is not formal independent qualification, certification, release acceptance or production authorization.
>
> 6. Require independently specified test expectations before implementation. The builder must not adjust expected outcomes merely to obtain passing tests.
>
> 7. Preserve standing autonomous implementation, repair, review and eligible merge authority within each authorized sprint.
>
> 8. No additional routine operator approval is required to merge S05 once all applicable conditions pass.
>
> 9. Do not modify the static plan or pinned Constitution. Record this operator decision as a dated, source-backed decision under docs/decisions/.

## Verbatim S05 definition

> **Objective.** Determine whether the registry-backed LocalExecutionPolicy preserves the behavior and safety boundaries of the historical hardcoded policy. Compare both paths using identical pinned inputs and configurations. The objective is behavioral equivalence and non-widening, not a new registry architecture.
>
> **Scope — exactly three fields:** allowed_units, allowed_adapters, allowed_actions. Preserve all other LocalExecutionPolicy restrictions and existing evaluator semantics.
>
> **Deliverable.** One bounded S05 PR containing: 1. Frozen comparison specification and expected outcomes. 2. Executable differential test harness. 3. Positive, refusal, boundary and negative cases. 4. Identical-input comparisons between original and registry-backed policies. 5. Tests demonstrating that registry data cannot widen permissions. 6. Explicit representation-coverage analysis. 7. Raw and summarized test results with exact revision identities. 8. Copilot technical review and disposition. 9. One concise S05 qualification/equivalence report.
>
> **Mandatory comparisons.** A. Equivalent permissions: identical results for the same effective policy on supported, representable inputs. B. Non-widening: the registry cannot allow an operation that the caller-constructed historical policy would refuse. C. Refusal behavior: absent, malformed, unsupported, tampered, unauthenticated, stale or inapplicable registry records produce the specified REFUSE disposition without modifying the caller policy. D. Negative and boundary conditions: empty intersections, disallowed actions, adapters and units, check ordering, incorrect versions, source mismatch, manifest substitution and invalid record selection. E. Representation limitations: explicitly enumerate historical policy values not expressible under the S03 record contract (empty registry allow-lists, restricted Unicode characters, whitespace and control characters, wildcards, oversized entries, excessive list lengths); separate unsupported representation from behavioral inequivalence. F. Trust limitations: preserve the trusted-host threat model; the consumer verifies installed source-file bytes, not the loaded Python code object; do not claim protection against a compromised interpreter, host administrator or trusted selection configuration. G. Evidence and failure preservation: retain raw failures, negative outcomes, test exclusions, blocked cases, execution configuration and exact source hashes; do not silently reclassify a failure as not applicable.
>
> **Test design.** Establish expected results before executing the comparison battery. Use the original historical policy as the behavioral reference. Use independently derived contract expectations for refusal, source authentication, non-widening and negative cases. Tests must not depend on the candidate implementation's output to determine what the expected result should be. Do not alter the frozen S03 validator or S04 consumer merely to make the differential tests pass. If a genuine defect is found, document it, reproduce it and prepare the smallest authorized correction; preserve the failing evidence. If a defect requires a material change to the accepted S03/S04 contract or Tier 1 admission semantics, stop that correction and route the decision to the operator.
>
> **Review and merge.** Request GitHub Copilot review on the exact final S05 PR head, with explicit examination of: test independence and oracle construction; behavioral-equivalence claims; non-widening and refusal cases; authentication and applicability assumptions; scope of unsupported historical policies; any hidden reliance on a self-selected manifest pin. Resolve material findings and rerun affected tests. Verify the final PR head immediately before merge. Merge autonomously only after all applicable checks and review conditions pass. Record the exact merge SHA, PASS/FAIL/SKIP, coverage, limitations and review disposition.
>
> **Acceptance language.** If the bounded battery and review pass, record: "S05 PASS — bounded differential equivalence demonstrated for the tested, representable LocalExecutionPolicy profile. Copilot-reviewed; not formally independently qualified." Do not claim universal equivalence, independent certification, production readiness or complete OCS qualification. If material differences remain unexplained, record S05 BLOCKED and preserve the evidence.
>
> **Limits.** Target 1-3 working days, maximum 5. One primary deliverable, normally one PR. Maximum productive parallelism for nonconflicting work; one integration owner. No additional rule families, general registry infrastructure, dynamic activation, production deployment, historical catalogue import or unrelated cleanup.
>
> **S06 boundary.** S06 is not authorized by this decision. Stop after S05 closeout. Provide a concise recommendation for the S06 cleanup scope without starting implementation.
>
> RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## Verified S04 closeout (item 1; builder check on 2026-10-24, GitHub REST)

PR #8 merged, merge SHA `0b76df2b982f83f48526694763303eefb32f1ac7`, merged head `7a3483c1eb68e0f398542af8ac8fc44cecef60ea`. PR #9 merged, merge SHA `4839747f409000651bf1a684e112b5552912fee1`, head `9105771a3f88d2001a3af20cae799ac2ac903bfd`. `docs/sprint-status.md` on `main` records S04 PASS with the first merge SHA. At `4839747f` the suite passes 331 of 331; the plan blob `6ece90f6...`, the frozen S03 validator (`afee88b3...`) and the baseline source (`2fc880da...`) match their pins. Item 2 is applied: S04 stands as PASS, bounded, Copilot-reviewed and not independently qualified.

## Builder notes (recorded, not an expansion)

- Item 4 makes Copilot the standing technical reviewer for authorized sprints. It does not change what Copilot review is: it reviews the PR diff and does not author an independent battery. The builder wrote the S05 oracle and harness. The oracle and expected outcomes are frozen and committed before the harness exists (item 6), and the harness pins their file hashes so an expected outcome cannot be quietly edited to obtain a pass. Any later change to a frozen expectation must be a separate, recorded amendment.
- The S05 report will use the acceptance language above and no stronger language.
- Operator authority over the pin is unchanged: this decision approves no manifest digest and activates no overlay.

## Conditions applied by the builder

Real GitHub Copilot review of the complete current PR on the exact head, attributable to `copilot-pull-request-reviewer[bot]`; material findings repaired and affected tests rerun; no CI added; merge bound to the exact verified head; no change to the frozen S03 validator, the S04 consumer, `baseline/`, the plan or the Constitution; stop at the S06 boundary. This supersedes nothing else.
