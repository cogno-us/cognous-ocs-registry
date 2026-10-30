# T0 read-only documentation review: Registry PR #79 (head 4c343b52a0baffde8631e3867cfbe55134fa50f4)

Registry clone HEAD verified 4c343b5...; tree clean after the review. Control Plane clone HEAD 739efe7d... verified. Constitution dcdbe3b... verified. No repo file modified; only collect-only and the deterministic annex scripts were run (PYTHONDONTWRITEBYTECODE=1).

Verdict totals: CONFIRMED 26, INCORRECT 8, UNSUPPORTED 3, UNVERIFIABLE 4.

## 1. SHAs, PR numbers, merge commits, dates (REST + git)

| Claim | Verdict | Evidence |
|---|---|---|
| Registry #75 merge 7cfeca80, #77 merge 188e90ef (head a40fe755), #78 merge 2815643c; all merged 2026-10-29 | CONFIRMED | `pulls/N` merge_commit_sha; a40fe755 is ancestor of 188e90ef, which is ancestor of main (git) |
| CP #94 19aeb939, #96 e9214718, #97 739efe7d on main; #95 fb9c7e06 base = branch `freshness-purpose-residual-regression` (not main) | CONFIRMED | `pulls/N` base.ref; fb9c7e0 is NOT an ancestor of CP HEAD; 19aeb93, e921471, 739efe7 are |
| Registry #58, #59, CP #87, Registry #52, #7, #76 open; #26, #34 merged with the quoted titles | CONFIRMED | REST |
| #76 head 138e2229, file path, status text "PROPOSED STATIC PLAN AMENDMENT, NON-AUTHORIZING", governance pin 1c2e920 | CONFIRMED | contents API at that sha |
| 00:27-28 check runs on the two main heads | CONFIRMED (CP); CONFIRMED with note (Registry) | Registry head has Analyze (actions) x2, Analyze (python) x2, pytest, all success. No check run named "CodeQL" exists; "CodeQL" is only the workflow/product name. Suggest "both Analyze jobs (CodeQL), pytest - success". UNVERIFIABLE as a distinct check |
| 00:11 dcdbe3b adds relative to 230c0aff only LICENSE, addendum, README change, schema | CONFIRMED | `git diff --stat` shows exactly those four |
| 00:11 addendum "not adopted by publication or merge"; OCS records pin 1c2e920 / 230c0af | CONFIRMED | addendum line 3; git grep on both repos |

## 2. Accounting vs IMPLEMENTATION-CLOSEOUT-2026-10-29.md (main)

19/19 integrated, 0 independently accepted, migration implementation CLOSED, merge chain table, #95-not-main note: CONFIRMED (closeout lines 3, 9-18, 30).

## 3. D-07 identity and hashes

CONFIRMED. runtime_authority.py on main sha256 prefix 45a27db8695ff9d2; b7eb11a and 061a986 give a4b4ac36cca6e75d. The other six (bounded c219f8825a8d, freshness 3f146ee11a34, policy_binding defdfac5fd60, rule_revision a3833f49e96d, reversibility 5edbadebb3aa, holder_inventory 76f5aaa63f49) are identical on main, b7eb11a and 061a986. The single hunk is `@@ -404,10 +404,12 @@` (lines 404-415 new). `a1de48c` src/tests/schemas tree-identical to main (only docs/final3-consumers.md differs). All five earlier heads (5ffd0ae, 4adb84b, b8fbe95, a1de48c, 55488d2) are ancestors of main via the #97 branch; fb9c7e0 is not.

## 4. Verbatim clause fidelity

CONFIRMED, all 10 rows. Programmatic comparison (split table row on `|`, strip, compare each of the three source cells to the document cells; script at scratchpad r1/clausecmp.py): 00 CA01, CA03, CA04, CA18, CA21 and 01 CA04, CA06, CA07, CA08, CA23 are character-for-character equal for Article, Required and Prohibited cells (em dashes included). Archetype A/B/D article lists match the addendum selection table.

## 5. Measured vs estimated figures

