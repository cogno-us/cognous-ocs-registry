# R08 contract `r08-v2`: Amendment 4 (trusted authorization pin: independently authenticated operation identity at the effect boundary; versioned addendum, DRAFT)

Status: **DRAFT AMENDMENT 4 to [`docs/r08-v2-contract.md`](r08-v2-contract.md), a versioned addendum. NOT effective until the Architect merges it.** It is read on top of the frozen text together with Amendments [1](r08-v2-contract-amendment-1.md), [2](r08-v2-contract-amendment-2.md) and [3](r08-v2-contract-amendment-3.md) and the ADR `decisions/2026-10-26-adr-ext-s4-0-integration-contract.md`. It edits no hash-pinned file. Documentation and contract tests only: it adds no code and authorizes no implementation, no deployment and no new trust root beyond the bounded local profile named in section 2. It changes no canonical binding member (the 14 members of contract 4 are unchanged, no claim member is added), no Registry log schema, no policy-generation rule, and no Control Plane decision authority. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD. Nothing here is "qualified".

Authorization: the Architect approved Option 1 (trusted-writer authorization pin) and the twelve binding decisions of the F-A1 reconciliation directive (2026-10-27) for the **design** only. Finding F-A1 (HIGH, candidate; `cogno-us/cognous-stack-qualification` PR #235, head `7b72de9a`): the Registry operation label that selects the activated record is read by the Runtime guard only from the claim's own policy binding, so a claim supplier that rewrites it to another validly activated operation and recomputes the (unkeyed) claim commitment obtains an effect that the true operation refuses. Compromise of the normal Control Plane issuance workflow was **not** demonstrated; the finding is that the Runtime holds no independently authenticated statement of the operation that was authorized.

**Central invariant.** The operation used for Registry authority enforcement MUST be the operation independently authorized by the Control Plane. A matching pair of supplier-controlled values does not establish authorization.

## 0. Frozen records stay frozen

| Frozen file | git blob (`git hash-object`) | sha256 |
|---|---|---|
| `docs/r08-v2-contract.md` | `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f` | `64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01` |
| `docs/r08-v2-contract-amendment-1.md` | `081dae56b8fdd3736022900f8dc224eafcd96189` | `dddc71ba19b2c853fea223cb3cd1ab0ed38ef606a55473381621f5581fbce0d0` |
| `docs/r08-v2-contract-amendment-2.md` | `e082331d729a6b07b2210a4fd02a06bba3a393c6` | `14f972f670892a60ebf2abeb354a644136b4544475afacd8b0e55738796e090c` |
| `docs/r08-v2-contract-amendment-3.md` | `c9bf1d39d60c4f15962855aa39e5d814052f2e77` | `e75b29125d71a922fc6f6087dfb10b7a50e2f7d714e6605b3575256a911e013f` |
| `docs/decisions/2026-10-26-adr-ext-s4-0-integration-contract.md` | `86cfef73b6f5b9cdb98f5d60108ed2c8af5ac925` | `d25af05dca5b466c5d274e1ca9e8085de727b13a1504356660f4b0e3f03f7e8c` |

`tests/test_contract_amendment_4_pins.py` recomputes these values and checks every quoted excerpt below against the frozen text. If a frozen file changes, that test fails and this addendum must be re-anchored by a new amendment, never by a silent edit.

## 1. Supersession and reconciliation table

| # | Frozen anchor | Frozen text (verbatim excerpt, tested as a substring) | Effect of this amendment |
|---|---|---|---|
| A-1 | `r08-v2` section 7.4, intro | `Executor-supplied metadata is never authority` | Extended, not weakened: the claim's `operation` and `consumer_id` are claim-carried assertions and are never the source of the governed scope for a pin-required destination (section 5). |
| A-2 | `r08-v2` section 7.4, item 2 | `the scope key built from the claim's` | Superseded **for a pin-required destination only**: the scope key is built from the authenticated pin members (section 5, step 6), and the claim's binding must equal them. Where the destination is not pin-required, item 2 is unchanged. |
| A-3 | `r08-v2` section 8, item 1 | `One trusted writer per store; never seeded from a claim, a selection or a caller-supplied value` | Applied unchanged to the pin store (section 3): exactly one trusted writer, never seeded from a claim. `provision_claim` is forbidden to create, replace, revoke or modify a pin. |
| A-4 | ADR 3.1 | `A separate store for selection state is not permitted: it cannot be atomic with the commit.` | Not contradicted. The pin store is **authorization state, not selection state** (section 8). Its inability to share a SQLite transaction with the effect is the reason section 6 defines a fence protocol and discloses its limits instead of claiming SQLite atomicity. |
| A-5 | ADR 3.6 | `A restore to a point between the last anchor update and the store head is undetectable by construction` | Applies unchanged to the pin store (section 7). A consistent restore of the pin store and its anchor is undetectable and is an explicit residual limit. |
| A-6 | ADR 7.5 | `Once committed, a later revocation or withdrawal does not roll the effect back` | Unchanged. Section 6 defines which effects are ordered before a revocation, and does not claim to undo them. |
| A-7 | Amendment 3, section 2, item 5 | `Items 1 to 4 do not read any claim member other than the already-validated` | Unchanged for the F-01 containment step. The new pin step (section 5) precedes it and is the only addition that reads claim members, and it reads them only to compare them with the pin. |

Nothing else in the frozen text is superseded. In particular: F-01 five-set containment (Amendment 3), the existing typed reason codes, the claim commitment validation, evidence-write atomicity, and "claim with no binding" (7.4 item 8) for a destination that is **not** pin-required are unchanged.

## 2. Trust model: exactly three roles

1. **Control Plane Authorization Authority (CPAA).** The Control Plane workflow. It alone makes and persists authorization decisions (`decide()`), and issues the approval-committed policy binding. It is the sole decision authority. This amendment gives it no new decision power.
2. **Trusted Authorization Installer (TAI).** A host-operated process running under a **dedicated OS identity** (the *installer identity*), outside the Runtime package. It authenticates persisted CPAA provenance (section 3.2) and installs, and only it installs, versioned pin state into the pin store. It makes no authorization decision: it only transcribes what the CPAA persisted and committed.
3. **Runtime Effect Executor (REE).** The Runtime destination. It reads installed pin state **read-only**, enforces it inside the existing atomic effect transaction, and cannot create, replace, delete, revoke or expand a pin.

A **claim supplier is none of these.** It runs as (or provides inputs to) the executor identity, and has no equivalent authority.

**Bounded local deployment profile (the only profile this amendment defines).** Handoff authenticity is **enforced OS custody**: no new HMAC, signature or Ed25519 scheme is introduced or authorized. The profile REQUIRES all of the following, and the guarantees below hold only if every item is true (a deployment that cannot show them is **not** in the profile):

- P-1. The installer identity, the executor identity and the CPAA service identity are distinct from the claim supplier's identity, and the supplier has no shell, credential or code-execution path into the installer or CPAA identities.
- P-2. The pin store directory, pin store file, fence file and anchor (section 7) are owned by the installer identity (the anchor by its custodian), mode `0644` files in a `0755` directory chain not writable by the executor identity at any ancestor.
- P-3. The CPAA persisted-decision store, its lock, the resolver store, and the host-config `RuntimeAuthorityProfile` (including its `policy_binding`) are writable only by the CPAA/installer identities and are readable by the installer.
- P-4. The pin store path, anchor path, fence path and the `authorization_pin_required` property are host configuration of the destination fixed at construction by the host. No claim, executor argument or caller value can set or redirect them.
- P-5. The executor opens the pin store with SQLite URI `mode=ro`, and the pin store is in rollback-journal mode (`journal_mode=DELETE`), never WAL: a WAL database cannot be opened read-only across OS identities.

**Explicitly excluded (assumptions, not proven defenses):** compromise of the installer identity; compromise of root or of the host; direct arbitrary writes to the pin store, its anchor or the CPAA stores; compromise of the CPAA; a supplier able to run arbitrary code as the executor identity and write the effect database directly (that supplier needs no claim). SQLite has no table-level write permissions: the boundary is the **file and OS identity**, never a table or a Python method.

### 2.1 Adversary capabilities (claim-supplier threat model)

| Adversary action | Outcome required by this amendment |
|---|---|
| Controls all claim content | Claim members are assertions; the pin is the authority (section 5). |
| Recomputes the unkeyed `claim_commitment` / `operation_commitment` | Refused unless the binding digest equals the pinned `binding_digest`; recomputing a hash over supplier data is not evidence. |
| Calls `provision_claim` and other ordinary methods | `provision_claim` writes no pin; for a pin-required destination, rows it first-writes (grant, approval, policy, evidence) do not confer authority (section 5, step 4). |
| Chooses the executable policy | Unchanged: F-01 containment against the activated record applies (Amendment 3). |
| Substitutes another validly activated operation | Refused: `pin_binding_mismatch`. |
| Selects another activated Registry record | The scope key is built from the pin; a different record cannot be selected. |
| Replays stale authorization (older pin, older revision, withdrawn decision) | Refused: terminal status, revision mismatch, or anchor regression (sections 4 and 7). |
| Writes, replaces, deletes or restores a pin file as the executor identity | Denied by OS permissions (P-2); **only when P-2 is actually deployed** and qualified by the real-OS tests of section 11. |

## 3. Normative contract: pin, handoff and writer

### 3.1 The authorization pin (`ocs-s4/authorization-pin/0.1`)

One pin row binds one persisted CPAA decision. Its **identity key is `decision_id`**. The payload members are existing canonical identifiers; no member is invented except the three installer-owned members marked (I).

| Member | Source (existing) |
|---|---|
| `tenant_id`, `institution_id`, `authority_domain` | persisted decision binding (`TenantAuthorizationBinding`) / authority context |
| `consumer_id`, `operation` | canonical binding body (14 members, contract 4), authenticated by `binding_digest` |
| `decision_id`, `effect_id`, `action_id` | persisted decision |
| `grant_id`, `grant_revision` | persisted decision binding |
| `approval_commitment` | persisted `decision.binding.runtime_authority` (lineage evidence) |
| `binding_digest`, `selection_epoch`, `activation_ref`, `policy_generation` | approval-committed policy binding (`PolicyBinding`) |
| `not_before`, `expires_at` | grant validity from the authority context (intersection already used for the claim interval) |
| `pin_epoch` (I) | strictly increasing integer per pin store |
| `status` (I) | `active`, `withdrawn`, `revoked`, `superseded` |
| `prev_pin_digest`, `pin_digest` (I) | hash chain over the canonical row bytes |

`grant_revision` is compared for equality only (it is not ordered in the Control Plane); order comes only from `pin_epoch`. `policy_generation` tracks selection activation and is not a grant/approval revision. A new `pin_epoch` is justified because no existing authorization-side member is monotone (Control Plane has no authorization high-water; ADR 4.2 generations belong to selection).

The pin is **append-only**: a row is never updated or deleted. The current state of a decision is its row with the highest `pin_epoch`.

### 3.2 Trusted handoff: source provenance and installer authentication

The CPAA exposes one minimal export (design level; a Control Plane change, separate PR): `export_authorization_pin(workflow, decision, *, snapshot, policy_binding_body) -> closed dict of the 3.1 CPAA-sourced members`. It is called by the installer, inside the existing handoff region (the same region in which claim issuance validates the snapshot), under the resolver handoff lock, and it:

1. loads the **persisted** decision from the CPAA record store (not a caller object) and requires it authorized;
2. re-resolves grant, approvals, policies and evidence under the handoff and runs the existing issuance validation (so a withdrawn/expired/superseded/unknown grant or approval yields no pin);
3. recomputes `catalogue_digest` from the **installer-owned host-config profile** and requires equality with the persisted `decision.binding.runtime_authority.catalogue_digest`, and recomputes `approval_commitment` from the handoff context and requires equality with the persisted value;
4. takes the canonical binding body and requires `binding_digest(body)` to equal the host-config `policy_binding.binding_digest` (the check issuance already makes), and also requires `selection_epoch` and `activation_ref` equality with it;
5. returns only values derived from steps 1 to 4. It never reads a claim, a caller-supplied `expected_*` kwarg as a source, or a Runtime row.

**What this proves and does not prove.** It proves that the host-config profile equals the profile the persisted decision committed to and that the binding body is the one the host configured. It does **not** prove CPAA approval authenticity (the existing trust model is unsigned, `docs/policy-binding-approval-generation.md` of the Control Plane), that the activation is still current (the Control Plane has no durable memory of Registry state), or that the host-config binding was built correctly from consumer state (ADR 4.1). Authenticity of persisted CPAA state rests on P-3. This is the stated trust-root limit; no cryptographic strengthening is authorized here.

**Writer capability.** Only the installer identity can open the pin store read-write (P-2). The installer holds no write access to the effect database, the selection tables, the Runtime package, or the claim path. It performs no network call inside any Runtime transaction.

### 3.3 Installation preconditions, idempotency and conflict

- Preconditions: step 3.2 succeeded; the anchor is available and consistent (section 7); no existing row for `decision_id` has a terminal status.
- Revision: `pin_epoch` = previous head epoch + 1.
- **Idempotency:** installing a payload whose canonical digest equals the current non-terminal row for `decision_id` is a no-op returning the existing epoch.
- **Conflict:** a different payload for an existing `decision_id`, any `active` row after a terminal row for the same `decision_id`, or a non-monotone `pin_epoch` is refused by the installer, logged, and **HOLDs** the Runtime if it is ever found in the store (section 5, step 3, `pin_conflict`).
- **Evidence:** every installer action appends a record `{action, decision_id, pin_epoch, pin_digest, fence_mode, anchor_before, anchor_after, outcome, installed_at}` to an installer-owned append-only log, outside the executor identity's write access.

## 4. Lifecycle

| Event | Installer action | Runtime effect |
|---|---|---|
| Initial installation | append `active` row for the new `decision_id` | claims for that decision may pass the pin step |
| Approval renewal / revision increase | a **new decision** (new `decision_id`, new `grant_revision` and/or `approval_commitment`) gets a new `active` pin; the old decision's pin is appended `superseded` | the old pin refuses once superseded; the claim's `grant_revision` must also equal the pin's |
| Supersession | append `superseded` | refuse |
| Withdrawal (approval or selection withdrawn upstream) | append `withdrawn` | refuse |
| Revocation (grant or approval revoked upstream) | append `revoked` | refuse |
| Expiry | none: derived from `expires_at` at the lock-time clock | refuse outside `[not_before, expires_at)` |
| Crash | see section 7 table | fail closed |

Terminal statuses (`withdrawn`, `revoked`, `superseded`) are **irreversible**: no later row may re-activate the same `decision_id`. An older approval's pin therefore cannot regain authority after withdrawal or replacement; regaining authority requires a fresh decision, a fresh pin and, per contract 7.5, a fresh approval under the current policy generation. An old `approval_commitment` is never reused as evidence of a new authorization.

## 5. Effect-time guard (inside the existing `BEGIN IMMEDIATE`)

For a destination configured `authorization_pin_required` (P-4), inside the existing atomic effect transaction, after the claim-state validation and before the Registry selection guard:

1. **Anchor and store verification.** Read the anchor (section 7) and open the pin store `mode=ro`. Anchor absent, unreadable, inconsistent, or the store unreadable, or `pin head < anchor.committed` or `anchor.intent > pin head`, or the hash chain from the anchored head to the store head broken: **HOLD** (`store_unknown`; causes `pin_anchor_unavailable`, `pin_anchor_inconsistent`, `pin_store_unreadable`, `pin_chain_broken`).
2. **Lookup.** Select the pin by the claim's `decision_id` (already compared to the envelope's by the claim-state check) and take the row with the highest `pin_epoch`. No row (store verified): **REFUSE** (`policy_identity_mismatch`; cause `pin_absent`). Pin lookup is by `decision_id` only, never by a path, label or scope key supplied by the claim.
3. **Conflict.** Non-monotone epochs, a non-terminal row after a terminal row, or two rows for one epoch: **HOLD** (`store_unknown`; cause `pin_conflict`).
4. **Status, freshness, lineage.** `status` is `active`; the lock-time clock is inside `[not_before, expires_at)`; the claim's `effect_id`, `action_id`, `tenant_id`, `institution_id`, `authority_domain`, `grant_id` and `grant_revision` equal the pin's; the claim's approval/grant rows in the effect database agree with the pin (for a pin-required destination those first-written rows confer no authority of their own; a disagreement refuses). Else **REFUSE** (`policy_identity_mismatch`; causes `pin_status:<status>`, `pin_not_valid_now`, `pin_lineage_mismatch:<member>`).
5. **Authorized operation vs claim.** `binding_digest(claim.policy_binding)` equals `pin.binding_digest`, and independently `consumer_id`, `operation`, `scope.tenant`, `scope.institution`, `scope.authority_domain`, `selection_epoch` and `activation_ref` of the binding equal the pin's. Else **REFUSE** (`policy_identity_mismatch`; cause `pin_binding_mismatch:<member>`). The digest function MUST be the one pinned by the shared vectors of `canonical_policy_binding`; its output is compared, never trusted from the claim.
6. **Registry selection from the authenticated operation.** The existing guard of contract 7.4 runs with its scope key built from the **pin's** `consumer_id`, `tenant`, `institution`, `authority_domain`, `operation` (and the digest-bound `family`), not from the claim. The pin never chooses a record, epoch or policy: the activated row, record identity, epoch, revocation, generation, trust-snapshot and expiry checks of 7.4 are unchanged and still decide.
7. **Containment and the rest.** Amendment 3 five-set containment, revocation, generation, trust, evidence-write and budget checks are unchanged and still required.
8. **Receipt.** The effect receipt records `pin_epoch`, `pin_digest` and the anchor `committed` value used, so the order of any later change is provable by epoch rather than by wall clock.
9. **Commit** only when every check holds. A claim with no binding on a pin-required destination is **refused** (`policy_identity_mismatch`; cause `pin_required_binding_absent`): an omitted binding cannot bypass the pin and there is no legacy fallback for a required scope. Legacy (ungoverned) execution exists only on a destination that is explicitly **not** configured pin-required, and carries no F-A1 guarantee.

