# V04 implementation handoff (inventory and starting point; NOT AUTHORIZED)

- Status: **HANDOFF INVENTORY ONLY. V04 is NOT AUTHORIZED.** A separate Architect directive is required before any V04 work. This page designs nothing new; it extracts what the adopted documents already fix. Where a source is silent it says so.
- Governing sources: [static plan v1.5](plans/PROJECT_PLAN-v1.5.md) section 4 (V04 row), [EXT-S4-0 ADR](decisions/2026-10-26-adr-ext-s4-0-integration-contract.md) (cited as ADR §), [r08-v2 contract](r08-v2-contract.md) (cited as contract §), and the baseline pins in [v03-cross-component-baseline.md](v03-cross-component-baseline.md): Registry `943ab183`, Runtime `b86fa5db`, Control Plane `1bee3696`.
- V04 scope per plan v1.5: **Runtime** durable scope-bound selection, activation, withdrawal, ratchet, generations, high-water, lineage and exact 24-member log; restore/anchor fence. Exit: durable state and replay negatives pass; any unknown/corrupt state HOLD.
- Out of V04: the effect-time guard inside `execute_claim_atomic`, typed refusal, evidence stream and I/O-in-transaction negatives are **V05**. V04 must not begin them.

## 1. Durable selection-state ownership

- Owner: the enforcing component. For Route B this is the Runtime destination (ADR §3.1; TR-01 decision 2). All selection state lives **in the same SQLite database file and connection discipline** as `execution_claims_v1`, `effect_budgets_v1` and the effect rows. A separate store is not permitted (it could not be atomic with the commit). Registry and Control Plane hold no copy that counts as authority.
- Exactly one trusted writer set: `activate_selection` and `sync` (names to be confirmed, ADR O-5), plus the revoke path inside `sync`. No claim, selection, caller value or UI request writes state; `provision_claim` seeding is never reused (ADR §3.1; contract §8 item 1).
- Closed table set (ADR §3.2, nine tables, one name set): `selection_activation_v1`, `selection_log_v1`, `selection_highwater_v1`, `selection_revoked_v1`, `selection_scope_required_v1`, `selection_generation_v1`, `selection_lineage_v1`, `selection_store_meta_v1`, `selection_evidence_v1`. Scope key and the three counters (`selection_epoch`, `policy_generation`, `activation_sequence`; no conversion between them) are defined in the same section.
- `policy_generation` is owned and issued by the Runtime writer, per governed scope, never derived from the epoch; the Control Plane reads it and compares by equality only (ADR §4.1–4.2). Range 1..2147483647 (ADR §4.3).
- Confirmed absent today (V03 grep of Runtime `engine/` at `b86fa5db`): no `selection_*` table, no `scope_required`, no `activate_selection`, no `sync` writer. **O-5 is therefore open**: the writer names are proposals, not existing symbols.

## 2. Activation and withdrawal boundaries

- Log entry types are the closed four `{activate, withdraw, revoke, sync}` (not extended). `sync` carries `cause` in `{none, baseline, ratchet_provision, non_participation}`; `revoke` may carry `issuer_key_revoked` (ADR §3.3).
- Every state change and its log entry commit in **one** `BEGIN IMMEDIATE` transaction; a half-completed activation rolls back (contract §8 item 2). The writers use the same file and the same locking as the effect path (ADR §7.1).
- `activation_ref` = the `entry_hash` of the `activate` log entry (ADR §3.3; contract §4.2). It is filled by the enforcing gate, never by the Registry; the Registry produces the binding with it null.
- Withdrawal: a `withdraw` entry bumps the generation (unless saturated), so an approval carrying the earlier generation fails equality (`approval_policy_generation_mismatch`, direction behind) (ADR §4.2). Withdraw and revoke are never blocked by saturation (AD-1; ADR §4.2, §10).
- One lineage per governed scope: the first `activate` binds `selection_id`; a different `selection_id` for an `activate` or `withdraw` is refused `selection_conflict` / `lineage_replacement_prohibited`. Carry-forward to a new lineage is **defined but NOT authorized** in V1 (ADR §3.7 item 4).
- Unacknowledged publication reads `UNKNOWN`, not `ACTIVE`; restart before the first successful `sync` refuses required scopes (contract §8 item 5; ADR §3.6).

## 3. Scope-bound high-water and anti-rollback requirements

