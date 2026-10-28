# G0 freeze record

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

G0 is an **inventory qualification, not an independent security qualification.** Nothing here is an independent assessment.

## 1. Immutable G0 baseline

| Item | Value |
|---|---|
| G0 PR | [#50](https://github.com/cogno-us/cognous-ocs-registry/pull/50) |
| Approved PR head | `e6c57f6980aa71581499b5fcdbc38a647ebbe304` |
| **G0 merge commit (merge commit method)** | `7208eb6f53f12677f138fe0c64ec48a2e58292b5` (parents `317eb76acb2847c534c3ce7c2180b89b4aef987d`, `e6c57f6980aa71581499b5fcdbc38a647ebbe304`) |
| Verification before merge | head unchanged and clean; four checks green (pytest, CodeQL, Analyze python, Analyze actions); 29 changed files, all G0 documentation, evidence, integrity tests or successor-program status |
| Post-merge CI on the merge commit | Push on main run 40609560305 success; Registry tests run 40609560460 success |
| G0 frozen location | `docs/family-migration/g0/` at `7208eb6f53f12677f138fe0c64ec48a2e58292b5`; git tree `16d53ccfcf42bc9d1d7e80ac08f9ae2bbadb966b`; evidence subtree `fcc4d99f19b1fb6e28f70d3a64205afafb921b00` |
| Registry source pin used by the inventory | `317eb76acb2847c534c3ce7c2180b89b4aef987d`; `git diff` between it and the merge commit shows only G0 documentation, tests and status, so Registry code is identical |

Machine-readable and report blob ids at the merge commit (git blob SHA-1; a later change to any of these files is a change to the frozen G0 baseline):

| File | Blob |
|---|---|
| current-candidate-ledger.json | c0db3c1736872ff37438073090c6782c8cbde79f |
| historical-crosswalk.json | 1f146f3d86235b3d1a4351cb5eff7b4c173509a1 |
| source-baseline.md | 288f1bc261f44e1ef6a5207e532f80bba5ad293f |
| family-eligibility-matrix.md | c0fbedf9ad7eb87e584b6d450cd37f35db9ef817 |
| migration-backlog.md | a688ebdc1667121e6378a063d20adbb8403f1a72 |
| unresolved-decisions.md | b2b4ddb05630d6ff8b649169656d5af79c63d0e5 |
| g0-exit-report.md | 531eb6753db56fa7b8d1fc72f3b65f4c1f2b6f7c |

## 2. Retained inventory

| Item | Count | Check |
|---|---|---|
| Historical S02 rows reconciled | 620 | historical-crosswalk.json |
| Current source-site records | 116 | current-candidate-ledger.json |
| Unique rule groups | 97 | ledger |
| Configurable candidate groups (already-governed + eligible-not-migrated + unresolved + blocked) | 33 | ledger |
| Eligible-not-migrated groups | 23 | ledger |
| Already Registry-governed groups | 5 | ledger |
| Retained-in-code groups | 56 | ledger |
| Out-of-scope groups | 8 | ledger |
| Unresolved groups | 4 | ledger |
| Blocked groups | 1 | ledger |
| Historical unresolved classifications | 32 | crosswalk |
| Unratified reclassification proposals | 20 | evidence/worker-B,C reclassification_proposals.json |

The counts are re-derived from the JSON by `tests/test_g1_preparation_integrity.py`, not asserted by prose alone.

## 3. Architect decision history (AD-01 to AD-24)

AD-01 ACCEPTED; AD-02 and AD-03 DIRECTION ACCEPTED (2026-10-27, recorded in the G0 closeout commit); AD-04 to AD-24 remain OPEN. No worker classification, proposed resolution or reclassification has been ratified. Original questions and evidence are preserved in `docs/family-migration/g0/unresolved-decisions.md`.

| Id | Question (truncated) | Disposition (truncated) |
|---|---|---|
| AD-01 | Reclassify M1: F1b is ALREADY-GOVERNED in f1ab; confirm M1 becomes negative-oracle closure. | **ACCEPTED** (2026-10-27). F1b is already governed through Registry r08-v2 `f1ab |
| AD-02 | Reconcile Plan v1.0 'F4/F5 not covered' with the registered `f4`/`f5` families; map M11/M12 to the remainder. | **DIRECTION ACCEPTED; detailed scope pending.** F4 and F5 are partially Registry |
| AD-03 | Contract path for every new Registry-carried field: new family id under r08-v2 (hand edits to `FAMILIES_V2` an | **DIRECTION ACCEPTED; successor contract pending.** Prefer a versioned successor |
| AD-04 | Add a single-source test tying `FAMILIES_V2` to `IDENTITY_FAMILIES` (no test asserts their key sets are equal  | OPEN |
| AD-05 | Ratify or replace the constant `MAX_SNAPSHOT_NODES = 1048576`, labelled PROPOSED in source. | OPEN |
| AD-06 | For institutions and authority domains: equality ('carried unchanged') or subset (what Runtime enforces)? | OPEN |
| AD-07 | May the Registry ever carry `max_amount`, `max_effects`, `allowed_target_prefixes`, `target_match`, given Amen | OPEN |
| AD-08 | Confirm F3 limits stay floors (at most host-owned lowering). | OPEN |
| AD-09 | Recovery window 86400 s and OpenShell timeout are the only low-risk resource candidates; confirm eligibility. | OPEN |
| AD-10 | Confirm F6 (Runtime permissions) and F7 (Runtime TTL) as OUT-OF-SCOPE. | OPEN |
| AD-11 | Mapping of the Registry F4 status scalar onto conflict/policy status when a runtime-authority profile exists. | OPEN |
| AD-12 | Retire or guard inert `policy_config.default_action`, `authority_records_from_policy_config` and demo helpers. | OPEN |
| AD-13 | Is `DedupeProfile` policy or a provider fact? | OPEN |
| AD-14 | Relationship of the hub's `ocs-registry-record/0` format to Registry r08-v2. | OPEN |
| AD-15 | Constitution checkout HEAD `a4dd1111` inverts tier numbering relative to pin `1c2e920f`; confirm the pin remai | OPEN |
| AD-16 | Replay-bundle and evidence-pack importers accept only Control Plane `7a4bcd40` / Runtime `c5e97e87` / manifest | OPEN |
| AD-17 | The verifier vendors reasons 0.1/0.2 only; the Control Plane ships 0.3 (eight more codes). | OPEN |
| AD-18 | Tenant-id bound 128 appears in 8 places across 3 repositories with no shared source. | OPEN |
| AD-19 | Are hub, exchange, replay-bundle and action-manifest reference values in scope for the migration program? | OPEN |
| AD-20 | Consequence-tier delay ceilings (T0 4h … T4 30d) are proposed and unenforced; owner confirmation needed (BLOCK | OPEN |
| AD-21 | Claim-scanner term tables: in scope of the Registry? | OPEN |
| AD-22 | Origin of the effect cap (W8-091): minimum of three declared integers; who owns each? | OPEN |
| AD-23 | F10 tier: Tier 3 supportable (worker) vs Tier 2 minimum (S02 section 3). | OPEN |
| AD-24 | Several test names cited by S02 are NOT FOUND in current Runtime tests; confirm the cited equivalents. | OPEN |

## 4. Preservation

The original machine-readable evidence is unchanged and remains in `docs/family-migration/g0/`. Corrections discovered after the freeze are recorded additively in [g0-erratum.md](g0-erratum.md), never by editing G0 files.