Any exception or inconsistency in steps 1 to 9 refuses or HOLDs; it never skips a step. No network call, registry call or socket inside the transaction.

## 6. Serialization and revocation-effective point

A separate SQLite file cannot join the effect transaction, and a second read of a separate database does **not** by itself establish atomic revocation (Architect decision 7). This amendment therefore defines one serialization order with an explicit lock, and states exactly what it guarantees.

**Fence.** One advisory lock file (`flock`) owned by the installer identity, mode `0644`, openable read-only by the executor (verified: `flock` shared and exclusive locks work on a read-only descriptor across OS identities, and a crashed holder releases the lock).

**Executor order.** (1) acquire the fence **shared** with a non-blocking deadline (failure: HOLD `verifier_unavailable`, cause `pin_fence_unavailable`); (2) `BEGIN IMMEDIATE` on the effect database; (3) section 5 steps 1 to 9, including the pin read; (4) `COMMIT` or rollback; (5) release the fence. Lock order is always fence then effect database. The installer never touches the effect database, so no cycle exists.

**Installer order for a terminal transition (withdraw, revoke, supersede).** (1) write the anchor intent; (2) try to acquire the fence **exclusive** with a deadline; (3) commit the pin row (`pin_epoch` N+1, rollback-journal commit, fsync); (4) release the fence; (5) write the anchor committed value; (6) append installer evidence recording `fence_mode`. Installation of a new `active` pin needs no fence (granting new authority cannot produce a post-revocation effect).