- `high_water_epoch` is kept per scope key (per lineage) in `selection_highwater_v1`; the snapshot high-water record (version, fingerprint, `valid_until`) is a singleton. A statement at or below the high-water cannot be re-activated; the old lineage's high-water row is retained forever (ADR §3.2, §3.7 item 3).
- Revoked `(selection_id, epoch)` pairs and revoked issuer `key_id`s are **never deleted and never scoped away** (`selection_revoked_v1`).
- The `scope_required` ratchet is keyed by **governed scope**, set one-way (by activating a `required` selection or an authenticated `ratchet_provision` entry), never seeded from a claim/selection/caller/UI, never cleared by selection, withdrawal, revocation, replay, restart or restore. `relax_scope_required` is **not authorized in V1** and no path may exist for it (ADR §3.4).
- Generation counters are keyed by governed scope and continue across any `selection_id`; starting value is the latest `baseline` entry's `baseline_floor` (0 at genesis) (ADR §4.2).
- Epoch saturation (2147483647) and generation saturation are terminal for re-activation in V1; revoke still works (ADR §3.7 item 5, §10).
- Replay rule: replaying the log derives row state, lineage binding, high-water, generation counter, revoked pairs/keys, log head, and the ratchet as the **OR of every `ratchet_after = true`**; a replay that clears a ratchet is a hash-chain/replay failure (ADR §3.3).
- Log, evidence and revoked-set rows are insert-only; there is no update or delete path in V1 (ADR §3.5).

## 4. The 24-member audit-log obligation (ADR §3.3)

Entry hash = `"sha256:" + hex(sha256(b"ocs-reg/s4/log-entry\n" + canonical_bytes(entry)))`. The entry has **exactly 24 members, all always present** (a non-applicable member is JSON `null`; never omitted), serialized with the Registry `canonical_bytes`:

1 `entry_version` (`ocs-s4/log-entry/1`) · 2 `activation_sequence` (1..2^53−1, gap-free, store-wide) · 3 `prev_entry_hash` (64 zeros only at sequence 1) · 4 `entry_type` · 5 `cause` · 6 `governed_scope_digest` · 7 `scope_key_digest` · 8 `selection_id` · 9 `selection_epoch` · 10 `selection_digest` · 11 `policy_generation` · 12 `supersedes` (object with `selection_id`, `epoch`, `selection_digest`, or null) · 13 `participation` · 14 `state_before` · 15 `state_after` · 16 `ratchet_after` · 17 `snapshot_version` · 18 `snapshot_fingerprint` · 19 `issuer_key_id` · 20 `reasons_registry_label` (always non-null; allow-list `{runtime-authority-reasons/0.3}`) · 21 `reasons_registry_sha256` (always non-null; allow-list `{sha256:58b29ef74b9bd49d3eae7278d8cce73c7cbc6a1095a07f7b9fa44f48a7b8c07f}`) · 22 `recorded_at` (lock-time clock, UTC with six fractional digits) · 23 `baseline_floor` · 24 `determination_ref`.

- The `entry_type` × `cause` × nullability matrix in ADR §3.3 is closed: any other combination is refused at write and rejected at replay (AR-25).
- The writer refuses (`field_invalid`) any entry whose members 20/21 are null or outside the allow-list; no default to 0.2 (AR-24). This is consumer custody of the build pin, not authenticated issuer publication, and every report must say so.
- `baseline` and `non_participation` require a non-null `determination_ref`; `non_participation` has extra preconditions (store `known`, ratchet unset, no authority-changing history for the scope) (ADR §3.3, AD-4).

## 5. Restart, restore and external-anchor failure controls

- `store_state = unknown` until baselined; lost state is unknown, never zero. Genesis baseline only for a `store_id` with **no anchor and no prior log anywhere**; recovery baseline only when a retained log copy passes chain verification and replay reproduces **every anchored digest**, with `baseline_floor` = the anchor's `generation_ceiling`. With no verified log copy the store stays `unknown`; **V1 provides no empty-table baseline** (ADR §3.6; AR-26).
- Anchor `ocs-s4/store-anchor/1` members: `store_id`, `head_sequence`, `head_entry_hash`, `evidence_head_sequence`, `evidence_head_hash`, `generation_ceiling`, `scope_required_digest`, `lineage_digest`, `highwater_digest`, `revoked_set_digest`, `floor_min_epochs_digest`, `floor_min_trust_snapshot_version`, `anchored_at`; digests are recomputed by replaying the log prefix to `head_sequence`, never from current tables. It is held **outside** the database it protects and advanced after each acknowledged log head.
- At open and before every guard: anchor absent, unreadable, ahead of the store, a different entry hash at the anchored sequence in either stream, a replay that does not reproduce the anchored digests, or a broken chain makes `store_state = unknown` → HOLD (`UNKNOWN_FAIL_CLOSED`) for every participation; required scopes refuse; optional scopes do not fall back. A store ahead of a stale anchor is accepted only if the chain from the anchored head verifies.
- Disclosed, unchanged limits: a database restore rolls revoked set and high-water back together and is detected only as far as the anchor is fresh; **a restore to a point between the last anchor update and the head is undetectable by construction**. V1 has no automatic custody mechanism; the anchor custodian, authentication and cadence are operator-gated. The emulator profile may use a host-held anchor file and must say so in every status report (ADR §3.6, §12 DT-01).
- Negatives to cover (ADR §11, state-side rows): AR-08, AR-10, AR-12, AR-17, AR-18, AR-21 (state part), AR-22, AR-23, AR-25, AR-26, AR-27. Rows that need the effect-time guard (AR-01..AR-07, AR-09, AR-13..AR-16, AR-19, AR-20) are **V05**, except where a V04 test can assert the state side alone.

