# G1 authorization recommendation (deliverable 8)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

This is a builder recommendation for the Architect's separate authorization decision. It authorizes nothing.

## 1. Recommendation

**Do not authorize contract development or any wave implementation yet. Consider authorizing a bounded "G1-M1" scope, oracle closure only, once PD-1 to PD-7 and PD-9 are decided and PR-1 to PR-3 are scheduled.**

Why split: M1's gaps are real (65, 11 HIGH, no topic FULL) but need no new field and no production change; the successor contract is a larger design with its own gates. Mixing them would let contract design drift into the oracle work or the reverse.

## 2. Proposed G1 scopes (each separately authorized)

| Scope | Content | Prerequisites | Recommendation |
|---|---|---|---|
| G1-A: oracle specification ratification | Ratify the independent-oracle specification, register and budget; designate the independent author and reviewer; decide PD-1..PD-7, PD-9 | Architect decisions | Authorize first |
| G1-B: M1 oracle development | Independent author writes vectors and harness for OW-1, OW-2, OW-8 first (Registry-only), then OW-4..OW-7, then OW-3 and OW-9 after rulings; mutation runs; independent review | G1-A; PR-1..PR-3 | Authorize after G1-A |
| G1-C: successor-contract design | SC-0 to SC-2 only: scope ruling, documentation-only draft, oracle-first vectors | PD-8; M1 suites version-parametrised | Do not authorize yet; decide after G1-A |
| Wave implementations (M2, M3, M10..M12) | Registry fields, wiring, qualification | G1-C complete | Not recommended now |

## 3. Order of work inside G1-B

OW-1 and OW-2 (Registry-only, no ruling needed beyond PD-3), OW-8 (after PD-2), OW-4 and OW-5 (durable path; needs PR-2), OW-6 and OW-7, then OW-3 and OW-9 (after PD-1 and PD-4). HIGH gaps first: M1-E-06, E-10, E-21, E-26, E-30, F-06, F-07, F-26, then those depending on rulings (E-12, E-34, F-08).

## 4. Exit criteria for G1-B (proposal)

All 65 gap ids accounted for (closed, merged into another oracle, or explicitly deferred with a reason); HIGH gaps closed with traceable expected outcomes and surviving-mutant report; no production change; builder tests and CI reported as builder evidence only; independent review recorded by the designated reviewer, not by the builder.

## 5. Risks

Environment gaps hide skipped tests (PyNaCl, Node); the pin mismatch (`943ab18`) may invalidate cross-repository assertions; a PD-1 ruling that implies containment would convert part of OW-3 into contract work; Amendment 4 is a draft, so pin-path closure may be impossible to claim; the effect-time path depends on the Registry package being importable (HOLD otherwise).
