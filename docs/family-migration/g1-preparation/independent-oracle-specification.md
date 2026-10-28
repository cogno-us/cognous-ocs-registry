# Proposed independent-oracle specification for M1 (deliverable 3)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

**Status: proposal.** No oracle exists, none is written by this document, and nothing here is independent. The builder (this lead and the AI workers) may specify what must be proven; it may not be the author or reviewer of the oracle that proves it. `m1-oracle-register.json` leaves `authored_by` null and `independent_author_designated` false for every oracle.

## 1. Independence requirements

1. **Designated independent author and reviewer** who did not build or review the Registry f1ab, Runtime containment or Control Plane binding code. Designation is an Architect act (PD-6). The V09 independent V08 Tier 1 qualification is NOT STARTED, and the independent V07 security review is OPEN; M1 oracles do not substitute for either.
2. **Derived from contract text, not from implementation.** Expected outcomes are written from `docs/r08-v2-contract.md`, Amendments 1-4 and the ADR EXT-S4-0 before the oracle author reads the implementation of the path under test. Where the text is silent the oracle is not written until the Architect rules (PD-1, PD-2, PD-3, PD-4); a characterisation oracle may pin current behaviour but is labelled CHARACTERISATION and may not be cited as proof of a contract property.
3. **No shared fixtures with the code under test.** The existing "independent" Stack Qualification F-01 requalification imports Runtime fixtures (same builder family; Worker F contradiction 4) and is therefore not independent evidence. Oracle fixtures are data (JSON vectors) plus a minimal harness that calls only public entry points.
4. **Second-implementation cross-check where the repository already has one.** The ext-s1-5 vectors are cross-checked with Node; the same practice applies to new composition vectors so that expected outcomes are not produced by the Python code they judge.
5. **CI is not independence.** A green run proves the vectors pass against the code; it does not qualify them.
6. **Mutation evidence** (section 4) is part of acceptance for HIGH gaps, run in disposable copies, never in a component checkout.

## 2. Oracle kinds and the vector shape

Kinds: positive, negative, differential, property, mutation, vector (as labelled per gap). A vector is a JSON object `{id, work_package, gap_ids, kind, basis, contract_basis[], inputs, expected{outcome, reason_code?, refusal_class?, evidence_cause?}, notes}`, where `basis` is SPECIFICATION, SPECIFICATION-PENDING-RULING or CHARACTERISATION and `expected` is filled by the independent author. Inputs always cover both sets independently (a case that varies institutions while holding domains fixed, and the reverse), single-member and multi-member lists, equal/narrower/disjoint/superset record-versus-caller relations, and the explicit `[]` case.

## 3. Work packages

| Package | Scope | Gaps (M1-) | Unresolved specification dependency |
|---|---|---|---|
| OW-1 | Registry decision-level and composer oracles for the two sets | E-03, E-05, E-06, E-07, E-08, E-09, E-10, E-11, E-16, E-18, E-27 | none |
| OW-2 | Token rule, validators and exact-match normalisation for the two sets | E-01, E-02, E-04, E-13, E-31, F-01, F-02, F-03, F-27 | PD-3 |
| OW-3 | Scope-versus-payload relation and identity binding | E-12, E-14, E-15, E-17, E-19, E-20, E-33, F-08, F-09, F-10, F-11, F-14, F-16 | PD-1 |
| OW-4 | Durable effect-time containment, deny-all and multi-member cases | E-21, E-22, E-23, F-04, F-05, F-06, F-07, F-17, F-18, F-19 | PD-2 |
| OW-5 | Differential oracles against baseline LocalExecutionPolicy | E-28, E-30, E-32, F-26, F-28 | none |
| OW-6 | Substitution, activation and supersession | F-12, F-13, F-15, F-20 | none |
| OW-7 | Revocation, stale state, recovery and restart | E-24, E-26, F-21, F-22, F-23 | none |
| OW-8 | Refusal reason compatibility (REFUSE vs HOLD, per-set attribution) | E-25, E-29, F-24, F-25 | PD-2 |
| OW-9 | Authorization-pin interaction with five-set containment | E-34, E-35, F-29, F-30 | PD-1, PD-4 |

Oracle-to-gap mapping, kind, basis, severity and dependency for all 65 candidates: [m1-oracle-register.json](m1-oracle-register.json) (one candidate oracle per gap; the independent author may merge candidates inside a work package but must account for every gap id).

Acceptance for a HIGH gap: (a) the oracle exists as data plus harness; (b) it passes on the pinned code; (c) at least the listed mutants fail it; (d) its expected outcome is traceable to a contract reference or an Architect ruling; (e) an independent reviewer, not the author, signs the traceability. CHARACTERISATION oracles are exempt from (d) and are reported separately.

## 4. Mutation targets (minimum)

Replace intersection with union or caller-only in `compose_f1ab` for each of the five keys; truncate the per-key loop to three keys; skip the institution check, or the domain check, in `check_effect` containment; replace subset with superset or equality; drop the `[]` deny-all branch for one key; swallow `policy_not_subset:<field>`; resolve a pin scope from the claim instead of the pin; use the stale epoch after supersession; return the caller policy on optional-participation failure without the registry narrowing. Mutants run in copies; surviving mutants are findings.

## 5. What the oracles may not do

Change production code, schemas, vectors in the frozen golden set, or reason codes; introduce widening; read secrets or call external services; claim independence on behalf of their author.