**Revocation-effective point.** A withdrawal, revocation or supersession becomes effective at Runtime at the **commit of its pin row** (step 3). Consequences:

- **D.** Every effect whose pin read follows that commit sees the terminal status and is refused.
- **Fenced mode** (exclusive fence acquired): no effect transaction is in flight when the row commits, so every effect's pin read, guard and commit lie wholly before or wholly after the row. No effect commits after the row with an older pin epoch.
- **Degraded mode** (deadline expired, for example a stalled or hostile shared holder): the row still commits and still refuses every later pin read, but an effect whose pin read preceded the commit may commit after it, bounded by that transaction's own lifetime. Such an effect is **ordered before** the revocation (E): its receipt carries the older `pin_epoch`, and the installer evidence says `fence_mode=degraded`. A revocation is never reported as preceding an effect whose receipt epoch is lower. A holder can force degraded mode but cannot prevent the row from committing or make any later pin read succeed.
- **F.** The check-then-commit race across the two files is **closed in fenced mode and bounded but not eliminated in degraded mode.** This is a disclosed limit (compare ADR 7.5), not a claim of SQLite atomicity.

**Propagation delay.** This amendment does not claim instantaneous Control Plane to Runtime revocation. Between the moment the CPAA records a withdrawal/revocation and the pin-row commit, effects pass under the then-current pin. That interval depends on the installer's reconciliation cadence, which the operator sets, and is reported as a residual risk. The existing Runtime-owned invalidating writers (grant/approval/policy status setters) remain in force and are additional, not replaced.

