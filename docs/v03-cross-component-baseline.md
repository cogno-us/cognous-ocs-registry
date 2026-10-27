# V03 cross-component baseline (OCS Registry → Runtime M1 vertical slice)

- Status: **RECONCILIATION RECORD. Documentation only. Non-authorizing.** Builder-authored; not independently qualified; no Tier 1; Ed25519 security review OPEN.
- Date: 2026-10-26 (UTC dates of the merges are 2026-10-26/27).
- Authorization: Architect directive "V03 BUILDER DIRECTIVE — cross-component pin and contract reconciliation" under [static plan v1.5](plans/PROJECT_PLAN-v1.5.md) (blob `1ba1139a2da827f1666df82a11e7f01a872da54b`). V03 only. V04–V09 NOT AUTHORIZED.
- Constitution pin: [`1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`](https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md).
- No source, schema or normative contract file was changed by V03. RELEASE, PUBLICATION and PRODUCTION: HOLD.

This page is the one place that states which commits form the V03 baseline, what each component has implemented, what is not implemented, and where the evidence is. It does not repeat the evidence packages.

## A. Component pins (accepted implementation commits)

Each pin is a merge commit; each was verified (2026-10-26/27) to be reachable from the repository's current `main`, and the merged tree is byte-identical to the reviewed PR head tree (`git rev-parse <head>^{tree}` equals `<merge>^{tree}` in all three repositories).

