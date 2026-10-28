# Open decisions and prerequisites (deliverable 7)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## 1. Decisions needed before any G1 authorization

| Id | Decision | Blocks | Owner / form |
|---|---|---|---|
| PD-1 | Relation between the scope (scope.institution, scope.authority_domain) and the payload sets allowed_institutions / allowed_authority_domains: independent or containment? The contract is silent; no code relates them. | OW-3, OW-9 (E-12, E-33, E-34, F-08, F-09, F-14, F-30) | Architect ruling; if the ruling changes semantics it is an amendment, which is contract work and not M1 |
| PD-2 | REFUSE versus HOLD for institution/authority-domain outcomes, and whether Amendment 3's use of `policy_identity_mismatch` for executor-vs-record containment is ratified; status of the unratified `ld02-outcome-map.json`. | OW-4, OW-8 (E-22, E-23, E-25, E-29) | Architect ruling |
| PD-3 | Token rule: contract text says 'no control, separator or `*`'; code and N-13 also refuse Cf, Cs, Co and unassigned code points. Which governs? | OW-2 (E-01, E-04) | Architect ruling or documentation erratum |
| PD-4 | Amendment 4 (authorization pin) is a DRAFT; Amendment 3 states it is not evidence that F-01 is closed. May M1 claim closure over the pin path? | OW-9 (E-35, F-29) | Architect ruling |
| PD-5 | Which Registry pin do Runtime and Control Plane tests use for cross-repository assertions: `943ab18` (current) or `317eb76a`? | OW-4..OW-9 | Architect decision after the diff is inspected (PR-1) |
| PD-6 | Designate the independent oracle author and reviewer; confirm they are distinct from the V07 security reviewer and the V08 Tier 1 assessor roles or state the overlap. | all packages | Architect designation |
| PD-7 | Oracle placement: Registry tests, separate oracle directory, or Stack Qualification. | all packages | Architect decision (recommendation: separate directory) |
| PD-8 | Successor contract approach A / B / C and which waves share a version. | later waves | Architect decision at G1 (not M1) |
| PD-9 | G0 AD-06 (equality versus subset for institutions and authority domains) remains OPEN and bears on OW-1 and OW-4 expectations. | OW-1, OW-4 | Architect decision |
| PD-10 | Accept the G0 erratum (g0-erratum.md) as additive documentation. | — | Architect acceptance |

## 2. Prerequisites (builder work that needs authorization or an environment)

| Id | Prerequisite | State |
|---|---|---|
| PR-1 | Inspect the Registry diff `943ab18..317eb76` and run the pin assertions at the chosen pin. | Not done (not read) |
| PR-2 | Prepared execution environment (PyNaCl, pydantic, Node, component directory variables) and a recorded baseline run of the Runtime, Control Plane and Stack Qualification suites at their pins. | Not done; baseline NOT RUN |
| PR-3 | Close the eight files the workers could not collect (recorded NOT RUN in the inventories). | Not done |
| PR-4 | Resolve the Stack Qualification claim that the other three sets are covered by the Runtime F-01 suite on the pin path (Worker F contradiction 3); that suite builds destinations without the pin. | Open finding |
| PR-5 | Confirm the proposed budget (test-budget-and-execution-boundaries.md). | Proposal |

## 3. Related G0 decisions still OPEN

AD-04 (single-source test tying `FAMILIES_V2` to `IDENTITY_FAMILIES`), AD-05 (ratify `MAX_SNAPSHOT_NODES`), AD-06 and AD-07 through AD-24 are unchanged and remain open (history in `g0-freeze-record.md`). AD-06, AD-07, AD-11 and AD-16/AD-17 bear on M1 or on the successor strategy as noted above; no worker disposition is ratified.

## 4. Not decided, not started

G1 implementation; any successor contract text; any change to the Registry schemas, Runtime or Control Plane; independent qualification; the V09 reviews; Ed25519 #26/#34; release, publication and production.
