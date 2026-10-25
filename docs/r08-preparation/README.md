# R08-PREP: authenticated selection, lifecycle, activation, custody and effective-policy consistency (architecture preparation)

Status: **DRAFT, documentation only.** Prepared under OCS-REG-PLAN v1.2 (blob `32319775c6e2d9c3fff1e2171c8f4c9d096911d6`) against registry `main` `e3f5bbc32f957a10822a15a1b642e48c63d428e9` (documents first drafted at `eb850c8d303961d099a123534121aeac280b242b`). Revised in place to apply the OCS Architect's disposition of PR #18 ("ACCEPT WITH AMENDMENTS"), an Architect ruling that is not operator approval.

## What this is, and is not

- This is architectural preparation only. It proposes candidate interfaces and contracts for a governed rule registry; every state machine, tuple and interface in it is a candidate model, not a normative or preapproved contract.
- It authorizes **no R08 or R09 implementation**, and no other phase. It does not authorize any rule-family migration, pin approval, runtime activation, new database or service, release, publication or production use.
- PR #13 (historical recovery inventory, merge `e20504df8d2c8ddf8b3944c0dabb0dcf5f1009b6`) and PR #17 (rule-family and schema analysis, merge `e3f5bbc32f957a10822a15a1b642e48c63d428e9`) are **MERGED SOURCE EVIDENCE, WITH PROVISIONAL CLASSIFICATIONS**. Their proposed schemas and classifications are not promoted to implementation requirements, and the merged documents are not edited. They are cross-referenced by file and decision ID, not repeated; open D-items (D1, D5, D6, D12) are not assumed adjudicated. No second inventory or schema-design workstream was created.
- **No registry record or selection was activated.** No authority, execution or cognitive behavior changed.
- **No qualification claim** is made. Nothing here is independently qualified. Evidence labels used in the documents: [EXISTING], [DEV-TESTED], [QUALIFIED], [PROPOSAL], [APPROVED], [PRODUCTION]; none is [QUALIFIED], [APPROVED] or [PRODUCTION].
- The F1 authority-to-effect guarantee is **UNQUALIFIED** (the local policy check occurs before the atomic claim transaction), and a registry selection is not an OCS execution grant.
- The frozen S04 consumer is an optional overlay: a refused overlay returns the caller policy unchanged, which is not mandatory fail-closed denial. Any mandatory behavior needs an approved successor contract and an independently qualified consumer.
- `COG-REG-SHARED-ADD-01` was supplied to the Architect, but its text and verified digest are not established in this repository and it was not inspected; no clause is inferred and no digest is asserted (`11-addendum-source-custody.md`). The Constitution (`1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`) is cited as pinned guidance; formal adoption is not claimed. The ISS Core PR #12 review (head `547b9052805b7e57ee44ae15f064725b97823405`) is reference only; ISS Core is not modified.

## Documents

| File | Content |
|---|---|
| `01-lifecycle-contract.md` | Record, selection and activation state machines; prohibited transitions; ownership of seven objects |
| `02-authentication-and-custody.md` | Trust model, authenticated selection, custody, refusal codes, prohibitions |
| `03-consumer-integration-contract.md` | Where selection, validation, evaluation, activation and revalidation live in OCS today; candidate interfaces |
| `04-effective-policy-consistency.md` | Candidate consistency tuple, binding without a competing check, changed-condition table |
| `05-minimum-operational-profile.md` | Candidate MSOP options and comparison |
| `06-qualification-contract.md` | Verification matrix, developer-versus-independent boundary, qualifier preconditions |
| `07-gcr-compatibility-boundary.md` | Shared candidates, negative isolation matrix, GCR-owner questions |
| `08-decisions-and-dependencies.md` | Reconciliation record, consolidated decision register, phase mapping, task independence |
| `09-implementation-readiness.md` | Readiness assessment and recommended first increment |
| `10-source-revision-reconciliation-and-review-closure.md` | Historical-baseline versus current-candidate source reconciliation; plan-text reconciliation; closure of the three Copilot findings |
| `11-addendum-source-custody.md` | Custody reference record for COG-REG-SHARED-ADD-01 (no text, no digest) |

Documents 01-07 were each drafted by a separate analysis lane from a shared brief and then reconciled; document 08 section 2 records the contradictions found. Decision IDs are prefixed by document (A-, B-, C-, LD-, E-, F-, G-); `LD-` avoids confusion with PR #17 `D1-D13`.

## Scope guard

The change touches only `docs/r08-preparation/`. `registry_contract/`, `registry_consumer/`, `registry_records/`, `baseline/`, `tests/`, the adopted static plans, the OCS Control Plane, the OCS Execution Runtime and ISS Core are unmodified. Release, publication and production remain HOLD.
