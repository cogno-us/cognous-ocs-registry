# R08 contract `r08-v2`: Amendment 4 (trusted authorization pin: independently authenticated operation identity at the effect boundary; versioned addendum, DRAFT)

Status: **DRAFT AMENDMENT 4 (revision 2: revocation serialization corrected after the Architect's review of head `d83899bd`; no unfenced terminal transition exists) to [`docs/r08-v2-contract.md`](r08-v2-contract.md), a versioned addendum. NOT effective until the Architect merges it.** It is read on top of the frozen text together with Amendments [1](r08-v2-contract-amendment-1.md), [2](r08-v2-contract-amendment-2.md) and [3](r08-v2-contract-amendment-3.md) and the ADR `decisions/2026-10-26-adr-ext-s4-0-integration-contract.md`. It edits no hash-pinned file. Documentation and contract tests only: it adds no code and authorizes no implementation, no deployment and no new trust root beyond the bounded local profile named in section 2. It changes no canonical binding member (the 14 members of contract 4 are unchanged, no claim member is added), no Registry log schema, no policy-generation rule, and no Control Plane decision authority. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD. Nothing here is "qualified".

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
| A-6 | ADR 7.5 | `Once committed, a later revocation or withdrawal does not roll the effect back` | Unchanged. Section 6 defines the single serialized order in which a terminal transition becomes effective and which effects precede it, and does not claim to undo a committed effect. |
| A-7 | Amendment 3, section 2, item 5 | `Items 1 to 4 do not read any claim member other than the already-validated` | Unchanged for the F-01 containment step. The new pin step (section 5) precedes it and is the only addition that reads claim members, and it reads them only to compare them with the pin. |

Nothing else in the frozen text is superseded. In particular: F-01 five-set containment (Amendment 3), the existing typed reason codes, the claim commitment validation, evidence-write atomicity, and "claim with no binding" (7.4 item 8) for a destination that is **not** pin-required are unchanged.

## 2. Trust model: exactly three roles

1. **Control Plane Authorization Authority (CPAA).** The Control Plane workflow. It alone makes and persists authorization decisions (`decide()`), and issues the approval-committed policy binding. It is the sole decision authority. This amendment gives it no new decision power.
2. **Trusted Authorization Installer (TAI).** A host-operated process running under a **dedicated OS identity** (the *installer identity*), outside the Runtime package. It authenticates persisted CPAA provenance (section 3.2) and installs, and only it installs, versioned pin state into the pin store. It makes no authorization decision: it only transcribes what the CPAA persisted and committed.
3. **Runtime Effect Executor (REE).** The Runtime destination. It reads installed pin state **read-only**, enforces it inside the existing atomic effect transaction, and cannot create, replace, delete, revoke or expand a pin.

A **claim supplier is none of these.** It runs as (or provides inputs to) the executor identity, and has no equivalent authority.

**Bounded local deployment profile (the only profile this amendment defines).** Handoff authenticity is **enforced OS custody**: no new HMAC, signature or Ed25519 scheme is introduced or authorized. The profile REQUIRES all of the following, and the guarantees below hold only if every item is true (a deployment that cannot show them is **not** in the profile):

- P-1. The installer identity, the executor identity and the CPAA service identity are distinct from the claim supplier's identity, and the supplier has no shell, credential or code-execution path into the installer or CPAA identities.
- P-2. The pin store directory, pin store file, per-decision fence directory and files (section 6.1) and anchor (section 7) are owned by the installer identity (the anchor by its custodian), mode `0644` files in a `0755` directory chain not writable by the executor identity at any ancestor.
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
- **Evidence:** every installer action appends a record `{action, decision_id, pin_epoch, pin_digest, intent_digest, anchor_before, anchor_after, outcome (pending_blocked | complete | refused), recorded_at}` to an installer-owned append-only log, outside the executor identity's write access.

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

1. **Anchor, admission barrier and store verification.** Read the anchor (section 7) and open the pin store `mode=ro`, then apply the section 7 decision table: a `terminal` intent covering the claim's `decision_id` HOLDs it (`pin_transition_pending`); anchor absent, unreadable or inconsistent, store unreadable, `pin head < anchor.committed`, an intent in any other relation to the head, or a broken hash chain from the anchored head to the store head HOLDs every decision (`store_unknown`; causes `pin_anchor_unavailable`, `pin_anchor_inconsistent`, `pin_store_unreadable`, `pin_chain_broken`). The per-decision shared fence of section 6.2 is held across steps 1 to 9.
2. **Lookup.** Select the pin by the claim's `decision_id` (already compared to the envelope's by the claim-state check) and take the row with the highest `pin_epoch`. No row (store verified): **REFUSE** (`policy_identity_mismatch`; cause `pin_absent`). Pin lookup is by `decision_id` only, never by a path, label or scope key supplied by the claim.
3. **Conflict.** Non-monotone epochs, a non-terminal row after a terminal row, or two rows for one epoch: **HOLD** (`store_unknown`; cause `pin_conflict`).
4. **Status, freshness, lineage.** `status` is `active`; the lock-time clock is inside `[not_before, expires_at)`; the claim's `effect_id`, `action_id`, `tenant_id`, `institution_id`, `authority_domain`, `grant_id` and `grant_revision` equal the pin's; the claim's approval/grant rows in the effect database agree with the pin (for a pin-required destination those first-written rows confer no authority of their own; a disagreement refuses). Else **REFUSE** (`policy_identity_mismatch`; causes `pin_status:<status>`, `pin_not_valid_now`, `pin_lineage_mismatch:<member>`).
5. **Authorized operation vs claim.** `binding_digest(claim.policy_binding)` equals `pin.binding_digest`, and independently `consumer_id`, `operation`, `scope.tenant`, `scope.institution`, `scope.authority_domain`, `selection_epoch` and `activation_ref` of the binding equal the pin's. Else **REFUSE** (`policy_identity_mismatch`; cause `pin_binding_mismatch:<member>`). The digest function MUST be the one pinned by the shared vectors of `canonical_policy_binding`; its output is compared, never trusted from the claim.
6. **Registry selection from the authenticated operation.** The existing guard of contract 7.4 runs with its scope key built from the **pin's** `consumer_id`, `tenant`, `institution`, `authority_domain`, `operation` (and the digest-bound `family`), not from the claim. The pin never chooses a record, epoch or policy: the activated row, record identity, epoch, revocation, generation, trust-snapshot and expiry checks of 7.4 are unchanged and still decide.
7. **Containment and the rest.** Amendment 3 five-set containment, revocation, generation, trust, evidence-write and budget checks are unchanged and still required.
8. **Receipt.** The effect receipt records `pin_epoch`, `pin_digest` and the anchor `committed` value used, so the order of any later change is provable by epoch rather than by wall clock.
9. **Commit** only when every check holds. A claim with no binding on a pin-required destination is **refused** (`policy_identity_mismatch`; cause `pin_required_binding_absent`): an omitted binding cannot bypass the pin and there is no legacy fallback for a required scope. Legacy (ungoverned) execution exists only on a destination that is explicitly **not** configured pin-required, and carries no F-A1 guarantee.

