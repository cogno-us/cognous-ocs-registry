# 6. Ordered PR and sprint execution plan

Status: **planning labels, not authorized work.** Scope is approved (eight fields, atomic Route B only, rulings R1 to R14). **No PR below may begin until the Architect issues implementation authorization separately.** Each PR is one bounded owner increment and ends in a draft PR. There is **no blanket auto-merge** for any `EXT-` PR: each needs one substantive Copilot review, targeted remediation, Architect review where its change is substantive (eight-field scope, atomic-route boundary, authority ownership, ADR decisions), exact-head verification, green required checks, and a merge commit. PR identifiers use the prefix `EXT-` because S1..S6 collide with the historical sprints S01..S06. Evidence wording for everything produced: "developer-tested, Copilot-reviewed where reviewed, not independently qualified". `max_amount` has **no task in this plan** (R7).

**Card rule.** Every card states: (1) exact source pin; (2) affected fields or governing contracts; (3) files it may change (everything else is forbidden); (4) existing tests it must preserve; (5) new negative tests it must add; (6) required GitHub checks; (7) independent qualification dependency; (8) rollback and stop condition. **Re-pin rule:** a pin written here is the analysed baseline; before a card starts, its author re-records the exact current head of every repository it reads, re-reads the affected lines, and stops if a pinned fact changed. A card never starts against a moved head silently. Check names are in the repo checks table (appendix); names are derived from workflow files and the required-ness of each is unconfirmed until `EXT-S2-G`.

**Frozen sets (shared by cards; each card leaves them byte-identical unless it says so).** *Registry frozen set:* `registry_contract/`, `registry_consumer/`, `registry_records/`, `baseline/`, `registry_successor/{__init__,common,record,selection,verify,compose,decision}.py`, `tests/test_r08_*.py`, `tests/r08_support.py`, `tests/test_s0{1,3,4,5,6}_*.py`, `tests/s05_*`, `docs/r08-s01*`, `requirements-s01.lock.txt`. *Runtime preserved tests:* `test_valid_flow_byte_identity.py`, `test_atomic_route_valid_flow_identity.py`, `test_route_a_local_policy_reason.py`, `test_security_admission.py`, `test_r2_atomic_operation_identity.py`, `test_atomic_post_commit_fault_injection.py`, `test_atomic_post_commit_unresolved.py`, `test_crashed_holder.py`, `test_atomic_grant_status_and_envelope_binding.py`, `test_atomic_approval_status_terminality.py`, `test_atomic_approval_terminality_flow.py`, `test_public_runtime_surface.py`, with blob `engine/safe_executor.py` = `2fc880da` and no atomic test skipped for a missing Control Plane. *Control Plane preserved tests:* `test_local_authority_effect_profile.py`, `test_claim_journal_stage.py`, `test_decision_input_commitment_profile.py`, `test_bounded_authorization.py`, `test_freshness.py`, `test_reversibility.py`, `test_runtime_authority.py`, `test_holder_inventory.py`, `test_operation_identity.py`, `test_merge_record.py`.

## Final EXT implementation PR sequence

| Sprint | PRs, in dependency order |
|---|---|
| S1 registry | `EXT-S1-0` registry test CI; `S1-1` ADR; `S1-2` v2 skeleton; `S1-3` F1; `S1-4` F4/F5; `S1-5` identity and LD-02 map; `S1-6` snapshot floor; `S1-7` Ed25519 adapter (parallel); `S1-8` conformance kit (parallel); `S1-9` adversarial battery |
| S2 Runtime | `EXT-S2-G` required-checks confirmation (no code); `S2-1` characterization; `S2-2` narrowing adapter |
| S3 Control Plane | `S3-1` characterization; `S3-2` `age_bounds` helper and bounds table; `S3-3` F4 wiring; `S3-5` R6 cap (source change); `S3-4` F5 wiring and R5. `S3-6` constructor hardening is **optional**, outside the minimum |
| S4 claim-bound integration | `S4-0` ADR; **`S4-4` Control Plane claim binding (mandatory, first)**; **`S4-2` Runtime destination and validation (mandatory, second)**; `S4-3` emulator gate in the registry repo. `S4-1` is retired (absorbed into `S1-5`) |
| S5 independent qualification | `S5-1` predeclaration; `S5-2`; `S5-3`; `S5-4a`; `S5-4b`; `S5-4c`; `S5-5`; `S5-6` freeze and execution record; `S5-7..n` remediation (budget three); `S5-8` gap report |
| S6 closeout | `S6-1` RC pin freeze; `S6-2` full exact-pin run; `S6-3` retention; `S6-4` truthful status; `S6-5` traceability; `S6-6` operator handoff |

Twenty-two S1 to S4 PRs (including the non-code `S2-G`), nine S5 PRs and six S6 PRs, plus optional `S3-6` and budgeted remediation. No sprint beyond S1 to S6 is created.

---

## S1 Registry governance foundation (registry repo)

Design (all S1 code cards): `r08-v2` is a strict additive successor implemented in **new files only** (`registry_successor/v2_*.py`); the seven `r08-v1` files, all `tests/test_r08_*.py`, `tests/r08_support.py` and the two v1 docs stay byte-identical (blob-pinned by a new test). `CODES_V2` is the 46 v1 code strings plus exactly one new code, `trust_snapshot_version_stale` (47). Signing domain `ocs-reg/r08-v2/selection\n`. There are no stored goldens for `r08-v1` today, so `S1-2` creates them. The v1 integrity tests forbid some imports and scan helper names `_refuse`/`fail`/`_fail` against the 46-code set, so v2 modules use `refuse_v2`/`fail_v2` and a new `tests/test_r08v2_integrity.py` scans all five names against `CODES_V2` (stated openly, not a loophole). v2 reuses v1 primitives by import; the ten-layer logic is ported into `v2_verify.py` and a differential test proves the port equals v1 on the v1 corpus. Typed payloads: F1 `f1-local-policy-sets` (five sorted duplicate-free token lists, each at most 256 entries; empty list is explicit deny-all; absent key is `field_missing`; sixth key is `field_unknown`); F4 `f4-authorization-age-bounds` (`status_max_age_seconds`, `approval_max_age_seconds`, strict JSON integers within the `EXT-S3-2` bounds); F5 `f5-action-class-status-age` (non-empty `classes` map, at most 64 keys, strict integers). Composition per field is `min(caller, registry)`; an invalid caller value is `composition_caller_invalid` and is never replaced.

