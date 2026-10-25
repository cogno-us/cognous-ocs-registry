# Lane E: contract and evidence status (read-only verification)

Pinned revisions read: OCS hub `51c579a3208149922649a31a6eb041106a4121c3`; Qualification `998d39c5ba1c9d537be8289f7658f2e9cde6cbba`; Registry `ce00520f91bf3986a08b4d13a1fb062057babc71`. Ledger rows: `lanes/E.jsonl` (37 rows, ids E01-E37; per-row four-axis verdicts are in `notes` as AXES arch/impl/qual/prod).

## 1. Key findings

1. No independent qualification of any registry contract exists in any of the three repos. The Qualification repo has no suite, expectation, battery row or result that mentions `ocs-registry-record`, `ocs-mandatory-manifest`, `registry_records`, `mandatory_checks`, `cognous-ocs-registry`, `r08-v1` or the AOI cases (grep over the whole repo, excluding the AI Security Wiki pages, returned nothing). In g8-r10 "registry" means The Index (`cognous-evidence-registry` b2485998), not the governance registry.
2. Adopted decisions exist, but wire contracts are not frozen. `docs/program-v0.2/m0-decision-record.md` (operator, 2026-10-22) approves packet rows 1-20 (rows 6, 10, 11 are review only). Contracts 1.2, 1.3, 1.4 and 1.7 still carry "Proposed contract draft ... No decision is recorded"; `/0` wire names are "provisional" (s05 Q4, Q17); the five Q17 profiles have no freeze record. `engineering-register.json`: all 24 steps are `planning_disposition: PROPOSED`.
3. Implemented, not qualified: hub `tools/registry_records.py` (2.1) and `tools/mandatory_checks.py` (2.3, with `/1` candidate), registry S03/S04/S05 and R08-S01 `registry_successor/`. All evidence is builder tests plus Copilot code review. Registry docs say so consistently (trust-limitations T10, sprint-status).
4. Source revisions: all mission pins resolve. Hub component-lock sha256 `dcd3ab9e...` equals the value in release-status and evidence-snapshot. Qualification run g8-r10-39690459403 has `pinned_sha == actual_sha == lock sha` for 13 of 14 lock components (verifier `c0b8ba1f` not probed). Registry frozen blobs (`validator.py` afee88b3, `consumer.py` bf382d00, `safe_executor.py` 2fc880da, s05 oracle 503851c4, expectations 37a68275, plans v1.1/v1.2/crosswalk) all match what tests/test_s06_integrity.py pins. `integrity-manifest.json` (74 files) matches HEAD blobs exactly; it asserts object identity only.
5. R08-S01 PR #19 is MERGED (GitHub API: merged_at 2026-10-25T05:07:45Z, head `f0765909b1aca44d149ec6bfe75966cb8a03c79b`, merge `783ff59f07d020d06e2ea9a32a257311527d9d82`). `docs/sprint-status.md` still says "DRAFT PR" and plan v1.3 line 97 says to verify merge status; the local clone is one shallow commit so git log cannot show it. Merge does not imply approval or activation (operator authorization says no activation, no verifier/key/trust root).
6. Activation and production: NOT READY on every axis. Hub step 2.4 "Not authorized"; registry has no activation, approved pin, verifier, key, trust root or Runtime wiring; independent Tier 1 qualifier "not designated" (F-01); hub `operational-trust-status.md`: "HOLD / NOT ESTABLISHED"; residual-risks R-REVIEW-C0/SELECTION/OPERATIONS open.

## 2. Claim verification table