Any exception or inconsistency in steps 1 to 9 refuses or HOLDs; it never skips a step. No network call, registry call or socket inside the transaction.

## 6. Serialization and revocation-effective point (strict order; no unfenced terminal transition)

A separate SQLite file cannot join the effect transaction, and a second read of a separate database does **not** by itself establish atomic revocation (Architect decision 7). This amendment therefore defines one serialized enforcement order built from three installer-owned mechanisms, and states what it does and does not guarantee. **No successful, effective terminal transition (withdrawal, revocation, supersession) may bypass the exclusive fence. There is no degraded or unfenced mode.** If the exclusive fence cannot be acquired, the terminal row is **not** committed, the committed authorization epoch does **not** advance, the transition is **not** reported effective, and it stays **pending** with its intent and provenance preserved.

### 6.1 Mechanisms

- **Per-decision fence.** One advisory lock file per pin `decision_id`, `fence_dir/<sha256(decision_id) hex>.fence`, created by the installer with the pin, owned by the installer identity, mode `0644`, in a directory the executor identity cannot write. It is openable read-only by the executor, and `flock` shared and exclusive locks work on a read-only descriptor across OS identities (verified by experiment; a crashed holder releases the lock). The executor derives the path from the claim's `decision_id` only through the fixed hash; the claim cannot name a path. An absent fence file refuses admission (HOLD `verifier_unavailable`, cause `pin_fence_unavailable`). The fence is **per decision** so that effects for unrelated decisions cannot prevent a terminal transition (see 6.4); `flock` is not assumed to give writer fairness, and the contract relies on no fairness property.
- **Pending-transition intent (admission barrier).** The anchor (section 7) carries at most one `intent` record `{epoch, decision_id, action, status, provenance_ref, intent_digest}`, where `action` is `terminal` or `install`, `epoch = committed_epoch + 1`, and `provenance_ref` binds the intent to the persisted Control Plane decision (`decision_id`, `approval_commitment`). The anchor is installer/custodian-owned, written only by atomic replace with fsync of file and directory, readable by the executor identity, and held outside the pin store's restore domain. The barrier is therefore installer-owned, durable, not modifiable by the claim supplier (P-2), visible to the Runtime before admission, independent of whether the installer process is alive, and fail-closed when unreadable or inconsistent (section 5 step 1).
- **Pin store.** The terminal pin row, committed under the exclusive fence (6.3).

