# Architect decision packet — OCS-REG-R1-START (2026-10-29)

Non-authorizing. Nothing below is decided by the Lead Builder. Accounting: 19/19 integrated, 0 independently accepted. Holds unchanged: Registry #58/#59 HELD; Control Plane #87 HELD; constructor tolerance NOT AUTHORIZED; Ed25519 #26/#34 HELD; V09 SEPARATE; Tier 1 DEFERRED, NOT WAIVED; publication, release, production HOLD. DEF-OBS-TOL-OVERFLOW-1 remains separate and is in no R1 candidate.

| # | Decision | Options | Lead Builder recommendation |
|---|---|---|---|
| D1 | Who is the independent qualification owner for F3-A and F3-B, and is F3 run against current `main`? | (a) designate owner now; (b) defer to the R7 freeze | (a): the handoff `01-...` is ready; no builder verdict is allowed |
| D2 | F3 before or after R1 | (a) F3 on current `main`, then R1 WP-1..4 with a differential; (b) skip R1 and go to freeze | (a) if R1 proceeds; the packages are chosen to leave F3 subjects mostly untouched |
| D3 | Registry pin for Control Plane qualification | Control Plane tests hard-code accepted Registry pins per suite; Registry `main` and `188e90ef` fail collection under `OCS_REQUIRE_REGISTRY_PIN=1`; `a40fe755` is code-identical to `main` outside documentation (verified by diff) and is the working pin for the r08-v8 suites only; the F4/F5-age gates need `6f600ab`, `test_v02` needs `943ab18`, and the workflow uses five pins | accept the workflow's per-suite pins (`a40fe755` for the F3 subjects) as the qualification pins; a later pin refresh is a separate reviewed change |
| D4 | Is R1 worth executing as planned? (superseded by D4′ in `05-...`) | Registry production consolidation is about zero under frozen-byte constraints; the original Control Plane ceiling of about 205 lines was an estimate and is not supported: the measured supported net is -96 lines (3.6%) | authorize only WP-0..WP-4 (unpinned files and tests); leave WP-5/WP-6 optional |
| D5 | Pinned-module changes (WP-5) | allow a deliberate re-pin of `registry_f4_age_governance.py`/`registry_f5_class_age_governance.py`, or forbid | forbid for now: it invalidates F3 transferability for about 78 lines of benefit (estimate: 64 + 14) |
| D6 | R1-E (Registry #76, open, unmerged, proposed) | merge as a static plan amendment; adopt later; or leave open | merge only as a static plan (no authorization); it is not an adopted revision today |
| D7 | Constitution revision for the program | this record uses `dcdbe3b…` for prompt-engineering; existing OCS adoption records pin `1c2e920…`/`230c0af…` | record an explicit adoption decision under ADOPTION.md if `dcdbe3b…` should govern OCS going forward |
| D8 | Stale documentation (non-historical) | Control Plane `docs/final3-consumers.md` section 6 says `main` lacks D-07 (true before #97); Registry `docs/r08-v8-contract.md` says no consumer exists; D-06 mutation counts differ between draft (65/2) and `summary.json` (64/3) | authorize a docs-only correction PR with new text; historical evidence files are not rewritten |
| D9 | CI gating of the D-06 binding tests | the 337 binding tests are not in a skip-asserting junit gate under the Registry pin | authorize adding one gate (a CI change, no behavior change) before the freeze |

Ready for review: `00-...` (source inventory), `01-...` (F3 handoff, no verdict), `02-...` (inventory), `03-...` (ranked candidates and plan), annexes A-C.

Updated by `05-...`: **D4′** authorize the single conditional post-F3 package R1-CP-A (-96 lines net, T3, touches F3-A files) or leave the Control Plane unchanged (recommended default); **D10** R1-E disposition (B recommended); **D11** whether R1 continues at all or the program goes from F3 to the freeze. F3-A and F3-B assignments: READY FOR ASSIGNMENT / OWNER BLOCKED (`assignments/`).