The fence is advisory: it binds code that takes it. It binds the honest Runtime path (the destination), which is the enforcement point; a supplier that executes arbitrary code in the executor process is excluded in section 2.

## 7. Anti-rollback and recovery (anchor)

An externally custodied monotonic **anchor** is required for the qualified anti-rollback profile (Architect decision 6).

**Anchor (`ocs-s4/pin-anchor/1`):** `pin_store_id`, `committed_epoch`, `committed_head_digest`, `intent_epoch`, `intent_head_digest`, `anchored_at`. It is held **outside the pin store it protects and outside its restore domain**, by a custodian the operator designates. It is written only by the installer protocol below; the executor identity can only read it.

**Update order.** (1) write `intent_epoch = N+1`; (2) commit the pin row; (3) write `committed_epoch = N+1` (and clear `intent`). Each write is an atomic replace of a small file with an fsync of file and directory.

**Runtime decision table** (pin head `H`, anchor committed `C`, intent `I`):

| State | Runtime |
|---|---|
| `I = C = H` | accept |
| `I = H = C+1` (crash after the row commit, before the committed write) | accept; the installer finalizes on restart |
| `I > H` (crash before the row commit, **or** a rolled-back store; indistinguishable) | **HOLD** until the installer reconciles |
| `H < C` (store older than the anchor) | **HOLD** |
| anchor absent, unreadable or malformed | **HOLD**; lost state is unknown, never zero |
| anchor older than the store (`C < H`) with an intact chain | accept; an old anchor is ahead-of-it store, not a rollback |
| pin store and anchor both restored consistently to an older point | **UNDETECTED** (disclosed limit, ADR 3.6) |

