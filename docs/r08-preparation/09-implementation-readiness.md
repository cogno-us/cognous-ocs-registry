# R08-PREP 09: Implementation readiness assessment

Purpose: state, per area, whether the architecture prepared in documents 01-08 is ready for implementation, what must be true first, and what the first increment could be once R07/R08 are approved. This is an assessment, not an authorization.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification. No R08 or R09 implementation is authorized by this document.

## 1. Sources and revisions examined

Registry `main` `e3f5bbc32f957a10822a15a1b642e48c63d428e9` (documents first drafted against `eb850c8d303961d099a123534121aeac280b242b`); plan v1.2 blob `32319775...`; crosswalk blob `a53a5b31...`; documents 01-08 of this directory; PR #13 (merge `e20504df...`) and PR #17 (merge `e3f5bbc3...`) as MERGED SOURCE EVIDENCE, WITH PROVISIONAL CLASSIFICATIONS; the Architect disposition of PR #18 (08 section 3a); Constitution `1c2e920f...`. Control Plane/Runtime historical and current revisions are kept separate (10). COG-REG-SHARED-ADD-01: text and digest not established in this repository (11); not inspected. No tests were run for the amendment revision.

## 2. Readiness verdict

**Precise verdict: NOT READY FOR IMPLEMENTATION; READY FOR ARCHITECTURAL REVIEW.** No R08 or R09 implementation, family migration, activation, pin approval or production integration is authorized. The F1 authority-to-effect guarantee is UNQUALIFIED. The first increment below is a candidate that may begin only after the operator separately authorizes it and the R08 contract decisions are complete. The architecture is specified well enough to take to operator and OCS Architect rulings (08 section 9); it is not specified well enough, and does not have the authority, to build. Reasons, each traceable to a document:

| Area | State | Why not ready |
|---|---|---|
| Successor contract and lifecycles (01) | Candidate state machines and ownership table | A-01, A-02 and E-03 ruled architecturally, implementation contract and E-09 still open; plan R08 gate (operator approves contract version and scope) not passed |
| Authentication and custody (02) | Candidate trust model; existing primitives identified; no new infrastructure demonstrated | B-01 and B-04 ruled in direction; B-02 not adopted; fitness assessment of ODES/BitRep/Control Plane facilities not done; no trust root, no enrolled issuer, no approved pin (T8) |
| Consumer integration (03) | Existing boundaries located with file:line; candidate interfaces I1-I4 | No call site for the consumer exists; production host owner deferred to the operator (C-01); emulator profile needs a named synthetic adapter; Runtime/Control Plane not authorized to change |
| Effective-policy consistency (04) | Candidate tuple and race table; selection is not a grant (Architect) | Needs an integration design for F1 (check occurs before the atomic transaction: UNQUALIFIED); LD-01, LD-05, LD-09; Runtime/Control Plane owners |
| Minimum operational profile (05) | Three options compared; Option 1 path recommended as a proposal | Option 1 (F1a) recommended by the Architect; operator has not adopted an MSOP (E-01); mandatory profile permitted as a design capability, activation unauthorized (D7) |
| Qualification (06) | 22-row matrix and qualifier preconditions | Independent qualification lead required but not designated (F-01/D13); ten matrix rows have no existing coverage |
| GCR boundary (07) | Shared candidates, matrix N-01..N-17, GCR-owner questions | GCR-owner rulings absent; addendum text and digest not established in the repository (G-09; 11) |

## 3. Preconditions by phase

| Phase | Must be true before implementation starts |
|---|---|
| R07 | Merged inventory classifications adjudicated by their owners (D1, D5, D6, D12 open); addendum custody (D10); operator adopts a migration profile |
| R08 | Operator approves successor contract version and scope; GCR Architect preliminary disposition; lifecycle, status and deny-all rulings (A-01, A-02, E-03, E-09); MSOP candidate adopted (E-01) |
| R09 | B-01..B-04, B-12 ruled; trust root and issuer enrollment procedure exist; independent security reviewer named; lifecycle approver roster (A-04) |
| R10 | C-01, C-03, LD-01, LD-02, LD-06 ruled; Runtime/Control Plane owners approve any hook or profile change; mandatory behavior only with an approved successor contract and independently qualified consumer; production path inactive |
| R11 | Per-family operator authorization, oracle, qualifier (F-01, F-04); classifications for any non-F1a/F1b family |
| R17 | Qualifier designated; candidate sources frozen; expectations frozen before execution |