| Component | Sprint | PR | Accepted merge commit | Reviewed PR head | Current `main` at V03 |
|---|---|---|---|---|---|
| `cogno-us/cognous-ocs-registry` | V01a | [#43](https://github.com/cogno-us/cognous-ocs-registry/pull/43) | `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` | `d9fb6b44b98aea2f1d65625ac40c5741b5463731` | `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` (the pin itself) |
| `cogno-us/cognous-execution-runtime` | V01 | [#145](https://github.com/cogno-us/cognous-execution-runtime/pull/145) | `b86fa5db8226a9a93a68d0f42bfa6b5cc5caa5fd` | `fccf1047926642058bc449f7b8f78eb7f2a95274` | `b86fa5db8226a9a93a68d0f42bfa6b5cc5caa5fd` (the pin itself) |
| `cogno-us/cognous-control-plane` | V02 | [#85](https://github.com/cogno-us/cognous-control-plane/pull/85) | `1bee3696ee6cd8037d142cdbcdb6020e052b0480` | `5cb180801623fc55a508485d6579eee59e42e372` | `1bee3696ee6cd8037d142cdbcdb6020e052b0480` (the pin itself) |

**Implementation SHA versus later documentation-only SHA.** At V03 no component's `main` has moved past its accepted merge, so there is no later documentation-only commit to distinguish. Registry `main` will move when the V03 documentation PR merges; that commit is documentation only and **does not replace** the Registry implementation pin `943ab183…` (no Registry source changes in V03). Later commits must not be substituted for these pins without a recorded requalification.

**Earlier read-pins named in the EXT-S4-0 ADR** (superseded for implementation purposes by the table above; kept for traceability):

| Component | ADR read-pin | Relationship to the accepted pin |
|---|---|---|
| Registry | `0fca88c6f6e945e608e8072d0e7c4d5713a4ed2e` | ancestor of `943ab183…`; `docs/r08-v2-contract.md` blob `ab66cc0e…` is **unchanged** between the two; only the ADR file and this status file were added or edited since |
| Control Plane | `fff27ebf356007e1eb3bb24198efc7e3e3f0c5eb` | ancestor of `1bee3696…`; the delta is exactly the 8 files of V02 (+1421/−4) |
| Runtime | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | ancestor of `b86fa5db…`; the delta is exactly `engine/registry_f1a_narrowing.py` and `tests/test_registry_f1a_narrowing.py` (+882) |
| Stack Qualification | `67dcaeffc955ef1b91388e0abd1ceff8eb87834c` | not re-read or re-pinned by V03 (no qualification workflow is in scope) |

### Immutable source blobs relied on (`git rev-parse <commit>:<path>`)

| Repository @ commit | Path | Blob | Role |
|---|---|---|---|
| Registry @ `943ab183` | `docs/r08-v2-contract.md` | `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f` | contract (unchanged) |
| Registry @ `943ab183` | `docs/decisions/2026-10-26-adr-ext-s4-0-integration-contract.md` | `86cfef73b6f5b9cdb98f5d60108ed2c8af5ac925` | EXT-S4-0 ADR (adopted, docs only) |
| Registry @ `943ab183` | `docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json` | `00e1cdd428ab9943570fd5a319549832b6178e20` | 15 valid / 128 invalid / 31 integer-boundary vectors |
| Registry @ `943ab183` | `registry_successor/decision.py` | `9be23f8caed899006dca3a9e61143451928a769e` | `verify_and_decide_v2`, v2 record entry |
| Registry @ `943ab183` | `registry_successor/record.py` | `823afb19acaf091b67ece1b992ff81facfcbf9c8` | frozen (EXT-S1-5 boundary guard) |
| Registry @ `943ab183` | `registry_successor/v2_f1ab.py` | `2614bb4d613f0db6aae4413cc05c2f4897adb193` | five-set `f1ab` payload |
| Registry @ `943ab183` | `registry_successor/v2_policy_identity.py` | `eea22798b729be849d6abd0847daa474872fe65a` | canonical effective-policy identity |
| Runtime @ `b86fa5db` | `engine/registry_f1a_narrowing.py` | `ca1722f5ed75e7a558be60e811c6fd4a37920a9b` | V01 non-effecting adapter |
| Runtime @ `b86fa5db` | `engine/safe_executor.py` | `2fc880dae37eac76e5074533435740ce0684209d` | **protected**, unchanged since the accepted baseline |
| Runtime @ `b86fa5db` | `engine/local_authority_effect.py` | `6b1319448a8d51dc865c7e3613f83cfb4bd87a58` | atomic destination; identical at `c5e97e87` |
| Runtime @ `b86fa5db` | `engine/atomic_local_control_plane_executor.py` | `d5ff31359f2d510a2e1573d2bc322ec0a75b6956` | identical at `c5e97e87` |
| Control Plane @ `1bee3696` | `src/agent_control_plane/canonical_policy_binding.py` | `d53a5b7e9d6180d1867a7f32061ba67cb0300514` | V02, new |
| Control Plane @ `1bee3696` | `src/agent_control_plane/local_authority_effect.py` | `12c6cc2755fb2835219d1fe61d57610e79e82d8e` | V02 successor claim profile |
| Control Plane @ `1bee3696` | `src/agent_control_plane/bounded.py` | `2cc8d998ff0a8fec3112a8b0634111fcf8fbef17` | **protected**, unchanged by V02 |
| Control Plane @ `1bee3696` | `src/agent_control_plane/policy_binding.py` | `426d47797e92f19690a21b4e8b5dc1c35d1b579c` | **protected**, approval-side `policy-binding/0.1` |
| Control Plane @ `1bee3696` | `src/agent_control_plane/runtime_authority.py` | `0b2c5e49c0cd3e0738e5c4c9e9d4fc8590563fa2` | **protected** |
| Control Plane @ `1bee3696` | `tests/fixtures/v02_legacy_claim_vectors.json` | `00e73f82058f2f0f839d52a3029f069e646485da` | frozen legacy no-binding claim vectors (generated on `fff27ebf`) |
| Control Plane @ `1bee3696` | `schemas/runtime_authority_reasons_0_3.json` | `b3b822874b7288fdaa015c9cdac960f39d6594bc` | reasons 0.3; `sha256sum` of the file = `58b29ef74b9bd49d3eae7278d8cce73c7cbc6a1095a07f7b9fa44f48a7b8c07f`, the digest the ADR (3.3 member 21) allow-lists; still equal at `1bee3696` |

## B. Contracts (version and canonical reference per boundary)

| Boundary | Contract | Canonical reference | Status |
|---|---|---|---|
| Registry record and selection (`r08-v2`, family `f1ab`) | `r08-v2` | [docs/r08-v2-contract.md](r08-v2-contract.md) (blob `ab66cc0e…`) | frozen; amendments [1](r08-v2-contract-amendment-1.md) and [2](r08-v2-contract-amendment-2.md) apply |
| Canonical policy binding | `ocs-policy-binding/1` (15 named top-level members, `scope` has 3) | contract section 4 and 4.1; digest domain `ocs-reg/r08-v2/policy-binding\n` | implemented by Control Plane V02 independently of Registry code |
| Claim carriage | declared optional claim field under a successor claim profile | contract 4.3; Control Plane profile `urn:cognous:profiles:local-authority-effect:0.2.0-proposed` | **proposed, non-production, not ratified**; legacy profile `…:0.1.0-proposed` unchanged |
| Approval-side binding | `policy-binding/0.1` | Control Plane `policy_binding.py` (protected) | distinct from the canonical binding; shared identity enforced at claim issuance |
| Cross-component integration and authority | EXT-S4-0 | [ADR](decisions/2026-10-26-adr-ext-s4-0-integration-contract.md) (blob `86cfef73…`) | **adopted as contract text; durable parts not implemented** |
| Reasons registry | `runtime-authority-reasons/0.3` | Control Plane schema above (digest `58b29ef7…`) | consumer-custody pin, not authenticated issuer publication; unchanged |

**Contract consistency result: PASS** (record: section F). Observation (documentation only, not repaired here): the ADR section 12 item 8 says "the 14 members of contract 4"; contract section 4 names **15** top-level members (`binding_profile`, `record_id`, `record_version`, `record_digest`, `selection_id`, `selection_epoch`, `selection_digest`, `family`, `consumer_id`, `scope`, `operation`, `effective_policy_digest`, `activation_ref`, `trust_snapshot_version`, `trust_snapshot_fingerprint`), and V02 implements those 15. Per plan v1.5 section 5 the exact named schema, not a count, is authoritative. The ADR text is left unedited (adopted record); a corrective erratum belongs to an Architect-approved ADR amendment.

## C. Implemented capabilities (developer-tested only)

1. **V01a — Registry r08-v2 record validation and five-set `f1ab` composition.** A valid, signed `f1ab` five-set record (units, adapters, actions, institutions, authority domains) reaches `applied` through `verify_and_decide_v2`; v1 and v2 record contracts are strictly separated at the v2 entry; malformed payloads, forged or modified signatures, wrong context, expired or withdrawn selections and expired snapshots refuse with typed codes. Evidence: [PR #43](https://github.com/cogno-us/cognous-ocs-registry/pull/43) (builder evidence at the pre-remediation head `e3f97ddd`: 6115 passed, 8 skipped, 0 failed; Architect disposition [ACCEPT](https://github.com/cogno-us/cognous-ocs-registry/pull/43#issuecomment-6430321729) at `d9fb6b44`).
2. **V01 — Runtime non-effecting Registry→Runtime narrowing (M1).** `engine/registry_f1a_narrowing.py` builds a narrowed `LocalExecutionPolicy` from an authenticated selection through the **existing** evaluator; no executor, SQLite, file, socket or subprocess use; result carries no authority. Evidence: [PR #145](https://github.com/cogno-us/cognous-execution-runtime/pull/145) (M1 module 85 passed / 1 skipped — M1-13 NOT RUN by definition; Runtime suite 598 passed / 44 skipped with the Registry pin, 513 / 44 without; Architect [ACCEPT](https://github.com/cogno-us/cognous-execution-runtime/pull/145#issuecomment-6430694385) at `fccf1047`). Needs `OCS_REGISTRY_PIN_DIR` and PyNaCl; otherwise the module is reported NOT RUN.
3. **V02 — Control Plane claim-carried canonical policy binding (EXT-S4-4).** A successor claim profile carries the validated canonical binding as a declared optional member covered by the existing `claim_commitment`; no-binding claims are byte-identical to the frozen legacy vectors; the binding is checked against the approval-side `policy-binding/0.1` (activation reference, epoch, digest) at issuance; grant and approval both remain required; malformed, substituted or undeclared members refuse; existing reason codes only. Evidence: [PR #85](https://github.com/cogno-us/cognous-control-plane/pull/85) (112 new tests; full suite 1338 passed / 91 skipped, historical; closeout 49/49 spot checks PASS, [builder report](https://github.com/cogno-us/cognous-control-plane/pull/85#issuecomment-6431633438), Architect [disposition](https://github.com/cogno-us/cognous-control-plane/pull/85#issuecomment-6431653937)). Recorded limitation: a binding that cannot be deep-copied raises `TypeError` before issuance (no claim, no authority).

## D. Not implemented

Every item below is absent from all three pinned commits (checked: Runtime `engine/` contains no `selection_*` tables, no `activate_selection` and no `sync` writer).

| Item | Where it is planned |
|---|---|
| Durable activation, scope-bound selection state, `scope_required` ratchet, generation counter, high-water, lineage binding, 24-member hash-chained log | V04 (Runtime) |
| Withdrawal persistence and anti-rollback (restore fence, external anchor check, recovery baseline) | V04 |
| Atomic effect-time enforcement: full claim verification, binding/effective-policy and lock-time guard inside `execute_claim_atomic`, typed refusal | V05 |
| Complete end-to-end governed execution (emulator over AR-01..AR-27) | V06 |
| Independent security qualification (Ed25519 / canonical base64 / binding / atomicity / restore), independent Tier 1 | V07 / V08 |
| Prevention of a no-binding Runtime bypass | V04/V05 (a claim without a binding is only refused once durable scope state exists) |
| Registry snapshot-floor enforcement (`verify_and_decide_v2` takes no floor inputs; M1-13 NOT RUN) | V04/V05 |

A claim carrying a valid canonical binding is **evidence, not authority**: the claim commitment is a self-consistency digest, not a signature, and the host-provided authority context is a trust dependency.

## E. Test and evidence references

Evidence is reused by reference; V03 did not rerun any full suite, the 143-vector Registry battery or any mutation campaign.

| Sprint | Evidence | Classification |
|---|---|---|
| V01a | PR #43 body and review comments (links in section C) | developer-tested, Architect-accepted for merge; not independently qualified |
| V01 | PR #145 body and Architect review (section C) | developer-tested, Architect-accepted for merge; not independently qualified |
| V02 | PR #85 closeout comments (section C) | developer-tested, Architect-accepted with limitations; not independently qualified |
| V03 | section F below (21 executed cases) | spot checks only; reproducibility, not qualification |

Known baseline caveat (plan v1.5 section 5): the Control Plane baseline reports 35 AGT failures that did not reproduce during V02 and whose cause is not established; none is concealed or claimed fixed.

## F. V03 reproducibility record (executed cases: 21 of a 50-case maximum)

Environment: CPython 3.13, pytest 8.3.5, PyNaCl installed in the Registry/Runtime environment, `OCS_REGISTRY_PIN_DIR` set to a checkout at `943ab183…` (clean). Each repository was checked out detached at its accepted pin.

| Repository @ pin | Cases | Result |
|---|---:|---|
| Registry @ `943ab183` (`tests/test_v01a_v2_record_path.py`: `v1a_01`, `v1a_02`, `v1a_05_forged_signature`, `v1a_11`, `v1a_14`, `v1a_16_v1_contract_records_are_refused_at_the_v2_entry`) | 6 | 6 PASS |
| Runtime @ `b86fa5db` (`tests/test_registry_f1a_narrowing.py`: `m1_02`, `m1_08_forged_signature`, `m1_16_protected_runtime_source`, `m1_17_adapter_source_has_no_effect_capable_imports`, `m1_18_registry_unavailable_fails_closed`, `m1_20` ×2, `m1_13`) | 8 | 7 PASS, 1 SKIP (M1-13, NOT RUN by definition) |
| Control Plane @ `1bee3696` (`a01` pin/inventory, `a02` valid Registry vectors byte-identical, `b01` commitment carriage, `l01[plain]` legacy byte identity, `l05` ×3 protected blobs) | 7 | 7 PASS |
| **Total** | **21** | **20 PASS, 1 SKIP, 0 FAIL** |

Non-test verifications (git and `sha256sum`, not counted as test cases): the three pins are ancestors of `main`; PR-head trees equal merge trees; Runtime `safe_executor.py`, `local_authority_effect.py` and `atomic_local_control_plane_executor.py` blobs are identical at `c5e97e87` and `b86fa5db`; Control Plane protected blobs match; reasons-0.3 digest matches the ADR allow-list; `r08-v2-contract.md` is unchanged between the ADR read-pin and the accepted pin; all 15 binding member names in contract section 4 are present in the Control Plane `canonical_policy_binding.MEMBERS` tuple (one-off name comparison, scratch script; the `a02` case separately shows byte identity with the Registry vectors). A `grep` of Runtime `engine/` for the ADR table names, `scope_required`, `activate_selection` and a `sync` writer found no match.

Cases not run at these pins are not claimed to pass.

## G. Holds and limitations

Independent Ed25519 review: OPEN (the Ed25519 adapter and core verifier hardening, PRs #26/#34, remain SECURITY-HELD). Independent Tier 1: NOT STARTED, no lead designated. Release: HOLD. Publication: HOLD. Production: HOLD. V04–V09: NOT AUTHORIZED. Synthetic keys imply no operational trust. External-anchor rollback window is a disclosed limit (ADR 3.6). Nothing here is a security clearance, certification or production-readiness claim.