**Recovery.** After a crash the installer reads the anchor and the store head, completes or abandons the intended epoch only by an explicit logged reconcile, and never resets a terminal status. A recovery that cannot show chain continuity from the anchored head leaves the store `unknown` (HOLD) and requires an explicit, logged re-baseline by the operator; it does not start from empty tables.

**Custody and qualification blocker.** The protocol is defined and the crash windows above are enumerated, but **no code can prove that the anchor is externally custodied**. A deployment that stores the anchor in the same restore domain as the pin store (for example the same volume restored by the same backup) satisfies the HOLD rows only against partial restores, not against a consistent restore, and is **not** qualified for anti-rollback. Anti-rollback is therefore qualified only for a deployment whose anchor custody the operator demonstrates as outside that restore domain; absent that, the anti-rollback guarantee is **unsupported** and is recorded as a qualification blocker, not deferred silently. No atomicity between SQLite and the external anchor is claimed beyond the three-step order and decision table above.

## 8. ADR reconciliation (3.1 and EXT-S4-0)

- **Selection state vs authorization state.** ADR 3.1 forbids a separate store for *selection state*: the closed table set of 3.2 (activation state, log, high-water, ratchet, revoked sets, snapshot) that decides which Registry record governs a scope, written only by the activation writers from Registry-signed statements. The pin store holds none of that: it holds the Control Plane's own authorization tuple (section 3.1). It is written from persisted CPAA decisions, never from a Registry statement, and it selects, replaces or overrides no Registry record, epoch, policy or scope row. The guard still resolves the Registry row through the unchanged selection store; the pin only fixes which `operation` and `consumer_id` the scope key is built from and requires the claim to equal it. The pin carries `selection_epoch` and `activation_ref` as identity members to compare, not as state to apply. The Registry and the Control Plane hold no authority copy of selection state, as before.
- **Atomicity.** ADR 3.1's reason for one database ("only one database gives one transaction") is respected for selection state, which stays in the effect database. The pin store cannot share that transaction because OS-level writer isolation requires a separately owned file; section 6 replaces the missing single transaction with a fence and states the limit rather than assuming atomicity.
- **One trusted writer per store.** Selection store: unchanged. Pin store: the installer alone, never seeded from a claim (A-3).
- **EXT-S4-0 7.1 / 7.4 / 12 item 8.** The guard still runs inside `BEGIN IMMEDIATE` on the effect database; the 14-member claim tuple is unchanged and no claim member is added; typed refusals use existing codes only (`policy_identity_mismatch`, `store_unknown`, `verifier_unavailable`; no new reason code).
- **r08-v2 and Amendments 1 to 3.** Section 1 lists every reconciled sentence. Amendment 1 4.3 (`policy_identity_mismatch` covers all identity members) is the reason the pin refusals reuse that code. Amendment 3 is untouched.