| Figure | Verdict | Evidence |
|---|---|---|
| 1,026 code lines (1,230 physical); 9,345 code / 11,922 physical in registry_successor; 11.0% | CONFIRMED (re-run annex/scripts/loc.py) | 1026/1230 and 9345/11922 reproduced |
| v4..v6 verify/selection/record AST-identical to v3 | CONFIRMED (re-run astcmp.py) | "identical" for all pairs |
| per-version 850/901/837/993 (mean 895), v7 101, v8 110, engine 1,290 | CONFIRMED (loc.py) | physical lines reproduced |
| 77 non-doc registry_* files match frozen manifest | CONFIRMED | recomputed sha256 of 77 entries, 0 mismatches |
| 20,013 documents, 0 disagreements | CONFIRMED (re-run diff_parsers.py) | 20013 / 0 / 0 |
| 15 groups, 151 redundant lines, 0.6% of tests/ | CONFIRMED (re-run test_dups.py) | 15 / 151; 151/25,273 = 0.597% |
| 337 D-06 binding tests | CONFIRMED (collect-only with pin a40fe755) | 115 + 27 + 195 = 337; unit file 54 |
| 8 digests, 61 _json_copy, 1 crypto_sign_open per decision | CONFIRMED (re-ran out/profile_callers.py) | 8 `common.digest`, 9 canonical_bytes |
| 10 timestamp parses, 984 us, 75+29 us | UNVERIFIABLE | scripts ts_args.py / time_decide.py not in PR; host-specific timing |
| 41 baseline failures (14+16+5 pytest-asyncio, 6 older pin); 64/64 consumer mutants; D-06 65/2 draft vs 64/3 summary.json | CONFIRMED | baseline-failures.txt, final3-consumers.md line 39, ci-scope-declaration-draft.md:23 vs mutation-final3/summary.json |
| 22 + 20 candidate classification totals | CONFIRMED | annex B line 57, annex C line 48 |
| Estimates (-41, -32, -2/-17, -45, 64+14, 205 / 7.7%) labelled "estimate" in 02, 03 and annex C line 237 | CONFIRMED labelled | arithmetic issues below |

### Required corrections (5)

**R-5a INCORRECT** 02 line 16. "19.5% excluding the data table" belongs to the combined 1,263 lines (annex B line 19, 255), not to 1,026. 1,026/(9,345-2,863) = 15.8%. Corrected text: "1,026 code lines (11.0% of the 9,345 code lines of `registry_successor/`; 15.8% excluding the 2,863-line data table; adding the v4..v6 decision modules, 1,263 code lines = 13.5%, or 19.5% excluding the data table)".

**R-5b INCORRECT** 02 line 3 ("the measurement scripts are in `annex/scripts/`") and 02 line 18. `annex/scripts/` has 9 scripts, but annex B cites dupmass.py, loc_by_version.py, importers.py, profile_callers.py, time_decide.py, ts_args.py and an inline `hashcheck` that are NOT in the PR; annex B/C section 3.5 paths point into the scratchpad `out/`. Corrected text: "The measurement scripts reproduced in `annex/scripts/` are astcmp, normdiff, loc, line_sim, deadnames, test_dups, diff_parsers, count_commitments and profile_governed; the scripts for the duplicate-mass, per-version LOC, importer, per-decision call-count and timing figures (dupmass, loc_by_version, importers, profile_callers, time_decide, ts_args) were run by the worker and are not included, so those figures are worker-reported (the 1,026 and 9,345 figures were independently reproduced with loc.py/astcmp.py)." Or add the six scripts to annex/scripts.

**R-5c INCORRECT** 02 line 18. "about 984 microseconds in total" reads as the cost of the repeats. Annex B REG-11/3.4: 984 us is the whole `verify_and_decide_v8` call; the repeated digests are 75 + 29 us. Corrected text: "(8 digest recomputations and 10 timestamp parses per `verify_and_decide_v8`; the whole call takes about 984 microseconds on the worker's machine, of which the repeated record and statement digests are about 104 microseconds; the repeats are re-checks, not waste to remove)". Mark as worker-measured.

**R-5d INCORRECT** 03 line 10 (rank 2 cost). "M, about 6 h of the 10 h" for CP-1 stage A. Annex C CP-1: stage A is "S (4 h)", stage B "M (6 h)". Corrected text: "S for stage A, about 4 h of the 10 h (M, 10 h for both stages)". Also 03 rank 1 cost "S, about 5 h" is CP-3 stages A+B (stage A 3 h); WP-2 is stage A only: add "(stage A about 3 h)".