### 6.2 Executor order

0. *Lock-free pre-check (liveness only).* Read the anchor; if a `terminal` intent covers the claim's `decision_id`, HOLD at once without touching the fence (`store_unknown`, cause `pin_transition_pending`). This step is not relied on for safety; it removes shared-lock churn from the covered decision so the installer can make progress (6.4).
1. Acquire the **shared** per-decision fence with a non-blocking deadline (failure: HOLD `verifier_unavailable`, cause `pin_fence_unavailable`).
2. **While holding the shared fence**, re-read the anchor. If a `terminal` intent covers the `decision_id`: release the fence and HOLD (`store_unknown`, cause `pin_transition_pending`). This read is the authoritative admission check.
3. `BEGIN IMMEDIATE` on the effect database (the existing transaction).
4. Validate the pin store and the anchor (section 5 step 1) and read the pin (section 5 steps 2 to 4).
5. Validate the claim against the pin (section 5 step 5).
6. Resolve the Registry scope from the authenticated pin (section 5 step 6).
7. Run the existing security checks, F-01 five-set containment, revocation, generation, trust and evidence checks (section 5 step 7).
8. Commit or roll back the effect transaction (receipt records `pin_epoch`, section 5 step 8).
9. Release the shared fence (always, including on every refusal and exception).

Lock order is per-decision fence, then effect database. The executor holds at most one fence and never waits on the installer.

### 6.3 Installer order for a terminal transition

1. **Validate** the transition against persisted Control Plane authority through the section 3.2 export path (the persisted decision is withdrawn, revoked, superseded, or its grant or approval no longer supports it). A transition the Control Plane does not support is refused and logged.
2. **Durably record the pending intent**: atomic replace of the anchor adding the `terminal` intent for `epoch = committed_epoch + 1`, fsync file and directory. Instant **T_int** = the completion of that replace.
3. **Admission barrier in force.** From T_int every executor that reads the anchor sees the intent and is held for that `decision_id` (6.2 steps 0 and 2). No new governed effect for the covered decision is admitted.
4. **Acquire the exclusive per-decision fence**, retrying with a bounded deadline and backoff. This is the only path to commit. If the deadline passes, the installer does **not** proceed: it appends evidence `{outcome: pending_blocked, decision_id, epoch, retries}`, leaves the intent and the barrier in place, and retries later. It never commits without the exclusive fence.
5. **Verify** under the exclusive fence: anchor `committed_epoch` equals the pin head, the intent equals the one recorded in step 2, the chain from the anchored head is intact, and no terminal row for the decision exists.
6. **Commit the terminal pin row** (`pin_epoch = intent.epoch`, `prev_pin_digest`, status, provenance) in rollback-journal mode and fsync; append the installer log record. Instant **T_c** = the commit (durable) of that row.
7. **Complete the external-anchor protocol**: atomic replace of the anchor setting `committed_epoch`, `committed_head_digest` to the new head and clearing `intent`, fsync. The unavoidable single-writer order is row first, anchor second (section 7); atomicity between SQLite and the external anchor is **not** claimed.
8. **Mark the transition complete** in the installer log (`outcome: complete`).
9. **Release the exclusive fence.**

