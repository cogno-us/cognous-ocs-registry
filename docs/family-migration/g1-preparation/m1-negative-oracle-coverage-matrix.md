# M1 negative-oracle coverage matrix (deliverable 2)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Coverage is for `allowed_institutions` and `allowed_authority_domains` specifically. FULL means an executable test or vector isolates the two sets for that topic; PARTIAL means the topic is exercised only through `allowed_units`, through all five sets together, or through fixtures that cannot distinguish the two sets. **No topic is FULL.** Evidence is read from source at the exact pins; no test was executed (collection only), so "tested" means "a test exists and asserts it", not "the test passes".

## 1. Coverage by topic

| # | Topic | Registry coverage (E) | Runtime/CP/SQ coverage (F) | Gaps | HIGH | Gap ids |
|---|---|---|---|---|---|---|
| 1 | allowed_institutions / allowed_authority_domains validation and bounds | PARTIAL | PARTIAL | 8 | 0 | E-01, E-02, E-03, E-04, E-05, F-01, F-02, F-03 |
| 2 | intersection-only narrowing | PARTIAL | PARTIAL | 7 | 2 | E-06, E-07, E-08, E-09, F-04, F-05, F-06 |
| 3 | deny-all representation | PARTIAL | PARTIAL | 3 | 2 | E-10, E-11, F-07 |
| 4 | identity and provenance binding (who may supply/select the record; scope.institution / scope.authority_domain vs payload sets) | PARTIAL | PARTIAL | 8 | 2 | E-12, E-13, E-14, E-15, F-08, F-09, F-10, F-11 |
| 5 | substitution attacks (swap record, swap family, cross-scope, cross-tenant, cross-version, replay of an older record) | PARTIAL | PARTIAL | 6 | 0 | E-16, E-17, E-18, F-12, F-13, F-14 |
| 6 | selection and activation boundaries | PARTIAL | PARTIAL | 4 | 0 | E-19, E-20, F-15, F-16 |
| 7 | effect-time enforcement (what the Registry requires of the Runtime; Registry code stops at composition) | NONE | PARTIAL | 6 | 1 | E-21, E-22, E-23, F-17, F-18, F-19 |
| 8 | revocation and stale-state behavior | NOT_APPLICABLE | PARTIAL | 4 | 0 | E-24, E-25, F-20, F-21 |
| 9 | recovery and restart behavior (what the Registry requires of the Runtime; kit models state generically) | NONE | PARTIAL | 3 | 1 | E-26, F-22, F-23 |
| 10 | refusal reason compatibility (typed codes, REFUSE vs HOLD, retry classes) | PARTIAL | PARTIAL | 5 | 0 | E-27, E-28, E-29, F-24, F-25 |
| 11 | caller-side normalisation and baseline LocalExecutionPolicy equivalence | PARTIAL | PARTIAL | 6 | 2 | E-30, E-31, E-32, F-26, F-27, F-28 |
| 12 | pin / authorization-pin interaction (F-A1) with the five-set containment | NONE | PARTIAL | 5 | 1 | E-33, E-34, E-35, F-29, F-30 |

Registry side: PARTIAL for topics 1, 2, 3, 4, 5, 6, 10, 11; NONE for 7, 9, 12; NOT_APPLICABLE for 8. Runtime/Control Plane side: PARTIAL for all twelve.

## 2. Totals

65 gaps: HIGH 11, MEDIUM 37, LOW 17 (35 from the Registry mapping, 30 from the Runtime/Control Plane mapping; some describe the same missing oracle from two sides, which the work packages in section 4 merge). Every gap is assigned to exactly one oracle work package and to one candidate oracle in [m1-oracle-register.json](m1-oracle-register.json).

## 3. HIGH gaps

