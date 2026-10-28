# M12 / F5 increment: Registry-governed per-class status age (`class_max_status_age_seconds`) (2026-10-28)

Status: **IMPLEMENTED IN AN OPEN, UNMERGED PR; NOT ACCEPTED.** Builder-side, non-authorizing, documentation only. Independent Tier 1 acceptance REQUIRED. V09 assurance separate. Ed25519 #26/#34 SECURITY-HELD. Release, Publication, Production HOLD.

## 1. Mandatory references
- Static Migration Plan v1.1, adoption merge `6f600ab1150f00ef3d96834159b1807e866a78b6` (`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`).
- Engineering Plan v1.5 (`docs/plans/PROJECT_PLAN-v1.5.md`).
- Independent Inventory Audit, PR #60, merge `6516446a4e551e50f2bb47c1d57fbf8ace27d7c5` (open decision AUD-D06 is the question answered here).
- Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; ADOPTION.md read at the same revision (non-authorizing; adoption is by exact revision and scope; a merge is not an adoption decision).
- Accepted baseline: Control Plane #88 merge `673ef092cf083b235b2c99e3cd4a6ad8361f2973`; Registry docs #62 merge `88cc72919ae9926737856f16259d5692ea16eefe` (both verified merged on GitHub).

## 2. Deliverables and exact pins
| Item | Where | Exact revision |
|---|---|---|
| A. Control Plane implementation | Control Plane PR [#89](https://github.com/cogno-us/cognous-control-plane/pull/89), branch `f5-class-age-governed-consumption` (OPEN, UNMERGED) | head `8fa99755c6a432fcc89786bd7bad1c274a65bb3d`, based on Control Plane `673ef092cf083b235b2c99e3cd4a6ad8361f2973` |
| B. Registry change | **None.** The existing r08-v2 F5 family (`f5-action-class-age-bounds`) is consumed unchanged; no new field, schema version or code | Registry pin used by tests and CI: `6f600ab1150f00ef3d96834159b1807e866a78b6` |
| C. Runtime change | **None.** | n/a |
| Dependencies | Registry checkout at the pin; PyNaCl from Registry `requirements-ed25519.lock.txt` (hash-locked); Control Plane `.[dev]` | pin in `tests/test_f5_class_age_governance.py` (`PIN`) and `.github/workflows/tests.yml` |

Control Plane files: `src/agent_control_plane/registry_f5_class_age_governance.py` (new), `tests/test_f5_class_age_governance.py` (new, 111 tests), `docs/registry-f5-class-age-governance.md` (new), `.github/workflows/tests.yml` (new pinned F5 step). Unchanged and sha256-pinned by tests: `bounded.py`, `runtime_authority.py`, `freshness.py`, `policy_binding.py`, `rule_revision.py`, `registry_f4_age_governance.py`.

## 3. Contract decision record (Phase 1)
Source: Control Plane `673ef09`, Registry `88cc729`. Probe: `evidence/probe1.py` / `probe1.out`.

| # | Question | Finding (source evidence) |
|---|---|---|
| 1 | Where is the effective class-age value selected? | Registry: `compose_f5` takes `min(caller, registry)` per class and keeps the caller value for a class the record does not name; a record class unknown to the caller is refused (`registry_successor/v2_age_bounds.py:213`, families `_F5`). Control Plane: the value is read from `self.runtime_authority_profile.actions[...].max_status_age_seconds` (`bounded.py:1358` `_class_age_bound`; `:1623`; the non-freshness status check; `runtime_authority.py` purpose-status check), and that profile is the validated snapshot of the constructor argument (`bounded.py:1286`). It is host configuration, set once at construction. |
| 2 | What does the original approval commitment bind? | `approval_commitment(profile, context)` (`runtime_authority.py:236`) hashes `profile.model_dump()` plus the approved `runtime_authority` spec, purpose ref and grant expiry. The dump contains every `ActionClass` (`runtime_authority.py:126-131`) and the freshness profile. The same profile hash is `catalogue_digest` in the persisted decision binding (`:473`). |
| 3 | Can the narrowed value be bound before approval issuance? | Yes. The effective profile is known at workflow construction; the issuer commits to `workflow.runtime_authority_profile`. Probe P1: equal value gives an identical commitment; a narrower value gives a different one. |
| 4 | Does changing the effective value invalidate an existing approval? | Yes, deterministically, with an existing code: an approval bound to the host profile holds `runtime_authority_approval_mismatch` against the narrowed profile (`runtime_authority.py:332-335`; probe P2); re-issued over the effective profile it authorizes. Equal or higher Registry values do not change the profile, so nothing is invalidated. |
| 5 | How is the selection identity carried? | By the workflow (`registry_f5_policy_identity`: Registry effective-policy digest of the effective class map + effective-profile digest) and, persisted, by `catalogue_digest` and `approval_commitment` in the decision binding. The Registry digest itself is a function of the effective class map, which the profile digest already covers; it is not separately persisted in the decision (limitation, section 8). |
| 6 | How are revocation or replacement detected? | Re-verification of the selection at construction, `decide`, `execute` entry and the commit gate; each must reproduce the bound class map and both digests. A decision persisted under one effective profile cannot execute under another (existing `authorization-critical inputs changed before effect`; tests M03, L10). |
| 7 | Do existing interfaces support this without changing protected evaluator semantics? | Yes: subclass + constructor profile + the existing `DefinitiveDestinationRejection`. Six source files are sha256-pinned unchanged by tests. |

**Recommended design (selected): effective-profile substitution at construction.** No stop condition was met: narrowing binds to `approval_commitment` without changing authority semantics; no approval is silently mutated; no new authorization mechanism and no evaluator change is needed; the tests run in CI.

**Rejected alternatives**
- *`policy_binding.age_ceilings` as the carrier (the R6 path).* It needs `binding_digest`, `selection_epoch`, `activation_ref` and `policy_generation` from an activation authority that does not exist yet (`activation_sequence` is reserved for EXT-S4-0); it forces `anchor_deadline_to_inputs` (an excluded parameter) and `approval-commitment/0.2`, so every approval issuer changes; its `binding_digest` is the EXT-S1-5 policy-binding identity, not the F5 effective-policy digest, so reusing it would invent semantics; and it only REFUSES a profile whose base exceeds a ceiling, it does not narrow. It is not needed to meet any requirement. Kept as a possible later hardening (decision D-4).
- *Add a separate Registry field to `ActionClass` or to the commitment preimage.* Changes the preimage of every approval; protected code; rejected.
- *Substitute the value at read time inside the evaluator (override `_class_age_bound` or patch `_resolve`).* Changes protected evaluator semantics and substitutes after the commitment was computed, which is the exact failure the Architect named; rejected.
- *Re-narrow the profile on every decision.* Policy substitution after approval issuance; rejected.
- *Treat the Registry value only as a ceiling the host profile must already satisfy.* Not the F5 composition (`min`); would refuse instead of narrow.

## 4. Consumer behaviour
- `GovernedClassAgeWorkflow` (subclass of the unchanged workflow). Host profile required; host class ages read per class id (two actions sharing a class id must carry the same age, else `class_age_ambiguous`). Registry called with required participation, exact `Ed25519Verifier`, host-fixed consumer, tenant, manifest institution/authority domain and a host-mapped operation id; only `applied`; defence in depth: result must not exceed the host value and must equal `min(host, record value)` for every class the record names.
- The scoped action's class MUST be named by the record (`scoped_class_not_governed` otherwise). This is stricter than Registry (which keeps the caller value for an unnamed class) and is an adapter-only fail-closed rule: required participation that says nothing about the class governs nothing.
- Mandatory floors preserved: a host value of 0 stays 0; Registry values are 1 to 2147483647 exact ints; a future-dated status stays refused by the existing `_fresh`.
- Outage extensions: DR-CP-AGE-1 decision 5 is applied only when `freshness.max_age_extension_seconds > 0`: `limit := min(host limit, min over governed classes of max(0, Registry value - narrowed base))`. Probe P4: without it a narrowed base of 30 with limit 300 extends to 330. Consequence to be aware of: a Registry value equal to the host value removes outage extensions (test X07). Extension rows recorded against the old base fail closed (`age_extension_invalid`; probe P4b, test X05).
- Refused at construction: no profile, a profile carrying `policy_binding`, an invalid host profile, a scoped action missing from the profile or manifest, a Registry class the host does not define, optional participation, a non-admitted verifier, a missing or already wrapped destination.

## 5. Lifecycle and effect boundary (lessons of F4 applied)
Boundaries: construction; start of `decide`; start of `execute`; commit gate immediately before `destination.apply` (the single commit point), implemented by wrapping the host destination so `apply` first re-verifies and, on refusal, raises the existing `DefinitiveDestinationRejection("registry_f5_selection_invalid")` (destination not called; attempt recorded `failed`, which blocks automatic retry). The held profile must still hash to the bound effective-profile digest at every boundary, so an attribute edit or `model_copy` cannot widen a bound (including between execute entry and the gate, test C08).

Architect's F4 disposition preserved, nothing new built: the residual delegated-apply window is accepted for bounded engineering only; stronger production atomicity remains unqualified; the host owns authoritative `selection_source` custody with durable rollback and epoch protection (the F4 custody document applies unchanged); no Control Plane ratchet.

## 6. Tests, mutation and CI
- 111 tests, local, exact pin, `OCS_REQUIRE_REGISTRY_PIN=1`: all PASS. Coverage map (requirement to test): 1-3 Registry below/equal/above: G02, G03, E01, E05; 4 multiple classes: G01, G05, X03; 5 unknown/missing classes: G06, G07, G09; 6 scope: G14, L07, L08; 7 invalid record/signature: G11-G13; 8 expired/revoked/withdrawn: G15, L01-L03; 9 replacement after issuance: M02, M03, L04, L05; 10 different policy under the same approval: M02, M06; 11 commitment mismatch: G04, M06; 12 class substitution: G05, M04; 13 decision-to-effect change: L02, M03, L10; 14 revocation after execute-entry verification: C01-C04; 15 no widening: G02, N01, N02, N05; 16 refusal without effects: E03, L01, L02, G18; 17 restart/recovery: L10; 18 F4 unchanged: S01 (sha pin), S02, and CI re-runs the F4 module.
- Mutation: `evidence/mutation-harness-mut5.py`, `evidence/mutation-results-final.json`: **27/27 killed** (widening guard, min cross-check, class age not applied, wrong class for every action, extension not composed, room measured wrongly, extension above host limit, no profile-modified check, all and each of the three change comparisons, ungated destination, plain-error gate, missing entry checks, scoped-class coverage, policy_binding refusal, scope check, execute-entry clock, ambiguity, manifest recheck, verifier admission, lax parser, optional participation, deny_all, applied-kind). A first run left 4 survivors (two redundant comparisons and two unreachable shape guards); tests N05/N06 were added so each is checked on its own, then 27/27.
- CI (Control Plane PR #89, exact head `8fa9975`): `test (3.11)`, `test (3.12)` (push and pull_request), `manifest-validator-parity`, CodeQL, Analyze (python), Analyze (actions): all success. The step "Run the Registry-governed F5 class-age tests (must not skip)" and the F4 step are success on both Python versions; the in-step junit assertion fails the job unless 0 skipped, 0 failed and >= 105 ran. Job logs are not retrievable from the builder network; the evidence is the step conclusion plus the in-step assertion.
- Full Control Plane suite (builder: Python 3.13.17, pydantic 2.14.1; raw logs in `evidence/`): base `673ef09` pinned 41 failed / 1398 passed / 90 skipped; this change pinned 41 failed / 1509 passed / 90 skipped (+111); unpinned 35 failed / 1325 passed on both (the new module NOT RUN, skipped). **Failure sets are identical to base** (`diff` empty). Cause now diagnosed: 35 are async tests failing with "async def functions are not natively supported" (pytest-asyncio not installed in the builder venv; CI installs `.[dev]`), and 6 (`test_v02_claim_policy_binding.py`) assert a different Registry pin (`943ab183`) than the pin used here. They are pre-existing and not regressions.

## 7. Parameter accounting (denominator 19, unchanged and adopted)
Merged basis before M12: **11 integrated, 8 eligible-not-integrated, 0 independently accepted** (F4 status and approval ages are merged as of Control Plane #88 `673ef092`).
`class_max_status_age_seconds` (RG-C-008, F5 `f5-action-class-age-bounds`): represented (r08-v2); enforcement integration implemented in Control Plane PR #89, **OPEN, UNMERGED**; independently accepted: no.
If #89 merges: **12 integrated, 7 remaining eligible-not-integrated, 0 independently accepted until formal qualification.** Open PRs are not counted as merged and green CI is not independent acceptance. Excluded and unchanged: constructor clock tolerance (AR-1/AR-2, Registry #58 held), identity/mandate ages (AR-4), `on_unreadable`, `requires_revocation_assurance`, reversibility, `anchor_deadline_to_inputs`, terminal revocation, ObservationPolicy fields, funded merge authorities. Held and not merged: Registry #58, #59, Control Plane #87.

## 8. Remaining technical limitations
1. Residual delegated-apply window (accepted for bounded engineering only; production atomicity unqualified).
2. `selection_source` rollback, epoch and revocation visibility are host custody duties; no Control Plane ratchet.
3. The Registry effective-policy digest is not persisted in the decision binding; the persisted evidence is the effective-profile digest (`catalogue_digest`) and `approval_commitment`, which cover the same class ages.
4. Profiles carrying `policy_binding` (approval generation, `age_ceilings`) are refused.
5. Equal Registry value plus a configured outage extension removes the extension (DR-CP-AGE-1 decision 5).
6. This workflow does not compose with the F4 `GovernedAgeWorkflow` (separate classes; F4 still refuses a profile).
7. Registry class ids must satisfy the Registry token rule and host ages must be within 0..2147483647 or the whole caller policy is refused (DR-CP-AGE-1 decision 7).
8. Builder-tested only; one interpreter and platform locally; independent review not performed.

## 9. Decisions requiring Architect approval
- **D-1** Accept effective-profile substitution at construction as the F5 commitment coupling (closes AUD-D06 for the class-age parameter only; it is not a precedent for `on_unreadable`, `requires_revocation_assurance` or other class fields without their own review).
- **D-2** Confirm the DR-CP-AGE-1 decision 5 consequence that an equal Registry value removes outage extensions, or direct a different treatment.
- **D-3** Confirm the adapter-only rule that the record must name the scoped class.
- **D-4** Decide whether F5 should later feed `policy_binding.age_ceilings` and the approval generation (needs an activation-authority decision first), or stay as implemented.
- **D-5** Decide whether a combined F4+F5 governed workflow is wanted (not built).
- **D-6** Merge decision for Control Plane #89 and this documentation PR (no automatic merge).
