# ADR-REG-S4-0: EXT-S4-0 consolidated integration and authority contract

- Status: **PROPOSED for Architect adoption (draft PR).** Docs only. **Nothing is implemented, activated, approved, qualified or released.** Every decision below becomes a contract only when the Architect adopts this ADR; until then it is a builder proposal.
- Authorization: Architect directive "EXT-S4-0 — NEXT EXECUTION TURN" (2026-10-26): one bounded contract PR; no EXT-S4 implementation; do not wait for a human cryptographic reviewer.
- Evidence status: **BUILDER-AUTHORED. AI-REVIEWED (one technical review, see the PR). NOT INDEPENDENTLY SECURITY-ASSESSED. NOT TIER 1 QUALIFIED.** No AI review in this program is independent qualification.
- RELEASE / PUBLICATION / PRODUCTION: HOLD. TIER 1: NOT STARTED. EXT-S4 implementation: NOT AUTHORIZED.
- Pins read (reading only, nothing executed against them): Registry `0fca88c6f6e945e608e8072d0e7c4d5713a4ed2e`; Control Plane `fff27ebf356007e1eb3bb24198efc7e3e3f0c5eb`; Runtime `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (`engine/local_authority_effect.py`, `engine/atomic_local_control_plane_executor.py`); Stack Qualification `67dcaeffc955ef1b91388e0abd1ceff8eb87834c`. `engine/safe_executor.py` is not read for change and is never modified.
- Preserves unchanged: `r08-v1`; `r08-v2` contract and amendment 1; ADR EXT-S1-1 (D-01..D-31) and amendment 1; ADR-REG-TR01; DR-CP-AGE-1; the EXT-S1-5 spec and vectors; Control Plane reasons 0.1 (121), 0.2 (164, frozen) and 0.3 (172, immutable); `policy-binding/0.1`; `approval-commitment/0.2`; Stack Qualification historical evidence. This ADR supersedes only where section 2 says so, by reading rule (merged files are not edited).

## 0. What this ADR resolves

| Item | Section | Disposition |
|---|---|---|
| Durable `scope_required` activation ratchet | 3.4 | Resolved |
| Consumer policy-generation ownership and custody; **N-8** | 4 | Resolved |
| `activation_sequence` versus `selection_epoch` (and `policy_generation`) | 3.2, 4.4 | Resolved |
| Authenticated withdrawal transition identity | 5 | Resolved |
| Optional-fallback eligibility and evidence; **N-7** | 6 | Resolved |
| Atomic Route B effect-time verification | 7 | Resolved; one Runtime/typed-refusal requirement for `EXT-S4-2` |
| Authenticated registry-label / evidence custody | 8 | **Architect decision AD-2** (two alternatives; recommendation) |
| Eight reasons-0.3 classifications | 9.2 | Resolved as consumer-boundary classes; names still await ratification (AD-3) |
| REFUSE / REFUSE_STALE / HOLD | 9.1 | Resolved at the consumer boundary; Control Plane outcome change is **AD-3** |
| **N-9** epoch saturation | 10 | **Architect decision AD-1** (two alternatives; recommendation) |
| Fallback basis strictness; `cause` vocabulary | 6.1, 3.3 | **Architect decisions AD-4, AD-5** |

## 1. Required invariants and where each is enforced

| # | Invariant | Enforced by |
|---|---|---|
| I-1 | The Registry never authorizes external effects | The Registry produces signed statements and a binding with `activation_ref = null`; it holds no activation state, issues no grant, calls no consumer (TR-01 decisions 5, 9) |
| I-2 | The consumer owns durable activation authority | Section 3: one trusted writer in the enforcing component's own store; ownership per family fixed by plan v1.3 section 5 and TR-01 |
| I-3 | Unknown authority fails closed | 3.6 (store states), 7.3 (unreadable state), 9.1 (HOLD), 9.3 (unknown reason code) |
| I-4 | Withdrawal cannot revive stale approvals | 4.2 (generation bumps on every withdraw), 5, mandatory six-step sequence D-16 |
| I-5 | Effect-time verification is atomic with commit | 7 (same database, same `BEGIN IMMEDIATE`, lock-time clock) |
| I-6 | No fallback from missing or unknown durable state | 6.1 (fallback bases are positive, authenticated state; absence of a row alone is never a basis) |
| I-7 | No silent version or authority downgrade | 3.4 (ratchet), 4.3 (closed versions), 9.3 (unknown code or version refuses), 5 (disposition is recorded, never inferred) |
| I-8 | Historical evidence stays immutable | Section 2 (supersession by reading rule), 3.5 (append-only), no edit to any merged file |

## 2. Reading rules and supersession (no merged file is edited)

| Frozen text | Read from now on as |
|---|---|
| Contract 8.3 and 7.4 line 8: "optional scopes report `overlay_not_applied`" for a restored or unknown store | Already superseded by Amendment 1 S-13/N-12: an unknown store is `UNKNOWN_FAIL_CLOSED` (HOLD) for every participation. This ADR keeps that and states it again in 3.6 |
| EXT-S1-5 spec section 12, N-7, N-8, N-9 "UNRESOLVED"; Amendment 1 section 349 and 367 | Resolved by sections 6, 4.1 and 10 of this ADR **when adopted** (N-9 pending AD-1) |
| Control Plane `docs/policy-binding-approval-generation.md`: `activation_sequence` RESERVED; withdrawn disposition PROVISIONAL | `activation_sequence` is defined in 3.2 and stays **outside** `policy-binding/0.1` and outside the claim in V1; the withdrawn shape is fixed in 5.2 and is the shape the Control Plane already implements, so the word PROVISIONAL is removed by adoption without a Control Plane change |
| Control Plane reasons 0.3 ownership record: eight names PROPOSED; HOLD everywhere | Classification in 9.2 is a consumer-boundary table; the Control Plane keeps returning `hold` (AD-3 alternative A). Names remain unratified until the Control Plane owner and Architect ratify (AD-3) |
| Contract 7.1 "`EXT-S4-0` freezes whether negative evidence shares the hash-chained log or is a companion stream" | Companion stream (6.3) |
| ADR D-17 fallback reasons `never_activated`, `withdrawn`, `expired` | Only the two N-12 bases survive (6.1); `expired` is superseded by N-12(c) (already recorded in Amendment 1 S-15) |
| TR-01 DT-01..DT-07 | DT-02 (high-water design) is answered by section 3; DT-04 by 3.6; DT-06 by 5 and 6.3; DT-01 (host naming) remains open (section 12) |

## 3. Durable consumer state

### 3.1 Owner and location

The enforcing component owns activation (TR-01 decision 2). For **Route B** that is the Runtime destination. All selection state lives **in the same SQLite database file, and is written through the same connection discipline, as the claim, budget and effect tables** (`execution_claims_v1`, `effect_budgets_v1`, effect rows), because only one database gives one transaction (7.1). A separate store for selection state is not permitted: it cannot be atomic with the commit. The Registry and the Control Plane hold no copy that counts as authority; a Control Plane host profile is a **read** of this state (4.1).

There is exactly one trusted writer: the activation writers `activate_selection` and `sync` (names to confirm at re-pin, O-5) and the revoke path inside `sync`. No claim, selection, caller value or UI request writes state directly. `provision_claim` seeding is never reused for state.

### 3.2 Table set (one closed name set)

| Table | Purpose | Key |
|---|---|---|
| `selection_activation_v1` | current row per scope: `activation_state` in `{active, withdrawn, revoked}`; no row = never activated | scope key |
| `selection_log_v1` | the single hash-chained, append-only activation log; closed `entry_type` in `{activate, withdraw, revoke, sync}` (not extended) | `activation_sequence` |
| `selection_highwater_v1` | `high_water_epoch` per scope; snapshot high-water record (version, fingerprint, `valid_until`) | scope key / singleton |
| `selection_revoked_v1` | terminal revoked `(selection_id, epoch)` pairs and revoked issuer `key_id`s | pair / key |
| `selection_scope_required_v1` | the `scope_required` ratchet, one row per scope key | scope key |
| `selection_generation_v1` | `policy_generation` counter per scope key | scope key |
| `selection_store_meta_v1` | `store_state` in `{known, unknown}`, store identity, baseline anchor reference | singleton |
| `selection_evidence_v1` | companion negative and fallback evidence stream (6.3) | `evidence_sequence` |

**Scope key** = the canonical ASCII tuple `(selection_id, consumer_id, tenant, institution, authority_domain, operation, family)` serialized exactly as the registry `canonical_bytes` profile (contract 4.1) and digested as `scope_key_digest` (`sha256:` + 64 lowercase hex). Identifier grammar is the contract 4.1 grammar; anything else refuses `field_invalid`.

**`activation_sequence`** (defined here, closes the Control Plane RESERVED member): the 1-based, gap-free position of an entry in the **store-wide** log, an integer in `1 .. 2^53 - 1`. It is assigned by the writer inside the transaction that writes the entry, it is part of the entry hash preimage, and the pair `(activation_sequence, entry_hash)` of the newest entry is the **log head** used by the restore fence (3.6). It is **consumer-assigned, evidence-only, never signed by an issuer, never an input to any approval, claim or Control Plane profile in V1, and never compared with, derived from or substituted for `selection_epoch` or `policy_generation`.** Putting it into a claim or a profile needs a new binding version (`policy-binding/0.2`); it is not an additive member of `0.1` (which refuses unknown members).

**Three counters, three owners, no conversion between them:**

| Name | Assigned by | Scope | Range | Used for |
|---|---|---|---|---|
| `selection_epoch` | selection issuer (signed statement) | per `selection_id` lineage within a scope | 1 .. 2147483647 | supersession order and high-water |
| `policy_generation` | consumer writer (4.2) | per scope key | 1 .. 2147483647 | approval continuity (D-16) |
| `activation_sequence` | consumer writer | store-wide log position | 1 .. 2^53 - 1 | log order, anchor, restore fence |

### 3.3 Log entry (hash chain)

Entry hash = `"sha256:" + hex(sha256(b"ocs-reg/s4/log-entry\n" + canonical_bytes(entry)))` where `entry` has exactly: `entry_version = "ocs-s4/log-entry/1"`, `activation_sequence`, `prev_entry_hash` (`sha256:` + 64 zeros only for sequence 1; sequence 1 is written only by the baseline operation of 3.6), `entry_type`, `scope_key_digest`, `selection_id`, `selection_epoch`, `selection_digest` (or `null` for `sync`), `statement_digest`, `policy_generation` (activate, withdraw, revoke only; `null` for `sync`), `supersedes` (the triple `(selection_id, epoch, statement_digest)` or `null`), `participation`, `state_before` and `state_after` (`activation_state` of the scope row, or `none`), `ratchet_after` (boolean), `snapshot_version`, `snapshot_fingerprint`, `issuer_key_id`, `cause`, `recorded_at` (lock-time clock). The closed **`entry_type`** set is not extended; the closed **`cause`** set is `none`, `issuer_key_revoked`, `baseline` (sequence 1 and re-baselines, a `sync`-class entry), `ratchet_provision` (sets the ratchet, a `sync`-class entry) and `non_participation` (records an authenticated never-required scope, a `sync`-class entry, 6.1). A `sync`-class entry with cause `baseline`, `ratchet_provision` or `non_participation` never activates, withdraws, selects or authorizes anything; it can only tighten (set a ratchet, record a baseline or a non-participation fact). `state_before`/`state_after` and `ratchet_after` make the row and ratchet **re-derivable by replaying the log**, so a row with no matching entry is detectable. These two objects (log entry, evidence row) are serialized with the registry `canonical_bytes` function under their own value rules (JSON `null` and nested triples are permitted in them); contract 4.1's no-`null` rule applies to the completed policy binding only. The digest-prefix constants differ per object so no hash can be replayed as another object's hash.

`activation_ref` (D-14) = the `entry_hash` of the `activate` entry. Because the preimage includes scope, epoch, selection digest, generation and sequence, it identifies one activation event and cannot be reused across scopes, epochs, generations or restores.

### 3.4 The durable `scope_required` ratchet (A4, D-06, contract 7.3)

- Set **one-way** by the writer, inside the same transaction, when a `required` selection is activated for the scope, or by explicit authenticated provisioning of the ratchet (a `sync`-class log entry with `cause = ratchet_provision` and `ratchet_after = true`; `entry_type` is not extended).
- **Never seeded from a claim, a selection presentation, a caller value or a UI request.** Never cleared by selection, withdrawal, revocation, replayed older statement, restart or restore.
- Once set: any presentation of `optional` for the scope (per call, per selection, per withdrawal) refuses `participation_mismatch`; a claim with no binding refuses (7.3 line 8(a)); a withdrawn or revoked scope is `REQUIRED, UNAVAILABLE` and refuses.
- **The only relaxation, `relax_scope_required`, is defined by contract 7.3 and is NOT authorized in V1.** No writer, entry type or code path exists for it. Adding one needs an ADR amendment and operator authorization.
- The ratchet is covered by the hash chain (every set is a log entry) and by restore custody (3.6). A restored store whose ratchet differs from the anchor is `unknown`, never "optional".

### 3.5 Append-only and immutability

Log, evidence and revoked-set rows are insert-only. There is no update or delete path in V1. Row state changes (`selection_activation_v1`) are always paired, in one transaction, with the log entry that explains them. Historical entries are never edited, re-hashed or compacted.

### 3.6 Store state, restore fence and anchor

- `store_state = unknown` until baselined. Lost state is unknown, never zero (contract 8.3 item 3). A store is baselined only by an explicit, logged `baseline` operation that writes sequence 1 and records the anchor reference.
- **Anchor** (`ocs-s4/store-anchor/1`): `store_id`, `head_sequence`, `head_entry_hash`, `evidence_head_sequence`, `evidence_head_hash`, `generation_ceiling` (the largest `policy_generation` issued in the store), `scope_required_digest` (digest over the sorted `(scope_key_digest, set)` pairs), `highwater_digest`, `revoked_set_digest`, `floor_min_epochs_digest`, `floor_min_trust_snapshot_version`, `anchored_at`. The digests are defined **at `head_sequence`** and are recomputed by replaying the log prefix up to that sequence (3.3), never from current tables. The anchor is held **outside the database it protects**, by a custodian the operator designates, and is advanced after each acknowledged log head.
- At open and before every guard, the Runtime compares the store with the anchor. **Anchor absent, unreadable, ahead of the store (`head_sequence` or `evidence_head_sequence` greater than the store's), a different entry hash at the anchored sequence in either stream, a log-prefix replay that does not reproduce the anchored digests, or a broken chain between the anchored head and the store head makes `store_state = unknown`.** A store *ahead* of a stale anchor is accepted only if the chain from the anchored head to the store head verifies. An unknown store is HOLD (`UNKNOWN_FAIL_CLOSED`) for **every** participation (N-12); required scopes refuse; optional scopes do not fall back (invariant I-6).
- Restart before the first successful `sync` refuses required scopes (contract 8.3 item 5). Unacknowledged publication reads `UNKNOWN`, not `ACTIVE` (DT-04).
- **Disclosed limit, unchanged:** a database restore rolls the revoked set and high-water back together; this is detected only to the extent the external anchor is fresh. **A restore to a point between the last anchor update and the store head is undetectable by construction** (the anchor is advanced after acknowledged heads, so a window exists); anchor cadence is an operator item. V1 provides **no automatic custody mechanism**: the anchor custodian, its authentication and its update cadence are operator-gated production items (section 12). The emulator profile may use a host-held anchor file and must say so in every status report.

## 4. Consumer policy-generation ownership and custody (N-8)

### 4.1 Ownership

`policy_generation` is **owned and issued by the enforcing consumer's trusted writer**, not by the Registry, not by the Control Plane and not by the selection issuer. It is *opaque to the Control Plane* (equality only; `policy-binding/0.1` is unchanged). A Control Plane policy-binding for a decision is **built by the host from a read of this state** (`binding_digest` from the registry binding, `selection_epoch`, `activation_ref`, `policy_generation`, `disposition`). The Control Plane never writes the generation and never infers it from the epoch (it is never derived from `selection_epoch`).

### 4.2 Issuance rule (generation continuity, D-16)

Per scope key, in `selection_generation_v1`, inside the transaction of each log entry:

- first `activate` for the scope: generation = 1;
- every later `activate`, `withdraw` or `revoke` that changes the row's state: generation = previous + 1;
- `sync` entries and refused transitions: no change;
- a `revoke` of a pair that is not the row's current epoch changes no row state and does not bump.

The generation never decreases and a state never returns to an earlier generation, so **withdrawing a narrowing yields a new, higher generation** and an approval carrying the earlier generation fails equality (`approval_policy_generation_mismatch`, direction *behind*). The generation is part of the entry hash preimage (3.3), so `activation_ref` fixes it: an approval/claim pair that agrees on `activation_ref` necessarily agrees on the generation. **Saturation (generation 2147483647):** only `activate` refuses (`field_invalid`, member `policy_generation`). `withdraw` and `revoke` are **never blocked by saturation**: they still write their log entry and change row state, the generation stays at the maximum (no bump), and the approval/claim chain is still severed because the new entry has a new `entry_hash`, so a prior `activation_ref` no longer matches (`approval_policy_activation_mismatch`). A saturated scope can therefore always be disabled, including `issuer_key_revoked`; it can only not be re-activated (remedy class of AD-1: new lineage).

### 4.3 Range and version (resolves N-8)

V1 range is **1 .. 2147483647**, the range the merged `policy-binding/0.1` already enforces (strict `int`, never `bool`). This is a **subset** of the placeholder 1 .. 2^53 - 1 named by N-8, so nothing already merged is invalidated; a wider range needs a new `policy-binding` version, never a silent widening. The commitment version is the closed set `{approval-commitment/0.2}` plus the legacy preimage, which is admissible **only where no governed policy exists for the scope** and is refused (REFUSE) for any scope that has a row, any history, a set ratchet, or an `unknown` store; an approval naming any other version refuses `approval_commitment_version_unsupported` even if its commitment matches. The enforcing component never accepts a version or authority form it does not recognize (I-7).

### 4.4 Custody

Generation, activation reference, log head and ratchet are covered by the same anchor and restore fence (3.6). A restored older store cannot re-issue an earlier generation because an older store than the anchor is `unknown`. Re-baselining after a restore must start every scope's generation **above the anchor's `generation_ceiling`** (and above any higher value the retained evidence shows); the baseline operation takes that floor as an input and refuses without it. If the anchor is lost or untrusted, the operator must supply a floor in writing that exceeds every generation ever issued; a re-baseline that cannot establish a floor leaves the store `unknown`. Because `activation_ref` is a fresh entry hash after any re-baseline, an approval from before the restore also fails on `approval_policy_activation_mismatch` even if a generation were reused.

## 5. Authenticated withdrawal transition identity

### 5.1 Identity

A withdrawal is an `r08-v2` selection statement with `disposition = withdraw` (A1/D-02) that names its predecessor (`supersedes` is required and exactly the current row), has a strictly higher epoch and no record pin. When the consumer applies it, it writes one `withdraw` log entry. The **withdrawal transition identity** is `transition_ref = entry_hash` of that `withdraw` entry (same `sha256:` + 64 lowercase hex form as `activation_ref`; one canonical representation, no second form). Its preimage includes the withdrawal statement digest, the issuer `key_id` that verified, the superseded triple, the new epoch and the new generation, so it is authenticated by the issuer's verified signature and bound to the consumer's own chain; neither side can forge it alone.

### 5.2 Control Plane shape (replaces PROVISIONAL)

For a withdrawn scope the host-supplied `policy-binding/0.1` is: `disposition = "withdrawn"`, `selection_epoch` = the withdraw statement's epoch, `activation_ref = transition_ref` of the withdraw entry, `policy_generation` = the withdraw entry's generation, **no** `binding_digest`, **no** `age_ceilings`. This is exactly the shape already implemented and validated at Control Plane `fff27ebf`; no Control Plane change is required.

### 5.3 Rules

- A withdrawn disposition is built by the host **only for an optional scope** whose ratchet is unset. For a ratcheted (required) scope the gate refuses upstream as `REQUIRED, UNAVAILABLE` and builds no authorizing profile. This is a **consumer obligation, not a Control Plane enforcement**: `policy-binding/0.1` accepts a withdrawn disposition for any scope and a withdrawn binding still matches an approval locally (documented Control Plane limit). The obligation is tested by AR-14. A withdrawn-disposition approval can never reach an effect through a binding-carrying claim: the claim's `activation_ref` would be a `transition_ref`, which never equals an `active` row's `activation_ref` (7.2), so the guard refuses. The optional fallback therefore proceeds only through a **no-binding claim** under 6.1.
- Withdrawal does not clear a revoked pair, does not lower the high-water, does not lower the ratchet, and does not reactivate any earlier approval (4.2).
- Reversal is only a fresh authenticated higher-epoch statement naming its predecessor, producing a new `activate` entry with a new generation and a new `activation_ref`.
- An invalid selection is reported under its own code and is never relabelled `selection_withdrawn` (D-02).

## 6. Optional-fallback eligibility and evidence (N-7)

### 6.1 Eligibility (closed; restates N-12/N-12(c) as one table)

The fallback to the caller policy (`overlay_not_applied`, `applied=false`, original `registry_code`, `fallback=caller_policy`) is admissible **only** when all of the following hold, read from trusted durable state under the guard lock, never from the claim or executor:

1. the scope is **optional** and `scope_required` is **unset**;
2. `store_state = known` and the anchor check passes;
3. exactly one positive, authenticated basis holds:
   - **`never_required_governed_policy`**: no row and no history for the scope key, the scope key is projectable, and the log holds a `sync`-class entry with `cause = non_participation` for that `scope_key_digest` (written only by the trusted writer from an authenticated non-participation determination); the **absence of a row alone is never this basis** (I-6; a refused projection never establishes it);
   - **`valid_withdrawal_fallback_transition`**: the current row is `withdrawn` by an authenticated `withdraw` entry of an optional selection (5.1), and the transition did not revive previous authority.

This is deliberately **stricter than contract 7.4 item 8(c)** ("no row and no history"); see AD-4. `selection_expired`, `selection_revoked`, `issuer_key_revoked`, `selection_epoch_stale`, unknown store, `family_unsupported`, `contract_unsupported` and any refused projection **never** admit the fallback. Revoked is a definitive refusal.

### 6.2 Evidence record `ocs-s4/fallback-evidence/1`

Written for every admitted fallback and every refused fallback attempt, with exactly these members: `record_version`, `evidence_sequence`, `prev_evidence_hash`, `scope_key_digest`, `outcome` (`fallback_admitted` or `fallback_refused`), `fallback_basis` (`never_required_governed_policy`, `valid_withdrawal_fallback_transition`, or `none`), `registry_code` (the original code, for example `selection_withdrawn`, `field_invalid`), `projection_refusal_code` (present only for a refused projection; `null` otherwise; **this closes the open layout in the EXT-S1-5 spec N-7**), `stage`, `member`, `original_selection_digest`, `transition_ref` (the withdraw entry hash, or `null`), `log_head_sequence`, `log_head_hash`, `ratchet_set` (boolean as read), `store_state`, `recorded_at`, `evidence_hash`.

### 6.3 Companion stream (decision of contract 7.1)

Evidence, negative evidence for rejected transitions and guard refusals live in `selection_evidence_v1`, a **companion append-only hash-chained stream**, not in `selection_log_v1`. Reasons: (a) the log vocabulary is closed and must not grow; (b) a guard refusal rolls back its transaction, so its evidence must be written afterwards in its own short transaction; (c) refused transitions never change authority state and must not be mistaken for it. **Exception that preserves atomicity:** the `fallback_admitted` row is inserted **inside the effect transaction** (before commit), so an admitted fallback never commits an effect without its evidence; only refusal rows are written after a rollback. Each evidence row records the log head it observed (`log_head_sequence`, `log_head_hash`) at its write time; that is corroborating evidence of ordering, not proof, and the evidence head is anchored (3.6) so truncation or rollback of the stream is detected. `evidence_hash` uses the domain `ocs-reg/s4/evidence\n`. Evidence write failure never converts a refusal into success and is itself surfaced (`evidence_unavailable`).

## 7. Atomic Route B effect-time claim verification

### 7.1 Atomicity (verified shape at Runtime `c5e97e87`)

`execute_claim_atomic` opens one `BEGIN IMMEDIATE`, reads the trusted clock **after** the lock, validates the claim state, reads grant, budget and operation rows, inserts the effect and commits in one SQLite transaction, with `_transaction_stage` seams (`after_begin`, `after_effect_insert_before_commit`). The selection guard is inserted **inside that same transaction**, after the lock-time clock is taken and before the effect insert, reading only rows in that connection. Consequences:

- no transition writer can interleave, because `activate`, `withdraw`, `revoke`, `sync` and ratchet writes also use `BEGIN IMMEDIATE` on the same file;
- no check-then-act gap exists outside the transaction;
- **no network I/O, registry call or socket inside the transaction**; the guard reads only local rows and the lock-time clock;
- an effect never commits against a row, epoch, revoked set, ratchet or generation that changed before the commit.

### 7.2 What the guard compares (contract 7.4, restated as the closed list)

Under the lock, a claim carrying a binding is refused unless every line of contract 7.4 holds (members well formed and `binding_digest` recomputed; scope key equal; row exists and `active`; `selection_id`, `selection_epoch`, `selection_digest`, record triple and **`activation_ref` equal the row**; epoch equals the scope high-water and meets the held floor; not revoked and issuer key not revoked; lock-time clock inside `[valid_from, valid_until)`; participation not weaker than the ratchet; snapshot version at or above the floor, fingerprint equal to the logged one, current snapshot record unexpired). `effective_policy_digest` is claim-carried evidence, checked for self-consistency only. Because `activation_ref` fixes the generation (4.2), **no separate generation member is carried in the claim** and the registry 14-member binding is unchanged.

### 7.3 Unreadable or indeterminate state

If any required row is missing, unreadable, inconsistent with the hash chain (a broken `prev_entry_hash`, a non-gap-free sequence, a row with no matching entry) or the store is `unknown`, the result is **HOLD** (`UNKNOWN_FAIL_CLOSED`), the transaction rolls back, no effect is written and no fallback is attempted.

### 7.4 Typed refusal (requirement for `EXT-S4-2`, no `safe_executor.py` change)

The Runtime atomic executor today maps every `PermissionError` to `authority_hold` / `current_authority_rejected` and carries only `str(exc)` (D-19). `EXT-S4-2` therefore raises a **subclass of `PermissionError` carrying a closed `code` and `refusal_class`** from the guard, defined in the new destination module. This **does edit two existing Runtime files**, as the S4-2 card already allows: the guard call inside `execute_claim_atomic` (`engine/local_authority_effect.py`) and a typed `except` before the generic one in `engine/atomic_local_control_plane_executor.py` that copies `code`/`refusal_class` into the result instead of only `str(exc)`; a subclass stays a `PermissionError`, so existing handling is preserved, and no code parses message text. `engine/safe_executor.py` is not touched. The profile activation checks (`_activate_profile`, `execute_claim_atomic`) refuse only the intent-profile and effective-grant tables; the selection tables in 3.2 are not among them, but `EXT-S4-2` must prove that with a test.

### 7.5 After commit

Once committed, a later revocation or withdrawal does not roll the effect back (disclosed limit, D07). Previously committed effects stay governed by their original effective-policy evidence; a current claim never reuses a stale identity.

### 7.6 Route A

Route A is not rechecked at the commit boundary (D-12) and every status report says so.

## 8. Authenticated registry-label and evidence custody

### 8.1 What exists

The Control Plane `registry_identity(label)` / `registry_admits` check a label against the build's own pinned digest. That is an **integrity check against the build, not an authenticated custody chain** (Control Plane docs). Reasons 0.3 cannot carry a per-code class (immutable bytes). The Architect's earlier ruling: the label-to-digest mapping must be retained with the evidence package and its trust must come from an authenticated publication or custody mechanism. **No such mechanism exists in any repository.**

### 8.2 Decision AD-2 (genuine conflict; Architect decision required)

**Conflicting requirements.** (R-a) The ruling that trust must come from an *authenticated publication or custody mechanism*. (R-b) The Registry may not gain a new signed statement kind without an `r08-v2` contract change, and the Control Plane has no signed-mapping contract; V1 must not invent one.

| | Alternative A (recommended): consumer-custody mapping | Alternative B: issuer-signed mapping statement |
|---|---|---|
| Mechanism | On each `activate`/`sync`, the enforcing component records, inside the hash-chained log entry, `reasons_registry_label` and `reasons_registry_sha256` of the registry its **own build pins**; every result row retains the label and the log head | A new `r08-v2` signed statement kind `registry-label-mapping` (label, sha256, code count) verified under the existing trust root and recorded on `sync` |
| Trust comes from | The consumer's own hash-chained, anchored log (custody by the enforcing component) | The existing issuer trust root (authenticated publication) |
| Changes needed | None to Registry or Control Plane contracts; Runtime log preimage gains two members at `EXT-S4-2` | New statement kind, verifier, vectors, trust-root governance; Registry + consumer PRs |
| Consequence | Proves *what the consumer's build pinned when it activated*, not what the issuer published; a build/registry mismatch is detected at activation and fails closed. Weaker against a compromised build | Closes the publication gap; but a new signed object extends the trust root's scope and needs its own review (and the independent cryptographic review that does not yet exist) |

**Recommendation: A for V1**, disclosed as a custody mechanism rather than authenticated publication, with B recorded as the successor if the Architect requires issuer-published mapping. Under A, status reports must not describe the mapping as "authenticated publication".

## 9. Outcome classes and the eight reasons-0.3 codes

### 9.1 Distinctions (closed, at the consumer boundary)

| Class | Meaning | Retry with the same input | Evidence `refusal_class` |
|---|---|---|---|
| `REFUSE` | Definitive: the request, binding, approval or configuration is invalid or unauthorized now | Never | `definitive` |
| `REFUSE_STALE` | **Not a new outcome kind.** A `REFUSE` whose cause is superseded, rolled-back or older authority (older epoch, older generation, earlier activation, withdrawn/revoked since); a fresh statement or approval at the current generation is the only remedy | Never with the same input | `stale` |
| `HOLD` | Authority state is unavailable, indeterminate or *ahead* of what can be verified (unknown store, expired current snapshot, carried generation above the durable generation); execution is prohibited; never success | Only after the state is restored or re-baselined | `indeterminate` |
| `DENY` | Evaluator policy denial on the `check` path (unchanged; not a registry-authority outcome) | Unchanged | n/a |

`refusal_class` is a member of the new companion record `ocs-s4/refusal-evidence/1`; `ocs-registry-failure-detail/1` is **not** changed. Stale epoch and withdrawal follow D-21 (REFUSE with a specific cause, HOLD only when indeterminate).

### 9.2 Classification of the eight proposed codes

The Control Plane keeps returning `hold` for all of them (systemic; `deny` is declared but never emitted, and no REFUSE_STALE exists). The **consumer boundary** classifies by the table below. Names remain PROPOSED, NOT RATIFIED (AD-3).

| Code | Class | Notes |
|---|---|---|
| `approval_commitment_version_unsupported` | REFUSE | definitive unsupported version |
| `approval_policy_generation_missing` | REFUSE | stripped or legacy approval; new approval required |
| `approval_policy_generation_invalid` | REFUSE | malformed |
| `approval_policy_generation_mismatch` | **by direction, decided by the consumer from durable state:** carried below the durable generation, REFUSE_STALE; carried above it, HOLD **for that decision only** (the profile or the store lags or was restored older; the anchor check of 3.6, not a single approval, decides `store_state`, so one stale or forged approval cannot force a store-wide HOLD) | The Control Plane compares equality only and stays opaque; direction comes from `selection_generation_v1`. If the durable generation is unreadable, HOLD |
| `approval_policy_activation_mismatch` | REFUSE_STALE if the carried `activation_ref` is an earlier `activate`/`withdraw` entry hash of the same scope in the log; REFUSE if it is not an entry of this scope's chain (substituted or foreign); HOLD if the log cannot be read | A digest has no order; the chain gives it one |
| `freshness_ceiling_exceeded` | REFUSE | trusted profile violates a ceiling |
| `freshness_ceiling_unanchored` | REFUSE | ceilinged profile without `anchor_deadline_to_inputs` |
| `policy_binding_invalid` | REFUSE | malformed trusted configuration |

### 9.3 Unknown codes, versions and authorities

A consumer that receives a reason code, registry label, commitment version, binding version or claim profile it does not recognize treats it as **HOLD with cause `unknown_reason`/`unknown_version`**, never as success and never as a downgrade to an older form. A v1 consumer never sees a v2-only code (D-02).

### 9.4 Decision AD-3 (genuine conflict; Architect decision required)

**Conflicting requirements.** (R-a) Batch 6 ruling 4.7 and D-21: definitive invalidity is REFUSE, stale is REFUSE_STALE, indeterminate is HOLD. (R-b) Control Plane `RuntimeDecision.result` is `authorized|hold|deny` and the gate emits only `hold`; changing it alters every existing definitive code, breaks golden and negative-control tests that assert `hold`, and reasons 0.3 is immutable.

| | Alternative A (recommended): consumer-boundary classification | Alternative B: Control Plane outcome change |
|---|---|---|
| Mechanism | Table 9.2 and class vocabulary 9.1 at the Runtime/host boundary; Control Plane unchanged | Control Plane emits `deny` for definitive codes and a new outcome kind for stale; new reasons registry revision if names change |
| Consequence | No Control Plane or registry-bytes change, and no re-pin; effect safety identical (any non-`authorized` result writes no effect). The Control Plane `hold` is not authoritative for classification, so every consumer must implement the table | One classification source, but a bounded Control Plane PR with owner and Architect review, a new reasons registry (0.4) if any name is renamed, golden-test churn and a further re-pin of Runtime and Qualification |

**Also required from the Architect/Control Plane owner:** ratify, rename or reject each of the eight names. Because 0.3 is immutable, a rename means a successor registry; the Qualification suite already keeps 0.2 (164) and 0.3 (172) as separate assertions and would add a third.

## 10. N-9 epoch saturation — Decision AD-1 (Architect decision required)

**Conflicting requirements.** (R-a) `selection_epoch` is bounded to 1 .. 2147483647 and a successor must name the same `selection_id` at a strictly higher epoch, so a scope at the maximum cannot advance **and cannot be withdrawn by statement** (withdraw also needs a strictly higher epoch). (R-b) the `r08-v2` bound is pinned in vectors, the Control Plane `INT_MAX` and the registry spec; changing it is a version change, not an edit.

| | Alternative A (recommended): accept fail-closed saturation | Alternative B: raise the ceiling |
|---|---|---|
| Mechanism | The scope stays in its current state and refuses further advance (`field_invalid`, member `selection_epoch`, typed). **Revocation is not epoch-gated** (it is keyed by `(selection_id, epoch)` and key id), so a saturated active scope can still be disabled by revoke (and, for generation saturation, 4.2 keeps withdraw and revoke available). The remedy is an operator procedure outside the Registry: issue a new `selection_id` lineage (new scope key) and activate it | Define a wider range (for example 1 .. 2^53 - 1) in a new `r08-v3`/`policy-binding/0.2` |
| Consequence | No contract change; at one new epoch per second the ceiling is about 68 years, so saturation is a theoretical operations case. Cost: a lineage rotation procedure to document and test (not built here) | Removes the case but is a coordinated version change across Registry, Control Plane and Runtime, with new vectors and a new re-pin; no current need |

Under A the same rule applies to `policy_generation` (4.2) and the evidence sequence.

## 11. Acceptance rows (named; assigned to the owning cards; no tests are written here)

| ID | Negative control | Must show | Card |
|---|---|---|---|
| AR-01 | Forged binding (altered member, recomputed commitment; altered stored claim JSON) | refused under the lock | S4-4, S4-2 |
| AR-02 | Substituted identity (each tuple member, `activation_ref` from another scope/epoch/event) | `policy_identity_mismatch` REFUSE | S4-2 |
| AR-03 | Expired at the lock (clock read after lock) | `selection_expired` REFUSE; never a fallback | S4-2 |
| AR-04 | Revoked before and after the lock | before: REFUSE; after commit: no rollback, disclosed | S4-2 |
| AR-05 | Stale epoch; row swapped between check and commit via `_transaction_stage` | `selection_epoch_stale` REFUSE_STALE; no effect | S4-2 |
| AR-06 | Grant/approval mismatch (neither alone suffices) | refused | S4-4, S4-2 |
| AR-07 | Change after authorization (withdraw, revoke, ratchet set after claim issue) | refused at commit | S4-2 |
| AR-08 | Restore/rollback: older store, ahead anchor, head hash mismatch | store `unknown`, HOLD for every participation | S4-2, S4-3 |
| AR-09 | Required-policy failure | never the caller policy | S4-2 |
| AR-10 | Ratchet downgrade by claim, selection, caller, restart, restore of older store | `participation_mismatch` / HOLD; ratchet survives restart | S4-2 |
| AR-11 | Six-step approval-revival sequence (D-16) with the generation counter | original approval stays invalid; fresh approval at the current generation succeeds | S3-4 (done), S4-3 |
| AR-12 | Generation direction: behind vs ahead | REFUSE_STALE vs HOLD | S4-2, S4-3 |
| AR-13 | Fallback bases: only the two positive bases admit; absent row alone, refused projection, expired, revoked, unknown store do not | per 6.1 | S4-2 |
| AR-14 | Withdrawn disposition on a ratcheted scope | refused upstream, no authorizing profile | S4-3 |
| AR-15 | Unknown reason code, label, version or profile | HOLD, never success | S4-2, S4-3 |
| AR-16 | Evidence write failure after a refusal; crash between an admitted fallback and its evidence | refusal stands, `evidence_unavailable` surfaced; an admitted fallback has its evidence in the same transaction or no effect | S4-2 |
| AR-17 | Saturation (epoch, generation) | activate refuses typed; withdraw and revoke (including `issuer_key_revoked`) still work and sever prior `activation_ref` | S4-2 |
| AR-18 | `activation_sequence` gap, hash-chain break, row with no matching entry, evidence-stream truncation | HOLD, store `unknown` | S4-2 |
| AR-20 | Legacy preimage presented for a scope with a row, history, ratchet or unknown store | REFUSE | S4-4, S4-2 |
| AR-21 | A single carried-ahead generation | HOLD for that decision; `store_state` unchanged | S4-2 |
| AR-19 | No registry call, socket or network I/O in a transaction | fails if any is made | S4-2, S4-3 |

## 12. Outstanding Architect decisions

1. **AD-1** N-9: accept fail-closed saturation with revoke and lineage rotation (A, recommended) or widen the ceiling (B).
2. **AD-2** Label/evidence custody: consumer-custody mapping (A, recommended, to be described as custody, not authenticated publication) or issuer-signed mapping (B).
3. **AD-3** Outcome vocabulary: consumer-boundary classification (A, recommended) or Control Plane outcome change (B); and ratification, rename or rejection of the eight proposed names.
4. **AD-4** Fallback basis 1: the strict positive `non_participation` log entry (A, recommended; narrower than contract 7.4 item 8(c), and drops `expired` per N-12(c)) or the literal "no row and no history, store known" reading (B; simpler, but a lost-then-rebaselined or never-provisioned scope would then fall back, which weakens invariant I-6).
5. **AD-5** The `cause` vocabulary additions (`baseline`, `ratchet_provision`, `non_participation`) as `sync`-class entries instead of new `entry_type` values (A, recommended; keeps the closed `entry_type` set) or an `entry_type` extension (B; needs an amendment to contract 7.1).
6. **DT-01** naming of the designated host/Runtime integration gate and **anchor custodian** (operator-gated for production; the emulator uses a host-held anchor).
7. **O-5** confirmation of the Runtime writer and claim function names at the re-pin.
8. Adoption of this ADR as the frozen claim-carried tuple (the 14 members of contract 4, **no new member**), digest profile (contract 4.1), table set (3.2) and entry vocabulary (3.3).

Not decided here, still open: independent human cryptographic review and the independent Tier 1 lead (GAP-G4-13); trust root and key ceremony; production anchor custody; any release, publication or production decision.

## 13. Recommended implementation sequence (not authorized)

1. Architect adopts this ADR and rules AD-1..AD-3 (docs only).
2. `EXT-S4-1`: **record "not required"** unless the Architect rejects 7.2 (no new claim member, so no residual wiring) and do not open the PR.
3. `EXT-S4-4` Control Plane claim-carried binding (serial; no `bounded.py` semantic edit; claim profile successor; no-binding claims byte-identical).
4. `EXT-S4-5` re-pin Runtime and Control Plane; supersede evidence at the old tuple.
5. `EXT-S4-2` Runtime destination: table set 3.2, writers, ratchet, anchor check, guard, typed refusal 7.4, evidence stream; never `safe_executor.py`.
6. If AD-3 ratifies renames: reasons successor registry and a third Qualification assertion; otherwise none.
7. `EXT-S4-3` registry-hosted emulator gate exercising AR-01..AR-19 end to end.
8. Independent qualification stays PREPARE-only until a lead is designated.

## 14. Limits of this ADR

- Docs only: no code was run, no vectors were generated, no digest in this ADR was computed by executing code. Runtime and Control Plane facts come from reading source at the pins above; the Runtime was not executed.
- Builder-authored; one AI technical review; no human cryptographic review; no independent qualification. The anchor, hash-chain and evidence designs are **designs**, not demonstrated properties.
- Section 3.6's restore detection is only as good as the external anchor's freshness; V1 provides no custody mechanism for it.
- RELEASE, PUBLICATION and PRODUCTION remain HOLD; Tier 1 NOT STARTED.