| # | Claimant and wording | Evidence cited | Evidence type | Pins match current? | Arch | Impl | Qual | Prod |
|---|---|---|---|---|---|---|---|---|
| 1 | hub `declarative-governance-registry.md`: "adopted engineering direction" (OCS-DGR-ARCH/1.0.0) | "operator instruction of 2026-10-21" (not stored in repo); operator-decisions.md row | decision statement | n/a | adopted | partial candidates | none ("not a claim of qualification") | none |
| 2 | m0-decision-record: rows 1-20 "Approved" | session transcript, builder transcription | operator decision, self-limited ("no other review is implied") | n/a | approved (not wire-frozen) | step 2.1, 3.1 authorized only | none ("does not freeze Qualification's independent expectations") | HOLD |
| 3 | contract 1.3 "Names are frozen at the M0 gate before any code" | none | future-tense obligation | n/a | PROPOSED | partial | none | none |
| 4 | s03/minimum-profile section 5 heading "Frozen qualification entry" | table of 8 prerequisites | label | n/a | all rows state "Open" | none | none | none. **Heading overstates; table says Open** |
| 5 | step 2.1 note "Candidate implementation, non-authorizing" | tools/registry_records.py + tests | builder tests, synthetic | HEAD 51c579a | candidate | yes | none | none |
| 6 | step 2.3 /0 and /1 manifest: "58-check candidate ... not an adopted or qualified control profile" | tools/mandatory_checks.py + tests | builder tests | verifier pin c0b8ba1f matches lock | candidate | /0 yes, /1 manifest only | none (Q13 assigns to Qualification, not done) | none |
| 7 | architect-disposition Q1-Q17 "binding for this programme" | hub doc | Architect rulings recorded by builder | n/a | rulings | per-item | none | none |
| 8 | hub component-lock `qualification_status: "accepted"`; evidence-snapshot `snapshot_status: current`, `accepted_default_release` | hub CI run 37694032916 at source 7e43d55c, 35 scenarios | hub-run CI of an EARLIER tuple | NO: release-status.md calls that tuple "superseded ... no new release run exists for the current lock" | n/a | n/a | not independent, wrong tuple | HOLD. **Overclaim/stale (CC-E3)** |
| 9 | release-status: g8-r10 "selected verdict PASS ... all 39 mandatory rows PASS" | Qualification g8-r10-39690459403 | controller run, same organization | YES (13 of 14; verifier unprobed) | n/a | component tests at lock pins | bounded: 36 rows removed from mandatory claim after results seen (D15); pre-reduction verdict INCOMPLETE | HOLD. Statement is accurately caveated in release-status |
| 10 | Qualification MVP acceptance gate | `process/mvp-acceptance/*` | all `.proposed`, adoption record blank, no dispatched run | NO: tuple CP 7a4bcd40, Runtime c5e97e87, Replay 40012b8c, EvidPack 7b9511f2, ODES 1a5e1d30 vs lock 0a41faa9, ec728da6, 028f63d1, a3ebbb90, e86a25a1 | n/a | harness only | NOT RUN, "PROVISIONAL, UNQUALIFIED" | none |
| 11 | Qualification reviewer designation: Copilot code review | draft record | DRAFT, not approved | n/a | n/a | n/a | "NOT independent test execution and NOT qualification" | none |
| 12 | registry sprint-status S03/S04/S05/S06: "PASS (bounded)"; S04-S06 "Copilot-reviewed, not independently qualified" | tests, Copilot bot reviews | builder tests + code review | blobs match | adopted (frozen = byte-pinned) | yes | none | none (T1, T7, T9, T11) |
| 13 | registry S05: "bounded differential equivalence demonstrated" | 1,728 + 168 pairs, R/E/B/X/PIN/LIM, 3 SKIP | builder-authored oracle (frozen before harness) | yes | n/a | yes | DEV-TESTED, not independent | none |
| 14 | registry R08-S01: "developer-tested foundation only; not a working registry" | registry_successor/, tests/test_r08_*.py, conformance spec | builder tests; test double verifier; QS13 amended after seeing candidate result | PR #19 head f0765909 / merge 783ff59f (merged) | Architect ACCEPT WITH AMENDMENTS (relayed, "not operator approval") | foundation | none; "Not independently qualified" | none |
| 15 | registry decision: Copilot "standing independent technical reviewer" | s05-authorization items 4-5 | operator exception | n/a | n/a | n/a | item 5: "not formal independent qualification" | none. Wording mixes "independent" with reviewer; caveat present |
| 16 | hub residual-risks "resolved/qualification_scope: tested locally" | examples/ evidence paths exist | hub-local tests | R-001/002/008 cite older revisions | n/a | n/a | not independent | R-REVIEW-C0 etc. open |
| 17 | hub status.md / snapshot | none | placeholder; "no execution has started" now false | stale | n/a | n/a | n/a | n/a |
| 18 | qualification repo orchestration-state: "MATCHED REFUND 20/20 PASSED ... OPERATIONAL QUALIFICATION DEFERRED", `selected: false` | native local trials | builder-run, bounded | pre-dates g8-r10 | n/a | yes | self-described as deferred | none |

## 3. Overclaims and wording hazards

