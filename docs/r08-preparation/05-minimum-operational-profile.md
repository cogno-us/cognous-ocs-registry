# R08-PREP Lane E: Candidate Minimum Supported Operational Profile (MSOP), options and recommendation

Purpose: propose the smallest credible operational profile (v1.2 §3.4) that would demonstrate a real working OCS registry, compare three scope options by which v1.2 §1 functions each exercises, and frame the operator decision. This lane designs no authentication (Lane B), lifecycle (Lane A), integration (Lane C), consistency (Lane D) or qualification (Lane F); it names them as expected inputs.

**Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.**

## 1. Sources and revisions examined

| Source | Revision |
|---|---|
| Registry repo `main` (read from the repository checkout) | `eb850c8d303961d099a123534121aeac280b242b` (verified by rev-parse) |
| Plan v1.2 §1, §2, §3.1-3.4, R07-R11, §7; crosswalk A1-A10 | blobs `32319775...`, `a53a5b31...` (not re-hashed here; paths as brief) |
| `docs/s03-contract.md`, `s04-implementation.md`, `trust-limitations.md`, `s02-inventory.md` §3-§7, `s06-next-family-recommendation.md`, `source-provenance.md` | at `eb850c8` |
| PR #17 `docs/registry-schema-analysis/` 04, 06, 08 (D1-D13, V1-V9), 09 | head `bdfb2b7268690d9406cc1de257dc6feede0fdb5a` |
| Execution Runtime clone | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (rev-parse verified). `engine/safe_executor.py` blob at clone head is `2fc880dae37eac76e5074533435740ce0684209d`, equal to the S01/S03 pin at `ec728da6` (also stated in source-provenance.md line 14) |
| Control Plane clone | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c`; grep only for `LocalExecutionPolicy` |
| Constitution | `1c2e920f...`, CA14, CA18, CA05 and the Tier table read in `ENGINEERING_CONSTITUTION.md` |

Not inspected: `COG-REG-SHARED-ADD-01` (unavailable; cited only through plan v1.2 and crosswalk); PR #13; PR #17 docs 02, 03, 05, 07 beyond what 04/06/08/09 state; GCR review documents; other lanes' outputs; the full S05 raw evidence; Control Plane `bounded.py`/`freshness.py`/`runtime_authority.py` internals; the older Control Plane pin `0a41faa9`. The S01/S02 Runtime pin `ec728da6` was not fetched; the equality of the safe_executor blob rests on source-provenance.md plus the identical blob at the clone head.

## 2. Findings from source

1. **[EXISTING]** S03 validator covers exactly one record type, `local-execution-allowlist`, supplying `allowed_units`, `allowed_adapters`, `allowed_actions` (`s03-contract.md` §1, §3). Each list must be non-empty; empty records are refused (§3). `status` lives inside the record (`active` only accepted) and `non_authorizing` must be `true`.
2. **[EXISTING]** S04 `apply_registry_overlay(caller_policy, trust, manifest_path, record_path)` computes `effective = caller ∩ registry` for those three fields only; every refusal returns the caller policy object unchanged (`s04-implementation.md` §1). It is an optional overlay; refusal is not denial. [DEV-TESTED] by `tests/test_s04_overlay.py` (builder-authored; Copilot technical review only).
3. **[EXISTING]** Authority in S04 is a manifest SHA-256 pin supplied via `TrustConfig` by the invoking operator code; the record is accepted only if its file hash equals the manifest value (s04 §2). This is integrity against a pin, not authentication of any author or approver (trust-limitations T2, T4). No pin is approved (T8).
4. **[DEV-TESTED]** S05 differential evidence compares original and registry-backed policy over a 1,728 + 168 grid plus frozen cases for representable values (trust-limitations §1; `tests/test_s05_equivalence.py`, not re-run by this lane). Three E05 lone-surrogate behavioral SKIPs remain; no equivalence is shown for that class (T12). Oracle is builder-authored (T10).
5. **[EXISTING]** Nothing calls the consumer. `LocalExecutionPolicy` is constructed by caller code (Runtime `control_plane_adapter.py:56,216`, `atomic_local_control_plane_executor.py:14` take a `policy` argument). There is no registry hook in Runtime at `c5e97e87`. Not established: how production callers build the policy.
6. **[EXISTING]** `LocalExecutionPolicy` has eight allow/ceiling fields plus `target_match` (`safe_executor.py:359-372`). F1a covers three; F1b is the two remaining allow-sets (`allowed_institutions`, `allowed_authority_domains`); `allowed_target_prefixes`, `max_amount`, `max_effects`, `target_match` are different semantics (S06 recommendation; PR #17 04 §F1b row).
7. **[EXISTING]** No Control Plane source in the clone at `7a4bcd4` references `LocalExecutionPolicy` or `safe_executor` (grep, no hits). So F1 fields are enforced by the Runtime local check only. A F1-only MSOP exercises the Runtime consumer; it does not make the Control Plane a registry consumer. F4/F5 are the families whose evaluators live in the Control Plane (s02 §3, rows F4, F5).
8. **[EXISTING]** The destination is synthetic SQLite (Runtime README line 24, line 172; trust-limitations T11). No production path exists in the sources inspected.
9. **[EXISTING]** s02 §3 normalises F1, F4, F5, F6 to Tier 1; S02 classifications are AI-worker-produced and provisional (s02 §1, §5).
10. **[EXISTING, consequence]** S03 cannot express deny-all (empty lists refused) and its refusal semantics are optional-overlay (T7). Mandatory participation therefore cannot be met by S03/S04 as frozen; plan §3.2 and PR #17 V4, D7 say the same. Option 1 in any "mandatory" form needs a successor contract and consumer.

## 3. Candidate design (all [PROPOSAL])

### 3.1 Architecture of the profile (common to all options)

An MSOP is defined by the **path**, not by the family count. Candidate profile tuple (fields mirror v1.2 §3.4):

| MSOP element | Candidate content |
|---|---|
| Policy families | Per option below. Each family bound to a registered code evaluator with source/build identity; no scripts or expressions |
| Supported consumers | Named Runtime policy-construction path (the one site that builds `LocalExecutionPolicy` before `check`). Control Plane named only if F4/F5 included. GCR: none (OCS-only) |
| Execution environment | **Safe emulator only**: Runtime with synthetic SQLite destination, CPython per the recorded runs (3.13.17). Not production, not a real adapter. An "effecting production path remains inactive" (plan R10 gate) |
| Authenticated selection | Domain-owner-approved selection manifest, exact record/version/digest/evaluator pins, epoch, tenant/institution scope, effective interval, revocation reference (v1.2 §3.1). Authentication mechanism is a Lane B input; pin-only (current) is stated as insufficient for "authenticated" |
| Participation | Per operation, not per consumer (PR #17 V5). Candidate: one **required** operation class (registry missing/refused gives HOLD/DENY, never caller fallback) and one **optional** class (S04 semantics preserved and labelled "not applied"). Mandatory mode needs deny-all semantics and a new consumer |
| Activation protocol | Consumer-owned: at policy construction, consumer verifies the approved selection (epoch, not revoked, in interval), verifies evaluator build identity, computes effective policy, and records an effective-policy identity (selection ID/epoch, record digest, evaluator identity, evaluation time) bound to the operation and evidence. Re-check at the Runtime effect boundary (Lane D defines the revalidation protocol). No activation from merge, status or `latest` |
| Versioning and revocation | New contract version (not `s03-v1` edits); anti-rollback via selection epoch; revocation by selection withdrawal independent of record status; record status leaves the record body or becomes advisory (PR #17 D3). Lane A defines the lifecycle state machines |
| Negative-case behaviour | Closed refusal vocabulary: missing, tampered, invalid, expired, revoked, superseded, unsupported, stale, incompatible, cross-scope, evaluator-unverified. Required class: HOLD/DENY. Optional class: overlay-not-applied, evidenced. Unknown composition refuses |
| Evidence and audit | Each decision records selection ID/epoch, record version and digests, evaluator identity, scope, outcome, refusal code. Evidence of refusals is retained as well as successes. Digest recorded is not proof of transaction-time authorization (brief) |
| Qualification | Independent oracle author and independent qualifier for Tier 1 admission (Lane F); developer, Copilot and independent evidence kept separate (v1.2 §7) |
| Unsupported | Production effects, GCR consumption, cross-domain atomicity, tenant multi-hosting beyond the declared scope, loaded-code attestation (T5), `target_match`/prefix families (D9), mandatory invariants as data, `latest` selection, registry-provided grants |

### 3.2 Options compared

| | **Option 1** Operationalize F1a (3 fields) | **Option 2** F1a + F1b (5 allow-set fields) | **Option 3** F1a/F1b + additional families |
|---|---|---|---|
| Families | `allowed_units/adapters/actions` | adds `allowed_institutions`, `allowed_authority_domains` | adds one or more of F6 (agent permissions), F1c (ceilings), F4, F5 |
| New evaluator or baseline | none (frozen blob `2fc880da`) | none (same evaluator, same type) | F6: new baseline; F1c: numeric semantics; F4/F5: Control Plane evaluators |
| Prerequisite decisions | D2, D3, D7, deny-all; D13 | plus D11 and a contract version change for `supplies` | plus D1/D4/D5/D6 as applicable; W8-091, W1-015 (F1c); W6-042 and 60-versus-300 (F4); W8-014 (F5): **depend on those open decisions** |
| Differential evidence | S05 exists for 3 fields (DEV-TESTED); must be redone against the successor contract and consumer | new battery for 2 fields; S05 machinery reusable | new oracle per family (PR #17 07 §2 expectation) |

Registry functions (v1.2 §1 items 1-7):

| v1.2 §1 item | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| 1 Admin workflow: create, validate, approve, publish, select, supersede, revoke, audit | Exercised fully (the workflow is family-independent) | Same; second family adds no new lifecycle function | Same; F4/F5 add a different authority owner (Control Plane) but no new step |
| 2 Registered consumers apply applicable records, refuse missing/tampered/etc. per profile | Exercised for one consumer (Runtime policy construction) | Same consumer; institution/domain fields add the scope-binding dimension (selection scope versus institution allow-set) | Adds consumers only with F4/F5 (Control Plane) |
| 3 No self-authority, no widening, no bypass of revocation | Exercised for intersection only | Same operator, more admission-relevant fields | F1c/F6 exercise new operators (min/max, per-key intersection with D5 absent-agent ruling) |
| 4 Integrated admission-to-effect path with CP/Runtime and evidence | **Partly**: Runtime effect check and evidence, not Control Plane (finding 7); safe emulator only | Same limit | Exercised for Control Plane only if F4 or F5 included |
| 5 GCR-compatible interface | Unexercised (OCS-only) | Unexercised | Unexercised |
| 6 Coverage register of families | Exercised: one family set implemented, others deferred/unresolved | Same | Larger register; more unresolved items to carry |
| 7 Independent qualification, recovery/rollback | Exercised once, at Tier 1, for a bounded surface | Marginally larger surface, same machinery | Multiple oracles, qualifier load grows |

Honest reading: the *registry functions* are exercised by the path (selection, activation, revocation, mandatory refusal, effect-time recheck), and F1a already carries all of that. F1b adds breadth and the strongest local admission boundary but **no new registry function**. Neither Option 1 nor 2 exercises: typed numeric composition (min/max), mapping composition, typed evidence-obligation composition or unknown-composition refusal on a non-set family, or the Control Plane as a consumer. Whether that gap makes a narrower profile insufficient is an operator judgment (v1.2 §3.4 asks R07/R08 to establish it; this lane shows the matrix, it does not establish it by itself).

### 3.3 Recommendation (not a decision)

**[PROPOSAL]** Smallest complete profile: **Option 1 families, but with the complete operational path** (required-participation successor consumer, authenticated selection, activation with epoch and revalidation, revocation, negative battery, Runtime wiring in the safe emulator, independent qualification). Reasons: F1a is the plan's candidate floor; the S05 machinery exists; a larger family set exercises no further lifecycle function; the real gaps in "operational" are in the path (finding 10, findings 3 and 5), not family count.

Option 2 is the cheapest **additive** step (S06 recommendation; PR #17 09 row 3; D11), and is reasonable if the operator wants institution/authority-domain scope exercised in the first profile. It should be chosen on that ground, not on the ground that it adds registry functions. Option 3 is not the smallest: include F4 or F5 only if the operator requires the Control Plane to be a registry consumer in the MSOP; both are blocked by open classifications. The required-participation profile cannot be built by reusing frozen S04 (finding 10).

**Distinction.** OCS-only MSOP: families above, Runtime (plus Control Plane only with F4/F5), safe emulator. GCR-compatible cross-domain profile: later (R14-R16), needs a separately approved and qualified GCR consumer and isolation evidence; no cross-domain completion claim attaches to any option here.

### 3.4 What an "operational" claim would still lack after the profile

- Independent qualification (none exists; S05 oracle is builder-authored; Copilot is not qualification, T10).
- An approved pin or approved signed selection (none; T8).
- Authentication of records and selections beyond file-hash pinning, with key custody and trust roots (Lane B; D2).
- Runtime wiring: no hook exists at `c5e97e87`; wiring modifies Runtime, which this repository does not own and which needs the Runtime owner's approval.
- Loaded-code integrity (T5), concurrency/changed-condition evidence (T11), production path and real adapters (none), Control Plane integration unless F4/F5 chosen, release and production authorization (plan R18).

### 3.5 Prohibited behaviors

No implicit `latest`; no activation from merge, status, digest or repository presence; no fallback to caller policy in a required operation; no registry-supplied grants; no loosening of the invariants kept in code (check order, `__post_init__`, target well-formedness, effect-count rules); no use of a refused or optional overlay as compliance evidence; no claim that a merged fixture manifest (`sha256:948ab4f4...`) is approved.

## 4. Constitutional and v1.2 mapping

CA18 (version, authenticate, review policy; protect invariants; fail closed on missing/unsupported records; independent review proportionate), CA14 (least privilege, bounded environment, enabled-path security review), CA05 (missing/stale prerequisites must not become approval). Tier 1 row (authority, admission) applies to F1, F4, F5, F6 (s02 §3). Plan mapping: §3.4 (MSOP), §3.1 (three objects), §3.2 (deny-all, participation), §3.3 (binding), R07 gate (operator adopts migration profile), R08 (contract and profile discovery), R09-R10 (selection, mandatory/optional integration), R11 (each family separately authorized and qualified), R17. Crosswalk: A9 (candidate, not adoption), A10, A3, A5, A7, A8.

## 5. Decisions raised

| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| E-01 | Adopt Option 1, 2 or 3 as the candidate MSOP | Operator | R08 contract scope and R09-R11 sequencing cannot be fixed; no operational claim is possible | D11, V6 |
| E-02 | Is a **required-participation** profile in the MSOP (and for which operation classes)? | Operator | Without it the MSOP can only be an optional overlay, so a refusal leaves a broader caller policy and "fully working" item 2 is not met | D7, V5 |
| E-03 | Deny-all expression and empty-record semantics in the successor contract | Operator / OCS Architect | Required profile cannot be specified; S03 refuses empty lists | V4 |
| E-04 | Is Control Plane a required registry consumer in the MSOP? (If yes, F4 or F5 enter and are blocked) | Operator / OCS Architect | If yes: blocked on W6-042, 60-versus-300 (F4) or W8-014 (F5) | D1 |
| E-05 | Named Runtime construction site and owner approval to add a registry hook | OCS Architect / Runtime owner | No real consumer integration; the profile remains standalone | none |
| E-06 | Execution environment declared as safe-emulator (synthetic SQLite) only | Operator | Otherwise the profile cannot honestly be called supported; no production path exists | none |
| E-07 | Authentication mechanism and trust roots for selection (Lane B) | Operator | No "authenticated selection"; activation stays prohibited | D2 |
| E-08 | Designate the independent qualification owner and oracle author for Tier 1 | Operator | Profile cannot be qualified; S05 limits carry over | D13 |
| E-09 | New contract version vs envelope-validator route for F1 (successor must not edit `s03-v1`) | OCS Architect | Frozen S03/S04 would be modified, violating v1.2 §2 | D3 |
| E-10 | Whether F1b joins as an additive second increment after the MSOP | Operator | Without a ruling, S07 stays unauthorized | D11 |

## 6. Risks and unresolved constraints

- The registry-function matrix is this lane's reading of source and plan; no test shows that a narrower profile fails to exercise a function. Operator and Lane F may reach a different view.
- Finding 7 rests on a grep of the Control Plane clone head only; the older pin `0a41faa9` and indirect consumption paths were not checked. Treat as [EXISTING] only for that grep.
- Where production callers build `LocalExecutionPolicy` was not established, so the hook location (E-05) is open.
- S05 equivalence applies to `s03-v1` shapes and the optional overlay; a successor contract and required consumer inherit none of it ([DEV-TESTED] label must not transfer).
- Option 2/3 estimates of effort and risk are judgment, not measurement.
- The profile depends on open S02 classifications for any family beyond F1a/F1b: W8-091, W3-063, W9-027, W8-014, W6-042, the 60-versus-300 relationship. F1a/F1b were not found to depend on an unresolved row in S02 §5 beyond the shared S06 A questions (deny-all, refusal semantics); this is not adjudicated here.
- Lane A, B, C, D, F interfaces are assumed, not designed: lifecycle state machines, selection authentication, Runtime/Control Plane wiring, effect-time revalidation, qualification gates.
- `COG-REG-SHARED-ADD-01` was not available; nothing in this document is checked against it.
