# R08-PREP Lane C: OCS consumer integration contract (Control Plane and Execution Runtime boundaries)

Purpose: locate, with file:line evidence, where registry selection, validation, evaluation, activation, grant validation and effect-time revalidation live today in the real OCS Control Plane and Execution Runtime. Then specify candidate interfaces (not implementation) for binding a registry-derived selection reference to the existing authority-to-effect boundary without adding a competing check or a second engine.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.

## 1. Sources and revisions examined

| Source | Revision | Note |
|---|---|---|
| Registry repo `cogno-us/cognous-ocs-registry` | `main` `eb850c8d303961d099a123534121aeac280b242b` (rev-parse) | `registry_consumer/consumer.py`, `docs/s04-implementation.md`, `docs/s02-inventory.md`, `registry_contract/validator.py` (constants only), plan v1.2 §§3.1-3.4, R09, R10 |
| Control Plane `cognous-control-plane` | clone head `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c`; S01/S02 pin `0a41faa972699f7ec3063967a14cd9bdd3e67d27` fetched | `bounded.py`, `rule_revision.py`, `local_authority_effect.py` (names only), `decision_input_profile.py` (header), docs list |
| Execution Runtime `cognous-execution-runtime` | clone head `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`; S01/S02 pin `ec728da6dc301a664b331ac8986afd6e850a1273` fetched | `engine/safe_executor.py`, `control_plane_adapter.py`, `atomic_local_control_plane_executor.py`, `local_authority_effect.py`, `effective_grant.py`, README, `docs/execution-boundary.md` |
| Qualification repo `cognous-stack-qualification` | `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` | only to see who constructs `LocalExecutionPolicy` in the chain fixtures |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, `ENGINEERING_CONSTITUTION.md` | CA03, CA05, CA06, CA09, CA12, CA14, CA18 read |
| PR #17 `docs/registry-schema-analysis/08-open-architectural-decisions.md` | merged: main `e3f5bbc32f957a10822a15a1b642e48c63d428e9` (PR #17 merge `e3f5bbc3...`; PR #13 merge `e20504df8d2c8ddf8b3944c0dabb0dcf5f1009b6`). Status: **MERGED SOURCE EVIDENCE, WITH PROVISIONAL CLASSIFICATIONS**; classifications and schemas are not adopted requirements. This lane read the head `bdfb2b72...` before the merge; the merged file also records Architect R07 rulings (including D7: a mandatory profile is permitted as a design capability, not authorized for activation; required-policy failure must not fall back to a broader caller policy) | D1-D13 referenced by ID only |