## 9. Fail-closed summary and typed reasons

| Condition | Result | Code | Cause string |
|---|---|---|---|
| anchor/pin store unreadable, inconsistent, chain broken, conflict | HOLD | `store_unknown` | `pin_anchor_unavailable`, `pin_anchor_inconsistent`, `pin_store_unreadable`, `pin_chain_broken`, `pin_conflict` |
| fence unavailable within the deadline | HOLD | `verifier_unavailable` | `pin_fence_unavailable` |
| no pin, terminal status, outside validity, lineage or binding mismatch, binding absent on a required destination | REFUSE | `policy_identity_mismatch` | `pin_absent`, `pin_status:<status>`, `pin_not_valid_now`, `pin_lineage_mismatch:<member>`, `pin_binding_mismatch:<member>`, `pin_required_binding_absent` |

Missing, invalid, stale, conflicting or unavailable pins prohibit governed effects. There is no silent fallback and no widening of legacy fallback.

## 10. Required evidence

Per effect: receipt members `pin_epoch`, `pin_digest`, anchor `committed_epoch`. Per installer action: the installer log record of 3.3. Per qualification run: the case ledger with exact component pins and OS identities used (section 11).

## 11. Qualification requirements

- A case battery with acceptance criteria declared before implementation: [`docs/f-a1-authorization-pin/qualification-plan.md`](f-a1-authorization-pin/qualification-plan.md) (at most 30 local executions; not run by this PR).
- **Writer-separation claims require real OS privilege-isolation tests** with at least two distinct non-root OS identities (installer, executor), real file ownership and modes, and `mode=ro` opens. Synthetic in-process mocks alone are insufficient evidence and must be reported as such.
- Independent requalification of V08 against the patched components is a separate authorized step. This amendment is not evidence that F-A1 is closed.