| Gap | Work package | Topic | Description (truncated) |
|---|---|---|---|
| M1-E-06 | OW-1 | intersection-only narrowing | Decision-level (verify_and_decide_v2) narrowing is exercised only for allowed_units (V1A-02); for the two sets the only decision-level case has identical single-element caller and registry sets. |
| M1-E-10 | OW-1 | deny-all representation | G0 worker A claim REFUTED at composer level and VERIFIED at decision/vector level: composer deny-all covers all five keys (32 combinations), but decision-level deny-all (V1A-03) and the single-dimension vectors (EP-011/012) are allowed_units only. There is no  |
| M1-E-12 | OW-3 | identity and provenance binding (who may supply/ | (c) No vector or test crosses scope.institution / scope.authority_domain with the payload sets. Neither contract text nor code states the intended relation (e.g. a statement scoped to inst-a pinning a record whose allowed_institutions is ['inst-b'], or whose a |
| M1-E-21 | OW-4 | effect-time enforcement (what the Registry requi | No executable Registry-side oracle for effect-time containment of the two sets. Amendment 3 is prose with text-pin tests; the five-set containment vectors (executor sets x record payload sets -> accept / REFUSE policy_identity_mismatch / HOLD store_unknown, in |
| M1-E-26 | OW-7 | recovery and restart behavior (what the Registry | Amendment 3 item 2 requires the Runtime to treat a stored record payload that is missing a set, non-canonical, or not well-formed under the Registry value rules as HOLD store_unknown. The kit stores the record pin (id/version/digest) only, never the payload; n |
| M1-E-30 | OW-5 | caller-side normalisation and baseline LocalExec | No differential/equivalence oracle between compose_f1ab effective sets and LocalExecutionPolicy.check for the two sets. The S05 harness is the template (independent oracle, frozen expectations) but is three-set only; nothing builds a LocalExecutionPolicy from  |
| M1-E-34 | OW-9 | pin / authorization-pin interaction (F-A1) with  | Interaction order: pin step 5 (scope.* vs pin) precedes step 6 (scope key from pin) and step 7 (five-set containment); the pin has no member for the five sets. No contract text or vector says that a record activated for the authorized institution may carry all |
| M1-F-06 | OW-4 | Intersection-only narrowing (adapter-level narro | Nothing in the engine builds the executor policy from caller policy and the activated record on the durable path: evaluate_with_registry_selection (the only code that computes caller INTERSECT record) is imported by no engine module (grep). The effect-time gua |
| M1-F-07 | OW-4 | Deny-all representation (empty set) for the two  | Durable and effect-time deny-all is untested for the two sets. No test activates a record whose allowed_institutions or allowed_authority_domains is [] and shows the claim is refused (policy_not_subset:<field>, zero effects), and no test runs an executor whose |
| M1-F-08 | OW-3 | Identity and provenance binding (who supplies/se | No Runtime test (and no SQ slice read) puts two governed scopes with different institution or authority_domain in one store and shows isolation: every Runtime/SQ governed fixture uses scope inst-a/domain-a/tenant-a and varies only `operation` (GS_OTHER, B-05,  |
| M1-F-26 | OW-5 | Caller-side normalisation and baseline LocalExec | No full-grid differential at the DURABLE effect boundary: governed claim with a NON-narrowing f1ab record versus the same operations on the ungoverned LocalExecutionPolicy path, across an institution x authority_domain grid (allow and every refusal reason). Th |

## 4. Oracle work packages

| Package | Scope | Gaps | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|
| OW-1 | Registry decision-level and composer oracles for the two sets | 11 | 2 | 8 | 1 |
| OW-2 | Token rule, validators and exact-match normalisation for the two sets | 9 | 0 | 7 | 2 |
| OW-3 | Scope-versus-payload relation and identity binding | 13 | 2 | 7 | 4 |
| OW-4 | Durable effect-time containment, deny-all and multi-member cases | 10 | 3 | 4 | 3 |
| OW-5 | Differential oracles against baseline LocalExecutionPolicy | 5 | 2 | 2 | 1 |
| OW-6 | Substitution, activation and supersession | 4 | 0 | 4 | 0 |
| OW-7 | Revocation, stale state, recovery and restart | 5 | 1 | 2 | 2 |
| OW-8 | Refusal reason compatibility (REFUSE vs HOLD, per-set attribution) | 4 | 0 | 1 | 3 |
| OW-9 | Authorization-pin interaction with five-set containment | 4 | 1 | 2 | 1 |

The four focus questions answered by the mapping:

- **Registry narrowing/deny-all for the two sets.** The G0 claim is correct at the decision level (`V1A-02`, `V1A-03` use `allowed_units` only) and refuted at the composer level (`test_r08v2_f1ab_family.py` covers all five keys).
- **Vectors.** No golden vector carries an f1ab record narrowing institutions or domains. Only EP-004 (all five sets empty), EP-007 and EP-008 (institutions and domains narrowed) in the ext-s1-5 data do, and their composition is checked with a test-local `compose()` and Node, never with `compose_f1ab`.
- **Scope crossing payload sets.** No test, vector or code does.
- **Runtime effect time.** Runtime F-01 tests 6 and 7 (and Stack Qualification A15/A16) isolate institutions and domains individually with REFUSE `policy_identity_mismatch`, cause `policy_not_subset:<field>`. Positive controls vary all five sets together. Under the pin (F-A1), containment is isolated only for `allowed_actions` and `allowed_units`; the pin has 17 members and no policy sets, so it cannot detect widening.

## 5. Limits of this matrix

Worker evidence only. Several results are INFERRED and labelled so in the topic JSON (for example the stride-7 sample of the baseline equivalence grid: 93 of 648 cells, 2 ALLOW, derived by enumeration and not run). Eight Runtime/Stack Qualification test files could not be collected in the workers' environment (PyNaCl or component directories absent) and are recorded NOT RUN. Not read: Registry `v2_token_table.py` body and `v2_age_bounds.py`, `tests/s05_oracle.py` and `tests/s05_expectations.json` (grep only), `docs/f-a1-authorization-pin/*`, the ADR EXT-S4-0, most of Stack Qualification (about 28,961 files), `registry_selection_authority.py` lines 172-700 and 960-1116 (signatures only), Control Plane `policy_binding.py` and `runtime_authority.py`.
