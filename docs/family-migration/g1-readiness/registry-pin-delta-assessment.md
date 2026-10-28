# Registry pin-delta assessment (PR-1, Phase B)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## 1. The end commit named in the directive

The directive names the end of the range as `317eb76acb2847c534c3ce7c2180b722d130fe8cb`. That object does **not exist** in the repository (`git cat-file -t` fails). The program pin is `317eb76acb2847c534c3ce7c2180b89b4aef987d` (merge of PR #49, the approved Registry family migration plan). This document uses the latter, flags the discrepancy, and does not treat the typed value as a pin. The Architect should confirm the corrected value.

## 2. Method

`git log 943ab18..317eb76a`, `git diff --stat`, `git diff --name-only`, and `git rev-parse <commit>:<directory>` for each code directory at five commits. No file was executed. Range: 13 commits, 24 files, +1,852 / -1 lines.

## 3. Code is unchanged

Git tree hashes (first 10 characters) of the seven Registry code directories at five commits. Identical hashes mean byte-identical trees.

| Directory | 943ab183 | a1169a05 | 1a4de326 | 317eb76a | 2afbd8cd |
|---|---|---|---|---|---|
| registry_adapters | `dcede40a6e` | `dcede40a6e` | `dcede40a6e` | `dcede40a6e` | `dcede40a6e` |
| registry_conformance | `0d6e818f99` | `0d6e818f99` | `0d6e818f99` | `0d6e818f99` | `0d6e818f99` |
| registry_consumer | `39640b15a8` | `39640b15a8` | `39640b15a8` | `39640b15a8` | `39640b15a8` |
| registry_contract | `d50de54705` | `d50de54705` | `d50de54705` | `d50de54705` | `d50de54705` |
| registry_records | `cc64f25119` | `cc64f25119` | `cc64f25119` | `cc64f25119` | `cc64f25119` |
| registry_successor | `5954fcf8e8` | `5954fcf8e8` | `5954fcf8e8` | `5954fcf8e8` | `5954fcf8e8` |
| baseline | `ae1ee8755c` | `ae1ee8755c` | `ae1ee8755c` | `ae1ee8755c` | `ae1ee8755c` |

Consequence: no change to f1ab composition, the validators, the policy-identity module, the reason-code tables, the adapters, the conformance kit or the baseline LocalExecutionPolicy exists between `943ab18` and `2afbd8cd`. The only non-documentation, non-test file in the delta is `tools/verify_v09_candidate.py`. The `tests/` tree grew from 54 to 58 files (additions only: `test_contract_amendment_3_pins.py`, `test_contract_amendment_4_pins.py`, `test_v09_candidate_integrity.py`, `test_v09_post_merge_record.py`). Frozen contract files `r08-v2-contract.md`, `amendment-1.md`, `amendment-2.md` are byte-identical across the range (`git diff --quiet`).

## 4. Commits in the range

| Commit | Content |
|---|---|
| ae7b590 | docs(v03): cross-component baseline, sprint-status update and V04 handoff (PR #44 content) |
| b1def84 | Merge PR #44 v03-cross-component-baseline |
| 153a8f0 | docs(r08-v2): Amendment 3 - Runtime-side policy-narrowing containment at the effect boundary (V07 F-01) (PR #45 content) |
| a1169a0 | Merge PR #45 f01-contract-runtime-narrowing |
| d83899b | docs(r08-v2): DRAFT Amendment 4 - trusted authorization pin (V08 F-A1) (PR #46 content) |
| 8ce3b53 | docs(r08-v2): Amendment 4 rev 2 - strict revocation serialization; remove degraded fence mode (PR #46 review) |
| 1a4de32 | Merge PR #46 f-a1-authorization-pin-contract |
| ae20e43 | V09: freeze-candidate package (PR #47 content) |
| b695f67 | Merge PR #47 v09-freeze-candidate |
| 71202f8 | V09 post-merge: record PR #47 merge, reconcile sprint status, independent V07/V08 review assignments (PR #48 content) |
| dabe69e | Merge PR #48 v09-post-merge-reconciliation |
| 2a28303 | docs: add registry all-eligible-family migration static plan v1.0 (PR #49 content) |
| 317eb76 | Merge PR #49 planning/registry-family-migration-v1 (= the program pin 317eb76a…) |

## 5. Security-relevant classification

| Area asked in the directive | Code change | Text/test change in the range | Assessment |
|---|---|---|---|
| f1ab composition and narrowing | none | none | UNCHANGED. Registry behaviour that the 65 gaps describe is the behaviour at `943ab18`. |
| Institution and authority-domain validation | none | none | UNCHANGED. |
| Policy identity | none | Amendment 3 item 3: the Runtime guard recomputes the Registry effective-policy digest from the executor's five sets (uses the existing Registry function). | No Registry code change; a new Runtime obligation is written down. |
| Reason vocabulary | none (CODES 46, CODES_V2 48, CODES_V2_REV2 51 unchanged) | Amendment 3 maps containment failure to the existing `policy_identity_mismatch`; Amendment 4 DRAFT names existing typed codes (tests/test_contract_amendment_4_pins.py asserts no new reason code). | No vocabulary change. SEMANTIC REUSE of a code whose Amendment 1 6.1 definition is about a claim-carried identity member (gap E-23, PD-2). |
| Authorization pinning | none in the Registry | Amendment 4 (DRAFT rev 2, 274 lines), `docs/f-a1-authorization-pin/implementation-proposal.md`, `qualification-plan.md`, `tests/test_contract_amendment_4_pins.py`. | NEW NORMATIVE-DRAFT TEXT, NOT EFFECTIVE. Pin has 17 members and no policy sets (E-34). No independent pin-path closure claim (PD-4). |
| Runtime containment | none in the Registry | Amendment 3, EFFECTIVE on merge (PR #45): effect-time subset containment of the five F1a sets, fail-closed HOLD on a bad record payload, no dependence on the claim supplier; `tests/test_contract_amendment_3_pins.py`. | NEW NORMATIVE TEXT. First contract statement of the check that gaps E-21, E-22, E-26, F-01 and F-05 to F-18 concern. States itself 'not evidence that F-01 is closed'. |
| Negative-oracle applicability | n/a | V09 candidate package (manifest, gate matrix, assignments), v03 baseline, plan v1.0. | All 65 gaps remain applicable. E-21, E-22, E-23, E-26, E-33 to E-35 gain normative anchors (Amendments 3 and 4); no gap is closed by the range. |

**Changed security-relevant behaviour, stated explicitly:** none in code. Changed security-relevant *contract text*: Amendment 3 (effective) and Amendment 4 (DRAFT). The five Amendment 3 obligations are enforced by the Runtime, not by the Registry (the Registry stops at composition, crosswalk row 7).

## 6. Three baselines (not merged into one)

| Baseline | Definition | Registry | Runtime / Control Plane / SQ |
|---|---|---|---|
| (1) Historical tested baseline | What the existing tests were written and run against. Runtime tests hard-code `943ab18` (`tests/test_registry_f1a_narrowing.py` PIN; `test_m1_20` asserts HEAD equals it). The SQ suites pin their own component sets: V07 `{SQ_V07_PINS['registry'][:8]}` / `{SQ_V07_PINS['control_plane'][:8]}` / `{SQ_V07_PINS['runtime'][:8]}`; V08-FA1 `{SQ_V08_PINS['registry'][:8]}` / `{SQ_V08_PINS['control_plane'][:8]}` / `{SQ_V08_PINS['runtime'][:8]}`. | `943ab1831e39fadac1eb2a414ae322ccfa09bc6a`; also `a1169a05…`, `1a4de326…` | Runtime `4199a6c7…` (original V07), `ac247daf…`, `3873a61b…`; CP `1bee3696…`, `d66ae07f…` |
| (2) Current implementation baseline | The code the program recorded as current in G0/G1 (PR #51 package). | `317eb76acb2847c534c3ce7c2180b89b4aef987d` (code trees identical to every Registry pin above) | Runtime `0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491`; CP `d66ae07fa240510efdcc11ed4b3e1189dcefc822`; SQ `bb9b08904192b5f50a49e00ed8de0cab80fd7c19` |
| (3) Proposed independent qualification baseline (PROVISIONAL) | Where an independent oracle would be executed. Proposal only; ratification is the Architect's (PD-5, PD-7). | `317eb76acb2847c534c3ce7c2180b89b4aef987d` identified ALSO by the seven code tree hashes above, so a later docs-only Registry commit does not silently move it | Same Runtime, CP and SQ pins as (2). Runtime `3873a61b…` has an identical engine/host/sandbox/tests tree to `0dde0ef7…` (empty `git diff` over those paths). |

Runtime delta that matters for oracle applicability. `ac247daf..0dde0ef7` adds the authorization-pin installer (`host/authorization_pin/installer.py`), `engine/authorization_pin*.py`, an 11-line change to `engine/registry_selection_authority.py` and the pin tests. The V07 suite pins the earlier Runtime `ac247daf`: it runs per-set containment WITHOUT the pin and cannot evidence the pin path.

## 7. PD-5 determination (prepared for the Architect, not decided)

1. `943ab18` is a valid CODE baseline for every Registry-behaviour assertion: five commits share identical code trees.
2. `943ab18` is NOT a sufficient DOCUMENT baseline: Amendment 3 and the Amendment 4 draft appear only later. An oracle that cites them must cite a commit at or after `a1169a05` (Amendment 3) or `8ce3b53`/`1a4de32` (Amendment 4 rev 2).
3. Historical pins must not be replaced automatically. The hard-coded identity assertion in the Runtime test is a commit-identity check and would fail at `317eb76a` although behaviour is identical.
4. Recommendation (provisional): record baseline (3) by commit AND by the seven tree hashes; keep `943ab18` as the historical label; let the oracle's own manifest, not Runtime tests, assert identity.