Installing a new `active` pin needs no exclusive fence (granting new authority cannot produce a post-revocation effect). It still writes the `install` intent before the row, and an `install` intent does not create an admission barrier for other decisions.

### 6.4 Where a terminal transition becomes effective, and why the order is strict

- **Effective at Runtime at T_c**, the durable commit of the terminal pin row under the exclusive fence. Before T_c the transition is **pending**, not effective, and is never reported as completed or effective. After T_c every pin read refuses the decision. Step 8 marks the administrative completion; the Runtime does not wait for it, because from T_c the pin row alone refuses (section 5 step 4) and a store whose head equals the intent epoch is accepted.
- **Admission is closed from T_int, which is before T_c.** The interval T_int to T_c is a fail-closed hold for the covered decision, not an unauthorized window.
- **Strictness argument (only these three facts are relied on; no cross-file atomicity is).** (a) The intent is durable and visible before the exclusive fence is requested (step 2 before step 4, fsync). (b) The exclusive fence excludes every shared holder, and a shared holder releases only after its effect transaction has committed or rolled back (6.2 step 9). (c) Every executor holds the shared fence while it reads the anchor and until its effect ends. Therefore an effect that read the anchor before T_int holds the shared fence until it ends, so T_c follows its commit; an effect that reads the anchor after T_int is held; and an effect admitted after the exclusive fence is released (after T_c) reads the terminal row. **No effect can commit using the previous active pin after T_c, and no transition can reach T_c while an earlier shared-fence effect is in flight.** The receipt `pin_epoch` is evidence consistent with this order, not the mechanism that enforces it.
- **Starvation resistance without `flock` fairness.** After T_int, new entrants for the covered decision do not retain the shared fence past one anchor read (and mostly skip it by the step 0 pre-check). The shared holders the installer waits for are therefore only the effects admitted before T_int, each bounded by its own transaction lifetime. Effects for other decisions use other fence files and cannot delay it. The installer's exclusive attempt can only be delayed by an honest in-flight effect finishing, or by a stuck or hostile shared holder; in that case the transition stays pending and the covered decision stays held (fail closed). The guarantee is therefore **safety under all conditions and progress when in-flight effects finish**; it is not guaranteed completion against a stuck holder. A stuck holder can only extend a hold that the barrier already imposes.
- **Residual: unresolved invariant bounded, not hidden.** Admission HOLD is per `decision_id`. An upstream revocation that affects several decisions leaves a not-yet-processed decision admissible under its own active pin until the installer reaches it (propagation delay, section 12). The existing Runtime-owned invalidating writers (grant, approval, policy status setters) remain in force and are additional, not replaced.

**Propagation delay.** This amendment does not claim instantaneous Control Plane to Runtime revocation. Between the moment the Control Plane records a withdrawal or revocation and T_int (the installer starting the transition), effects pass under the then-current pin. That interval depends on the installer's reconciliation cadence, which the operator sets, and is reported as a residual risk.

The fence and the barrier bind code that takes them. They bind the honest Runtime path (the destination), which is the enforcement point; a supplier that executes arbitrary code in the executor process is excluded in section 2.

## 7. Anti-rollback and recovery (anchor, pending intent)

An externally custodied monotonic **anchor** is required for the qualified anti-rollback profile (Architect decision 6).

**Anchor (`ocs-s4/pin-anchor/1`):** `pin_store_id`, `committed_epoch`, `committed_head_digest`, optional `intent` (section 6.1), `anchored_at`. It is held **outside the pin store it protects and outside its restore domain**, by a custodian the operator designates. Only the installer protocol writes it; the executor identity can only read it.

**Update order for any append (install or terminal).** (1) write the `intent` (atomic replace, fsync); (2) for a terminal transition acquire the exclusive fence; (3) commit the pin row; (4) write `committed_epoch = intent.epoch` and clear `intent` (atomic replace, fsync). SQLite and the anchor are different files and no atomicity between them is claimed: the order makes every crash state either safe or HOLD.

**Runtime decision table** (pin head `H`, anchor committed `C`, intent `I` if present):

