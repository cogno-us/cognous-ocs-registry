# R08-PREP Lane F: Qualification contract and bounded verification matrix

Purpose: a source-based matrix of the adverse conditions a future operational registry must be qualified against, mapped to what existing S03/S04/S05 tests already touch, with an explicit boundary between developer regression testing and independent qualification, and a statement of what a qualifier needs before Tier 1 families can be activated. It reuses the existing OCS qualification infrastructure and ISSBench V2. It proposes no competing test system.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.

## 1. Sources and revisions examined

| Source | Revision | Used for |
|---|---|---|
| Registry repo `main` | `eb850c8d303961d099a123534121aeac280b242b` (rev-parse confirmed) | S03 contract and tests, S04 consumer and tests, S05 spec, report, `tests/s05_expectations.json`, `docs/trust-limitations.md` |
| Plan v1.2, crosswalk | blobs `32319775…`, `a53a5b31…` | R09, R10, R17, section 3.3/3.4, gates G2–G6, A10 |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (rev-parse confirmed, text read) | EP7, CA04, CA05, CA16, CA18, CA23, "How the articles work together" section 4, risk tiers, evidence discipline |
| `cognous-stack-qualification` | `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` | README, `docs/execution-contract.md`, `docs/refusal-test-template.md`, `docs/release-gate/pre-registration.md`, `docs/adversarial-test-plan.md`, suite layout |
| ISS review qualification plan | PR #12 head `547b9052…`, `gcr-registry-qualification-plan.md` | Q01–Q15 GCR scenarios, ISSBench V2 ownership |
| PR #17 `registry-schema-analysis/` | head `bdfb2b72…` | `07-schema-qualification-plan.md` (successor validation scenarios), `08` D1–D13, V1–V9 |
| Control Plane clone | `7a4bcd40…` (head; S01/S02 pin was `0a41faa9…`, not diffed) | `docs/runtime-authority-profile.md`, `EffectTimeRefusal` in `bounded.py` |

