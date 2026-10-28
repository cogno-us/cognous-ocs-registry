# Independent Registry eligibility audit — numerical reconciliation

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

All numbers below are computed by `tools/reconcile.py` from the ledgers in this directory (`--check` recomputes them in CI); none is typed by hand.

## 1. Answer to the Architect's question

Of **444** distinct canonical logical rules reconciled from the 620 historical records, the 97 current groups and the repository-coverage sweep:

| Measure | Rules | Configuration parameters | Share |
|---|---|---|---|
| Registry-governed (implemented and integrated at the Runtime enforcement boundary; NOT independently accepted) | 4 | 9 | 33.3% |
| Registry-eligible, not yet governed | 8 | 10 | 66.7% |
| **Registry-manageable total (governed + eligible)** | **12** | **19** | 100% |
| …as a share of all canonical rules | 12 of 444 |  | 2.7% |
| …as a share of the 52 rules that carry at least one configurable parameter (parameter ledger) | 12 of 52 |  | 23.1% |
| Unresolved or blocked (decision needed before eligibility can be stated) | 4 |  |  |

### Pass 2 correction (parameter level)

Pass 2 re-derived the denominator at parameter level (`parameter-reconciliation.md`, `parameter-catalogue.json`). Of **80** distinct configurable parameters carried by **52** of the 444 canonical rules, **19** are Registry-manageable (9 governed + 10 eligible; 12 rules; 18 narrowing units) = **23.8%** of configurable parameters and 2.7% of all canonical rules. 12 are represented in the Registry, 9 are integrated at an enforcement boundary, 0 are independently accepted. 3 blocked and 1 unresolved parameters are reported separately and excluded from the numerator. The percentages by rule depend on how rules are partitioned; the percentages by parameter are the stable figures.

The denominator for *all* rules is granularity-dependent (how finely protected mechanisms are split); the manageable count and the configuration-bearing count are the robust figures. See §6.

## 2. Implementation state of the manageable rules (three separate facts)

| Layer | Rules | Parameters | Share of manageable rules |
|---|---|---|---|
| Represented in the Registry | 6 | 12 | 50.0% |
| Integrated at an enforcement boundary | 4 | 9 | 33.3% |
| Independently accepted | 0 | 0 | 0.0% |

Implemented rules are those whose Registry representation AND enforcement-boundary integration are both merged. Nothing is independently accepted: V09 independent qualification is open and builder CI does not establish acceptance.

Governed rules (counted once each; M2/M3 members are not double counted):