**R-5e INCORRECT** 04 D5 "about 64 lines of benefit (estimate)". 03 WP-5 gives "about 64 + 14 lines"; annex C adds CP-6 -8. Corrected text: "for about 78 lines of benefit (estimate: CP-1 stage B 64 + CP-3 stage B 14; CP-6 adds about 8)".

**R-5f INCORRECT (annex C, internal arithmetic)** line 98: "36, plus 12 + 12 ... minus the 8-line shared payload reader = 40" does not add (36+12+12-8 = 52; table and 03 use 36 + 24). Corrected text: "Measured duplicate: 4 x 9 = 36 parser lines plus 12 + 12 = 24 extractor lines (60 lines; the existing 8-line `_record_payload` is the shared copy to keep); estimated net about -41". Also annex C line 63 and line 145: "unchanged thresholds (73/111/148/99/388/576/858)" is wrong for the first two: `tests.yml` thresholds are 70/105/148/99/388/576/858 (lines 67, 92, 126, 150, 183, 217, 251); 73/111 are the collected counts. Correct to "thresholds 70/105/148/99/388/576/858; collected counts 73/111/148/99/388/576/858". 03 line 11 and 38 use "gate counts"; accept, but state "counts" not thresholds.

**R-5g UNSUPPORTED (soft)** 02/03 205-line ceiling: the annex C table sums to 209 (96+45+41+19+8), not 205 (labelled "a sum of estimates", so acceptable if it says "about 205-209"). Suggested: "approximately 205-210 physical lines (estimate; the sum of the per-candidate estimates)". 03 line 38 "collected count unchanged (3,082)": that number is a merge of two single-pin collect-only runs (2,898 + the 73 + 111 of the 6f600ab-pinned files; annex C line 215). Suggested: "(3,082 = 2,898 under the a40fe755 pin plus 184 for the two files that need the 6f600ab pin)".

**R-5h UNSUPPORTED** 02 line 26 ("effort hours and the tier mapping in annex C are the worker's assumptions ... and are re-mapped to T0-T4 in 03"). 03's tier column is identical to the worker's mapping; no re-mapping against TESTING_POLICY is shown. Under TESTING_POLICY T3 ("authority, trust, ... security controls"), CP-1 (verifier admission `verifier_not_admitted`, Registry verdict handling) and CP-3 (strict parse feeding `scoped_class_not_governed`/`effective_policy_invalid`) are plausibly T3, not T2; CP-9 T1 is consistent. Corrected text: either "tiers in 03 are the worker's mapping, not yet reconciled to TESTING_POLICY T0-T4; CP-1 and CP-3 may be T3 on that definition (Architect to confirm)" or re-map explicitly.

Minor: 03 rank 2 "3 x 30 byte-identical" - annex C says identical after version rename and v6 differs by one docstring line; use "identical after version-token renaming (v6 differs in one docstring line)".

## 6. Unsupported qualification / acceptance / clearance claims

None found. Searched 00-04 for pass/qualified/accepted/ready/cleared/certified/release/production/secure: every hit is a negation, a verbatim clause, a hold, or the record's own "no verdict" statement. One label issue:

**R-6 INCORRECT** 00 line 3: "Status: BUILDER_TESTED planning/inspection record". No test was run for this work (02 line 3: "no test suites were run"); the label implies tested. Corrected text: "Status: BUILDER_INSPECTED planning/inspection record (documentation only; no test suite was run)". (If BUILDER_TESTED is a mandated lifecycle label, state "BUILDER_TESTED: document and claim consistency checked only".)

## 7. Holds and limitations

Registry #58/#59, CP #87, constructor tolerance NOT AUTHORIZED, Ed25519 #26/#34 HELD, V09 SEPARATE, Tier 1 DEFERRED NOT WAIVED, publication/release/production HOLD, DEF-OBS-TOL-OVERFLOW-1 (record path exists): all present in 00 section 5 and 04 line 3 - CONFIRMED complete versus closeout line 27.

**R-7a INCORRECT** 00 line 45: "a host change fully masked by a narrower Registry value". Closeout line 26 and 01 line 44 say "stricter Registry overlay/value". Corrected text: "a host change fully masked by a stricter Registry value is not refused".