### EXT-S1-0 Registry test CI (CI only)
1. **Pin:** registry `d61ef729` (or current `main`); no source change.
2. **Governs:** the meaning of "required GitHub checks" for the registry (no `.github/` exists at the pin; the only observed check on PR #22 is `Analyze (python)`, which looks like CodeQL default setup, an inference).
3. **May change:** new `.github/workflows/registry-tests.yml` (pytest on the pinned Python, hash-locked install of the existing `requirements-s01.lock.txt` whose cited lock sources are also absent at the pin: the card either restores them or records the gap); nothing else.
4. **Preserve:** all existing tests unchanged and runnable.
5. **New negatives:** a deliberately failing test on a throwaway branch proves the check fails the PR (not merged); a check proves `tests/test_s06_integrity.py` is executed.
6. **Required checks:** the new `Registry tests / pytest` (name proposed) and `Analyze (python)`; the operator confirms they are required (`EXT-S2-G`).
7. **Qualification dependency:** none; builder only.
8. **Rollback/stop:** revert the workflow. Stop if the existing suite cannot run in CI without editing a frozen file, or the lock sources cannot be restored (record the gap and ask the Architect whether local-run evidence is accepted).
Estimate 1 to 1.5 days. Parallel; before the first registry code merge.

### EXT-S1-1 ADR: r08-v2 versioning and registry contract (docs only)
1. **Pin:** registry `d61ef729`; reads Runtime `c5e97e87` (blob `2fc880da`), Control Plane `7a4bcd40`, ADR-REG-TR01.
2. **Governs:** RT-F1a-01..03, RT-F1b-01..02, CP-F4-04, CP-F4-07, CP-F5-01; ledger `R08-V1-SUCCESSOR-FOUNDATION`, `FAILURE-REFUSAL-SEMANTICS`; DT-02, DT-03, DT-04; MC-03, MC-04, MC-06; LD-02 (pointer); rulings R1 to R14.
3. **May change:** new `docs/decisions/<date>-adr-r08-v2.md`, new `docs/r08-v2-contract.md`, and `docs/p1-extraction-plan/06` S1 rows only. Decides: the additive design; the 47-code set; signing domain; family ids; identity field list and digest profile; snapshot-version floor semantics; DT-03 naming map; required/optional behaviour per family; registry-side restore/rollback/custody conformance (R13); that `max_amount` is a deferred extension (no slot, no task); that the emulator host lives in the registry repo (R12). **Must not touch:** the frozen set, any code, `.github/`.
4. **Preserve:** everything (docs only); link check.
5. **New negatives:** review checklist only: no `max_amount` field/slot/task; no 5 s floor; no cross-bound; nothing called qualified.
6. **Required checks:** `Analyze (python)`; the registry test check once `S1-0` exists.
7. **Qualification dependency:** feeds QG-05/06/10/12 predeclaration as a spec; builder-authored; the independent author reads the ADR, never `tests/`.
8. **Rollback/stop:** revert. Stop if the Architect rejects it, it requires editing a frozen file, or it reopens a binding ruling. Estimate 2 to 3 days. First; serial.

### EXT-S1-2 r08-v2 skeleton: contract dispatch, family table, v1 freeze goldens
1. **Pin:** registry = `S1-1` merge; reads no other repo.
2. **Governs:** GAP-G2-01 (registry half), MC-06, R8, LD-02 (code set declared).
3. **May change (all new):** `registry_successor/v2_codes.py` (47 entries declared now), `v2_dispatch.py`, `v2_record.py`, `v2_selection.py`, `v2_compose.py`, `v2_verify.py`, `v2_decision.py`; `tests/test_r08v2_v1_freeze.py`, `test_r08v2_integrity.py`, `test_r08v2_dispatch.py`, `test_r08v2_differential.py`; `tests/golden/r08-v1/*.json`; `docs/r08-v2-implementation.md`. The production family table is empty (every family refuses); a test-only table registers the v1 three-set F1a for the differential. **Must not touch:** the frozen set.
4. **Preserve:** every `tests/test_r08_*.py` (190 definitions) including the four `test_r08_integrity.py` guards; spec-conformance and regression files; `test_s06_integrity.py`; S05 equivalence and expectations.
5. **New negatives:** blob pins of the seven v1 files, support file, tests and both docs; v1 corpus goldens replay identically; v2 refuses `r08-v1` record, selection and envelope (`contract_unsupported`) and v1 refuses `r08-v2`; a v1-domain signature does not verify under the v2 domain and vice versa; unregistered or case/whitespace-varied family is `family_unsupported` and a required operation never returns the caller; differential equals v1 on every re-sealed corpus input; `CODES_V2` is 47 with its first 46 equal to `common.CODES`; no forbidden import.
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-15 and QG-05; the freeze proof is builder evidence; the differential is not an oracle.
8. **Rollback/stop:** delete the new files and goldens (no v1 byte changed). Stop if any existing test fails, a frozen blob changes, a v1 golden differs, or the differential disagrees (a port bug: fix v2, never v1). Estimate 5 to 8 days; if more than 8, stop and report rather than split silently. After `S1-1`; serial.

### EXT-S1-3 F1 five-set family
1. **Pin:** registry = `S1-2` merge; reads Runtime `c5e97e87` (`safe_executor.py:413-423`).
2. **Governs:** RT-F1a-01..03, RT-F1b-01..02; C11, C02, D02, C18, TC-L06-009/011/013; V1-M1..M3.
3. **May change:** new `v2_family_f1.py`; one registration edit each in `v2_dispatch.py`, `v2_compose.py`, `v2_decision.py`; `tests/test_r08v2_f1.py`; `tests/golden/r08-v2/f1-*.json`; the contract doc's family section. **Must not touch:** the frozen set.
4. **Preserve:** the `S1-2` list; `test_r08_compose_decision.py` (the F1a reference semantics); S05 equivalence.
5. **New negatives:** each of five fields absent is `field_missing`; empty list per field is a valid deny-all (all 32 empty/non-empty combinations compose with exact `deny_all_fields`); a sixth key or an `allowed_max_amount` key is `field_unknown`; wildcard, unsorted, duplicate, 257 entries, non-string, control character refused; a caller missing one of five sets is `composition_caller_invalid`, never allow; property grid: effective is a subset of caller and of registry in every dimension; a required operation with a missing or invalid record never returns the caller; optional gives `overlay_not_applied` with the caller unchanged; deny-all constructs no policy (the registry imports no `engine`).
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-01 and QG-07; builder-only; the oracle is written without reading `tests/s05_oracle.py` or `test_r08v2_f1.py`.
8. **Rollback/stop:** revert; shape frozen for `S2-2` only after merge. Stop if composition ever returns a value outside the caller intersection or a payload shape differs from the ADR (a shape change after `S2-2` starts needs an ADR amendment). Estimate 3 to 4 days. After `S1-2`; serial with `S1-4`.

### EXT-S1-4 F4 and F5 families
1. **Pin:** registry = `S1-3` merge; reads Control Plane `7a4bcd40` (`bounded.py`, `runtime_authority.py:87`) and the **`EXT-S3-2` bounds table, which must be merged first**; no placeholder bound may merge.
2. **Governs:** CP-F4-04, CP-F4-07, CP-F5-01; R1, R2, R3; V1-C2, V1-C3.
3. **May change:** new `v2_family_f4.py`, `v2_family_f5.py`; registration edits in the three shared v2 files; `tests/test_r08v2_f4.py`, `test_r08v2_f5.py`; goldens; docs section. No import of Control Plane code. **Must not touch:** the frozen set.
4. **Preserve:** `S1-2` and `S1-3` lists.
5. **New negatives (per field and per class):** `"60"`, `60.0` (refused at load), `true`, `null`, `-1`, `0`, `lo-1`, `hi+1`, `2**53`, `10**30` refused with a stable code; absent is `field_missing`; third key is `field_unknown`; empty `classes` is `field_invalid`; 65 classes refused; registry less than, equal to, greater than caller (effective is the minimum and never exceeds the caller); an invalid caller value refuses and the registry value is not substituted; **no cross-bound between status and approval (R2: a combination valid per field but inverted is accepted)**; **no 5 s floor test (value 1 accepted if the bounds allow it)**; required refusal never yields the default 60 or the caller; optional returns the caller unchanged; the family never emits `applied_deny_all`.
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-03 and QG-04 at the oracle level; Control Plane behaviour is verified by the independent oracle in `S5-3`.
8. **Rollback/stop:** revert. Stop if the bounds table is not accepted (hold the PR, never guess), or any test shows a registry value exceeding the caller. Estimate 3 to 4 days.

### EXT-S1-5 EffectivePolicyIdentity, binding projection, LD-02 code-map adoption
1. **Pin:** registry = `S1-3`, `S1-4` and `EXT-S4-0` merged; reads the LD-02 map (`data/ld02-outcome-map.json` of this plan, ratified in the `S1-1` ADR).
2. **Governs:** MC-03, MC-04, LD-02, V1-M4 (registry half), R10, R11; **absorbs the retired `EXT-S4-1`**.
3. **May change:** new `registry_successor/v2_identity.py`; edits to `v2_verify.py` (report fields and snapshot fingerprint hook), `v2_decision.py`, `v2_codes.py` (disposition metadata only); new `docs/r08-v2/ld02-code-disposition.md`, `tests/test_r08v2_identity.py`, `tests/test_r08v2_code_disposition.py`. **Must not touch:** the frozen set.
4. **Preserve:** `S1-2` to `S1-4` lists; v1 `PolicyDecision`/`VerificationReport` unchanged (blob pin).
5. **New negatives:** the identity object carries exactly the members of the claim `policy_binding` ([04](04-component-ownership-and-adapter-matrix.md)) and a projection function produces the claim member; deterministic and key-order independent; every identity member changes the digest when mutated alone (**substituted policy identity**); a caller-policy change changes `caller_policy_digest`; different snapshot content with the same id/version gives a different fingerprint; identity populated on `applied` and `applied_deny_all`, `complete=false` on parsed refusals, absent on unparsable, never complete on a required refusal; **non-ASCII vector: registry digest versus the Control Plane `commitment` profile named in the ADR**; map completeness `set(map) == set(CODES_V2)` (47, none dropped or merged); no required-policy code maps to an authorizing disposition (R10); the injectivity test (distinct codes keep distinct cause fields).
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-06, QG-09, QG-10, QG-11; the oracle spec for identity is predeclared from the ADR.
8. **Rollback/stop:** revert (additive). Stop if an R11 identity member cannot be derived from verified inputs, or the map lacks any of the 47 codes. Estimate 4 to 6 days. Serial (shares `v2_verify.py`, `v2_decision.py`).

### EXT-S1-6 Snapshot-version floor, new code, snapshot builder
1. **Pin:** registry = `S1-5` merge.
2. **Governs:** DT-02, DT-04 (registry contract); R13 (registry-side vectors; the durable floor belongs to the enforcing component); revocation rollback.
3. **May change:** `v2_verify.py` (new input `min_trust_snapshot_version`, checked inside the trust layer), `v2_decision.py` (pass-through), new `v2_snapshot.py` (deterministic builder and canonical serializer with bounded lifetime and entry counts), `tests/test_r08v2_snapshot.py`, the contract doc. **Must not touch:** the frozen set; `TrustSnapshot` is reused unchanged.
4. **Preserve:** prior lists.
5. **New negatives:** version below the floor is `trust_snapshot_version_stale`; equal is accepted only for idempotent redelivery and equal-with-a-different-fingerprint is refused; a floor that is not an int, a bool, 0 or negative is refused; floor unset reproduces the `S1-5` corpus; an older snapshot omitting a revocation is refused (revocation rollback); an expired snapshot is reported before the version check; the builder rejects an over-long lifetime and unsorted, duplicate or oversize inputs.
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-05, QG-08, QG-16; builder-only; an independent security review is recommended (revocation).
8. **Rollback/stop:** revert (the new code is unreachable when the floor is unset). Stop if an older snapshot can pass. Estimate 2 to 3 days. Serial.

### EXT-S1-7 Ed25519 SignatureVerifier adapter (outside the core; R9)
1. **Pin:** registry `S1-1` merge.
2. **Governs:** R9 (B-10); V1-M5; GAP-G3-07 (explicitly not closed).
3. **May change (all new, outside `registry_successor/`):** `registry_adapters/ed25519_verifier.py`, `requirements-ed25519.lock.txt` (hash-locked, exact pins, one candidate library recorded in the PR), `tests/test_adapter_ed25519.py`, `tests/vectors/ed25519-synthetic.json`, `docs/adapters/ed25519.md`. Only synthetic keys labelled `SYNTHETIC-TEST-ONLY`; no operational root, ceremony or key distribution. **Must not touch:** the frozen set.
4. **Preserve:** `test_r08_integrity.py` (the adapter is outside the package), the FakeVerifier tests.
5. **New negatives:** RFC 8032 known-answer vectors pass; flipped bit in message, signature or key fails; wrong key; truncated or extended signature; all-zero key and signature; non-canonical S; small-order key; a v1-domain message does not verify as v2; wrong algorithm string; non-bytes inputs; a backend exception is caught and returns `False`; the dependency absent gives an explicit unavailable error and the core still returns `verifier_unavailable`; every pin has hashes.
6. **Required checks:** registry test check plus a hash-lock verification job; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-12, QG-05, QG-08; an independent security review requested.
8. **Rollback/stop:** delete the adapter, lock and vectors. Stop if a vector disagrees with RFC 8032, the library cannot be hash-locked on the CI platforms, or any non-synthetic key appears. Estimate 3 to 5 days. Parallel.

### EXT-S1-8 Consumer conformance kit (vectors, pure functions)
1. **Pin:** registry `S1-1` merge (extended after `S1-5`/`S1-6` if they land first).
2. **Governs:** DT-02, DT-04; QM-19, QM-22; R13 (the store and its durability belong to the enforcing component).
3. **May change (all new):** `registry_conformance/highwater.py` (pure `advance(state, observation)`, no I/O), `registry_conformance/vectors/*.json`, `tests/test_conformance_kit.py`, `docs/conformance/README.md`. Explicitly not an authoritative store.
4. **Preserve:** the `S1-2` list.
5. **New negatives:** equal, older and newer selection epoch per scope; revocation set monotonic and never cleared by restore; activation epoch; snapshot-version high-water; restart with state intact; **restore from a backup older than the last acknowledgement fails closed until acknowledged**; lost state yields unknown, not zero; torn write; concurrent writers; clock skew at the interval edge; rollback by an older snapshot; custody (state replaced by an older copy); verdicts `ACCEPT`, `REFUSE_STALE`, `UNKNOWN_FAIL_CLOSED`; the kit refuses malformed vectors.
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** feeds QG-05, QG-08, QG-09, QG-16 predeclaration; the vectors are handed to the Runtime and Control Plane owners.
8. **Rollback/stop:** delete the new directories. Stop if a vector requires the registry to hold state or contradicts ADR-REG-TR01 ownership. Estimate 4 to 6 days. Parallel.

### EXT-S1-9 Adversarial battery with the real verifier
1. **Pin:** registry = `S1-6` and `S1-7` merged.
2. **Governs:** V1-M5; QM-02, 04, 06, 07, 13, 14, 20, 22; R9, R11, R13.
3. **May change (new, tests only):** `tests/test_r08v2_adversarial.py`, `tests/vectors/adversarial/*.json` (synthetic keys), `docs/r08-v2/adversarial-battery.md`. A failing case is reported, not fixed here.
4. **Preserve:** all prior lists.
5. **New negatives (real Ed25519, v2 path, required and optional):** forged signature; altered statement with the original signature; altered record with re-computed digests; replayed older epoch; replay across tenant, consumer, operation, institution, domain; expired and not-yet-effective at exact boundaries; superseded without a chain; revoked selection; revoked key; key not in the snapshot; signer without exact authority; expired snapshot; snapshot below the floor; older snapshot hiding a revocation; wrong participation; unselected record pin; v1-signed document replayed as v2; unknown family; identity mismatch against the expected claim commitment.
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** handed to the independent oracle author; never labelled qualified.
8. **Rollback/stop:** delete the new tests. Stop and report (do not patch here) on any case accepted that should be refused. Estimate 4 to 6 days. Last in S1.

---

## S2 Runtime configuration adapter (Runtime repo; no edit to `engine/safe_executor.py`)

Adapter specification (for `S2-2`): module `engine/local_policy_narrowing.py` with one pure function `narrow_local_policy(caller_policy, effective_sets) -> NarrowingResult` (`outcome` in `NARROWED`, `DENY_ALL`, `REFUSED`; `policy`; `reason`; `empty_dimensions`; `narrowed_dimensions`). It refuses a caller that is not exactly a `LocalExecutionPolicy`; requires exactly the five keys; accepts only exact tuples (sorted, duplicate-free) or frozensets of non-empty `str`, with no coercion; requires every effective set to be a subset of the caller's (`widening_refused`); builds with `dataclasses.replace` so `__post_init__` re-runs and copies `allowed_target_prefixes`, `max_amount`, `max_effects`, `target_match` untouched; on any empty dimension returns `DENY_ALL` **with** the constructed deny-all policy (adapter contract, not constructor validation) and records the registry cause first; on refusal returns `policy=None` and never the caller policy; has no parameter that could carry an executor-supplied authority string (R11), no registry import, no I/O, no clock. The adapter has no route-specific code; its output is a drop-in `policy=` for either executor. **Only Route B is in the registry-mediated effect-time guarantee, and that guarantee comes from S4, not from S2.**

### EXT-S2-1 Runtime characterization battery (test-only)
1. **Pin:** Runtime `c5e97e87`; `safe_executor.py` blob `2fc880da`.
2. **Governs:** RT-F1a-01..03, RT-F1b-01..02; `check` order and reason texts; `__post_init__` set rules. `max_amount`, `max_effects`, targets appear only as **existing, untouched behaviour** (two pin tests, labelled "existing, untouched, not part of V1").
3. **May change (new only):** `tests/test_local_policy_characterization.py`, `tests/test_local_policy_characterization_expected.json`. **Must not touch:** `engine/`, `safe_executor.py`, existing tests, fixtures, `.github/`, `docs/`.
4. **Preserve:** the Runtime preserved tests plus `test_amount_binding_and_known_limits.py` and `test_adapter_forwarding.py`.
5. **New negatives/characterizations:** per-dimension denial per field per route with exact reason text and first-failure-wins order (Route A `observe`, Route A `execute_snapshot`, Route B with the claim left `issued` and no effect row); empty-set deny-all through all three call sites for each of the five fields; an omitted constructor argument gives `TypeError`; malformed sets (`set`, `list`, bare `str`, `frozenset({1})`, empty-string element) give `ValueError` naming the field; exact-string membership (no case folding, wildcard, prefix); `dataclasses.replace` leaves the original unchanged.
6. **Required checks:** `Workflow Sanity / no-tabs`; `Python safety boundary / Component-local checks`; `... / cross-component / safety-tests`.
7. **Qualification dependency:** the builder-authored baseline for QG-01; recorded "builder-authored, not independent"; the QG-01 oracle is written separately without reading these files.
8. **Rollback/stop:** revert. Stop if a new test fails at the pin (record the discrepancy, do not change source), if an existing test changes outcome, or if a test needs an `engine/` edit. Estimate 2.5 days. Parallel; merges before `S2-2`.

### EXT-S2-2 Narrowing adapter (new file)
1. **Pin:** Runtime `main` after `S2-1` (blob still `2fc880da`); input shape frozen by `EXT-S1-3`.
2. **Governs:** RT-F1a-01..03, RT-F1b-01..02; V1-M3. Out of scope: `max_amount`, `max_effects`, targets, selection identity and effect-time binding (`S4`).
3. **May change (new only):** `engine/local_policy_narrowing.py`, `tests/test_local_policy_narrowing.py`, `tests/test_local_policy_narrowing_route_flows.py`. **Must not touch:** `safe_executor.py`, `control_plane_adapter.py`, `atomic_local_control_plane_executor.py`, `local_authority_effect.py`, `engine/__init__.py`, existing tests, `.github/`.
4. **Preserve:** the `S2-1` list and files unchanged; `test_public_runtime_imports_without_test_modules` (the module imports without test modules or the registry).
5. **New negatives:** per-dimension denial through the adapter on Route A observe, Route A `execute_snapshot` and Route B, compared with the frozen `S2-1` expectations; empty set per field and all five empty gives `DENY_ALL`, never the caller policy; widening refused per field plus a grid over small universes; omitted deployed value fails closed; missing, extra, non-str or case-variant key, `max_amount` as a key, nested value, wrong value types, duplicate or unsorted tuples, empty-string element, `str` subclass: all `REFUSED`, no exception escapes; non-`LocalExecutionPolicy` callers (subclass, duck type, `None`, dict) refused; **Route A unchanged** (with the module imported but not called outcomes and bytes are identical; the blobs of `control_plane_adapter.py` and `safe_executor.py` are unchanged); the caller policy is not mutated; purity (no module state, I/O or registry import).
6. **Required checks:** the `S2-1` set plus `Durable refusal capture / cross-component / refusal (3.11)` and `(3.12)`. `Worker21`, `OpenAPPA` and `OpenShell` checks firing is the signal that a forbidden file was touched: stop.
7. **Qualification dependency:** feeds QG-01 and QG-07; differentials are builder-authored; the oracle runs them in `S5-2` against the merged candidate.
8. **Rollback/stop:** revert (additive, no caller in the repository). Stop if the blob of `safe_executor.py` differs, any existing test changes outcome, an executor or `engine/__init__.py` must be edited, a registry import is needed, or `S1-3` changes field names or the empty/absent rules. Estimate 3 days. Built in parallel against a fixture; merges after `S2-1` and `S1-3`.

### EXT-S2-G Required-checks confirmation (no code)
1. **Pin:** repository settings.
2. **Governs:** what "required GitHub checks" means for every card in all four repositories (required-check lists, rulesets and merge queues cannot be read from the clones).
3. **May change:** none; repository settings by the operator or Architect, evidence attached to the execution record (dated export of the ruleset).
4. **Preserve / 5. negatives:** none.
6. **Required checks:** n/a.
7. **Qualification dependency:** establishes that the delegated cross-component jobs (which run qualification suite revision `1c1755ff`, not `be1994a9`) are merge-blocking.
8. **Rollback/stop:** none. Stop merging if required checks cannot be confirmed; unknown is treated as not required. Estimate 0.25 operator days. Before the first merge.

---

## S3 Control Plane configuration adapter (Control Plane repo)

Header correction: S3 now contains **one Control Plane source change, `EXT-S3-5` (R6)**; the earlier "no edit to `bounded.py`" no longer holds for S3 and holds only for `S3-1` to `S3-4`. Ages and bounds are specified in [04](04-component-ownership-and-adapter-matrix.md).

### EXT-S3-1 Characterization (test-only)
1. **Pin:** Control Plane `7a4bcd40` (zero `src/` diff); optional Runtime test-only sibling at `c5e97e87` pinning what `control_plane_adapter.py:340-345` forwards.
2. **Governs:** CP-F4-04, CP-F4-07, CP-F5-01; MC-06 G2/G3 (input); R4.
3. **May change:** new `tests/test_age_bound_characterization.py` (Control Plane); new `tests/test_view_carries_age_bounds.py` (Runtime sibling).
4. **Preserve:** all tests; anchors `test_revocation_expiry_stale_status_and_policy_change_hold`, `test_stale_approval_identity_and_mandate_hold`, `test_future_resolver_timestamp_beyond_clock_tolerance_holds`, `test_status_age_at_dispatch_can_reach_twice_the_bound`, `test_input_anchored_deadline_refuses_a_status_that_was_old_at_opening`, `test_cache_age_bound_is_inclusive_and_stale_is_refused`.
5. **New characterizations:** boundary grid (bound-1, bound, bound+1; future within and beyond tolerance) for grant, conflict, policy, identity, mandate and approval, including the missing conflict and policy staleness tests; bound 0 behaviour; inclusive equality; `RA:341` negative age refused with no tolerance; `inf`/huge on the no-profile path disables staleness (pinned as a known limit); a huge int overflows in the freshness path; `observed_at` near year 9999 overflows before the future check; an extension never moves F4 outcomes; the dispatch deadline and 2x window; the cached-purpose bound; `AttemptJoin.class_max_age` records the base.
6. **Required checks:** `Tests / test (3.11)`, `Tests / test (3.12)`, `Tests / manifest-validator-parity`; Runtime sibling: the Runtime `S2-1` set.
7. **Qualification dependency:** none to merge (builder-authored, labelled so); expected values frozen before `S3-2`..`S3-5` so the QG-03/04 oracle author can reuse them.
8. **Rollback/stop:** revert the test files. Stop if a test fails at the pin (the pin or the analysis is wrong) or needs a `src/` edit. Estimate 3 to 4 days. Parallel.

### EXT-S3-2 `age_bounds` helper and bounds table (pure, no wiring)
1. **Pin:** `S3-1` merge on the `7a4bcd40` lineage.
2. **Governs:** CP-F4-04, CP-F4-07, CP-F5-01; R1, R2, R3.
3. **May change:** new `src/agent_control_plane/age_bounds.py` (with the code-owned `AGE_MIN`, `AGE_MAX` table that `S1-4` consumes); new `tests/test_age_bounds.py`. No existing file; nothing imports it.
4. **Preserve:** the full existing suite.
5. **New negatives:** the strict grid for caller and registry (`bool`, `float` including `60.0`/`nan`/`inf`, `None`, `str`, `Decimal`, int subclass, `0`, `-1`, `AGE_MAX+1`, `10**30`, `2**53`, `2**53+1`); caller-first order (an invalid caller with a valid registry value refuses, never the registry value); registry greater than caller gives the caller and `registry_value_not_narrowing`; equal; `min` over a grid; no cross-field coupling; a host floor never lowers; `clock_tolerance_seconds` negative, bool or float refused; required and invalid gives HOLD with the caller value not returned; inputs not mutated.
6. **Required checks:** Control Plane `Tests` set.
7. **Qualification dependency:** the oracle spec for the grid is predeclared by the independent author before the PR result is shown (`S5-1`/`S5-3`); a builder grid does not count.
8. **Rollback/stop:** revert two files. Stop if the helper must coerce anything, or an owner survey shows `AGE_MAX` below an in-use host value (raise the constant by ruling, not silently). Estimate 3 to 4 days.

### EXT-S3-3 F4 wiring
1. **Pin:** `S3-2` merge; Runtime `c5e97e87`; merges after `EXT-S1-4`.
2. **Governs:** CP-F4-04, CP-F4-07; V1-C2; R1, R2.
3. **May change:** new `src/agent_control_plane/host_age_policy.py` (factory returning the kwargs for `BoundedAuthorizationWorkflow`); new `tests/test_host_age_policy.py`. **Not** `bounded.py`.
4. **Preserve:** the `S3-1` grid; approval-binding block tests; single-effect gate tests; approval tests in `test_runtime_authority.py`.
5. **New negatives:** absent registry input gives a byte-identical `BoundedRunRecord`; narrowed refuses earlier, never later (bound-1, bound, bound+1 for all four F4 consumers); required and invalid never returns the caller value; an invalid caller refuses before construction; the Runtime per-call view receives the narrowed values; grant, operation, policy and independence checks unchanged; no approval is invalidated by F4 narrowing.
6. **Required checks:** Control Plane `Tests` set.
7. **Qualification dependency:** QG-03 run by the independent author on the exact head; `S3-3` is not "qualified" until then.
8. **Rollback/stop:** revert; hosts keep their literal kwargs. Stop if an existing record changes byte-wise with no registry input, or narrowing needs a new constructor kwarg (the view will not forward it). Estimate 2 to 3 days.

### EXT-S3-5 R6 extension cap (Control Plane source change)
1. **Pin:** `S3-1` merge (parallel with `S3-3`; must precede `S3-4`).
2. **Governs:** R6; CP-F5-01; extension rows in `freshness.py:130-201`.
3. **May change:** `src/agent_control_plane/runtime_authority.py` (`ActionClass` flag, default false and omitted from dumps while unset; reason-code list), `freshness.py` (`extension_defects` input and the new code constant), `bounded.py` (`_class_age_bound`, `record_age_extension`, recorder passthrough only), the reason-registry file if it lives elsewhere; new `tests/test_age_extension_cap.py`. Owner approval for this `src/` change is a precondition (authority-path edit; reserve an additional independent technical review).
4. **Preserve:** the extension tests in `test_freshness.py` (record, refusal, signer, re-check at use, window, limit measured from the trusted base, laundering), the extension tests in `test_reversibility.py`, `test_every_emitted_reason_code_is_in_the_versioned_registry`, `test_code_split_produces_vocabulary_change_row`, default-dump key-set tests.
5. **New negatives:** an un-narrowed class with a valid signed extension is raised exactly as before; a capped class with a valid signed `from=N, to=N+k` is refused with `age_extension_registry_capped` (refusal row persisted, bound still `N`, deadline `opened+N`, no extension id, grant status at age `N+1` refused); the same row injected directly into the store is ignored (defence in depth); a pre-narrowing row `from=C` is `age_extension_invalid`; `E > C-N` and `to > C` leave the bound at `N`, never above `C`; a second un-narrowed class in the same profile is still extendable; capped plus irreversible gives both defects; the cached-purpose path receives `N`; a property grid over `(N, k)` (`effective <= N` when capped); default-profile dump bytes unchanged and setting the flag changes `approval_commitment`; F4 outcomes never change under an extension. **Mutation legs:** dropping the `_class_age_bound` branch fails the injection test; dropping the record-time refusal fails the refusal-row test.
6. **Required checks:** Control Plane `Tests` set plus `O6 P1B durable refusal / scoped-qualification` (touches `bounded.py`).
7. **Qualification dependency:** NX-11 / QG-03 independent mutation leg (`S5-3`).
8. **Rollback/stop:** revert (flag absent keeps dumps byte-identical). Stop if default-profile dumps or any existing commitment changes, the cap affects an un-narrowed class, or the design needs a new workflow kwarg. Estimate 4 to 6 days. Serial on Control Plane shared files.

### EXT-S3-4 F5 wiring including R5
1. **Pin:** `S3-3` and `S3-5` merge heads.
2. **Governs:** CP-F5-01; C01; V1-C3; R5, R6, W8-014.
3. **May change:** `host_age_policy.py` (adds `build_effective_profile` and the read-only `incompatible_approvals` pre-flight); `tests/test_effective_profile_binding.py`. No change to `approval_commitment` or the check at `runtime_authority.py:268-271`.
4. **Preserve:** `test_profile_is_part_of_the_approval_commitment`, the mismatch test and helper in `test_runtime_authority.py`, `test_holder_inventory.py`, `test_operation_identity.py`, the freshness extension tests, the default-dump key-set tests.
5. **New negatives:** an approval issued under the caller profile against the narrowed profile gives `runtime_authority_approval_mismatch` with no effect; an effective-profile approval passes; one good plus one stale approval mismatches; F4-only narrowing leaves approvals valid; the R6 flag toggles the commitment; the pre-flight lists exactly the stale approvals; narrowing withdrawn does not revive an old approval (NX-12); the dispatch deadline and cached-purpose bound shorten; `AttemptJoin.class_max_age` records the narrowed value; a class is flagged only when `narrowed`; the caller profile object is not mutated; the Runtime view carries the flag through the profile.
6. **Required checks:** Control Plane `Tests` set.
7. **Qualification dependency:** QG-04 and the approval-mismatch battery (`S5-3`), independent.
8. **Rollback/stop:** revert; hosts use the caller profile. Stop if approvals issued under the effective profile fail at the pin, or narrowing is applied after issuance in any fixture without the pre-flight reporting it. Estimate 3 to 4 days.

### EXT-S3-6 (optional, owner approval) Constructor hardening
1. **Pin:** after `S3-5` and `S4-4`. 2. **Governs:** CP-F4-04/07, clock tolerance, R3. 3. **May change:** `bounded.py` `__init__` using `age_bounds`; `ActionClass` strict `ge=1` only if the owner accepts the default-path change; optionally reorder the anchor append after the future check at `bounded.py:2017-2024`; new `tests/test_constructor_age_validation.py`. 4. **Preserve:** everything in `S3-1`; every test that builds a class at 60. 5. **New negatives:** every rejected type at the constructor and at `ActionClass`; negative tolerance; overflow raises a typed refusal, not `OverflowError`; a year-9999 `observed_at` refuses and never crashes. 6. **Checks:** Control Plane set plus the durable-refusal scoped check. 7. **Qualification:** independent grid rerun; an explicit default-path change for invalid inputs, labelled. 8. **Rollback/stop:** revert; must not ride with `S3-3` or `S3-4`; stop if any valid existing configuration is rejected. Outside the minimum; 3 to 4 days if approved.

---

## S4 Claim-bound cross-component integration

### EXT-S4-0 Integration ADR (docs only, registry repo)
1. **Pin:** registry `S1-1` merge; Runtime `c5e97e87`; Control Plane `7a4bcd40`; blob `2fc880da`.
2. **Governs:** F1a/F1b five sets; R10-F-01/02/03; LD-02, LD-03, LD-09; DT-01..07; ADR-REG-TR01; R11 to R14.
3. **May change:** new `docs/decisions/<date>-adr-ext-s4-claim-carried-policy-binding.md`; `docs/p1-extraction-plan/04,05,06` rows for S4 only. Freezes: the binding schema and member names, the successor claim profile URN, the one digest profile (with a non-ASCII vector), the closed code list, the tenant and operation mapping, digest-only versus carrying the sets in the claim (roughly up to 160 KB per claim if sets are carried), whether H-1 is in V1, the stale-sync disposition (so NX-03/04/08 have dispositions), and the structured carrier for the registry cause.
4. **Preserve:** docs gate only. 5. **New negatives:** a review checklist: each negative control NX-01..NX-12 has a named acceptance row.
6. **Required checks:** `Analyze (python)`; registry test check.
7. **Qualification dependency:** none; the independent author predeclares from this ADR (`S5-1`).
8. **Rollback/stop:** revert. Stop if the Architect does not adopt mandatory Control Plane carriage or the digest profile. Estimate 3 to 4 days.

### EXT-S4-4 Control Plane claim binding (mandatory; lands first)
1. **Pin:** Control Plane `7a4bcd40` (re-pin to the head after any merged `S3` source PR).
2. **Governs:** claim profile and commitment; `provision_local_execution_claim` and `materialize_local_execution_claim` signatures; claim interval clamp; R11. Decision 3 of the ADR (F4/F5) is unchanged.
3. **May change:** `src/agent_control_plane/local_authority_effect.py`; new `tests/test_policy_binding_claim.py`; a docs line for the profile. If it adds a profile member it joins the Control Plane shared-file queue.
4. **Preserve:** Control Plane tests `test_local_authority_effect_profile.py` (including tampered-claim, requested-expiry and handoff-provisioning tests), `test_claim_journal_stage.py`, `test_decision_input_commitment_profile.py`, `test_bounded_authorization.py`; baseline claim bytes identical.
5. **New negatives:** **forged binding** (altered member with a stale commitment; relabelled baseline profile with a binding key; successor profile without a binding); **substituted identity at issuance**; a binding with `valid_until <= now`; the clamp cannot extend the grant; a non-tenant claim with a binding is refused; changed authority between resolve and provisioning is still refused; the binding is not visible in `policy_state` or `authority_state`; a probe in `tools/adversarial_mutations.py` for removal of the binding verification branch (the tool's contents are UNVERIFIED and must be read first).
6. **Required checks:** Control Plane `Tests` set.
7. **Qualification dependency:** QG-09/QG-12 claim-forgery cases (`S5-4b`, `S5-5`).
8. **Rollback/stop:** additive and inert when the kwarg is `None`; revert. Stop if baseline claim bytes change. Estimate 6 to 9 days.

### EXT-S4-2 Runtime policy-bound destination and validation (mandatory; lands second)
1. **Pin:** Runtime `c5e97e87`; Control Plane at the `S4-4` merge commit.
2. **Governs:** F1a/F1b enforcement at the atomic commit; every R11 check; R13 state; the `execute_claim_atomic`, `provision_claim` and `_claim_model` hooks.
3. **May change:** `engine/local_authority_effect.py` (inert hooks only), `engine/atomic_local_control_plane_executor.py` (opt-in `policy_binding`, `provision_claim` passthrough), new `engine/policy_bound_atomic_destination.py` and `engine/policy_binding.py`, new tests, `docs/local-authority-effect-profile.md`. **Never** `engine/safe_executor.py`.
4. **Preserve:** the Runtime preserved tests (all six `test_r2_atomic_operation_identity.py` tests and the post-commit and crashed-holder tests included); none skipped for a missing Control Plane; blob `2fc880da`.
5. **New negatives:** **forged claim/policy binding** (a recomputed commitment over an altered binding; an altered stored `claim_json`); **substituted policy identity** (each tuple member); **expired selection** at the lock with the barrier; **revoked selection**; **stale activation epoch**; **mismatched grant and approval** (revoked grant with a valid binding, valid grant with a revoked selection: neither suffices); **changed policy after authorization** (a new epoch activated between check and commit via `_transaction_stage`); **revocation before effect commit** (and after commit: no rollback); **restore and rollback** (restored DB, floor and log-head mismatch); **required-policy failure** (no binding, absent row, withdrawn row: never a baseline fallback); the seeding hazard (a row deleted then re-provision must not seed); a forged or omitted executor digest; the base destination has no tables; no registry call or socket inside a transaction; every new check mutation must fail a test.
6. **Required checks:** the Runtime set including `Worker21 local authority-effect profile / cross-component` (path match).
7. **Qualification dependency:** QG-08/09/16 batteries by a designated lead (none designated).
8. **Rollback/stop:** inert by default; revert. Stop if a preserved test changes bytes, `safe_executor.py` would need an edit, or tests skip for lack of the Control Plane. Estimate 10 to 15 days. Serial on the two shared Runtime files; after `S4-4`.

### EXT-S4-3 Emulator integration gate (registry repo; R12)
1. **Pin:** registry head; the exact merge commits of Runtime and Control Plane; the evaluator blob.
2. **Governs:** gate verify, bind, activate, sync, deny-all, claim issuance, executor mode; required versus optional; V1-M4..M6.
3. **May change:** new `registry_integration/` and its tests only; no Runtime or Control Plane file; not the qualification repo. Modelled on the qualification-repo synthetic host so the independent oracle does not test its own fixture.
4. **Preserve:** all `tests/test_r08_*.py`; the Runtime and Control Plane preserved lists run unmodified in the same job.
5. **New negatives:** the ten negative controls end to end on Route B; deny-all constructs no policy; an optional refusal reports "overlay not applied"; no registry import in Runtime or Control Plane; no network inside a transaction (patched socket); sync lag does not override the commit-time row; a restart before the first sync refuses required scopes.
6. **Required checks:** registry test check; `Analyze (python)`.
7. **Qualification dependency:** hands the oracle spec to the qualification repo; never self-labelled qualified.
8. **Rollback/stop:** revert. Stop if the host needs a Runtime or Control Plane edit. Estimate 6 to 9 days. After `S1-5`, `S1-6`, `S1-7`, `S2-2`, `S4-2` and `S3-4`.

---

## S5 Independent qualification and remediation (qualification repo)

Conventions: paths DOCS `docs/release-gate/p1-config-extraction/`, PROC `process/p1-config-extraction/`, SUITE `suites/p1-config-extraction/`, WF `.github/workflows/p1-config-extraction.yml`, RES `results/p1-config-extraction/` are **proposed** (none exists; confirm at `S5-1`). Existing suites, `process/mvp-chain/*`, `scenarios/` are never edited; no known-limit test is moved or deleted. Pin for every card: **candidate pin TBD at the `S5-6` freeze**; the current source pins are characterization pins only. Required checks for every card: `Catalog validation / validate`, `Qualification dashboard build / validate-and-build`, `Cross-component migration integrity / integrity` (paths under `suites/`), and the new WF from `S5-2`. Rollback for every card: revert the PR (docs, suites and process only; no source repository is touched). Estimates are author-days excluding lead review. **All S5 and S6 work is PREPARE-only until an independent lead is designated** ([07](07-independent-qualification-matrix.md)): outputs are labelled "builder-side inspection; Tier 1 not qualified".

- **EXT-S5-1 Predeclaration and PREPARE record** (3 days). Gate QG-14. Files: DOCS predeclaration, gate matrix v2, run protocol; PROC placeholders; the preregistration test (digest check). Preserve the release-gate inventory and preregistration tests. Negatives: a test failing if any file claims "qualified" or a verdict without a designation record; QG-02 must read DEFERRED. Dependency: independent oracle author. Stop: the eight-field V1 or any ruling is not recorded.
- **EXT-S5-2 QG-01 and QG-07** (6 days). Files: SUITE `test_qg01_*.py`, `test_qg07_*.py`, oracle, PROC expectations, WF. Preserve `test_scn_c11.py`, S05/S01 builder tests (read-only). Negatives: caller x registry grid, omitted deployed value, exact-string membership, check order and reason text, F1b trusted-context independence, caller unmodified, a widen mutation per field, containment over larger universes; Route B only. Dependency: blind oracle author; needs `S1-3`, `S2-2`. Stop: any expectation edited after a result is seen.
- **EXT-S5-3 QG-03 and QG-04 (QG-02 deferred stub)** (7 days). Files: SUITE `test_qg03_*`, `test_qg04_*`, `test_clk_f4.py`, PROC, DOCS `qg02-deferred.md` (preserved text, no tests). Negatives: boundary grid, R1 min grid, strict-int grid, per-field bounds read from source, no cross-bound, no 5 s floor assertion, NX-11, NX-12, mutation legs. Dependency: `S3-2..S3-5`, a lead. Stop: a bound read from source disagrees with the ADR (BLOCKED, not waived).
- **EXT-S5-4a QG-05, QG-06, QG-15** (7 days). Files: SUITE `test_qg05_*`, `test_qg06_*`, `test_qg15_*`, a synthetic-key helper, PROC. Preserve all `tests/test_r08_*.py`, S05, S06 integrity, TC-L05-013 (NOT_RUN kept). Negatives: NX-05, NX-10, forged/altered/wrong-key/key-revoked under the real verifier, 47-code completeness, v1 golden byte-identity, v2-only fields refused by v1. QS13 is held for lead re-adjudication. Stop: any `r08-v1` golden diff.
- **EXT-S5-4b QG-08, QG-09, QG-10 and LIM-A1** (10 days). Files: SUITE `test_qg08_*`, `test_qg09_*`, `test_qg10_*`, `test_lim_a1_route_a_documented.py`, a host driver that imports none of the registry host's code, PROC, WF. Preserve the worker21 tests, `test_local_authority_effect.py`, the pinned-executor and paired-request positive controls, `test_ruling4_lost_ack.py`, the C07/D07 limits. Negatives: NX-01 (a)-(h), NX-02, NX-03, NX-04, NX-06, NX-07, NX-08 with mutation legs, repeated runs and raw logs; LIM-A1 limit assertions. Dependency: `S4-0`, `S4-4`, `S4-2`, `S4-3`, a lead. Stop: nothing to execute until S4 code exists (BLOCKED, never PASS by analogy); any test named as Route A protection is rejected.
- **EXT-S5-4c QG-16 durability, recovery, rollback, custody** (6 days). Files: SUITE `test_qg16_*`, PROC. Preserve `test_process_termination_transaction_boundaries`, NC2/NC6 rows. Negatives: NX-09, crash at each stage, lost high-water state, snapshot custody (unreadable, truncated, symlink, foreign owner), destination unavailable, repeated runs. Dependency: lead; `S4-2` tables. Stop: no durable state yet means BLOCKED.
- **EXT-S5-5 QG-11 and QG-12** (6 days). Files: SUITE `test_qg11_*`, `test_qg12_*`, PROC. Preserve `test_evidence_substitution_or_loss_is_rejected`, C03/C04/C12/C13/D08, the adversarial tests, KNOWN_GAP rows. Negatives: identity, epoch and expiry in evidence; substituted or omitted identity refused with an accepted differential; forged binding family; manifest and pin substitution; symlink, FIFO, oversize; confused deputy; dropped fields; a mutation leg for every NX control; the `safe_executor.py` blob check. Dependency: an evidence reviewer other than author, builder and runner, else "not performed". Stop: loaded-code replacement (LIM-1) is disclosed, never claimed.
- **EXT-S5-6 Freeze and execution record** (5 days). Files: PROC `freeze.proposed.json` (digest of every expectation, candidate SHAs, blob), RES (raw logs, junit, collected-test lists, `SHA256SUMS`, repetitions), DOCS report. Preserve every retained test with its failures, skips, XFAIL and NOT RUN; the 11 undeclared known-limit tests are declared first (owner action). Negatives: freeze-before-execution check; digest mismatch test. Dependency: the designated lead only; in PREPARE this card produces only a builder-side inspection record.
- **EXT-S5-7..n Remediation** (3 days each, budget three). One builder fix per PR in the owning repository; this repository changes only the candidate pin and re-runs the affected gates with unchanged expectations and a new RES folder. Stop: two rounds on one gate escalates to the operator.
- **EXT-S5-8 Gap report** (3 days). DOCS only: open BLOCKED gates, LIM-A1, deferred QG-02, GAP-G4-01..13 status. Stop: any wording that softens "NOT INDEPENDENTLY QUALIFIED".

## S6 Release-candidate evidence and closeout (qualification repo; docs, process, results only)

Same conventions as S5. **EXT-S6-1** RC pin freeze (2 days; exact heads, component-lock hash; any head change reopens affected gates; negative: pin/lock-hash mismatch refusal test). **EXT-S6-2** full exact-pin run (5 days; all existing suites and limit listings preserved; a failing applicable test blocks; reclassification is recorded before the result is seen). **EXT-S6-3** evidence retention (2 days; negative: retention-index completeness test). **EXT-S6-4** truthful status report (2 days; "Tier 1: INDEPENDENTLY QUALIFIED by <lead> at <pins>" only if designated and executed, else "NOT INDEPENDENTLY QUALIFIED; builder-tested; Copilot-reviewed"; Route B only, Route A and `max_amount` stated as excluded or deferred; negative: a test rejecting forbidden phrases; operator adjudication). **EXT-S6-5** traceability closeout (3 days; R1..R14 and GAP-G4-01..13 mapped; stop if any ruling has no gate). **EXT-S6-6** operator handoff (1 day). Release, publication and production remain with the operator and are never inferred.

---

## Effort and critical path (judgement, not measured)

| Sprint | Engineer or author days | Main uncertainty |
|---|---|---|
| S1 registry | 31 to 46 | `r08-v2` new-file surface and port drift; Ed25519 hash-lock; registry CI creation |
| S2 Runtime | 5 to 8 | Characterization coverage for institution/domain/adapter that does not exist at the pin |
| S3 Control Plane | 15 to 21 (optional `S3-6`: +3 to 4) | `AGE_MAX` survey; R6 vocabulary change; F5 approval coupling |
| S4 integration | 25 to 37 | New durable Runtime state and custody; the Control Plane claim change moves both heads; digest-profile hazard |
| **Builder subtotal S1 to S4** | **76 to 112** | |
| S5 independent qualification | 53 (plus up to 9 remediation) | No lead designated; oracle independence; race and clock gates need repetition |
| S6 closeout | 15 | Any head change reopens gates |
| **Total** | **144 to 189** | Supersedes the earlier 58 to 93, which assumed conditional claim carriage, no R6 source change, no `r08-v2` surface and a smaller S5/S6; `max_amount` adds nothing (deferred) |

Estimates exclude operator and lead scheduling latency and assume the PR cards run as specified with one substantive review each. **Critical path:** `S1-1`, `S4-0`, `S4-4`, `S4-2` (about 21 to 31 days) in parallel with `S1-2`..`S1-5` (about 16 to 24 days after `S1-1`, with `S3-2` before `S1-4`) meeting at `S4-3` (6 to 9 days), then `S1-9` and `S5-4b`/`S5-6`, then `S6`. With three builders and one independent author the minimum calendar time is roughly 12 to 16 weeks; with no designated lead the qualification part cannot close and the candidate reads "NOT INDEPENDENTLY QUALIFIED".

## Review and merge discipline

Bounded owner increments only; one substantive Copilot review per PR (comment-only; cited as "Copilot-reviewed", never "qualified"; it is not evidence review or qualification); targeted remediation; Architect review for any change to the eight-field scope, the atomic-route boundary, authority ownership or an ADR decision; reserve additional independent technical review for code affecting authority, activation, canonical state or external effects (`S1-6`, `S1-7`, `S3-5`, `S4-2`, `S4-3`, `S4-4`); exact-head verification; green required checks; merge commits only. **No blanket auto-merge** applies to any `EXT-` PR; each merge needs its own authorization. A new issue is a V1 blocker only if it violates an approved scenario, a mandatory security boundary or an explicit gate; otherwise it is marked DEFERRED with owner and impact.

## Appendix: repo checks table

Required-check lists, rulesets and merge queues **cannot be read from the clones** and no API access to the Runtime, Control Plane or qualification repositories was available; names marked `~` are derived from workflow file text, not observed on a live PR. `EXT-S2-G` confirms which are required.

| Repo (pin) | Checks (displayed name) | When it runs |
|---|---|---|
| Registry (`d61ef729`) | No in-tree workflows. Observed on PR #22: `Analyze (python)` (CodeQL default setup is an inference). After `S1-0`: `Registry tests / pytest` (name proposed) | Registry tests run in no GitHub check before `S1-0` |
| Runtime (`c5e97e87`) | `Workflow Sanity / no-tabs` ~ (every PR); `Python safety boundary / Component-local checks` ~ and `... / cross-component / safety-tests` ~ (PRs on `engine/**`, `tests/**` and listed docs; a `docs/p1-extraction-plan/**` PR does not trigger them); `Durable refusal capture / cross-component / refusal (3.11)` and `(3.12)` ~ (any `engine/**` file); `Worker21 local authority-effect profile / cross-component` ~ (only if the PR touches `local_authority_effect.py`, the atomic executor, `local_authority_effect_recovery.py`, `safe_executor.py`, `refund_intent.py`, five named tests or two docs); `OpenAPPA ... / cross-component` ~ and `OpenShell ... / cross-component` ~ (fire on `safe_executor.py` or `control_plane_adapter.py`: seeing them on an `S2` PR means a forbidden file was touched) | Delegated jobs run the qualification suite revision `1c1755ff` at the PR head, not `be1994a9` |
| Control Plane (`7a4bcd40`) | `Tests / test (3.11)`, `Tests / test (3.12)`, `Tests / manifest-validator-parity` ~ (every PR; runs `pytest` and `tools/adversarial_mutations.py`); `O6 P1B durable refusal / scoped-qualification` ~ (only if `bounded.py` is touched) | |
| Qualification (`be1994a9`) | `Catalog validation / validate` ~ and `Qualification dashboard build / validate-and-build` ~ (every PR); `Cross-component migration integrity / integrity` ~ (PRs under `suites/**`, `migrations/**`); the new `p1-config-extraction` workflow from `S5-2` | A docs-only qualification PR runs the first two only |

Registry tests and the Runtime atomic tests have a known evidence hazard: Runtime CI skips the atomic tests when `agent_control_plane` is not on the path, so a green Runtime check is **not** evidence by itself; every card that preserves those tests requires a non-skipped run at an exact Control Plane pin.