**Two baselines kept separate (Architect LD-06):** HISTORICAL BASELINE = S01/S02 pins (Runtime `ec728da6...`, Control Plane `0a41faa9...`); CURRENT CANDIDATE = current heads, verified at integration: Runtime `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`, Control Plane `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (unchanged since this lane ran). No integration baseline is selected here; R10 selects a new exact-source candidate after checking contract differences (see `10-source-revision-reconciliation-and-review-closure.md`); no automatic migration because heads advanced; historical results are not rewritten.

**Pin comparison [EXISTING]:** a `git diff --stat` of `engine/` (Runtime) and `src/` (Control Plane) between the S01/S02 pins and the clone heads shows exactly one changed file in each: `local_authority_effect.py` (Runtime +52/-3; Control Plane +8/-2). Blob hashes of every file cited in section 3 other than `local_authority_effect.py` are identical at both revisions (checked with `git hash-object` for `safe_executor.py`, `control_plane_adapter.py`, `atomic_local_control_plane_executor.py`, `bounded.py`, `rule_revision.py`). All line numbers below therefore hold at both pins, except any claim about `local_authority_effect.py`, which I cite at clone heads only and did not diff in detail.

**Not inspected:** `COG-REG-SHARED-ADD-01` (unavailable; cited only through plan v1.2/crosswalk); Control Plane resolver implementations beyond the in-memory `policy_status`; Action Manifest, Governed Exchange, ODES contracts, Replay Bundle exports; no upstream test suite was run by this lane; `cognous-open-control-stack` hub (not cloned); `tests/test_s04_overlay.py` not re-run (cited from `docs/s04-implementation.md` section 7). The S02 worker rows were not adopted: statements below rest on source reads.

## 2. The answers in one table (details and evidence in section 3)

| # | Question | Where it is today | Label |
|---|---|---|---|
| 1 | Registry selection resolved | Nowhere in OCS source. Only the registry-side S04 overlay, caller-invoked with explicit paths and operator-supplied pin | [EXISTING] (S04 only) |
| 2 | Selected record validated | S04 consumer, `consumer.py:210-267`, calling the frozen S03 `validate_record_text` | [EXISTING], [DEV-TESTED] by `tests/test_s04_overlay.py` (builder-written) |
| 3 | Deterministic evaluator executes | `LocalExecutionPolicy.check`, Runtime `safe_executor.py:410-427` | [EXISTING] |
| 4 | Activation owner | The caller who constructs `LocalExecutionPolicy` and the executor. In OCS source that is an unnamed host integrator; no non-test caller exists in the Runtime or Control Plane | [EXISTING] for the fact; ownership statement is [PROPOSAL] |
| 5 | Grant validation owner | Control Plane `BoundedAuthorizationWorkflow._resolve_inputs`, `bounded.py:2239` ff. (grant block precedes 2448) | [EXISTING] |
| 6 | Effect-time revalidation owner | Control Plane `execute()` re-resolves at effect time, `bounded.py:1685-1711`; optional atomic store revalidates at commit, Runtime `local_authority_effect.py:675-760, 782` | [EXISTING] |
| 7 | Selection references in decision evidence | Not today. Existing grant-policy channel (`policy_versions`, `PolicyStatus.digest`, `rule_identity`, `ResolutionInput`) is for grant policy refs; a selection is not a grant, so it is not adopted as the channel (4.3) | [EXISTING] channel; binding is [PROPOSAL] |
| 8 | Registry refusal effect | S04: caller policy unchanged, `consumer.py:93-94, 270-279` | [EXISTING] |
| 9 | Policy unavailable | Differs by layer; see 3.7 | [EXISTING] |
| 10 | Evaluator revision discovery | None. Operator supplies blob id and SHA-256 in `TrustConfig` | [EXISTING] |

## 3. Findings from source

### 3.1 Evaluator and policy construction (items 3, 4)
- `LocalExecutionPolicy` is a frozen dataclass, `safe_executor.py:358-372` (class at 359); `__post_init__` (374-394) fail-closes on non-frozenset or empty entries; `check` (410-427) evaluates in fixed order: institution, domain, adapter, action, target, unit, amount, effects, effect count. [EXISTING]
- It is called from three places: `control_plane_adapter.py:101` inside `observe()`; `safe_executor.py:890` in `LocalDestinationExecutor.execute_snapshot`; `atomic_local_control_plane_executor.py:69` before claim execution. [EXISTING]
- The class docstring says it "does not establish institutional authorization" and runs only after the Control Plane revalidates and invokes the adapter (`safe_executor.py` ~870-880). [EXISTING]
- **Who constructs it:** `PinnedControlPlaneExecutor.__init__` and `AtomicLocalControlPlaneExecutor.__init__` take `policy` as a required caller-supplied argument and raise if absent (`control_plane_adapter.py:216-235`; `atomic_local_control_plane_executor.py:14-27`). Searching the Runtime and Control Plane trees finds no non-test, non-README construction. The README quick start builds it inline (`README.md:~82`). In the qualification repo it is built by synthetic hosts and test helpers (for example `suites/mvp-chain/kwflow_fixtures/baseline/tools/mvp_ingress/synthetic_host.py:126`). The Control Plane never references `LocalExecutionPolicy`. [EXISTING] So "the caller" is the **host integrator** that wires a workflow, destination and policy into an executor; OCS source does not name a production host. This is an unresolved ownership fact, not something the registry may assume.
- Policy values are not carried into Control Plane decisions. A local refusal is recorded with `failure_class="policy_denial"`, `reason_code="local_policy_rejected"` and the exception text as `detail` (`safe_executor.py:892-893`); no policy identity or digest is recorded. [EXISTING]

### 3.2 Selection resolution and record validation (items 1, 2, 8)
- S04 `apply_registry_overlay(caller_policy, trust, manifest_path, record_path)` (`consumer.py:270-279`) is the only selection code. Paths are explicit; the pin (`manifest_sha256`) and Runtime source commitments come from the operator-supplied `TrustConfig` (`consumer.py:67-80`). No discovery, network, store or signing. [EXISTING]; behaviors [DEV-TESTED] (builder battery, Copilot review, "not independently qualified", `s04-implementation.md` section 7).
- Order: caller type exact, trust shape, installed evaluator file re-hash, manifest pin, manifest shape, runtime match, record file hash, S03 validation, identity match (`consumer.py:210-253`). Effective = caller intersect registry for three fields only (255-266). [EXISTING]
- Refusal returns the caller's policy object unchanged with `overlay_applied False` (`consumer.py:93-94`); an unexpected exception also returns refuse (`consumer.py:276-279`). This is an optional overlay, not denial (`consumer.py:14-16`). [EXISTING]
- Limits that matter for integration: `record_source` is not verified (`s04-implementation.md` sections 3, 8); it verifies evaluator file bytes on disk, not the loaded code object (section 8); nothing calls the consumer. [EXISTING]

### 3.3 Grant validation (item 5)
- `BoundedAuthorizationWorkflow._resolve_inputs` (`bounded.py:2239`) reads grant, requirement, conflict, policy, approval, evidence through a trusted `resolver` and accumulates reason codes. Grant checks include status, revision, tenant, validity window, scope and identity (`bounded.py:2380-2430`). The workflow is constructed with a `resolver` and `records` by the host (`bounded.py:1264-1300`); the Runtime adapter refuses to run without a workflow that has a resolver (`control_plane_adapter.py:226-230`). [EXISTING]
- Decision-time and effect-time resolution of grants belongs to the Control Plane with the host-configured resolver as trusted source. In Route B the Runtime destination additionally revalidates the authoritative grant row at commit: `_validate_claim_state` checks revision, active status, institution/domain/tenant, retained revocation and validity interval under the effect transaction (`local_authority_effect.py:675-760`, section 3.4; also stated in document 04 finding 2). The Runtime has no grant-resolution role of its own and does not decide grants; it enforces the stored authority state at commit. The registry adds neither check. [EXISTING]

### 3.4 Effect-time revalidation (item 6)
- `decide()` (`bounded.py:1629-1659`) resolves inputs, records the decision. `execute()` (1662-1833) requires the persisted, identical, authorized decision (1675-1679), re-runs `_resolve(...stage="effect")` (1685), and refuses with an `EffectTimeRefusal` row if any reason arises or if `current != persisted.binding` (1690-1711). Only then does it observe the destination and call `destination.apply` (1792 ff.). A comment states no re-read occurs after validation (1782-1783). [EXISTING]
- Route A (`PinnedControlPlaneExecutor`): `execute()` builds a per-call workflow view and calls `workflow.execute`; `LocalExecutionPolicy.check` runs inside the adapter at `observe()` (called from `_observe_and_reconcile`) and again in `apply -> execute_snapshot` (`control_plane_adapter.py:101, 142-150`; `safe_executor.py:890`). [EXISTING]
- Route B (optional `AtomicLocalControlPlaneExecutor`): `policy.check` runs before the claim (`atomic_...py:69`), then `execute_claim_atomic` in the destination store revalidates claim state (grant, approval, policy version/status, evidence) in one SQLite transaction (`local_authority_effect.py:675-760`; policy rows at 746-758). `LocalExecutionPolicy` is not evaluated inside that transaction. [EXISTING]. The brief's "unavailable policy" and "effect-time" cases for this route rest on the store's state tables, which are written by trusted host credentials (`effective_grant.py:docstring`, `docs/execution-boundary.md:145`).
- Residual window: freshness/0.1, where configured, narrows but does not close the check-to-commit gap (`bounded.py:1797-1800` comment). [EXISTING]

### 3.5 Existing reference channel for policy identity (item 7)
- A grant carries `policy_versions: [{ref, version}]`; at both decision and effect time each ref is read via `resolver.policy_status(ref)` and compared on version, status, tenant and institution; mismatches add `policy_stale_or_changed`, `policy_version_changed`, `policy_superseded`, `policy_status_unknown` (`bounded.py:2448-2474`). Approvals bind to `commitment(policy_versions)` (`2483, 2511`), so a policy-version change after approval invalidates the approval. [EXISTING]
- `PolicyStatus` has an optional `digest` ("opt-in rule-revision/0.1 content pin", `bounded.py:199-207`). Under a configured `RuleRevisionProfile`, an unadopted digest adds `policy_status_unknown` (`bounded.py:2471-2474`). Adoption is a signed `RuleRevision` row naming a configured signer different from the reviser (`rule_revision.py:87-136`); signer is an asserted, unauthenticated name and the store has no keyed integrity (`rule_revision.py:1-14`). [EXISTING]
- Decisions and refusals carry `ResolutionInput` rows (digest/version/status scalars via an explicit allowlist, `bounded.py:2243-2262`) and `rule_identity` for `policy`-type inputs only (`bounded.py:1313-1318, 1654, 1705`). [EXISTING]
- A registry `selection` is not a `policy` input, a grant `policy_version` or a `RuleRevision` row today. [EXISTING] (absence)

### 3.6 Discovery of compatible evaluator revisions (item 10)
- S03 fixes `EVALUATOR_ID = "engine.safe_executor.LocalExecutionPolicy.check"` and `EVALUATOR_BINDING = "registered-code-reference"` (`registry_contract/validator.py:34-35`). The S04 manifest must carry exactly those and the Runtime `source_blob_id`/`source_sha256`, which must equal operator-supplied values (`consumer.py:200-207, 231-233`). Compatibility is therefore exact-file-hash equality for one pinned file, not a range or capability query. The Runtime itself exposes capability strings only for its destinations (for example `sqlite-effective-grant/0.1`, `control_plane_adapter.py:62-72`), not for the policy evaluator. [EXISTING]

### 3.7 Policy-unavailable behavior (item 9)
| Layer | Condition | Behavior | Evidence |
|---|---|---|---|
| S04 overlay | any refusal | caller policy unchanged, may be broader than registry would allow | `consumer.py:93-94` [EXISTING] |
| Runtime | no policy passed | executor construction raises `ValueError` | `control_plane_adapter.py:232-233` [EXISTING] |
| Control Plane | grant policy_status unreadable or missing | `policy_missing`, `policy_stale_or_changed`, hold | `bounded.py:2451-2454` [EXISTING] |
| Control Plane | policy status stale / unknown / unadopted digest | hold reasons | `bounded.py:2456-2474` [EXISTING] |
| Atomic store | authoritative policy row absent or not active | `PermissionError` before commit | `local_authority_effect.py:746-758` [EXISTING] |

## 4. Candidate contract (all [PROPOSAL])

### 4.1 Ownership model and the six-way distinction
- **Registry** supplies RECORD and SELECTION artifacts and a read-only consumer library. It never evaluates, activates or authorizes, and it is not an OCS authority engine.
- A registry **selection is not an OCS execution grant** (Architect ruling C-03). It is independently authenticated governance configuration. A grant remains a separate authority; selection state must not be modelled as a grant, grant policy row or grant status merely because grant policy rows already support atomic revalidation.
- **Host integrator** owns ACTIVATION. The Runtime owns evaluation of `LocalExecutionPolicy`. The named **production** host/application owner is **not designated** (C-01, deferred); the operator designates it before R10 and no production caller is invented here. For the initial bounded emulator profile a named **synthetic integration adapter** would stand in; it is explicitly not proof of a production integration.

| Step | Meaning | Owner | Where (today) |
|---|---|---|---|
| A. Selection authentication | Verify the authenticated selection statement and trust root | Registry verifier contract (document 02); trust root per operator | Not in OCS source; S04 only pin-checks bytes |
| B. Effective policy evaluation | Compute `caller ∩ registry`, evaluate `LocalExecutionPolicy.check` | Runtime (`safe_executor.py:410-427`) | Runtime, per call, before the claim on Route B |
| C. OCS grant authorization | Grant, approval, evidence, freshness | Control Plane decision/effect-time resolution; Route B destination re-reads stored grant state at commit | `bounded.py`; `local_authority_effect.py:675-760` |
| D. Pre-commit policy applicability | Is this exact selection/record/evaluator still the applicable configuration at commit | **Undefined today**; needs an OCS design (LD-01, 04) | none |
| E. Effect commitment | Atomic claim consumption and effect | Runtime destination (`execute_claim_atomic`) | `local_authority_effect.py:782` ff. |
| F. Evidence recording | Decision/refusal/receipt rows | Control Plane and Runtime records | `bounded.py`, destination tables |

### 4.2 Interface I1: consumer resolution (registry to host)
Input: operator-held trust config (pin, evaluator build commitments, explicit selection reference); caller baseline policy. Output: `{disposition, reason, effective_policy, selection_ref}` where `selection_ref` is a minimal, non-authorizing reference object (selection id/epoch, record id/version/digest, evaluator id and build commitment, trust-root id). Tuple contents are document 04; authenticated origin is document 02. I1 must be a **pure function of operator-held inputs**: no discovery, no `latest`, no network, no write. S04 already satisfies the shape except `selection_ref`, authentication and epoch. Evolution of S04 requires an approved successor contract; frozen S04 is unchanged.

### 4.3 Interface I2: binding the reference to the existing boundary (no second authority engine)
**Amended.** The earlier preference to express a selection as grant `policy_versions` / `PolicyStatus.digest` is withdrawn (Architect C-03/LD-01). The existing channel (3.5) shows how OCS revalidates *grant policy references*; it is not a model for registry selections, and `rule_revision.py` signers are asserted names (3.5). Candidates that remain, all requiring an OCS design owned by the OCS Architect with Runtime and Control Plane owners (R10):
1. **A separately defined selection-applicability term** checked inside a supported atomic boundary, distinct from grant rows, bound by an exact-match tuple (document 04 section 4.2).
2. **An independently defensible binding protocol** that prevents a policy change from widening the executable operation between `policy.check` and effect.
3. **Evidence-only attachment** to Runtime/Control Plane records (3.5): permitted for audit, **insufficient** to prove the selected policy remained authorized at commit; recording a digest does not prove atomic evaluation.

**F1 limit (UNQUALIFIED).** `LocalExecutionPolicy.check` runs before the claim transaction on Route B (`atomic_local_control_plane_executor.py:69`, then `execute_claim_atomic` at `local_authority_effect.py:782`; revision `c5e97e87`). Adding selection identifiers to a claim policy row therefore does not establish atomic revalidation of every F1 restriction. Until an integration design shows either re-evaluation within a supported atomic boundary or a binding protocol that prevents widening between check and effect, **the F1 authority-to-effect guarantee is UNQUALIFIED.** No second OCS authority engine is created.

Prohibited under I2: treating a matching digest as authority; deriving grant validity from selection state or selection validity from grant state; widening the caller policy; recording a policy digest and claiming transaction-time authorization; a registry call inside the commit transaction; a second grant lookup; global cross-domain atomicity claims.

### 4.4 Interface I3: refusal and mandatory profile (candidate)
- Optional profile: frozen S04 behavior (caller policy unchanged, "overlay not applied"). Never described as denial.
- Mandatory profile: merged Architect R07 ruling D7 permits it as a design capability, **not authorized for activation**. It needs (a) an approved successor contract, (b) an independently qualified consumer, (c) a defined refusal that the host must treat as HOLD or DENY per the crosswalk in document 04 section 4.3. Required-policy failure must never fall back to a broader caller policy. The registry cannot force the host to stop; mandatory means the host contract says so and a qualification shows it. Mandatory floors remain in code (`__post_init__`, `check` order).

### 4.5 Interface I4: evaluator compatibility discovery
No dynamic discovery. A **compatibility declaration** beside the record family lists evaluator id, binding and acceptable Runtime source commitments (blob id and SHA-256), each approved by the OCS owner; the consumer matches the installed file and otherwise refuses (reason `runtime_source_unverified`). No ranges, "newest compatible" or capability probing. Authentication of the list: document 02; entry into the tuple: document 04.

### 4.6 Failure behavior (candidate; S04 unchanged where it defines it)
Unknown manifest field, composition, evaluator or version: REFUSE. Registry unreachable: optional profile keeps caller policy; a required operation is HOLD at host construction. A selection that changes between decision and effect is not detected by any existing mechanism for `LocalExecutionPolicy` values (F1 limit above) and must be stated as such, not papered over; selection validity at initial admission is insufficient if it changes before commit (document 04 LD-09).

## 5. Constitutional and v1.2 mapping
- CA03 (contract before code): successor consumer contract needed before any wiring. CA05 (fail closed, do not invent policy): unknown composition/evaluator refuse; I will not invent the host's refusal semantics. CA06: evidence of refusals retained (`EffectTimeRefusal`, rule-revision refusal rows). CA09: R10 is a canonical admission/integration change and must serialize. CA12: no unqualified degradation; optional overlay must not be presented as equivalent to mandatory. CA14: bounded read, least privilege; S04 excludes host administrators. CA18: governance-critical policy must be authenticated and protected invariants stay code (`__post_init__`, `check`). [Read in the pinned Constitution; formal adoption is not inferred.]
- Plan v1.2: §3.1 three objects, §3.3-binding effect-boundary binding ("OCS independently rechecks at the actual authority-to-effect boundary"), §3.4 MSOP candidate, R09 (authentication/custody, trusted activation configuration), R10 (wiring, mandatory/optional, effect-time identity, "without claiming global atomicity"), R12 (distribution/auditability). Crosswalk A2, A3, A5 (scope clarified), A9 (candidate not adoption).

## 6. Decisions raised
| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| C-01 | **Architect: defer.** Operator designates the production host owner before R10; Runtime owns `LocalExecutionPolicy` evaluation; a named synthetic adapter serves the emulator profile only | Operator (designate); OCS Runtime integration owner | Without a designated owner "consumer-owned activation" has no production owner; R10 cannot start | related D7 |
| C-02 | Mandatory profile: permitted as a design capability by the R07 D7 ruling; activation not authorized | Operator | No mandatory behavior may be activated | D7 |
| C-03 | **Architect: amended.** Selection is not a grant; evidence-only is insufficient; an integration design is required (4.3); F1 guarantee UNQUALIFIED until then | OCS Architect with Runtime and Control Plane owners (R10) | No detection of a changed selection at commit exists | D2 |
| C-04 | Who authenticates `PolicyStatus.digest` adoption (current signer is an asserted name, `rule_revision.py:7-13`) | OCS Architect / Independent qualifier | Selection binding would inherit unauthenticated signers | D2 |
| C-05 | Evaluator compatibility declaration format and approver (I4) | OCS Architect | No compatible-revision discovery; every Runtime change forces manual re-pin | none |
| C-06 | Route A, Route B, or both are in scope for the MSOP | Operator | Different revalidation owners (CP vs atomic store); selection binding differs | none |
| C-07 | F1 amount/effects ceilings classification (W8-091, W6-042, W8-014 dependence) before any numeric field joins I1 | Operator | Only the three allow-list fields can be consumed; designs here depend on that open decision | D1, D6 |
| C-08 | 60-versus-300 observation relationship, W3-063 and W9-027 if freshness or dedupe fields are considered | Operator | Any F4/F7 consumer binding is blocked | D1, D4, D12 |

## 7. Risks and unresolved constraints
- Registry source-of-truth for activation does not exist in OCS: the S04 consumer is called by nobody (`s04-implementation.md` section 8). Everything in section 4 is design on top of a consumer with no call site.
- The only existing effect-time revalidation of a policy identity (3.5) concerns grant policy refs, not the Runtime-local `LocalExecutionPolicy`. A narrowed local policy is not re-observed at effect time by the Control Plane; the Runtime evaluates it per call, but nothing proves which selection produced it. The overlay's values are therefore bound only by the host's construction.
- Route B: `LocalExecutionPolicy` is evaluated before the claim and not inside the atomic transaction (3.4); a selection change between that check and commit is not detected by any existing mechanism. [EXISTING] (absence); a separately defined selection-applicability term would be checked inside the transaction only if an approved design provisions it (4.3); F1 guarantee is UNQUALIFIED until then.
- Rule-revision adoption is asserted-name, unauthenticated, plain-JSON store without keyed integrity (`rule_revision.py:7-13`); using it for selection inherits that.
- Same-host file/database access can bypass the Python modules (`docs/execution-boundary.md:110, 145`); out of scope for the registry.
- Evidence I did not see: any Control Plane production resolver; how ODES exports carry `rule_identity`; whether any host in the wild passes a registry-derived policy. Labels [DEV-TESTED] here mean the S04 builder battery only; there is no [QUALIFIED], [APPROVED] or [PRODUCTION] item in this document.
- Interfaces expected from other lanes: Lane B (authentication of pin, manifest, signer); Lane D (consistency tuple and epoch contents; how `selection_ref` and the matched evaluator commitment are bound).