## 6. Existing interfaces V04 must reuse

Runtime @ `b86fa5db` (do not reimplement):

- `engine/local_authority_effect.py`: `AtomicAuthorityEffectDestination(root, *, clock, database_name)` over `DurableRefundDestination`; its `_connect()`, the trusted `clock`, `BEGIN IMMEDIATE` discipline, `_transaction_stage` seams, and the existing tables (`authority_grants_v1`, `authority_approvals_v1`, `authority_policies_v1`, `authority_evidence_v1`, `execution_claims_v1`, `effect_budgets_v1`, `authority_effect_receipts_v1`, the revocation tables). New tables belong in the same database via this connection discipline.
- `engine/atomic_local_control_plane_executor.py`: `AtomicLocalControlPlaneExecutor` (`provision_claim`, `execute`, `reconcile`). V04 does not change the executor path.
- `engine/registry_f1a_narrowing.py` (V01): the only Registry-facing entry (raw-text inputs, exact `Ed25519Verifier`, host-supplied trust). Registry is resolved from the host environment, not vendored; do not add a Registry copy or dependency to Runtime (`m1_20`).
- Registry (reuse, do not fork): `registry_successor.common.canonical_bytes` (the log-entry serializer, ADR §3.3), `registry_successor.decision.verify_and_decide_v2`, and the EXT-S1-8 conformance kit (`registry_conformance/`, merged via PR #28; vectors include policy state, guard, concurrent writers, state tampering and verdict semantics) as the vector source for transition behaviour. The kit defines the pure transition function only and is **not** an authoritative store (contract §8 item 7).
- Control Plane (read side only): approval-side `policy-binding/0.1` (`binding_digest`, `selection_epoch`, `activation_ref`, `policy_generation`, `disposition`) and the V02 canonical binding; a host builds the Control Plane binding from a **read** of the Runtime state (ADR §4.1).

## 7. Protected code V04 must not modify

- Runtime `engine/safe_executor.py` (blob `2fc880da…`) — never modified.
- Runtime V01 adapter `engine/registry_f1a_narrowing.py` and its tests — frozen unless a defect is demonstrated and separately authorized.
- Control Plane `bounded.py` (`2cc8d998…`), `policy_binding.py` (`426d4779…`), `runtime_authority.py` (`0b2c5e49…`) and the frozen legacy claim vectors — untouched.
- Registry `record.py` (frozen by the EXT-S1-5 boundary guard) and the merged r08-v2 contract/ADR text (no normative edits; amendments only by Architect decision).
- Do not edit the guard call inside `execute_claim_atomic` in V04: that insertion (ADR §7.4 notes it edits two existing Runtime files) is V05.
- No new normative contract member, reason code, claim authorization path or policy interpreter.

## 8. Missing contracts and genuine blockers

Genuine blockers for **production**, not for an emulator-profile V04:
- Anchor custodian, its authentication and cadence (ADR §12 DT-01) — operator-gated; V04 may use a host-held anchor file and must label it so.
- Trust root, key ceremony, snapshot channel custody — operator-gated; synthetic keys only.
- Independent human cryptographic reviewer and Tier 1 lead — not designated; Ed25519 review OPEN; PRs #26/#34 SECURITY-HELD.

Open items V04 must resolve or ask about (not blockers to starting once authorized):
1. **O-5**: writer and claim function names are unconfirmed; none exist at `b86fa5db` (V03 check). The Architect must confirm names or delegate the choice.
2. (Resolved by reading ADR §3.2: the closed set is the nine tables listed in section 1; no open question.)
3. Whether V04 carries Runtime-side snapshot-floor inputs: `verify_and_decide_v2` has none (M1-13 NOT RUN); the plan places floor enforcement at V04/V05.
4. Count wording: ADR §12 item 8 says "14 members" of the binding; contract §4 names 15 and V02 implements 15. The named schema governs (plan v1.5 §5); a corrective ADR amendment is for the Architect.
5. Lineage carry-forward and `relax_scope_required` are explicitly NOT authorized; V04 must not add them.
6. CCTV vector-license status remains open (plan v1.5 §5).

Next implementation dependency: **V04 needs an explicit Architect authorization plus confirmation of O-5 (writer/claim names).** Nothing else in the Registry, Control Plane or Runtime pins blocks it.
