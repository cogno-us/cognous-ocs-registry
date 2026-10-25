# Operator decision record — D1 to D5 (S01)

- Date: 2026-10-24
- Authority: Cognous operator (plan authority per OCS-REG-PLAN v1.1)
- Source: operator instruction delivered in the Claude Code S01 builder session on 2026-10-24 (attachment `fe645684-attachment.txt`, "OPERATOR DECISION RECORD — D1 THROUGH D5"). Recorded here by the builder; not independently countersigned. No retrospective approvals are fabricated.
- Reviewed candidate head named by the operator: `d6e39d34945e39e2d34cab85ffb7822e721875c4`. The builder's later head adds only the documentation and test-comment changes listed in PR #1; it is validated separately.
- Plan: https://github.com/cogno-us/cognous-ocs-registry/blob/s01-baseline/docs/plans/PROJECT_PLAN-v1.1.md
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md

## D1 — Historical baseline selection
APPROVED: Adopt g8-r10 as the authoritative historical reference for the OCS registry migration program.
Hub tag `review-v0.1-g8-r10-20261022`; hub commit `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c`; component-lock SHA-256 `dcd3ab9e4e737c7e50f4bc38c2439438f156da64c9eb1e46725f477973da59ff`; Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`.
This is an explicit operator selection for registry migration. Do not describe g8-r10 as the original OCS release, a published release or an independently qualified baseline. Preserve exact source identity and provenance.

## D2 — S01 implementation boundary
APPROVED: Accept the Runtime-only LocalExecutionPolicy implementation as the bounded S01 baseline. S01 does not require importing the Control Plane, Replay Bundle, Evidence Pack or complete historical OCS. Retain the imported source byte-identically unless a separately authorized correction becomes necessary. Preserve the documented mismatch between the embedded CONTROL_PLANE_COMMIT and the g8-r10 component lock; do not modify the embedded historical revision merely to harmonize documentation. Do not claim that Runtime-only tests establish complete OCS behavior. Control Plane scanners, policy_gate, reason vocabularies and mandatory-check manifests may be examined during S02 but are not retroactive S01 requirements.

## D3 — Licensing
APPROVED: Apache-2.0 for newly authored Cognous material in this repository. Preserve the applicable original licensing obligations for imported material. Retain Apache-2.0 notices for the Cognous engine source and MIT notices for applicable upstream Moltbot material. Do not relicense imported third-party material by implication. Add the appropriate repository-level licensing documentation, preserving source-specific attribution. Attribute any copied upstream test-envelope material to its original source. Verify ownership and applicable license obligations before representing newly authored or imported material as distributable under Apache-2.0. No publication authorization is granted.

## D4 — S01 review, acceptance and merge
APPROVED: Conditional autonomous merge of PR #1 after focused independent review and exact-head validation. No additional operator approval is needed for routine repairs or for merging PR #1 once every condition is satisfied:
1. Verify the selected g8-r10 baseline and exact source provenance.
2. Verify imported file identity and retained licensing obligations.
3. Verify clean-clone reproduction at the final PR head.
4. Preserve actual PASS, FAIL and SKIP results.
5. Obtain focused independent technical review covering source provenance, implementation boundaries, testing and licensing.
6. Resolve material review findings.
7. Run all configured applicable required checks successfully.
8. Document the historical Control Plane revision mismatch without silently modifying source.
9. Preserve untested behaviors as explicit limitations.
10. Confirm that S01 introduced no unauthorized registry implementation or behavioral change.
11. Confirm that the final PR matches the authorized S01 scope in OCS-REG-PLAN v1.1.
12. Verify the exact final PR head immediately before merge.
Builder-side self-review does not establish independent qualification; where independent qualification was not performed, report that limitation truthfully. Do not invent CI results where no CI workflow exists. If an acceptance condition cannot be established, leave PR #1 unmerged and report the specific blocker. On satisfaction of all conditions: mark PR #1 ready, merge using an authorized GitHub actor, record the exact merge SHA.

## D5 — Conditional S02 authorization
APPROVED: S02 is pre-authorized, subject to successful S01 closure. Effective only after: (1) S01 satisfies D4; (2) PR #1 is merged; (3) the accepted baseline and merge SHA are recorded; (4) `docs/sprint-status.md` records S01 PASS; (5) the next assignment is checked against the unchanged S02 section of OCS-REG-PLAN v1.1. If S01 remains BLOCKED, S02 remains BLOCKED. S02 must not modify runtime behavior, implement the registry, import the historical rule catalogue, or begin S03.

## Standing instructions recorded
Static plan not rewritten; the v1.1 custody-path wording is an editorial defect that does not block S01 and gets no new revision. After merge, update operational references to canonical main-branch paths. `docs/sprint-status.md` is the sole live status document. Release, publication and production remain HOLD.
