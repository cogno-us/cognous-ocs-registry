# OCS-REG-R1-NEXT outcome: PR #79 corrections, R1-E disposition, F3 assignment status, Control Plane crosswalk

Status: planning record. **Non-authorizing.** Supersedes the savings figures and tiers in `02`/`03` where they differ. Sources: Registry `main` `2815643c3e15fbc6aadadbf88dc7596f10120992`, Control Plane `main` `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`, Ergonomics `main` `bea582b378af1b0d6854ffe3a1de40df5ad7a0ab` (read-only). Inspection records are annexes D (crosswalk), E (R1-E), F (exact-head review of #79). Accounting: 19/19 implementation integrated, 0 independently accepted.

## 1. PR #79 exact-head review and corrections

An independent read-only reviewer checked #79 at `4c343b52a0baffde8631e3867cfbe55134fa50f4`: 26 confirmed, 8 incorrect, 3 unsupported, 4 unverifiable (annex F). Confirmed: all SHAs, PR numbers, merge commits and dates; accounting; the D-07 identity (reached `main` through #97, `fb9c7e0` is not an ancestor); all ten verbatim clause rows (programmatic diff, 0 differences); the re-run measurements (1,026/9,345 lines, 20,013-document differential, 151 test lines, 337 tests, 77 frozen files); no qualification, acceptance or clearance claim. The incorrect and unsupported items are corrected as new text in `00`, `01`, `02` (section 4), `04` and below. The `BUILDER_TESTED` label in `00` was replaced (no tests were run), D3 now states the pin is per suite (a40fe755 is sufficient for the F3 subjects, not for the whole suite), and the 205-line ceiling is superseded by section 4. Unverifiable items remain stated as such.

## 2. R1-E (Registry #76) reconciliation — recommended disposition: **B, supersede with a smaller addendum, scheduled after R6**

Source-backed reasons (annex E): (1) the Ergonomics claims hold at `bea582b` (0.1.0-draft, non-authorizing; four-component `stack` extra; no Registry/EffectivePolicySnapshot; only `demo` runs `acp`); (2) its pinned Control Plane `0a41faa97269…` is an ancestor of `main` but contains **no** Registry-governed layer, so any E2/E3 work forces a pin bump; (3) the inspection APIs E1-E3 assume do not exist: the governed layer is not exported from `agent_control_plane/__init__.py`, `acp` has no registry/inspect command, and Registry `main` has no packaging, CLI or `__all__` (except `registry_consumer`) — E2/E3 are a new-API track that the addendum's own STOP conditions cover, and E2's trust/epoch and missing-binding diagnoses would read persisted bindings; (4) ordering conflict: R2-R4 reshape verification, identity and snapshot code, and adding an Ergonomics SHA to the R7 freeze enlarges the T4 candidate with a new repository; (5) no authority conflict (E2-E6 respect the non-goals) but wording guards are needed for "expected vs actual decision" and local classifications. The smaller addendum keeps presentation-only static rendering (E4), schemas/tests/docs (E5, E6) and a pin inventory (E1) as a report; it removes E2/E3 commands, the "parallel with R5" ordering, the mandatory Ergonomics SHA in the freeze/qualification candidate and the `1c2e920` governance pin; Ergonomics stays one-way and non-authorizing, with no signing, activation or policy-write authority. Outline: annex E section 5. No file in #76 is modified by this record; merging, replacing or closing #76 is an Architect decision.

## 3. F3-A / F3-B assignments

Two schema-validated Archetype D packets (`assignments/F3-A.assignment.json`, `F3-B.assignment.json`; verbatim CA04/06/07/08/23 with task bindings; frozen subjects on `main`; criteria with PASS/FAIL/BLOCKED conditions; negative controls; raw-evidence and cost limits; paid execution not authorized). **F3-A: READY FOR ASSIGNMENT / OWNER BLOCKED. F3-B: READY FOR ASSIGNMENT / OWNER BLOCKED.** No F3 execution was performed and no verdict is made. The `R1-NEXT` packet (Archetype A, verbatim CA01/03/04/18/21) records this work package.

## 4. Control Plane simplification: bounded source crosswalk (annex D; supersedes annex C figures)

The reviewer re-derived every candidate by transforming copies of the source and counting physical lines (helper, wrappers and retained loaders counted), with differentials on copies against a **fake** Registry (no suite run; unverified against a real pin). **The supported net reduction is -96 lines (3.6% of the 2,674-line layer), not about 205; doing every candidate would give about -118.** Raw line count is secondary; the semantic gain is the point.

| Item | Verdict | Net lines (measured on copy) | Semantic gain | Tier / F3-A impact |
|---|---|---|---|---|
| CP-1 A (revocation, irreversibility, final3) + B′ (F5-age, F5-unreadable): one Registry-verdict adapter | GO (conditional) | -35 and -18 = -53 | 6 hand-written copies become 1 helper + F4 inline; a five-of-six partial fix can no longer occur; one defect would now affect five families | T3; edits F3-A subject files (final3, F5-age, F5-unreadable) |
| CP-3: one strict-JSON parser/record reader | GO (conditional) | -42 (0 differences on 30,022 documents) | 4 parsers + 2 extractors become 1 reader; adds one import edge to the revocation module | T3; edits F3-A files (effective_policy, F5-age, F5-unreadable); F5-age is byte-pinned (one re-pin line) |
| CP-8: duplicate dev requirement | GO | -1 | hygiene | T1; no F3-A impact |
| CP-2, CP-4a, CP-4b, CP-6 | LEAVE | -2, -1, -16, -3..-9 | small; touches refusal/composition/identity | T3; F3-A files |
| CP-5, CP-7, CP-9 | NO-GO | 0 / 0 / (139 lines in 13 groups, not hoistable: the helpers use module globals) | — | — |

Errors in the earlier inventory corrected by the crosswalk: CP-1 stage B and CP-2 were overstated (the importlib seams force each module to keep its loader; F4 cannot move); CP-1 and CP-3 are T3 not T2; CP-4a is not T1 (it feeds persisted row order); CP-9's 151 lines are not hoistable (139 measured); some cited import lines and the CP-7 mint line numbers were wrong. The 64-mutant consumer harness would need re-pointing after CP-1 (final3 `_verified` mutants) or CP-4a. All Registry candidates stay out of scope (byte-frozen). DEF-OBS-TOL-OVERFLOW-1 is excluded.

**Assessment and recommendation: leave the Control Plane code unchanged by default.** The only package with a real semantic gain is a single post-F3 package (CP-3 + CP-1 A/B′ + CP-8, -96 lines net) that touches three F3-A subject files and one byte-pinned module, forces F3-A re-scoping (or must run after the F3-A verdict, with a post-change differential) and a mutation-harness re-point. Whether the semantic gain justifies that qualification cost is Architect decision D4′ below; if not authorized, R1 reduces to the baseline capture and the freeze.

## 5. Proposed next work packages (none dispatched)

1. Architect: decide D1-D9 (`04-...`) and D4′/D10-D11 below.
2. Designate the independent F3-A/F3-B owner; execute F3 (Gate 3).
3. WP-0 baseline capture (no code) — unchanged from `03`.
4. Only if authorized (Gate 4): one optional package `R1-CP-A` = CP-3 + CP-1 A/B′ + CP-8, after the F3 verdicts, with a differential run against a real pin and a targeted F3-A re-scope; everything else in `03` WP-1..WP-6 is withdrawn (CP-9 not hoistable; CP-4, CP-2, CP-6 leave).
5. R1-E: Architect disposition of #76 (B recommended); the smaller addendum is drafted only after R6.

Additional decisions: **D4′** authorize `R1-CP-A` (conditional, post-F3) or leave the Control Plane unchanged (recommended default); **D10** R1-E disposition A/B/C (B recommended); **D11** whether R1 as a program remains worthwhile given -96 lines and zero Registry production change, or the program proceeds directly from F3 to the freeze and the single Tier 1 campaign.
