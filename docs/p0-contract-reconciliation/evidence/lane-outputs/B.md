# Lane B: Registry contract reconciliation (V0.2 R0 vs Registry v1.2/R08)

Sources and pins: OCS hub `51c579a3208149922649a31a6eb041106a4121c3` (`docs/program-v0.2/**`, `docs/declarative-governance-registry.md`, `tools/registry_records.py`, `tools/mandatory_checks.py`); Registry `ce00520f91bf3986a08b4d13a1fb062057babc71` (`docs/plans/*`, `docs/r08-preparation/*`, `docs/r08-s01-contract.md`, `docs/r08-s01-implementation.md`, `docs/s03-contract.md`, `registry_successor/`, `registry_contract/`). Qualification `998d39c5ba1c9d537be8289f7658f2e9cde6cbba`. Ledger: `B.jsonl` (17 rows).

## Key findings

1. **Two different record types, one shared vocabulary.** V0.2 `ocs-registry-record/0` is a whole governance rule-set (rule_table, evaluators, reason_map, epoch, predecessor). R08 `r08-v1` is a per-family typed configuration record (F1a payload) plus a separate signed selection. Neither carries the other's content, so most dimensions are compatible-with-adapter, not conflicting. Do not merge schemas.
2. **The v1.2/R08 documents never cite V0.2 R0/2.1/2.3/2.4** (no hit for `program-v0.2`, `1.3-registry`, `ocs-registry-record`, `OCS-DGR` in `docs/r08-preparation`, `docs/r08-s01*`, `PROJECT_PLAN-v1.2.md`). Agreement on partitions, fail-closed, no latest, no fallback is convergent. Plan v1.3 section 2 is the first registry document that names R0.
3. **What V0.2 actually adopted vs proposed.** Adopted by decision record: the three-partition direction (`operator-decisions.md` line 10, OCS-DGR-ARCH/1.0.0), ADR-P01 JCS-for-new-commitments (`m0-decision-record.md` row 1), ADR-P03 hub-owned immutable digest-pinned location (row 3). Everything else in R0/2.1/2.3/2.4 is a proposed or candidate contract (1.3 header: "Proposed contract draft ... No decision is recorded"; 2.1 "not a frozen schema"; Q17 lists no registry-record freeze; Q13 "2.4 NOT YET AUTHORIZED", all four gates unmet). Q11 (`/1` with version isolation) and Q12 (sequence) are architect rulings authorizing preparation only.
4. **No independent qualification exists for V0.2 registry code** (qualification repo HEAD has no reference to `ocs-registry-record`, `registry_records`, `mandatory-manifest`). Registry side: R08-S01 is developer-tested only; `FakeVerifier` test double, no cryptography, no verifier, no trust root, `operationally_authorized` always False.
5. **R08-S01 merge state.** `registry_successor/` is present on main HEAD ce00520, but `docs/sprint-status.md` still calls PR #19 a "DRAFT PR". Merge SHA of PR #19 not verified (shallow clone).
6. **V0.2 is silent on revocation**; R08 fills it (key, selection, expiry, floor). V0.2 is silent on typed value payloads; R08 fills it for F1a only.

## Crosswalk (semantics side by side)

| Dimension | V0.2 R0 / 2.1 / 2.3 / 2.4 | Registry v1.2 / R08-S01 | Verdict | Ledger row |
|---|---|---|---|---|
| Record identity | `registry_id`, `schema_version`, `profile` `ocs-registry-record/0`; 1.3 sec. 3 (conceptual); 2.1 | `contract_version r08-v1`, `kind`, `family`, `record_id`, `record_version`, `non_authorizing`; r08-s01-contract sec. 2 | compatible-with-adapter | B03 |
| Canonicalization | RFC 8785 JCS, profile `rfc8785-jcs`; legacy = named historical profile (M0 row 1) | `json.dumps(sort_keys, separators, ensure_ascii=True)` (`common.py:102-107`), unnamed, no profile member | compatible-with-adapter (candidate C2) | B02 |
| Versioning and digests | `sha256:` over record minus `digest`; `epoch` in record, strictly increasing; `predecessor` = active digest | `record_digest` + `payload_digest`; `record_version` per id; `supersedes` {id, version, digest}; epoch lives in selection | compatible-with-adapter | B04 |
| Registered evaluators | (id, integer version) + `qualification_ref`; exact pair match against manifest and every rule (Q2) | id + binding + Runtime blob id + sha256, repeated in selection; no qualification_ref | compatible-with-adapter | B05 |
| Mandatory-check manifests | `ocs-mandatory-manifest/0` (impl.), `/1` conditional applicability (candidate, no `/1` registry validator) | none (out of F1a scope) | compatible (orthogonal) | B06, B07 |
| Typed configuration | named as registry data; no payload field defined | exact F1a payload, deny-all, intersection composition | compatible; V0.2 gap filled | B09 |
| Policy applicability | rule-level `always`/predicate; `/1` closed predicates; resolver by policy version, class, profile, assurance (not built) | selection scope tuple exact-match + per-operation participation | compatible-with-adapter (different axes) | B08 |
| Approval and selection | digest pin held outside the store; "pinned and immutable, not signed" | signed selection statement, trust snapshot, authority grants, single-signer policy | compatible-with-adapter (R08 is the "later step") | B10, B11 |
| Activation | only via Control Plane gate; refusal list (sec. 5); epoch owner "Control Plane at activation"; 2.4 not authorized | consumer-owned; host integrator unnamed (C-01); selection authority issues epoch | **genuinely incompatible as written (boundary), bounded** | B12 |
| Revocation and epochs | no revocation; epoch strictly greater than active | key, selection, expiry revocation; `min_epochs` floor; `resolve_authoritative` refuses | compatible (R08 superset) | B13 |
| Failure and refusal | closed codes (2.1, 26 in 2.3); refusal leaves previous behavior; UNKNOWN != ACTIVE | 46 closed codes; required => HOLD (`required_policy_unavailable`), optional => `overlay_not_applied`; LD-02 mapping open | compatible-with-adapter | B14 |
| Rollback and recovery | rollback by higher epoch; offline age bound else hold; original bytes for replay | forward epoch; older snapshot is rollback; held => new attempt; retain decision-time evidence | compatible-with-adapter | B15 |
| Decision binding (extra) | rule-set digest, evaluator ids and versions, epoch bound by deciding component (F3) | 11-member tuple; F1 authority-to-effect UNQUALIFIED | compatible-with-adapter | B16 |
| Location and pin carrier (extra) | ADR-P03 hub-owned; pin-carrier owner open | records live in registry repo; custody undecided | UNVERIFIED / unresolved boundary | B17 |

