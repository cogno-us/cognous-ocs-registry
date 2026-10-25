# R08-PREP 11: Source-custody reference record for COG-REG-SHARED-ADD-01

Purpose: record what is and is not established in this repository about the shared addendum `COG-REG-SHARED-ADD-01`, so that no document treats a reconstructed summary as the source. This is a custody reference record, not a copy, summary or interpretation of the addendum.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.

## 1. Status

| Field | Value |
|---|---|
| Document identifier | `COG-REG-SHARED-ADD-01` |
| Stated date | 2026-10-24 (as given in the Architect's PR #18 disposition) |
| Stated description | 7-page proposed-contract addendum; "architectural direction approved in principle, implementation not authorized" (crosswalk header) |
| Supplied to | The OCS Architect (Architect disposition of PR #18, section 11; merged PR #17 file 08, ruling D10) |
| Text in this repository | **NOT ESTABLISHED.** No file in this repository contains the addendum text |
| Verified digest | **NOT ESTABLISHED.** No digest is recorded here; none is inferred or fabricated |
| Authoritative source location | **NOT ESTABLISHED** (to be named by the operator) |
| Custody verification | **NOT PERFORMED** |
| Inspected by this preparation | **No** |

## 2. Where the identifier is referenced at `main` e3f5bbc32f957a10822a15a1b642e48c63d428e9

`docs/plans/PROJECT_PLAN-v1.2.md`, `docs/plans/PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md`, `docs/s06-consolidation-report.md`, `docs/decisions/2026-10-24-s06-authorization.md`, `docs/decisions/2026-10-24-post-s06-architectural-direction.md`, `docs/sprint-status.md`, `docs/registry-schema-analysis/README.md`, `05-common-envelope-proposal.md`, `08-open-architectural-decisions.md`. Each reference is a citation of the identifier or of a section number; none carries the text.

## 3. What may and may not be relied on

- Section numbers cited by the crosswalk (for example A2 "addendum sections 1, 3, 5, 7-8"; A4 "4, 10"; A7 "6"; A8 "12-13") are the crosswalk's claims. They were not verified against the addendum.
- The characterizations in plan v1.2 and the crosswalk are the adopted plan's own statements and are cited as such. They are not clauses of the addendum.
- GCR/OCS shared-envelope conclusions in documents 01-09 that depend on the addendum (notably 07 and the envelope field names in 01, 02 and 04) remain **provisional**. If the addendum text differs from any of them, the addendum governs once its text and digest are established, and the document in question is wrong in that respect.
- No normative reliance on the addendum is permitted until durable repository custody and an exact verified digest exist (merged PR #17 file 08, D10 ruling).

## 4. Proposed custody procedure (candidate; requires the operator's action)

1. Operator supplies the original addendum bytes from its authoritative source, and states that source.
2. The registry documentation custodian computes a SHA-256 over the exact supplied bytes and records the algorithm, digest, byte length, acquisition date and acquirer.
3. The bytes are stored under a stable path in this repository (or an operator-named custody location with a pointer here), unmodified; any rendering, extraction or summary is a separate, labelled derivative with its own identity.
4. The OCS and GCR Architects interpret the clauses; interpretation notes are separate documents and never replace the source.
5. Documents 01-09 are rechecked against the established text; each divergence is recorded, not silently edited.

## 5. Decisions

| ID | Decision | Owner | Blocking consequence |
|---|---|---|---|
| G-09 | Supply the authoritative addendum content and name its source | Operator | Shared-envelope conclusions stay provisional; R08 envelope work and R14 crosswalk cannot rely on it |
| G-09a | Verify and record digest and byte length; store the source | Registry documentation custodian | No normative reliance possible |
| G-09b | Interpret clauses against documents 01-09 and the shared candidates S1-S9 | OCS Architect and GCR Architect | Cross-domain contract interpretation stays unverified |

Phase: R08 (envelope) and R14 (crosswalk). Cross-reference: merged PR #17 file 08, D10.
