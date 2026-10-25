# Operator decision record — S03 authorization (2026-10-24)

- Decision date: 2026-10-24 (as issued by the operator). GitHub recording time: this file's first commit in the S03 PR; the decision was issued before it was recorded, and no retrospective approval date is claimed.
- Authority: Cognous operator (André de Lima), per OCS-REG-PLAN v1.1 change control ("the operator alone authorizes material scope/sprint transitions").
- Source: message from the operator in the Claude Code S03 builder session on 2026-10-24 ("I approve proceeding with S03", followed by the text "OCS REGISTRY — Proposed S03 Authorization"). This file is a builder transcription of that message, not a repository original, and is not independently countersigned. The pasted text still carries the heading "Status: PROPOSAL — requires operator approval"; the operator's approval sentence preceding it is what authorizes it.
- Plan: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`, unchanged). The plan heading "S03 ... PLANNED; NOT AUTHORIZED" is static plan text; authorization is carried by this decision, as for S02 under D5.
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md

## Verbatim decision

> Authorize S03 only, as defined in OCS-REG-PLAN v1.1, limited to a minimal registry contract for the LocalExecutionPolicy allowed-units, allowed-adapters and allowed-actions fields.
>
> Requirements:
>
> 1. Reuse existing OCS contract and evaluator concepts.
> 2. Specify stable identities, versions, source digests, applicability, evaluator bindings and deterministic failure treatment.
> 3. Preserve all existing mandatory admission and authority invariants.
> 4. Define focused positive, negative, malformed and missing-record acceptance cases before implementation.
> 5. Use maximum productive parallelism with one integration owner.
> 6. Keep the sprint to one primary deliverable and normally one PR, targeting 1–3 working days.
> 7. Permit autonomous routine repairs, Copilot review and eligible merge under the standing operator delegation.
> 8. Do not implement a registry, modify Runtime behavior or import the historical rule catalogue.
> 9. Stop at the S04 boundary.
>
> Release, publication and production remain on HOLD.

## Builder interpretation (recorded, not an expansion)

- Plan S03 exit names "schema, validator, tests and fail-closed outcomes"; requirement 8 forbids implementing a registry. The builder reads these together as: a record contract, a standalone pure record validator and tests are in scope; a record store, loader, lookup, activation, population, or any Runtime wiring is not. The validator lives outside `baseline/`, imports nothing from `engine`, and reads no files. If the operator intended contract and acceptance cases only, the validator and its tests can be dropped without touching the contract.
- Plan "No general-purpose interpreter, arbitrary scripts or new enforcement authority" is applied literally: the evaluator binding is a closed list with one registered code reference.
- No active record is committed. The only example record is `proposed` and synthetic.

## Conditions applied by the builder

Real GitHub Copilot review of the complete current PR on the exact head, attributable to `copilot-pull-request-reviewer[bot]`; material findings repaired and tests rerun; no CI added; merge bound to the exact verified head; scope remains the contract; stop at S04. This does not extend D4 or the S02 merge authority beyond S03. It supersedes nothing else.
