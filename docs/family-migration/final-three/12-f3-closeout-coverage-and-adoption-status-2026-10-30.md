# F3 closeout: coverage-limit dispositions and constitutional adoption status (12)

Work package OCS-F3-CLOSEOUT-20261030. Documentation only. Basis: the successor readjudication's bytes were NOT available to the Lead Builder, so the eight coverage items are taken as reported by the Architect directive. Nothing was executed for this document. Developer evidence below is developer evidence and is never independent evidence. No UNVERIFIED outcome is converted to PASS. Classes: A = required for the current F3-A acceptance boundary; B = suitable for deferred qualification; C = outside F3-A scope.

## 1. Coverage-limit dispositions
| # | Item | Class | Basis | Disposition |
|---|---|---|---|---|
| 1 | A25(a): authority-domain member not isolated end-to-end | **A** | Oracle `03` expectation 1 and 8 name scope members; `authority_domain` is the fifth scope leaf (`effective_configuration_binding.py:43`). Developer tests cover the persisted side and `tenant_id` replay; no builder test changes the live authority domain alone. | Stays inside the acceptance boundary. Outcome UNVERIFIED. Needs one independent isolation (decision under domain X, live side rebuilt under domain Y, all else equal, run execute and pin-export). If not isolable, status is "not independently demonstrated for this member". |
| 2 | A25(e): host and effective profile digest members not isolated end-to-end | **A** | Named in `03` expectation 1. Developer tests `test_c06` (host only) and `test_c07` (effective only) isolate each; they are developer evidence. Known limit: a host change fully masked by a stricter Registry value is not refused (documented limit, not a defect). | Stays inside the acceptance boundary. Outcome UNVERIFIED. Two independent fixtures needed; state the masked-host limit alongside. |
| 3 | Mutant D06-M06 survived the original run; killed by a targeted content check | **C** (becomes B only if it maps to a required oracle member) | Mutation results are developer evidence and not an F3-A expectation. The label `D06-M06` was not found in the repositories, so its mapping is UNVERIFIED. | Record both outcomes side by side (survived originally; killed by content check). No new mutation campaign. The original survival is preserved, not rescored (CA06). |
| 4 | Pin-export supports the F4 family declaration only | **C** for members unreachable by pin-export; F4-reachable members remain in A (items 1, 2) | Developer test helper documents that profile-bearing families are refused by pin-export. Pin-export is read-only and non-authorizing. | Declare as a scope limit in the verdict. Not a PASS of pin-export for all 22 members. |
| 5 | Python 3.12 not exercised independently (3.11 only) | **B** | No oracle expectation mentions an interpreter version. Repository CI runs a 3.11/3.12 matrix (developer evidence). | Defer. Record "independently qualified on 3.11 only". |
| 6 | Cross-process real-clock behaviour not qualified | **C** | Oracle requires a separate process, not a real clock. The digest excludes time (`02`, D-06.3). Time-dependent enforcement belongs to F3-B, which is not reopened. | No action; outside the F3-A oracle. |
| 7 | `provision_local_execution_claim` not exercised | **B** | Claim issuance enters via the successor interpretation scope C. The `provision_*` entry point adds a callable check and sink call over the shared materialize path. | Defer. Not reported as covered unless the shared path is shown exercised. |
| 8 | DEF-OBS-TOL-OVERFLOW-1 remains open | **C** | `04`: recorded, not fixed, not in authorized scope; the binding bounds the tolerance but does not fix the defect. | OPEN, SEPARATE. No F3-A action. Do not state the binding fixes it. |

Risk statement: only items 1 and 2 map to an explicit oracle requirement with an identified material risk (a member that is not independently shown to cause refusal could be silently dropped by a regression). This closeout adds no tests, no runs and no widened scope.

## 2. ResolutionCheck observation
See `11`, section 8. Disposition: documentation clarification only (the entries are pre-existing, non-authorizing and unchanged). No code repair. A separate Control Plane documentation PR is suggested for `docs/effective-configuration-binding.md:113` and `docs/authorization-pin-export.md:5`; not done here.

## 3. Constitutional adoption status
Reference: `09-constitutional-adoption-crosswalk-2026-10-30.md` (merged Registry PR #82; clause-compare output in `09a`).
* Constitution articles CA01-CA23: byte-identical across the OCS technical baseline `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, the later revision `230c0af` and the prompt-engineering convention `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c`. No clause conflict was found.
* Differences found: the meaning of the Tier 1/Tier 3 labels changed between revisions; process texts differ; the testing policy T0-T4 applies prospectively.
* Not established: a formal instrument in the form required by `ADOPTION.md` (exact revision, scope, effective point, reserved powers, exceptions) for the newer revisions. None was invented here. This remains a visible governance completion item for the Architect.
* Effect: the baseline `1c2e920` is preserved and nothing in this closeout silently modifies constitutional adoption.