## 12. Residual risks (stated, not closed)

1. Trust root is OS custody of the installer identity and of the CPAA stores (P-1 to P-4). Compromise of the installer, of root, or of the CPAA defeats the boundary.
2. The CPAA record store, resolver and host-config profile are unsigned (`docs/policy-binding-approval-generation.md`); installer authentication of the handoff is not cryptographic.
3. A consistent restore of the pin store and its anchor is undetectable; external anchor custody is an operator item that code cannot prove.
4. Degraded fence mode leaves a bounded in-flight window; fenced mode closes it.
5. The revocation reconciliation cadence sets the Control Plane to Runtime propagation delay.
6. A supplier or crash can leave the fence or a hot journal such that executors fail closed (availability loss, not an integrity break).
7. Other first-writer rows written by `provision_claim` (grant, approval, policy, evidence) remain supplier-seeded; for a pin-required destination they confer no authority beyond agreement with the pin, but hardening them is outside this amendment.
8. `max_amount`, `allowed_target_prefixes` and the executor-integrity limits of Amendment 3 section 3 remain.
9. Implementation is unauthorized; no part of this contract has been executed against code.

## 13. Compact implementation sequence (not authorized)

See [`docs/f-a1-authorization-pin/implementation-proposal.md`](f-a1-authorization-pin/implementation-proposal.md): (1) Control Plane export; (2) host installer and pin library; (3) Runtime guard and `provision_claim` restriction; (4) deployment profile and OS-isolation test harness; (5) independent qualification. Each step is a separate, Architect-reviewed PR in its own repository.