| Rule | Parameters | Wave / evidence |
|---|---|---|
| LR-F1D-TARGET-POLICY | 2 | COMPLETED-IMPLEMENTED: M3 (Registry PR #56 merge b7e6a173; Runtime PR #153 merge f7a55e2a) |
| RG-F1A-ALLOW-SETS-FIVE | 5 | COMPLETED-IMPLEMENTED: r08-v2 f1ab (Registry PR #29 merge f618cdf5); Runtime effect-time guard (registry_selection_authority.py) |
| RG-F1C-MAX-AMOUNT | 1 | COMPLETED-IMPLEMENTED: M2 (Registry PR #54 merge ba98dd26; Runtime PR #151 merge 99f5f053, PR #152 merge dabaa770) |
| RG-F1C-MAX-EFFECTS | 1 | COMPLETED-IMPLEMENTED: M2 (Registry PR #54 merge ba98dd26; Runtime PR #151 merge 99f5f053, PR #152 merge dabaa770) |

Represented in the Registry but not integrated (the Control Plane has no consumer):

| Rule | Parameters | Wave |
|---|---|---|
| LR-F4-STATUS-APPROVAL-AGE | 2 | M11 |
| LR-F5-CLASS-STATUS-AGE | 1 | M12 |

## 3. Historical reconciliation (620 records)

| Historical class (frozen) | Rows | Registry Governed | Registry Eligible | Retain In Code | Caller Or Issuer Owned | Provider Or Host Owned | Out Of Scope | Unresolved | Blocked |
|---|---|---|---|---|---|---|---|---|---|
| CONFIGURABLE-CANDIDATE | 43 | 4 | 12 | 10 | 2 | 7 | 6 | 0 | 2 |
| INCIDENTAL-CONDITIONAL | 51 | 0 | 0 | 35 | 2 | 6 | 7 | 1 | 0 |
| MANDATORY-INVARIANT | 354 | 0 | 0 | 350 | 1 | 0 | 3 | 0 | 0 |
| REFUSAL-OR-REASON-VOCABULARY | 50 | 0 | 0 | 50 | 0 | 0 | 0 | 0 | 0 |
| SERIALIZATION-OR-EVIDENCE | 90 | 0 | 0 | 83 | 0 | 0 | 7 | 0 | 0 |
| UNRESOLVED | 32 | 0 | 0 | 23 | 3 | 1 | 5 | 0 | 0 |
| **Total** | 620 | 4 | 12 | 551 | 8 | 14 | 28 | 1 | 2 |

- Every one of the 620 rows appears exactly once as a primary crosswalk row; original IDs and original classes are unchanged (CONFIGURABLE-CANDIDATE 43, INCIDENTAL-CONDITIONAL 51, MANDATORY-INVARIANT 354, REFUSAL-OR-REASON-VOCABULARY 50, SERIALIZATION-OR-EVIDENCE 90, UNRESOLVED 32).
- 74 rows were reclassified by a worker relative to what their historical class implied; 21 rows carry a final (lead-adjudicated) disposition that differs from the worker's, each with a recorded reason; 15 rows were re-keyed by the lead to separate a mechanism from the parameter it sits beside.
- Source status: {'FOUND': 499, 'MOVED': 121} (no row is treated as deleted; coordinates that drifted were re-located by symbol).

## 4. Canonical rules

| Origin | Rules |
|---|---|
| G0-CURRENT-ONLY | 39 |
| HISTORICAL | 308 |
| HISTORICAL+G0 | 50 |
| LEAD-SPLIT | 6 |
| REPO-COVERAGE | 41 |
| **Total** | 444 |

| Disposition | Rules |
|---|---|
| REGISTRY-GOVERNED | 4 |
| REGISTRY-ELIGIBLE | 8 |
| RETAIN-IN-CODE | 350 |
| CALLER-OR-ISSUER-OWNED | 20 |
| PROVIDER-OR-HOST-OWNED | 21 |
| OUT-OF-SCOPE | 37 |
| UNRESOLVED | 2 |
| BLOCKED | 2 |
| **Total** | 444 |

359 rules contain at least one historical row; 44 are G0-current rules with no historical row; 41 were discovered by the repository-coverage sweep (none of those is Registry-eligible).

## 5. Reconciliation with the G0 inventory (116 source sites, 97 groups)

The provisional G0 conclusion was 5 already-governed + 23 eligible-not-migrated = 28 of 97 groups. Group-level movement:

| G0 disposition -> audit disposition | G0 groups |
|---|---|
| ALREADY-GOVERNED -> CALLER-OR-ISSUER-OWNED | 1 |
| ALREADY-GOVERNED -> REGISTRY-ELIGIBLE | 3 |
| ALREADY-GOVERNED -> REGISTRY-GOVERNED | 1 |
| BLOCKED -> OUT-OF-SCOPE | 1 |
| ELIGIBLE-NOT-MIGRATED -> BLOCKED | 2 |
| ELIGIBLE-NOT-MIGRATED -> CALLER-OR-ISSUER-OWNED | 2 |
| ELIGIBLE-NOT-MIGRATED -> OUT-OF-SCOPE | 4 |
| ELIGIBLE-NOT-MIGRATED -> PROVIDER-OR-HOST-OWNED | 2 |
| ELIGIBLE-NOT-MIGRATED -> REGISTRY-ELIGIBLE | 9 |
| ELIGIBLE-NOT-MIGRATED -> REGISTRY-GOVERNED | 4 |
| OUT-OF-SCOPE -> CALLER-OR-ISSUER-OWNED | 1 |
| OUT-OF-SCOPE -> OUT-OF-SCOPE | 5 |
| OUT-OF-SCOPE -> PROVIDER-OR-HOST-OWNED | 2 |
| RETAIN-IN-CODE -> CALLER-OR-ISSUER-OWNED | 3 |
| RETAIN-IN-CODE -> OUT-OF-SCOPE | 2 |
| RETAIN-IN-CODE -> PROVIDER-OR-HOST-OWNED | 8 |
| RETAIN-IN-CODE -> RETAIN-IN-CODE | 42 |
| RETAIN-IN-CODE -> UNRESOLVED | 1 |
| UNRESOLVED -> CALLER-OR-ISSUER-OWNED | 2 |
| UNRESOLVED -> PROVIDER-OR-HOST-OWNED | 1 |
| UNRESOLVED -> UNRESOLVED | 1 |

The audit disagrees with G0 on 39 of 97 groups after lead adjudication (the independent pass-1 group audit flagged 30 before merges, splits and cross-checks). Grouping verdicts: {'OVER-MERGED': 13, 'SUPPORTED': 77, 'UNDER-MERGED': 7}.

Why the headline moved (each item is detailed in `eligibility-decisions.md`):

1. The four M2/M3 groups (max_amount, max_effects, target prefixes, target match) are no longer *eligible-not-migrated*: they are implemented and integrated at the Runtime effect-time guard on current main. They move to REGISTRY-GOVERNED, not accepted.
2. G0's ALREADY-GOVERNED label is overstated for the F4/F5 age scalars (RG-A-007, RG-A-008) and for `age_ceilings` (RG-C-021): the Registry composes them, but the Control Plane has no Registry consumer. They are REGISTRY-ELIGIBLE with the Registry half represented.
3. RG-C-031 (`default_action`) was labelled ALREADY-GOVERNED but has no Registry slot; it is issuer-authored manifest data.
4. Several G0 eligible groups are not Registry-manageable on the audit evidence (host/provider facts, issuer data, no enforcement boundary, or synthetic): RG-B-016, RG-C-037, RG-D-015, RG-D-018, RG-D-020, RG-D-021, RG-D-022 (synthetic). RG-F11, RG-D-012 and RG-F7-DEDUPE are unresolved on ownership; RG-C-011 stays eligible (rank-raising overlay, MEDIUM, retained reviewer disagreement).
5. Several duplicates collapse: RG-A-007 + RG-C-003 + RG-C-004; RG-A-008 + RG-C-008 + RG-C-021 (+ a re-discovered class status age bound); RG-C-031 + RG-D-003.
6. RG-C-005 and RG-C-006 (identity/mandate age, clock tolerance) are monotone in shape but excluded by accepted decision DR-CP-AGE-1 as host-owned, so they are BLOCKED on an Architect reversal rather than eligible. RG-C-018 (freshness nonce toggle) stays out of the manageable set (host-owned: a Registry cannot enforce it). RG-C-024 (funded merge authorities) moves to unresolved.

## 6. Integrity checks (enforced by `tests/test_audit_registry_eligibility_integrity.py`)

- 620 primary historical rows, no duplicates, no deletions; original classes preserved; IDs equal the frozen G0 crosswalk.
- Every row maps to exactly one canonical rule; every rule has exactly one disposition; rule-level totals equal the sum of dispositions.
- No retained mandatory control is mapped into an eligible or governed rule (the reconciler fails on such a contradiction).
- Every one of the 116 G0 source records maps to exactly one canonical rule; M2/M3 composite members are counted once (nine governed parameters in total).
- The committed ledgers equal a fresh recomputation from the worker evidence and the lead adjudications.
- The 38 frozen G0/S02 evidence files are byte-identical (git blob ids) to the pinned baseline.

## 7. Coverage limits (do not read this audit as exhaustive)

- Static source review only; no test suite was run. Worker classifications are AI-produced; the Audit Lead verified the high-impact reclassifications named in `eligibility-decisions.md` against source and ran an independent blind second review (see `worker-cross-check-results.md`).
- Historical-row classification for the 494 non-candidate rows relied on risk-targeted source reading; the blind re-audit sampled 178 retain-in-code rows (148 risk-selected + 30 random), not all 545.
- Repository coverage: Runtime and Control Plane files already covered by S02/G0 were grep-scanned, not re-read. Action Manifest and Governed Exchange schemas, examples, docs and tests, the Stack Qualification repository (about 10 of 28,961 files read) and parts of the Stack Orchestrator were not reviewed in full.
- The count of *all* canonical rules depends on how finely protected mechanisms are split; only the Registry-manageable and configuration-bearing counts are decision-grade.
- Observations that are not migration defects: see `unresolved-architectural-decisions.md` §3.

### Pass 2 repository coverage (Worker F)

| Repository | Pinned commit | Production files | Examined | Confidence | Unexamined surfaces |
|---|---|---|---|---|---|
| cognous-stack-orchestrator | 721f4406 | 43 | 15 | MEDIUM | First-audit I3 read 22 modules in full; this pass did NOT re-read them (relied on I3 + spot checks of vocabulary.py/observer.py).; Scenario modules read by constant-grep only, not line by line (conne… |
| cognous-stack-qualification | bb9b0890 | 139 | 12 | MEDIUM | results/ (27,615 files) and suites/ (816, vendored component test copies) not read: evidence and test code, not production policy.; release-gate preregistration.json (272 KB), mandatory-battery, cand… |
| cognous-action-manifest | fa170815 | 21 | 8 | HIGH | examples/ and docs/ not read; schemas read via constraint grep not full read.; cli.py exit/strictness logic only grepped (no strict-warnings mode found). |
| cognous-governed-exchange | 7f7569b0 | 9 | 5 | MEDIUM | gax_ref_runtime.py (1597 lines) and transport.py (1432 lines) not read line by line.; docs/*.md profile docs not read; tests not read. |
| cognous-open-control-stack | 51c579a3 | 67 | 4 | MEDIUM | First-audit G0/I2 already covered context_journal, operational_state, mvp_ingress/*, mvp_env_record, mandatory_checks, registry_records; not re-read here.; docs/ (872) and examples/ (332) unread; tes… |
| cognous-evidence-registry | b2485998 | 39 | 4 | MEDIUM | Not re-read: protocol/epistemic_engine.py, app/evidence/service.py, chain/*.mjs, IndexProtocol.sol (I2 reviewed). |
| cognous-evidence-attestation | 981036c3 | 24 | 4 | MEDIUM | db/, models detail, tests not read; I2 coverage relied on for rest. |
| cognous-replay-bundle | 40012b8c | 32 | 4 | MEDIUM | importers.py (2099 lines) is not read line by line; only const/revision tables and pattern grep.; programme2_profiles.py (735) read by grep/head only. |
| cognous-governance-evidence-pack | 7b9511f2 | 30 | 3 | MEDIUM | importer.py body, models.py, validator.py, renderer not re-read (I2 read admission/validator rules). |
| cognous-institutional-governance | 03a90c14 | 17 | 3 | MEDIUM | 250+ governance .md/.yaml docs, constitutional-design requirements, tools/validate_bootstrap.py not read. |

No repository is claimed to be exhaustively covered. Worker F found no missed eligible or unresolved parameter; six non-eligible catalogue entries were added (`worker-evidence/I4.json`).