## 4. Recommended first implementation increment (proposal, after R07/R08 approval)

[PROPOSAL] Smallest increment that proves a piece of the path without touching OCS components or activating anything: **an Architect-accepted candidate only: a registry-repository-only successor-contract validator and selection-statement verifier for the F1a three-field family, as pure functions of operator-held inputs, with deny-all and unknown-composition refusal, and no Runtime or Control Plane wiring, no activation and no pin approval.** Its oracle and expected results would be authored by the designated independent qualifier before the candidate runs (F-01), reusing the S05 machinery only where the qualifier re-approves expectations (F-04). It would exercise QM-01, QM-02 (partially), QM-05, QM-08, QM-11, QM-13 and QM-14 of 06 and leave QM-04, QM-06, QM-07, QM-09, QM-12, QM-15..QM-22 to later increments. It depends on B-01 and B-10 for the verification primitive and dependency footprint. It must not begin until the operator separately authorizes it and the R08 contract decisions are complete, and a validator-only increment must not be described as a fully operational registry. No increment is authorized by this PR.

## 5. Acceptance-criteria self-check (what this PR does and does not establish)

| Criterion | Where addressed | Honest limit |
|---|---|---|
| Source-pinned and internally consistent | Sources tables in every document; 08 section 2 | Lane source claims were not independently re-derived by the integration owner; field names not yet harmonized (R-11) |
| Explicit lifecycle ownership | 01 (seven-object ownership table) | Candidate; A-01 unruled |
| Coherent trust model | 02 | No trust root or key custody exists; the model is not demonstrated |
| OCS integration points | 03, 04 | No call site for the consumer exists today |
| Exact revalidation boundaries and failure behavior | 04 sections 2, 4, 5 | Boundaries are the existing atomic SQLite profile; selection binding needs successor profile work |
| Credible minimum profile | 05 | Operator has not adopted it |
| Negative and changed-condition qualification | 06 | Designed, not executed; no qualifier |
| GCR compatibility without authority transfer | 07 | Secondary evidence for GCR side; addendum not inspected |
| No silently settled unresolved classification | 08 sections 4, 5 | Dependence of F1a/F1b on open rows is not adjudicated |
| Every remaining decision has a named owner and blocking consequence | 08 section 4 and the per-document tables | Owners are proposals of the lanes pending ruling |
| No implementation or activation | Whole PR | Documentation only |

## 6. Risks and unresolved implementation constraints

- The registry consumer has no caller; the host integrator is unnamed (C-01). Everything in 03 and 04 is design on top of an uncalled library.
- Same-host file or database access can bypass Python modules (Runtime `docs/execution-boundary.md`); a signed selection does not defend a compromised host (02, 04).
- Loaded-code integrity (T5) is unaddressed unless B-09 is approved.
- Effect-time identity binding records what was checked; only the lock-held recheck over rows the destination reads establishes authority, and only within one SQLite database (04).
- Pin-versus-head divergence in Runtime/Control Plane behavior (08 R-09, LD-06, 10); no integration baseline selected.
- The ISS review was written against a pre-merge v1.2 text; merged v1.2 controls (08 R-08).
- Independence is a property of named actors; the existing qualification repository concedes it cannot establish independence from inside the repository (06).
- No evidence in this PR is [QUALIFIED], [APPROVED] or [PRODUCTION].

## 7. Confirmation

This PR changes documentation under `docs/r08-preparation/` only. It changes no code, authority, test, runtime behavior, registry record, selection, pin, baseline artifact or production behavior, and activates nothing.