| State | Runtime |
|---|---|
| no intent, `H = C` | accept |
| no intent, `H > C`, chain from the anchored head verifies | accept (store ahead of a stale anchor, ADR 3.6) |
| no intent, `H < C` | **HOLD, all decisions** (`store_unknown`, `pin_anchor_inconsistent`) |
| intent, `I.epoch = C+1`, `H = C` (row not committed) and `I.action = terminal` | **HOLD for `I.decision_id` only** (`store_unknown`, `pin_transition_pending`); other decisions admitted |
| intent, `I.epoch = C+1`, `H = C` and `I.action = install` | accept; the decision has no active pin yet (REFUSE `pin_absent` for it) |
| intent, `I.epoch = C+1`, `H = C+1`, row at `H` matches the intent descriptor (row committed, anchor completion pending) | accept; the terminal row refuses its decision |
| intent with any other relation (`I.epoch != C+1`, `H > I.epoch`, `H < C`, row at `H` does not match the descriptor) | **HOLD, all decisions** (`pin_anchor_inconsistent`) |
| anchor absent, unreadable or malformed | **HOLD, all decisions** (`pin_anchor_unavailable`); lost state is unknown, never zero |
| pin store unreadable (for example a hot journal), chain broken, conflict | **HOLD, all decisions** (`pin_store_unreadable`, `pin_chain_broken`, `pin_conflict`) |
| pin store and anchor both restored consistently to an older point | **UNDETECTED** (disclosed limit, ADR 3.6) |

**Crash and recovery cases (terminal transition).**

| Case | State left behind | Runtime | Required installer recovery |
|---|---|---|---|
| A. crash before the intent is durable | nothing changed | no barrier; the revocation is not pending | the installer re-derives the transition from persisted Control Plane authority on restart; until T_int the delay is the propagation delay (section 12) |
| B. crash after the intent, before the exclusive fence | intent present, `H = C`, no lock held | covered decision HELD | mandatory start-up reconcile: re-validate against the Control Plane (6.3 step 1), then run steps 4 to 9 |
| C. crash while holding the exclusive fence | OS releases the lock; intent present; either `H = C`, a hot journal, or the row committed | `H = C`: covered decision HELD; hot journal: HOLD all (`pin_store_unreadable`); row committed: accept, terminal row refuses | reopen the pin store read-write (SQLite recovery rolls back an uncommitted row), then reconcile as B or E |
| D. crash before the terminal row commit | as B or C | as B or C | as B |
| E. crash after the row commit, before the anchor completion | `H = C+1 = I.epoch`, intent present | accept; terminal row refuses the decision | verify the row at `H` against the intent descriptor, then step 7 and 8; a mismatch is `pin_anchor_inconsistent` (HOLD all) and requires an operator re-baseline |
| F. restart with a pending intent | intent present | covered decision HELD | the installer MUST reconcile every intent before accepting new work; it never clears an intent by itself |
| G. anchor unavailable or inconsistent | n/a | HOLD all | the installer refuses to write; recovery needs an explicit logged operator re-baseline permitted only when chain continuity from the anchored head can be shown (ADR 3.6); it never starts from empty tables |
| H. installer unavailable while a revocation is pending | intent present, barrier in anchor | covered decision HELD indefinitely (the barrier does not depend on the installer process) | none until the installer returns; the transition is not reported effective or complete |

Rules that hold in every case: a pending terminal intent is **never cleared without a verified completion**, never silently expires and never reactivates its decision; there is **no abandon operation** for a terminal intent (abandoning it would reactivate authority the Control Plane withdrew); regaining authority needs a fresh decision, a fresh pin and a fresh approval (section 4). The installer never fabricates a terminal commit: the pin row at `intent.epoch` is the only evidence of T_c, and the installer log is reconstructed from the row after a crash, not the reverse. A store rolled back to an earlier active pin is detected as `H < C` or as an intent with `H = C` and in both cases is HELD rather than treated as active; the only undetected rollback is the consistent restore of the store and the anchor.