- O1 (CONFLICTING) `component-lock.json` `qualification_status: "accepted"` / `qualification_evidence` and `collateral/evidence-snapshot.json` `"snapshot_status": "current"` versus `docs/release-status.md` (earlier tuple "superseded"). The cited run is a hub workflow on an earlier tuple. Do not cite as qualification of the current lock.
- O2 `s03/minimum-profile-and-coverage.md` section 5 headed "Frozen qualification entry"; every row is "Open".
- O3 Copilot review: described as qualification nowhere found, but the standing designation wording ("independent technical reviewer") and "PASS" sprint labels need the caveat each time. Always quote "Copilot-reviewed, not independently qualified".
- O4 "Frozen" in registry docs means byte-pinned blobs plus Architect direction ("Retain S01-S06 results and frozen evidence without amendment", a builder transcription "not independently countersigned"). It does not mean qualified.
- O5 hub M0 gate definition requires independent review and pre-frozen independent expectations; neither is evidenced. `m0-decision-record.md` records operator approval of recommendations only.
- O6 Stale status text: registry `sprint-status.md` "R08-S01 DRAFT PR" and "Plan: v1.1" header after PR #19 merge and v1.3 approval; hub `historical-status-snapshot.md` "no execution has started"; hub #184 vs #193 controller references.
- O7 Qualification-repo statements of independence: its own README says "A separate repository does not establish reviewer independence", pre-registration OD-4 "independence from the authors cannot be established from inside the repository". Treat g8-r10 as operator-organization controller evidence.
- O8 Naming hazard: "registry" = The Index (`cognous-evidence-registry`), the governance registry (OCS-DGR), and the `cognous-ocs-registry` repo. Ledger rows should always use the full name.

## 4. Candidate genuine conflicts

CC-E1 Canonical JSON profile (low severity; likely REUSE_WITH_ADAPTER, not a design change)
- Side A: ADR-P01 approved (m0-decision-record.md row 1; implemented `tools/registry_records.py` ~line 97): JCS RFC 8785, keys sorted by UTF-16 code unit, non-ASCII emitted literally; "legacy form retained as a named historical profile".
- Side B: registry `registry_contract/validator.py:75` and `registry_successor/common.py:103`: `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=True)`; F1a strings admit non-ASCII letters (`common.py:199` excludes only Unicode categories C and Z).
- Existing behavior: byte-identical for ASCII-only content with integer-only numbers; digests diverge for any non-ASCII value.
- Consequence: the same logical F1a record hashes differently under hub and registry rules, breaking digest pins if records cross repos.
- Resolution: name the registry form as a separate profile identifier (ADR-P01 allows this) or restrict r08-v1 F1a strings to ASCII. No operator decision needed.
- Affected: registry r08-v1, hub 2.1, any pin carrier. P1 impact none; P2/P3 (record format), P6 (digest pins).

CC-E2 Two coexisting record contracts (for Lane B to confirm): hub `ocs-registry-record/0` (candidate, step 2.1) and registry S03/`r08-v1` (frozen/implemented). Registry docs never cite `docs/program-v0.2/` (historical-recovery/unresolved.md: no rule entry cites it). Consequence: duplicated architecture work risk. Recommended: declare r08-v1 F1a the V1 profile and map to hub `/0` fields via adapter; no redesign. Impact P2/P3.

CC-E3 Lock/collateral "accepted/current" versus release-status "superseded" (documentation inconsistency, hub only). Consequence: a reader can cite stale acceptance as qualification of the current lock. Resolution: hub owner corrects fields or adds `superseded` marker; P0 cites release-status wording. Impact P6 evidence claims.

Unresolved authority boundary (not a conflict): ADR-P03 "hub-owned immutable digest-pinned artifact ... no new repository" versus registry program's own repository and the R09 custody question; no registry doc cites ADR-P03. Resolve at R09; P1 unaffected.

## 5. Things I could not verify

- Operator decisions D-1 to D-4 and O-1/O-2 on hub issue #193, controller issues #193/#184 and Qualification controller #218 (external issues).
- Primary text of the 2026-10-21 operator instruction adopting OCS-DGR-ARCH/1.0.0 (cited, not stored).
- Orchestrator-repo contracts and branches (event store, lock, producer observation, source-preserving handoff): not in lane sources; Orchestrator a745e131 and branch SHAs are quoted from hub docs only.
- Whether any hub test passes: I did not run any suite (read-only brief, no pyc writes). "Builder tests pass" counts are quoted from sprint-status (e.g. 347 passed S05; 63 passed S01), not re-run.
- Whether the Qualification repo `main` has moved after 998d39c5 or hub after 51c579a (no network git fetch performed; only `gh api` for PR #19/#20 state).
- PR #19 Copilot review outcome and any later amendments beyond the head SHA recorded above.
- Merge-time of the v1.3 approval is 2026-10-25T05:36:52Z (PR #20, merge ce00520f), after PR #19.