**R-7b UNSUPPORTED** 00 line 47 heading "Holds (verbatim, unchanged)": text is reformatted ("Registry #58/#59: HELD"; "DEFERRED, NOT WAIVED" vs closeout "DEFERRED NOT WAIVED"). Corrected text: "Holds (substance verbatim from the closeout, unchanged)" or reproduce closeout line 27 exactly.

**R-7c minor** 00 line 38 calls #58/#59 "M11 constructor-tolerance work"; #58 is "M11 PR-1 ... f4t-control-plane-clock-tolerance", #59 is "M11 accounting + controlled pause/handoff (docs only)". Suggest "M11 clock-tolerance work and its pause/handoff record".

Ed25519 #26/#34 "NOT INDEPENDENTLY SECURITY-ASSESSED / NOT TIER 1 QUALIFIED": CONFIRMED (docs/adapters/ed25519.md:7, core-security doc line 3, program-closeout line 61).

## 8. Internal consistency

- Candidate IDs, class counts, WP names, annex section references (annex A section 1, 00 section 2, 03 sections) all resolve. CONFIRMED.
- 01 lines 14 and 48 and 04 D8 name `docs/r08-v8-contract.md` without repository; it exists only in Registry (not in CP). **R-8a INCORRECT (clarity)**: write "Registry `docs/r08-v8-contract.md`" (contract line 3 "no Control Plane consumer exists" confirmed).
- 01 line 35 "Python 3.11-3.13": pyproject says `>=3.11`; CI matrix is 3.11 and 3.12 only. **R-8b UNSUPPORTED**: write "Python >=3.11 (CI: 3.11, 3.12)".
- D-06 line refs in 03 WP-4 (test_irreversibility_governance.py L381, dedicated L329, composed L253) CONFIRMED to be the literal-order assertions.
- Annex A section 0 times are local (PDT); GitHub UTC times are 16:18:00 etc. No conflict.

## 9. Decision packet (04)

| ID | Verdict | Note |
|---|---|---|
| D1, D2, D6, D7 | CONFIRMED | consistent with sources |
| D3 | **INCORRECT (incomplete)** | `ACCEPTED_PINS` (tests/test_f5_class_unreadable_governance.py:28) does hard-code the pins, and Registry main/188e90ef are rejected by the code. But `tests/test_f4_age_governance.py:20` and `tests/test_f5_class_age_governance.py:21` require exactly `6f600ab`, `test_v02_claim_policy_binding.py:45` requires `943ab18`; with only a40fe755 I reproduced "2898 collected, 2 errors" (f4 and f5-age). So a40fe755 is not "the qualification pin" for all F3-A sources. Corrected text (04 D3 and 01 line 35): "accept `a40fe755` as the pin for the FINAL3, revocation, irreversibility, composed and D-06 binding suites; the F4 and F5 class-age suites (73 + 111 tests) require a second Registry checkout at `6f600ab1150f00ef3d96834159b1807e866a78b6` (as CI does), and `test_v02` a third (`943ab18...`)". The "code-identical outside documentation" statement is CONFIRMED (diff a40fe755..2815643c outside docs is empty; a40fe755..188e90ef touches 10 docs files only). |
| D4 | CONFIRMED | 205/7.7% labelled estimate (see R-5g) |
| D5 | INCORRECT | see R-5e |
| D8 | CONFIRMED | final3-consumers.md section 6 line 57 says main lacks D-07 (stale); r08-v8-contract.md "no Control Plane consumer exists"; 65/2 vs 64/3 verified. "Before quotation not verbatim" and "family_schema_revision accepts null": UNVERIFIABLE (not checked) |
| D9 | CONFIRMED | tests.yml has no step naming the three D-06 binding files; plain `pytest` step (line 32) has no OCS_REGISTRY_PIN_DIR; gates at lines 67-251. 337 reproduced |

## What could not be verified

Registry-side timing (984 us), 10 timestamp parses and the scripts behind them (not in PR); "Before comment quotation not verbatim" and null `family_schema_revision` (01 line 48); a CP run against Registry 188e90ef (rejection inferred from `_head not in ACCEPTED_PINS`, not executed); distinct "CodeQL" check run; worker effort hours and all savings estimates (not measurable).