**Custody and qualification blocker.** The protocol is defined and the crash states above are enumerated, but **no code can prove that the anchor is externally custodied**. A deployment that stores the anchor in the same restore domain as the pin store (for example the same volume restored by the same backup) satisfies the HOLD rows only against partial restores, not against a consistent restore, and is **not** qualified for anti-rollback. Anti-rollback is therefore qualified only for a deployment whose anchor custody the operator demonstrates as outside that restore domain; absent that, the anti-rollback guarantee is **unsupported** and is recorded as a qualification blocker, not deferred silently.

## 8. ADR reconciliation (3.1 and EXT-S4-0)

- **Selection state vs authorization state.** ADR 3.1 forbids a separate store for *selection state*: the closed table set of 3.2 (activation state, log, high-water, ratchet, revoked sets, snapshot) that decides which Registry record governs a scope, written only by the activation writers from Registry-signed statements. The pin store holds none of that: it holds the Control Plane's own authorization tuple (section 3.1). It is written from persisted CPAA decisions, never from a Registry statement, and it selects, replaces or overrides no Registry record, epoch, policy or scope row. The guard still resolves the Registry row through the unchanged selection store; the pin only fixes which `operation` and `consumer_id` the scope key is built from and requires the claim to equal it. The pin carries `selection_epoch` and `activation_ref` as identity members to compare, not as state to apply. The Registry and the Control Plane hold no authority copy of selection state, as before.
- **Atomicity.** ADR 3.1's reason for one database ("only one database gives one transaction") is respected for selection state, which stays in the effect database. The pin store cannot share that transaction because OS-level writer isolation requires a separately owned file; section 6 replaces the missing single transaction with a per-decision fence plus a durable admission barrier and states the limits rather than assuming atomicity.
- **One trusted writer per store.** Selection store: unchanged. Pin store: the installer alone, never seeded from a claim (A-3).
- **EXT-S4-0 7.1 / 7.4 / 12 item 8.** The guard still runs inside `BEGIN IMMEDIATE` on the effect database; the 14-member claim tuple is unchanged and no claim member is added; typed refusals use existing codes only (`policy_identity_mismatch`, `store_unknown`, `verifier_unavailable`; no new reason code).
- **r08-v2 and Amendments 1 to 3.** Section 1 lists every reconciled sentence. Amendment 1 4.3 (`policy_identity_mismatch` covers all identity members) is the reason the pin refusals reuse that code. Amendment 3 is untouched.

## 9. Fail-closed summary and typed reasons

| Condition | Result | Code | Cause string |
|---|---|---|---|
| anchor/pin store unreadable, inconsistent, chain broken, conflict; a pending terminal transition covering the decision | HOLD | `store_unknown` | `pin_anchor_unavailable`, `pin_anchor_inconsistent`, `pin_store_unreadable`, `pin_chain_broken`, `pin_conflict`, `pin_transition_pending` |
| per-decision fence file absent or not acquirable within the deadline | HOLD | `verifier_unavailable` | `pin_fence_unavailable` |
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
4. Progress of a terminal transition depends on in-flight effects finishing; a stuck or hostile shared-fence holder keeps the transition pending and the covered decision held (fail closed, availability loss for that decision only). Admission HOLD is per `decision_id`: a multi-decision upstream revocation is processed decision by decision.
5. The revocation reconciliation cadence sets the Control Plane to Runtime propagation delay.
6. A supplier or crash can leave a fence held, a pending intent or a hot journal such that executors fail closed (availability loss, not an integrity break). A pending terminal intent has no abandon operation.
7. Other first-writer rows written by `provision_claim` (grant, approval, policy, evidence) remain supplier-seeded; for a pin-required destination they confer no authority beyond agreement with the pin, but hardening them is outside this amendment.
8. `max_amount`, `allowed_target_prefixes` and the executor-integrity limits of Amendment 3 section 3 remain.
9. Implementation is unauthorized; no part of this contract has been executed against code.

## 13. Compact implementation sequence (not authorized)

See [`docs/f-a1-authorization-pin/implementation-proposal.md`](f-a1-authorization-pin/implementation-proposal.md): (1) Control Plane export; (2) host installer and pin library; (3) Runtime guard and `provision_claim` restriction; (4) deployment profile and OS-isolation test harness; (5) independent qualification. Each step is a separate, Architect-reviewed PR in its own repository.