Not inspected: COG-REG-SHARED-ADD-01 (unavailable; cited only through plan v1.2 and the crosswalk); the effect-boundary definitions of REFUSE/HOLD/DENY/RETRY were taken from document 04 after integration (this lane first drafted working definitions, since replaced); ISSBench V2 repository itself (only the ISS review's description of it); Runtime head `c5e97e87…` effect path; the Control Plane diff between the g8-r10 pin and head; GitHub Actions evidence of any run.

## 2. Findings from source

1. **[EXISTING]** The registry's recorded S05 oracle is builder-authored. `tests/s05_oracle.py` (blob `503851c4…`) and `tests/s05_expectations.json` (blob `37a68275…`) were committed before the harness; the oracle imports nothing under test (test `Z3`, pinned by `Z1`/`Z2`). `docs/s05-equivalence-report.md` states the builder wrote both oracle and harness and that Copilot review is "code review, not independent qualification". `docs/trust-limitations.md` T10 says the same.
2. **[EXISTING]** The operator designated Copilot as standing technical reviewer as an exception, "not formal independent qualification" (`docs/decisions/2026-10-24-s05-authorization.md`, items 4–5). The same file says it is a builder transcription, "not independently countersigned".
3. **[DEV-TESTED]** S03 N/M/X/O cases, S04 N1–N27/P/R1/F/O/B and S05 G1 (1,728 pairs, 46,656 comparisons), G2 (168 pairs), R01–R34, E01–E20, B01–B05, X (11), PIN-1..3, LIM-1..3 all pass as recorded at `eb850c8` (S05 report: 16 harness tests, 347 in suite). All of it is for one three-field allow-list family under a trusted-host threat model (T1), an optional overlay (T7), with no activation, expiry, tenant scope, signing, cache, revocation, concurrency or Runtime wiring (T9, T11).
4. **[EXISTING]** S04 refusal semantics: any refusal returns the caller policy object unchanged with `overlay_applied False`. This is "overlay not applied", not "denied" (`docs/s04-implementation.md` section 1). The matrix therefore cannot count any S04 refusal as evidence of mandatory fail-closed behavior.
5. **[EXISTING]** S04 holds no clock, no tenant field, no cache, no persistence: `registry_consumer/consumer.py` header says "no writes", reads files once; grep of consumer and validator finds no expiry, tenant or institution logic. Rows for expiry, tenant, cache and negative-record custody are therefore uncovered, not weakly covered.
6. **[EXISTING]** The qualification repo is organized as: a scenario catalog (`scenarios/catalog.json`, 40 Cognous cases, all NOT RUN as catalog entries), executable suites under `suites/`, a controller (`tools/v1_validation.py`, dispatch-only workflow) that records per-requirement verdicts under `results/v1-validation/…`, and a pre-registration (`docs/release-gate/pre-registration.md`) that freezes expected outcomes and declared limits before runs. README states: "A green local run of a suite is material for the qualification controller, not a recorded verdict" and "This is not independent certification."
7. **[EXISTING]** The qualification repo's own pre-registration admits independence limits: OD-4 says "independence from the authors cannot be established from inside the repository"; the owner chose one author and one checker. The comparator plans "had no independent review". So even existing OCS infrastructure does not itself prove independence; independence is an attribute of designated actors, not of the repository.
8. **[EXISTING]** Reusable harness: `docs/refusal-test-template.md` and `suites/_refusal_template.py` give five legs for effect-time refusal scenarios: (a) no destination row read through an independent read-only connection, (b) typed refusal row naming expected and observed input versions, (c) positive control at the same enforcement point, (d) mutation of the refusal writer must fail leg (b), (e) provenance label `code-reading` or `run`. Holders without a refusal are `coverage_unknown`, never "expired".
9. **[EXISTING]** Control Plane head `7a4bcd40`: effect-time refusal outcome is `hold`; `deny` "is declared but emitted only by the Microsoft AGT adapter" (`docs/runtime-authority-profile.md` lines ~58, 77, 104–105); refusal rows are typed `EffectTimeRefusal` with `stage` `effect_time_revalidation`, `changed_inputs`, `reopen_conditions`. Existing Control Plane tests revoke a grant mid-flow (`tests/test_runtime_authority.py`). These concern grants, not registry selections; they are adjacent evidence, not registry coverage.
10. **[EXISTING]** The ISS review marks Q03/Q05/Q06/Q11/Q12/Q13/Q15 "NOT EXECUTED until a corresponding actual consumer exists" and says ISSBench V2 owns independent GCR qualification, developer CI is not independent qualification, and expected results are frozen before candidate execution (`gcr-registry-qualification-plan.md`).
11. **[EXISTING]** PR #17 `07-schema-qualification-plan.md` already designs successor scenarios V/S/C/H/O/N and states "Designed, not executed". This lane does not repeat them; the matrix cross-references them as `PR17-07 <id>`.

## 3. Developer regression testing versus independent qualification

| Aspect | DEVELOPER REGRESSION TESTING (exists) | INDEPENDENT QUALIFICATION (not performed; none [QUALIFIED]) |
|---|---|---|
| Purpose | Keep the builder's own contract from regressing | Establish, for exact sources and profile, that the candidate meets expectations the builder did not shape (CA04, Constitution "How the articles work together" section 4) |
| Who writes the oracle | Builder (S03/S04 battery committed before code; S05 oracle and expectations frozen before harness) | A qualifier not the candidate author, who freezes expected results before execution; builder-supplied expectations are "proposals, not independent certification" (Constitution evidence discipline) |
| Who runs it | Builder session, CI | Qualifier or a controller run under qualifier-owned configuration; for OCS candidates the existing controller (`tools/v1_validation.py`) and suites; for GCR candidates ISSBench V2 |
| Who reviews | Copilot (operator exception): code review only | Designated independent qualification owner (plan G4/G6) plus, for authority-bearing paths, independent security review (R09 gate) |
| What S05 PROVES | For representable values of three fields, registry-backed policy equals historical policy and never widens, against a frozen oracle that matches the historical class (A–G findings) | Nothing it proves is independent |
| What S05 does NOT prove | Independent authorship of the oracle; other fields or families; authentication; activation; expiry; tenant scope; revocation; cache; concurrency; Runtime or Control Plane integration; real adapters; other Python versions; E05 behavior (3 SKIPs); production | n/a |
| Allowed claim label | [DEV-TESTED], "Copilot-reviewed, not independently qualified" | [QUALIFIED] only with named qualifier, frozen candidate SHA and manifest digest, frozen expectations, retained raw adverse traces |
| Verdict rules | Pass/fail of pytest | Constitution: mismatch against resolved frozen expectations is FAIL; unresolved mapping or unavailable evidence is BLOCKED or NOT ASSESSED; qualifier may not adjust expectations; verdict transfers only to exact sources and profile |

[PROPOSAL] Any S05 case (R01–R34, E, X, PIN) a qualifier chooses to reuse must be re-derived or independently re-approved as an expectation; reuse of builder expectations without that step stays [DEV-TESTED].

## 4. Candidate qualification contract (all [PROPOSAL])

### 4.1 Outcome vocabulary

REFUSE, DENY, HOLD and RETRY are used exactly as defined in `04-effective-policy-consistency.md` section 4.3 (candidate, pending decision LD-02). In particular RETRY is a new transaction under a freshly resolved pin with a new attempt identity, never a replay and never automatic for an in-doubt effect. Under the optional profile the outcome of every record, selection and activation row below is "overlay not applied, caller policy stands" (frozen S04), recorded as such and never as DENY. Outcomes marked "mandatory" are [PROPOSAL] and depend on an approved successor contract and consumer. Cell values below that say "HOLD or RETRY" mean HOLD, with RETRY only as defined in 04 section 4.3.

### 4.2 Reuse, not a new system

Each future row becomes a TestSpec in the existing catalog/suite structure of `cognous-stack-qualification` for OCS candidates (suite under `suites/`, expectations pre-registered in `process/release-gate/` style, controller verdict per requirement row, refusal template legs a–e for effect-boundary rows). GCR-side rows (Q01–Q15 of the ISS plan) stay in ISSBench V2. [PROPOSAL] The registry repository keeps only developer regression tests.

### 4.3 Prohibited in qualification evidence

Qualifier-visible fixtures built by the candidate author; expectations edited after candidate execution; "NOT APPLICABLE" for a check that is merely missing or disabled; treating an S04 refusal as mandatory denial; treating a digest match as authorization; citing a PR merge as selection; counting an executor acknowledgement as destination observation; claiming global cross-domain atomicity.

## 5. Matrix

Layers: RV record validation, SA selection authentication, AC activation, EV evaluation, EB effect boundary. Coverage column: S03 cases, S04 battery IDs (`tests/test_s04_overlay.py`), S05 IDs (`tests/s05_expectations.json`). "None" means no existing registry test touches it. Coverage labels are all [DEV-TESTED] where cited; "None" is a gap. PR17-07 IDs name designed, unexecuted scenarios.

| ID | Condition | Layer | Expected outcome [PROPOSAL] (optional / mandatory) | Existing coverage [DEV-TESTED] | Evidence an independent qualifier must see |
|---|---|---|---|---|---|
| QM-01 | Invalid records (bad JSON, duplicate keys, unknown fields, wrong types, bad values, bad digests, status, supersession) | RV | REFUSE / REFUSE | S03 P6, N1–N3, N9–N14, M1–M5, X1–X3, O1; S04 N14, N15, N17; S05 R03–R06, R10, R17–R21, R29, R30, R33, E01–E19 (representation refusals) | Qualifier-authored invalid corpus (fuzz plus frozen list), each with frozen reason code; raw refusal outputs; proof closed reason set unchanged; for successor schema PR17-07 V/M/K/I/D/U rows |
| QM-02 | Unauthenticated selection (self-consistent attacker manifest, altered record re-digested, no pin) | SA | REFUSE / HOLD | S03 L1 (integrity not authenticity pinned as ACCEPT); S04 N1, N2, N5, N6, N18; S05 R07, R08, R09, R25, R32, PIN-1..3, LIM-2 | Evidence of who holds the trust anchor, identity and key custody, and a qualifier-run substitution attempt; today only byte-pin custody exists (T4). A signed or identity-bound selection does not exist, so row is NOT EXECUTABLE for authentication proper |
| QM-03 | Wrong consumer / namespace (record or selection for another consumer, another system's selection) | SA, AC | REFUSE / HOLD | Partial: evaluator id/binding only: S03 N4, N5; S04 N12, N13; S05 R19, R20. No `target_consumer` or namespace field exists | PR17-07 A1, A4, A5, S6, N1, N2 executed; proof no parameter reads another system's store |
| QM-04 | Wrong tenant or institution (cross-tenant substitution, wrong scope) | SA, AC | REFUSE / HOLD | None (T9: no tenant scoping) | Selection-bound tenant/institution scope tuple, cross-tenant substitution battery run by qualifier (R09 exit lists cross-tenant) |
| QM-05 | Wrong evaluator revision (installed source differs, blob/sha mismatch, in-process replacement) | RV, AC | REFUSE / HOLD | S03 N6, N7, I1; S04 N8–N11; S05 R13–R16, R34, LIM-1 | Qualifier computes expected identities from source independently; LIM-1 stays a stated limit: in-process replacement undetected (T5) |
| QM-06 | Expired selection (clock past validity; not yet effective) | AC | REFUSE (caller stands, T7 by time) / HOLD or DENY | None (no clock or validity interval; PR17-07 S10–S12, O4 designed) | Trusted time source declared, clock-skew and boundary instants frozen in advance, deterministic clock injection log |
| QM-07 | Revoked selection (withdrawn after approval; mid-operation revocation) | SA, AC, EB | REFUSE / HOLD, no unauthorized commit | Adjacent only: record `status` withdrawn S03 N1, S05 R17. Selection revocation None; pin-only trust cannot detect rollback or revocation (PR17-07 section 2 note) | Revocation reference/epoch design, revocation published after activation, effect-time recheck using refusal template legs a–e with revocation=True, positive control at same enforcement point. ISS Q05, Q06 analogues |
| QM-08 | Unknown record version / envelope / family / contract version; stale or future version | RV, SA | REFUSE / HOLD | S03 N8, M6; S04 N7, N12, N22; S05 R05, R06, R11, R12. Envelope/family unknown: none (PR17-07 U1–U3) | Frozen version table; refusal never selects `latest`; anti-rollback evidence (R09) |
| QM-09 | Missing required policy (required profile, no selection or no record) | AC, EB | n/a under optional: caller stands / HOLD or DENY without unsafe fallback | Optional refusals only: S04 N16, N17, N18; S05 R01, R02, R28. Mandatory behavior: None (not authorized, T7) | Approved mandatory profile (MSOP), per-operation participation (PR17 V5), proof of no permissive default, no canonical mutation (ISS Q02) |
| QM-10 | Invalid provenance (bad `authored_at`, `decision_ref`, source blob; forged `record_source`) | RV, SA | REFUSE / REFUSE for shape; authenticity not decidable | S03 N7, N13; S05 LIM-3 (`record_source` unverified pinned as limit) | Qualifier-run check that provenance claims are not trusted; authenticated provenance custody mechanism does not exist, so authenticity part is a gap |
| QM-11 | Policy widening attempt (registry superset of caller, union instead of intersection, relaxing payload) | EV | Clamp to intersection, no refusal; widening defect surfaces as refusal | S03 W1; S04 P2, P3, P4, F4; S05 G1, G2, B group, scratch mutations (uncommitted) | Qualifier-authored oracle of the composition law over its own universe; committed mutation set with kill results; for new families PR17-07 W1b, W2 |
| QM-12 | Incompatible composition (two records, no ruled direction, dependency missing) | AC, EV | REFUSE `composition_unsupported` / HOLD | None (one record, one family) | PR17-07 C1–C4, H3; cross-family field-ownership; depends on PR #17 D4 and D3 |
| QM-13 | Record substitution (different bytes, id, digest than selected) | SA | REFUSE / HOLD | S04 N2–N4; S05 R07, R08, R22, R23, R27 | Byte-level substitution battery run by qualifier against the selection pin |
| QM-14 | Selection substitution (replaced manifest, older pinned selection, two selections for one scope) | SA | REFUSE / HOLD | S04 N5, N6; S05 R09, R24, R31. Rollback to older pinned selection: None, stated undetectable | Epoch/anti-rollback design and qualifier replay of an older valid selection; hash chain or anchor evidence |
| QM-15 | Concurrent policy replacement (selection or record changes between check and effect) | EB | HOLD or RETRY under fresh evaluation; never silent hot-swap / HOLD | None (T11: concurrency not tested) | Deterministic barriers (not sleeps) at each pause point, named linearization contract, destination state read independently; "prevented" versus "detected only" classification (existing adversarial plan convention) |
| QM-16 | Changed authority (grant revoked, approver removed, authority epoch moved) | EB | HOLD / HOLD | Registry: None. Adjacent: Control Plane `tests/test_runtime_authority.py` grant revocation (grants, not selections) | Refusal row naming expected and observed authority versions; binding of effective-policy identity to the commit (plan section 3.3) |
| QM-17 | Changed evidence (evidence invalidated, stale freshness) | EB | HOLD; reliance eligibility lost, history kept | None. Domain partly GCR-owned | Distinguish OCS evidence checks from GCR reliance (ISS Q09); no claim until a consumer exists |
| QM-18 | Failed effect-time commitment (identity not bound, commit fails, ambiguous ack) | EB | HOLD / HOLD; ambiguous ack not durable proof (Constitution) | None for policy identity. S05 X (11 end-to-end cases) bind no selection identity | Decision/evidence record carries selection id/epoch, record digest, evaluator revision (R10 exit); failure injection at commit; receipt is evidence not authority |
| QM-19 | Recovery and replay (restore, restart, replay of revoked selection) | EB, AC | Historical pin inspectable; no reactivation | None. Adjacent: qualification repo restore-boundary tests for destination (not registry) | Restore procedure naming what is restored and what stays external; ISS Q13 analogue; replay cannot reactivate revoked selection |
| QM-20 | Cache inconsistency (stale cache, invalid cache, registry outage) | AC, EB | HOLD or RETRY bounded / HOLD | None (S04 has no cache: each call re-reads and re-verifies; this is a design property not a test) | Cache bound declared; stale-cache and outage injection; isolation of unrelated domain (ISS Q15); R09/R10 lists stale cache |
| QM-21 | Negative-record custody (refusal produces durable, attributable negative evidence) | EB, AC | HOLD with durable refusal row; acknowledged vs crash-durable distinguished | None. S04 returns a result object and writes nothing; F3 only checks the caller policy is untouched | Refusal template leg (b) and (d) (mutate the writer, scenario must fail); original bytes preserved for failures (Constitution historical custody); crash-durability not claimable from an emulator (Constitution). Tier 1 criterion "negative-evidence custody" |
| QM-22 | Operational rollback (revert to earlier release, selection or configuration; key rotation) | EB, AC | HOLD on identity mismatch; documented rollback only through new authorized selection | None | R17 rollout/rollback and restore drills; proof rollback cannot lower a mandatory floor or reactivate superseded records |

## 6. Coverage-gap list (rows no existing test touches)

Fully untouched: QM-04 tenant/institution, QM-06 expiry, QM-12 composition, QM-15 concurrency, QM-17 changed evidence, QM-18 effect-time commitment, QM-19 recovery/replay, QM-20 cache, QM-21 negative-record custody, QM-22 rollback.
Touched only for the optional overlay or only adjacent: QM-02 (no authentication beyond byte pin), QM-03 (evaluator only; no consumer namespace), QM-07 (record status, not selection revocation), QM-09 (no mandatory profile), QM-10 (shape only; authenticity unverifiable), QM-14 (rollback undetectable), QM-16 (grants only, outside registry).
Reasonably covered at developer level for the three-field family only: QM-01, QM-05, QM-08, QM-11, QM-13. These stay [DEV-TESTED] and are not independent.
Also uncovered: the three E05 behavioral SKIPs; fields beyond the three allow-lists; any Runtime-wired path.

## 7. Constitutional and v1.2 mapping

Read in the Constitution at `1c2e920f…`: EP7 (separate contribution, inspection, independent qualification; a passing test cannot certify itself); CA04 (qualification designed before acceptance; do not fit an oracle to implementation or substitute developer tests); CA05 (fail closed without inventing policy; negative controls); CA08 (honest PASS/FAIL/BLOCKED); CA16 (no silent claim promotion; lifecycle states); CA18 (authenticate governance-critical policy; protect invariants); CA23 (accountable certification); "How the articles work together" section 4 (independent expectations recorded before acceptance; qualifier cannot adjust frozen expectations; result transfers only to exact sources); Tier table (Tier 1 includes authority, admission, trust, authentication, atomic state, negative-evidence custody, independent acceptance logic, with "focused independent review proportionate to the identified critical risk"); evidence discipline (developer suites are not independent qualification; emulator results do not establish durability; ambiguous commit ack is not durable proof; mismatch is FAIL, unresolved mapping is BLOCKED). I did not find an Article that names how many independent qualifiers are needed or who may be one; that is not established by the text.

| Matrix element | v1.2 / crosswalk |
|---|---|
| QM-02, 04, 06, 07, 13, 14, 20, 22 | R09 exit (negative tests for forged, altered, replayed, cross-tenant, expired, superseded, revoked selection, source substitution, stale cache, missing custody, rollback) and its independent security review gate; G2 |
| QM-09, 15–19, 21 | R10 (effect-time boundary, in-flight revocation, HOLD/DENY for required policy, bounded caching, no global atomicity); section 3.3 commit-boundary revalidation; G3 |
| QM-11, 12 | section 3.2 composition; R08 |
| Independence rules | R17 ("signed independent qualification verdict with negative evidence and residual-risk ownership"; "ordinary developer/Copilot PASS is insufficient"; freeze candidate source and manifest digests at the qualification boundary); G4 (independent Tier 1 sign-off), G6 |
| Crosswalk A10 | ACCEPT: independent oracle/expected results; negative, cross-domain, replay, restore, atomic-refusal coverage; ISSBench V2 owns ISS V6 candidates; OCS existing infrastructure remains OCS-owned; "no evidence of registry integration yet" |

## 8. Before Tier 1 families can be activated: what a qualifier needs

[PROPOSAL] checklist; each item is a precondition, not something this document grants.
1. A designated independent qualifier (person or organisation) for OCS-side Tier 1 registry families, distinct from the builder and from Copilot, with recorded independence from authors. Operator decision (PR #17 D13, still open). Without it S05 limits carry over and G4 cannot be met.
2. For GCR implementation profiles, ISSBench V2's owner designated as qualifier for the GCR side, as in A10 (the ISS plan names ISSBench V2; its repository was not inspected).
3. An approved MSOP (v1.2 section 3.4; PR #17 V6) naming rule families, evaluator/build pins, consumers, optional-or-mandatory per operation, selection and custody mechanism, tenant scope and excluded capabilities. Rows QM-09 and QM-04 cannot be specified without it.
4. A successor contract and authenticated selection custody (R09) in a form that can be attacked; today only a byte pin exists.
5. Frozen candidate SHA, schema and selection manifest digest, evaluator build, profile, clock and inputs, with expectations authored and frozen by the qualifier before candidate execution; amendments dated and recorded, never to obtain a pass.
6. A safe environment and real consumer paths for rows QM-15 to QM-22; synthetic-only suites cannot substitute (plan section 3.4).
7. A declared qualifier-owned oracle for each family beyond the S05 profile (PR17-07 section 5).
8. Residual-risk owner named for each stated limit (T1–T14 carry over).

## 9. Decisions raised

| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| F-01 | Designate the independent qualifier for OCS Tier 1 registry families (identity, independence from builder and Copilot, scope) | Operator | G4 sign-off, R17 verdict, any `[QUALIFIED]` label, activation of any Tier 1 family | D13 (cross-reference, not restated) |
| F-02 | Confirm ISSBench V2 as the GCR-side qualifier and whether OCS and GCR rows run under one coordinator with separate oracles | GCR owner, Operator | R15, G5, cross-domain claims | V7; ISS plan |
| F-03 | Approve REFUSE/HOLD/DENY/RETRY definitions (Lane D) and confirm the Control Plane `hold` convention for required profiles | OCS Architect | QM expected outcomes cannot freeze; row expectations for QM-06, 07, 09, 15–21 | V5 |
| F-04 | Rule on whether builder-authored S05 expectations may be re-approved by the qualifier or must be re-derived | Independent qualifier | Reuse of S05 R/E/X cases as independent evidence | none |
| F-05 | Choose the qualifier-owned suite home and controller wiring in `cognous-stack-qualification` for registry rows | OCS Architect, Operator | Where TestSpecs live; avoids a parallel system | none |
| F-06 | Decide trusted time source and clock-skew rules for expiry rows | OCS Architect | QM-06 not executable | V1 |
| F-07 | Decide whether selection rollback and revocation detection (epoch/anchor) is in the MSOP | Operator | QM-07, 14, 22 remain limitations rather than tests | V1, V2 |
| F-08 | Name the residual-risk owner for T1–T14 | Operator | R17 exit | none |

Dependencies on open classifications: QM-12 and the family-specific rows depend on PR #17 D3, D4, D6 and on unresolved W3-063 (cond D4 in PR17-07); none are settled here. The 60-versus-300 relationship (T13) is untouched; no row assumes either value.

## 10. Risks and unresolved constraints

- The matrix is a design, not an executed plan. No row beyond the S03/S04/S05 citations has run, and "coverage" means a test touches the condition, not that the expected outcome is independently approved.
- Independence is a property of named actors. The qualification repo itself concedes independence cannot be established from inside the repository (OD-4); a designated qualifier is therefore a precondition, not an output of tooling.
- Citation of S05 R/E/X IDs relies on the frozen expectations file at `eb850c8`; E05 behavioral comparison is SKIPPED, so no equivalence is claimed there.
- The Control Plane `hold` convention is read at head `7a4bcd40`; the g8-r10 pin (`0a41faa9…`) was not diffed and Runtime head `c5e97e87…` effect path was not inspected.
- Lane D's vocabulary may differ from section 4.1; matrix outcome cells must be reconciled to it.
- Outcomes for mandatory profiles are proposals under an unauthorized profile (T7). Several rows (QM-02, 10) cannot be fully tested until an authentication mechanism exists.
- Emulator or synthetic results do not establish real-environment durability, identity or resilience (Constitution); QM-19–21 need that distinction in any verdict.
- COG-REG-SHARED-ADD-01 is unavailable; any requirement it imposes on qualification is not reflected here.