Stylistic, not conflicts: field names (`digest` vs `record_digest`, `predecessor` vs `supersedes`, `issuer` vs `provenance.authored_by`), code names, hex-prefix usage, record vs selection placement of epoch (adapter), "required/advisory" (rule status) vs "required/optional" (operation participation; keep the terms distinct in P1).

## Candidate conflicts

### T1 (genuine, bounded): activation and epoch authority owner
- **V0.2 requirement:** `1.3-registry-r0.md` sec. 3 table: `epoch`, owner "Control Plane at activation"; sec. 5: "A registry becomes active only through the Control Plane's own gate"; `2.4-architect-defaults-successor-note.md` default 5: "Control Plane owns selected effective epoch and activation decision; custody outside the registry store" (operator gate: "Final cross-component authority commitment"). Status: architect default, not adopted; 2.4 not authorized (Q13).
- **Registry requirement:** `PROJECT_PLAN-v1.3-DRAFT.md` sec. 3 item 3: "Activation is consumer-owned"; sec. 5: Runtime owns F1a/F1b/F1c/F6, Control Plane owns F4/F5; `r08-preparation/03` sec. 4.1: "Host integrator owns ACTIVATION. The Runtime owns evaluation ... The named production host/application owner is not designated (C-01)"; `r08-s01-contract.md` sec. 3: epoch is a field in the selection authority's signed statement.
- **Existing behavior:** neither side implements activation. Registry S04 overlay is caller-invoked with an operator pin; r08 `verify_selection` only reports technical verification.
- **Consequence:** for Runtime-enforced families two parties could each claim to hold the "active epoch" (Control Plane per V0.2, host per R08); anti-rollback high-water state has no owner (R08 B-05); risk of split-brain policy (v1.3 sec. 3 item 6, R10 gate).
- **Recommended resolution (reuse, no redesign):** one ADR by the OCS Architect with Control Plane and Runtime owners. Selection authority issues the epoch (R08); the enforcing component's own gate performs activation and holds the high-water epoch and the V0.2 sec. 5 refusal list (Control Plane for Control Plane-enforced policy; the named C-01 host for Runtime families); the registry holds neither. This keeps Control Plane authority intact and transfers none to the registry. Not an operator decision (OCS-internal; no OCS/GCR choice).
- **Affected components:** Control Plane, Execution Runtime, host integrator (C-01), registry, hub 2.4 package.
- **P1-P6 impact:** P1 none (inventory can proceed); P2 blocks custody/activation design (R09); P3 adapters must not embed activation; P4 (R10/R12) blocked until the owner is named; P6 oracle needs the activation owner.

### C2 (borderline, resolve by naming; not counted as genuine): canonicalization profile
- V0.2: M0 row 1 "ADR-P01 canonical JSON: JCS for new commitments, legacy kept as a named profile: Approved"; 2.1 `CANONICAL_PROFILE='rfc8785-jcs'`.
- Registry: `common.py:102-107` legacy form for new r08-v1 commitments, no profile identifier in records or signing input (`b"ocs-reg/r08-v1/selection\n" + canonical_bytes`).
- Consequence: identical logical content with non-ASCII strings hashes differently; a Control Plane verifying both record families needs two canonicalizers. Resolution: name r08-v1's form as the legacy profile (ADR-P01 allows this) or give r08-v2 JCS before any pin is approved (nothing is activated, so cost is low). Affected: registry, any Control Plane/Runtime verifier. P2/P3.

### Not conflicts (watch items)
- Evaluator qualification gate: V0.2 refuses unqualified evaluators at activation; F1a evaluator has none. Intended refusal until Qualification supplies a ref (B05).
- Fallback wording: V0.2 "previous behavior unchanged" (refused candidate) vs R08 "no fallback to older epoch" (invalid current required selection). Different events (B14).
- Registry location (B17): unresolved, becomes a conflict only if a decision places the same artifact class in two repositories.

## Could not verify
- Merge SHA and merge state of registry PR #19 (shallow clone; sprint-status.md stale).
- Whether `COG-REG-SHARED-ADD-01` constrains any dimension (text and digest not in repo; r08-preparation/11).
- Independent qualification of V0.2 2.1/2.3 or R08-S01: none found; absence only shows no reference in the checked repo HEAD.
- Control Plane/Runtime source behavior behind the F3 claims (Lane C); line citations to locked repos are carried from V0.2 documents, not re-read.
- Whether ADR-P01 was intended to bind registry-repo records (scope not stated).
