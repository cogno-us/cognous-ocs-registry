# R08-PREP Lane A: Registry lifecycle contract (RECORD / SELECTION / ACTIVATION and the four adjacent objects)

Purpose: specify candidate state machines for the three registry-lifecycle objects, identify required and prohibited transitions, define the seven-object ownership table, and show how the frozen `s03-v1` `active` gate coexists with a successor format. Evidence labels follow the BRIEF. COG-REG-SHARED-ADD-01 was NOT available and is cited only via plan v1.2 and the crosswalk.

**Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.**

## 1. Sources and revisions examined

| Source | Pin |
|---|---|
| Registry repo `main` | `eb850c8d303961d099a123534121aeac280b242b` (verified `git rev-parse HEAD`) |
| Plan v1.2 (`docs/plans/PROJECT_PLAN-v1.2.md`) §3.1, §3.3, R08, R09 | blob `32319775...` (as supplied; blob hash not recomputed) |
| Crosswalk A3, A4, A5 | blob `a53a5b31...` (as supplied) |
| Frozen S03: `docs/s03-contract.md`, `registry_records/*.record.json`, `docs/s03-example-record.json` | at `eb850c8` |
| Frozen S04: `registry_consumer/consumer.py`, `docs/s04-implementation.md`, `registry_records/*.manifest.json`, `docs/trust-limitations.md` | at `eb850c8` |
| PR #17 `08-open-architectural-decisions.md` (D1-D13, V1-V9), `05-common-envelope-proposal.md` §2-4 | head `bdfb2b7268690d9406cc1de257dc6feede0fdb5a` (verified) |
| ISS review: envelope-compatibility, transaction-binding, authority-crosswalk | ISS Core PR #12 head `547b9052...`, files in the eight ISS review documents (head not re-verified; the files cite PR #16 head `100aa407...`, i.e. they review a pre-adoption v1.2 draft) |
| Constitution `ENGINEERING_CONSTITUTION.md` | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (verified); CA03, CA05, CA06, CA12, CA15-CA22 read |

Not inspected: COG-REG-SHARED-ADD-01; `ADOPTION.md` and `ORCHESTRATION.md` (so no claim of formal adoption is made); Control Plane / Runtime clones (this lane needs only the frozen baseline S03/S04 already pins; no divergence between S01/S02 pin and clone heads was examined); PR #13; the other five ISS review documents; S02 evidence directory.

## 2. Findings from source

F1 [EXISTING] S03 record carries `status` in {`proposed`,`active`,`superseded`,`withdrawn`}; only `active` is accepted (`status_not_active`, check #8). `status` is inside the digested body: `record_digest` covers "the whole record without `record_digest`" (s03-contract §3).
F2 [DEV-TESTED] (S03 tests N1, P6) The shipped example record is `proposed` and is refused `status_not_active`; ACCEPT only after in-memory status change and re-digest.
F3 [EXISTING, derived by reading the spec] Because `status` is digested, flipping v1 from `active` to `superseded` changes v1's digest. v2's `supersedes.record_digest` names v1's digest at the time v2 was authored. So under `s03-v1`, a chain-consistent v1 can never be rewritten to `superseded` without breaking v2's pointer or creating a second digest for the same `(record_id, record_version)`. `superseded` and `withdrawn` are therefore expressible only as new bytes, never as an in-place transition. This is an inference from the text and was not executed; flag for Builder confirmation. This is why a successor must not model record lifecycle as an in-record mutable field.
F4 [EXISTING] `version_not_latest` compares `record_version` to `latest_known_version`; S04 supplies that value from the **manifest's selected version** (consumer.py `context`; s04 doc "Context custody"). So the frozen "latest" is "the version the manifest pins", not a registry-computed newest. A newer v2 file existing does not invalidate a manifest pinning v1 unless the operator re-pins. [DEV-TESTED] by S04 battery (not individually re-run here).
F5 [EXISTING] S04 manifest `s04-v1` is the only selection-like object: fields `record{record_id,record_version,record_digest,file_sha256}`, `record_source` (unverified, informational), `evaluator`, `runtime{source_blob_id,source_sha256}`. It has NO epoch, tenant/scope, effective interval, approver, withdrawal/revocation reference, or revision counter. Its authority is solely that its bytes hash to `TrustConfig.manifest_sha256`, which is operator-supplied configuration (consumer.py header; trust-limitations T2).
F6 [EXISTING] Revocation under S04 = the operator changes the pin or removes the file; there is no revocation record, no revocation check at use time, no expiry (s04 §8, trust-limitations T9).
F7 [EXISTING] The consumer is an optional overlay: every refusal returns the caller policy object unchanged, `overlay_applied False`; "not a denial and not a compliance claim" (s04 doc). Not mandatory fail-closed.
F8 [EXISTING] The consumer reads files, validates, and returns a policy; it writes nothing. No ACTIVATION record, no evidence commitment, no commit boundary exists. `OverlayResult` is the only output.
F9 [EXISTING] S03 supplies no authentication (s03 §3: "integrity, not authenticity"; test L1). Digest chain `supersedes` proves ancestry-by-hash, not that the supersessor was approved.
F10 [EXISTING, source-asserted] Plan v1.2 §3.1 defines record lifecycle draft/validation/approval/publication/supersession/archival; selection approval/publication/withdrawal/revocation "independent of record status"; activation/evaluation/commit/revalidation "domain-owned, not global registry status". Crosswalk A3 ACCEPT: ISS review `envelope-compatibility` §Selection lists `selection_id, selector_authority_ref, scope, consumer_domain, exact_record_refs, selection_revision_or_epoch, valid_interval, withdrawal_or_revocation_ref, selection_custody_proof` as candidate requirements; `transaction-binding` §Bounded sequence gives freeze, pre-commit revalidation, "REFUSE/HOLD or retry as new independently evaluated transaction; never silently update the pin."
F11 [EXISTING, constitution text] CA18 (version, authenticate, review policy; protect invariants), CA17/CA19 (finality, only competent authority confers canonical standing; merge mechanics are not adoption), CA06 (retain supersession/adverse evidence), CA20 (scope, expiry, revocation), CA22 (rollback of decision config cannot reverse a committed effect), CA05 (missing/stale prerequisites never become approval or not-applicable), CA16 (no silent promotion of lifecycle labels). The constitution states no particular storage or rules engine is required.

## 3. Candidate contract / design [PROPOSAL throughout]

### 3.1 Cross-cutting rules (apply to all three machines)
- C1 Each machine has its own state variable, owner, store, log and version counter. No machine reads another machine's state as a precondition of *its own* transition except through an exact, digest-pinned reference (see 3.5).
- C2 State is an append-only event history; "current state" is a derived projection. Transitions are new signed/authenticated events, never mutation of the digested artifact (corrects F3).
- C3 Every transition event carries: machine, object id, from-state, to-state, actor identity, role/authority reference, authenticated-by (Lane B interface), event time, reason code, predecessor event digest, and the exact artifact digest it concerns.
- C4 Any state not in the allowed table is PROHIBITED. Unknown state/transition on read = REFUSE (CA05); a consumer never defaults an unknown status to active.
- C5 No transition is implied by another: no auto-approve on validation success, no auto-select on publication, no auto-activate on selection approval, no auto-supersede on "newer record exists", no auto-anything on PR merge or repository presence.
- C6 Time: all times are UTC instants from the owning authority's clock, recorded in the event; consumers evaluating expiry use their own explicit evaluation time (Lane D defines representation and skew tolerance).
- C7 Terminal states are terminal. Correction is a new object/version, never a reopened state (CA17: reopening is a new authorized decision with ancestry).

### 3.2 RECORD machine (candidate states: draft, validated, approved, published, superseded, withdrawn, archived)

| Aspect | Candidate rule |
|---|---|
| State owner | Registry record steward role (OCS Architect delegate); one owner per family. Not the consumer, not the selector. |
| Approval authority | Independent of author (author != approver) and of the validator. Approver = family approval authority named in an approval-authority roster (scope: family, contract_version). Tier-1 families: independent review per CA18/CA23; level is open (A-04). |
| Authentication | Each transition event authenticated per Lane B interface I-B1 (below). Digest-only (pin-only) is insufficient for approved/published/withdrawn events. |
| Preconditions | draft->validated: strict schema + canonical-form + digest checks (S03 validator semantics reused for `s03-v1`; successor validator for new format). validated->approved: validation result bound to exact record digest, independent approver, impact assessment present where CA18 requires it, no unresolved D1 classification for the family. approved->published: approval event digest-matches record; publication target is the immutable record store. |
| Version increments | Content change => new `record_version` (strictly +1 per `record_id`) and new digest; state changes do NOT change `record_version` or digest (C2). `contract_version` is orthogonal. |
| Effective-time rules | A record has NO effective interval (PR #17 05 §3 and §2 agree; D-open (b)). `valid_from/until` belongs to SELECTION. Publication time is informational. |
| Supersession | Event `superseded` on version N emitted when version N+1 reaches `published`, referencing N+1 digest; N remains retrievable and verifiable forever (plan §3.1 immutable history; CA06). Supersession affects only *eligibility for new selection*; it does not alter any existing SELECTION (see 3.3, X-3). |
| Revocation | Records are not "revoked"; authority is. `withdrawn` = steward/approver declares the record must not be newly selected (defect, security issue). Withdrawal never deletes, never edits bytes, and signals SELECTION owners; it does not revoke selections (selector decides; see X-4). |
| Evidence commitments | Each event hashes into a per-record transition log (digest chain). Validation report, approval rationale, rejected alternatives and objections retained (CA06). |
| Retry/recovery | Validation is idempotent and deterministic; re-running yields the same verdict for the same inputs. A failed validation leaves `draft`; fix = new `record_version`. Partial publish (store write succeeded, event not logged, or inverse) = state is the last logged event; reconciler (Builder routine) compares store to log and raises a discrepancy, never self-heals state upward. |

Allowed transitions (REQUIRED set): draft->validated; draft->withdrawn (abandon); validated->approved; validated->draft (rejected, with reason; new version required to proceed); approved->published; approved->withdrawn; published->superseded; published->withdrawn; superseded->archived; withdrawn->archived; superseded->withdrawn (defect found later). 
PROHIBITED: any transition skipping a state (draft->approved, validated->published, draft->published); approved/published->draft (no un-publish into draft: use withdrawn); superseded->published or withdrawn->published (reinstatement = new record_version); any transition out of archived; any state change performed by the record's own content; self-approval by author; supersession by an unapproved/unpublished successor; supersession as a side effect of digest `supersedes` pointer alone (the pointer is a claim, the event is the fact); deletion of any state or event.

Archived = removed from default discovery and retained under CA06 retention; archival is not erasure; authorized erasure is a separate governed decision (plan §3.3 non-forgetting; GCR-owned for cognitive material).

### 3.3 SELECTION machine (candidate states: proposed, approved, effective, withdrawn, revoked, expired)

| Aspect | Candidate rule |
|---|---|
| State owner | The consumer domain's selection authority (OCS: OCS authority owner / Control Plane side; GCR: GCR owner). Never the registry record steward, never a shared cross-domain authority (A4: cross-domain selection authority REJECT). |
| Approval authority | Domain selection approver, independent of the record author and record approver for the pinned records, and of the proposer. Scoped by CA20: actor, role, domain, action, tenant/scope, time, limits, issuer. Operator is ultimate authority for MSOP membership (plan §3.4). |
| Authentication | Selection events and the selection manifest authenticated per Lane B interface I-B2; "self-attested approval" is invalid (ISS envelope review). The consumer verifies against its own trusted activation configuration (S04 TrustConfig pattern F5), never against anything the manifest says about itself. |
| Preconditions | proposed: exact `(record_id, record_version, record_digest)` refs for each record, evaluator `(id, revision, build/source identity)`, consumer_domain, tenant/scope, requested interval, participation mode (mandatory/optional, per operation: V5 open). proposed->approved: every referenced record is `published` and not `withdrawn` at approval time (checked, recorded, but the dependency is one-way: see X-3); composition check passes (unknown composition REFUSES); approver independence satisfied. approved->effective: authenticated epoch published AND `valid_from` reached under the authority's clock AND no revocation event. |
| Version increments | A selection is immutable once approved. Any change of pins, scope or interval = new `selection_revision` with strictly increasing `epoch` per `(selection_id, consumer_domain, scope)`; old epoch goes to `withdrawn` (planned replacement) by event. Anti-rollback: consumers hold a high-water epoch (Lane D/C interface); an older epoch is refused (R09 anti-rollback). |
| Effective-time rules | Interval `[valid_from, valid_until)` lives here only. `expired` is derived: evaluation_time >= valid_until, with an explicit event recorded when observed. No `valid_until` = perpetual only if the approver explicitly states "no expiry" (PR #17 05 open (a)); default absent interval = not effective. No retroactive interval edits. |
| Supersession | A newer epoch for the same scope supersedes the older one only by explicit approved event, never because it is newer. At most one `effective` epoch per `(consumer_domain, scope, family, operation)` at an evaluation time; two overlapping effective = conflict = REFUSE for both (CA05; no tie-break by recency). |
| Revocation | `revoked` = authority or approver declares the selection invalid immediately, for cause (compromise, defect, authority loss). Distinct from `withdrawn` (orderly end) and `expired` (time). A `withdrawal_or_revocation_ref` points at the authenticated event. Revocation reaches consumers via a revocation check at activation and at commit/effect boundary (Lane C/D). Revocation does not reverse committed effects (CA22); compensation needs distinct authority. |
| Evidence commitments | Approval, interval, pins, revocation events hash into a selection log; the selection manifest digest is what ACTIVATION binds. Rejected proposals and objections retained. |
| Retry/recovery | Approval is not retried automatically. A lost-publication selection (approved, epoch not published) stays `approved` and is not effective. Epoch publication is idempotent by digest. Revocation publication failure is an incident: the authority log is the truth; consumers with stale view are bounded by the freshness rule from Lane D. |

Allowed (REQUIRED): proposed->approved; proposed->withdrawn; approved->effective; approved->withdrawn; approved->revoked; effective->withdrawn; effective->revoked; effective->expired; approved->expired (never became effective before `valid_until`).
PROHIBITED: proposed->effective; any path into `effective` without an authenticated epoch; effective->approved or any backward move; withdrawn/revoked/expired -> any state (re-issue = new epoch); effective by record status, digest match, PR merge or repository presence; approval whose referenced record is not `published`; selection resolved to `latest`/newest/highest version; widening an approved selection in place; revocation implied by record `withdrawn` or `superseded` (and vice versa); one selection authority acting for another domain.

### 3.4 ACTIVATION machine (candidate states: resolved, validated, applicable, evaluated, committed / refused / held)

Activation is per operation, domain-owned, and is not stored in the registry (PR #17 05 §4 agrees). It exists in the consumer's own transaction/evidence store.

| Aspect | Candidate rule |
|---|---|
| State owner | The consumer (OCS Control Plane/Runtime per its own boundary; GCR Governor per its own). One instance per operation attempt. |
| Approval authority | None for the activation itself: activation is a determination, not an approval. Its authority input is an `effective` selection; the consumer additionally applies its own mandatory floors in code. Authority-to-effect remains with OCS (a selection is not an execution grant). |
| Authentication | Consumer verifies selection manifest, record bytes and evaluator identity against its trusted configuration (Lane B I-B3), per attempt. Results are not cached across a state-changing boundary without the freshness rule (Lane D). |
| Preconditions | resolved: exact selection+epoch located by explicit scope key, not discovery of `latest`; record/evaluator refs resolved by digest. validated: record passes the validator for its contract_version (S03 `status` gate for `s03-v1` formats applies here: see 3.6); selection authenticity and non-revocation checked at evaluation time T. applicable: tenant/scope, operation, evaluator build, profile match; unmatched = not applicable only where the participation mode is optional AND the contract defines it (CA05: never silently). evaluated: deterministic evaluator run with frozen inputs. committed: revalidation at the commit/effect boundary succeeds and the decision is recorded with the binding tuple (Lane D). |
| Version increments | None on registry objects. Activation attempt id is new per attempt. Changed selection epoch mid-flight => this attempt cannot be committed under the old epoch (transaction-binding case table). |
| Effective-time rules | Evaluation time T is explicit, recorded and frozen for the attempt; revalidation uses T_commit. A selection that was effective at T and expired/revoked at T_commit blocks commit. |
| Supersession / revocation | Not applicable to activation as an object; a committed activation record is historical and never amended. Under changed policy a re-evaluation is a NEW attempt (constitution §3, "new distinct event"). |
| Evidence commitments | Each state entry appends an evidence record (selection id/epoch, record and evaluator digests, operation context, evaluation time, decision, commit/effect reference) per ISS envelope item 3. Refusals and holds are recorded with reason; a refusal is evidence, not an absence. |
| Retry/recovery | refused is terminal for the attempt. held (selection store unavailable, revocation status unknown, concurrent state change) may resume only as a NEW independently evaluated attempt under current state (no pin update in place). Required profiles: unavailable status = HOLD/REFUSE. Optional-overlay profile: refusal leaves caller policy and reports truthfully "overlay not applied" (frozen S04 behavior F7), never as compliance. Commit failure is not admission success. |

Allowed (REQUIRED): resolved->validated; resolved->refused; validated->applicable; validated->refused; applicable->evaluated; applicable->refused; evaluated->committed; evaluated->refused (revalidation failed); evaluated->held; any pre-terminal state->held; held->(new attempt at resolved), not held->same attempt.
PROHIBITED: skipping validated or applicable; committed without recorded revalidation at the owning boundary; held->committed; refused->anything; activation from a selection that is not `effective` at T and T_commit; activation inferring authority from record status `active`/`published`; silent fallback to caller-broader policy under a mandatory profile; silent fallback to an older epoch or `latest`; reuse of GCR admission as OCS grant or the reverse; any claim of global cross-domain atomicity.

### 3.5 Cross-machine interface (one-way, digest-pinned)
| Reference | Direction | Meaning |
|---|---|---|
| SELECTION -> RECORD | by exact `(id, version, digest)` | Selection says "this published digest". Later record `superseded`/`withdrawn` does not mutate the selection; it raises a signal (X-3, X-4). |
| ACTIVATION -> SELECTION | by `(selection_id, epoch, manifest digest)` | Activation binds exactly one epoch. |
| ACTIVATION -> RECORD | via the selection only | Consumer never resolves a record independent of a selection. |
| Signal RECORD withdrawn -> selectors | notification event | Informational; selector owner decides to revoke/withdraw/keep. Whether a selection over a withdrawn record may remain `effective` is a policy choice (X-4 decision A-06), default candidate: consumer REFUSES activation if any pinned record is `withdrawn` at T. |

### 3.6 Coexistence of the frozen `s03-v1` `active` gate and a successor format [PROPOSAL; cross-reference D3, V3, no decision]
1. `s03-v1` is frozen: `contract_version` selects the validator. The successor uses a distinct `contract_version` value; `s03-v1` records continue to be judged by the unchanged S03 validator and S04 consumer (check #4 `contract_unsupported` already refuses any other version in the frozen validator, so successor records cannot be accepted by frozen code by accident).
2. For `s03-v1` the in-record `status` remains the only activity signal and the gate is unchanged: only `active` accepted. In this world RECORD state, SELECTION (manifest pin) and activity are conflated by design; this is the documented frozen limitation, not extended.
3. A successor record omits an activity-bearing `status` (or restricts it to author intent such as `proposed`/`withdrawn`, the option PR #17 05 §2 floats; D3 remains open). Lifecycle position comes from the RECORD event log (3.2), activity from SELECTION (3.3). A consumer of a successor record MUST NOT read any record field as activation.
4. Bridge for legacy records, if ever wanted [PROPOSAL, optional, needs D3 ruling]: a SELECTION may pin an `s03-v1` record (digest + file hash, as in S04). The frozen gate then acts as an additional *record-level precondition inside ACTIVATION validated*, in addition to and never instead of selection effectiveness. Selection `effective` + record `status != active` => refuse (existing behavior). Selection `effective` + record `active` => proceed. Record `active` alone => nothing (this is consistent with F4: S04's manifest is the real gate).
5. Legacy `status: superseded|withdrawn` in `s03-v1` records are, per F3, only expressible as new bytes with new digests. They are honored by the frozen validator if presented, but the successor lifecycle does not rely on them: legacy supersession/withdrawal is expressed by SELECTION withdrawal and by the new machine's events keyed to the legacy digest.
6. No frozen text, test, schema or semantics is rewritten. The successor adds a new contract; the frozen contract is read by reference. Migration of a record from `s03-v1` to successor is a new record_version authoring through the RECORD machine, not a status change.

### 3.7 Seven-object ownership table [PROPOSAL; reflects plan §3.1, A3, A5]
| Object | Owner | Lifecycle (candidate) | Authority conferred? |
|---|---|---|---|
| RECORD | Registry record steward; family approval authority | draft, validated, approved, published, superseded, withdrawn, archived | None (non-authorizing) |
| SELECTION | Consumer-domain selection authority (OCS or GCR separately) | proposed, approved, effective, withdrawn, revoked, expired | Designates which published record may be considered; not a grant |
| ACTIVATION | Consumer (per operation) | resolved, validated, applicable, evaluated, committed/refused/held | Determination for one operation only |
| EVALUATION | Domain-owned deterministic evaluator (registered code identity) | pending, completed(allow/deny/refuse), error; immutable once completed | Produces a result under frozen inputs, not authority |
| ADMISSION | OCS: Control Plane/Runtime admission to effect. GCR: Governor cognitive admission | domain-defined; separate for each domain | OCS admission is not GCR admission and vice versa |
| COMMIT | Owning canonical store: OCS effect/ledger, GCR Governor StateDelta | prepared, committed, failed; revalidation precedes committed | Records outcome; cannot be reversed by registry change (CA22) |
| EVIDENCE | Domain evidence custodian; registry holds only record/selection logs | appended, never mutated; retention state: retained/expired-by-authorized-policy | None; custody only |
Lanes B, C and D define mechanics for EVALUATION/ADMISSION/COMMIT/EVIDENCE; this lane only fixes ownership and separation. Exact states for the last four are domain-owned and not specified here beyond the above.

### 3.8 Interfaces expected from other lanes
- I-B1 (Lane B): authenticated record-event, I-B2 authenticated selection-event/manifest with approver identity and role evidence, I-B3 consumer-side verification against trusted configuration; key/identity lifecycle and revocation-of-signers (signer revoked => events after revocation invalid; events before remain historically valid).
- I-C1 (Lane C): consumer entry points returning typed refusals per activation state; participation mode per operation; no-discovery rule retained.
- I-D1 (Lane D): the binding tuple (selection id/epoch, record digests, evaluator build identity, scope, evaluation time, decision, commit/effect ref), revalidation protocol at commit, freshness/high-water-epoch rule, time and skew representation.

### 3.9 Failure and refusal behavior (all machines)
Unknown state, unknown transition, missing authority roster, unauthenticated event, digest mismatch between event and artifact, or conflicting concurrent events on one object => REFUSE the dependent operation and raise an incident; never default-allow or choose the newest. Divergent logs (two valid-looking events for one object) freeze that object (HOLD) pending steward/authority resolution.

## 4. Constitutional and v1.2 mapping
| Topic | Constitution (read) | Plan v1.2 | Crosswalk |
|---|---|---|---|
| Three-object separation, independent lifecycles | CA18, CA19 (merge/validation is not adoption) | §3.1, R09 | A3 |
| Immutable history, supersession ancestry | CA06, CA17, CA22 | §3.1 "immutable history", §3.3 non-forgetting | A3, A6 (GCR-owned) |
| Authenticated policy and approvals | CA18, CA20, CA23 | §3.5 threat model (section 3.3 duplicate-numbered heading in the plan), R09 | A4 |
| Versioning, boundary compatibility | CA12, CA15, CA21 | R08 (successor schema distinct from S03), §7 | A4 |
| Fail closed without inventing policy; stale/unknown not approval | CA05 | §3.3, R10 | A5 |
| Revocation, expiry, delegated scope | CA20 | §3.1 selection, R09 | A3 |
| Committed effects not reversed by config rollback | CA22 | §3.3 | A5 |
| No label promotion | CA16 | §6 gates | n/a |
Plan sections: R08 (successor contract, status, effective time, selection pin), R09 (three lifecycles, anti-rollback, revocation), R10 (activation, effect-time boundary), R16 (cross-domain). Not mapped: R11-R15, R17-R18 beyond dependency.

## 5. Decisions raised
| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| A-01 | Adopt the three-machine split and the allowed/prohibited transition sets (3.2-3.4) as normative, or amend | Operator / OCS Architect | R08 schema `status`/event fields and R09 build cannot start; Lane B/C/D cannot freeze interfaces | V3, V1 |
| A-02 | Record `status` in successor format: absent, author-intent only, or event-derived | Operator / OCS Architect | Successor schema cannot be written | D3, V3 |
| A-03 | Selection granularity: per operation vs per consumer profile; one-effective-per-scope rule and conflict handling | OCS Architect | Selection key and conflict rule undefined; Lane C wiring blocked | V5, V1 |
| A-04 | Independent-review level for record approval and selection approval of Tier-1 families; approver roster and independence rule | Operator / Independent qualifier | Approved/effective cannot be reached legitimately for any Tier-1 family | D13, D2 |
| A-05 | Perpetual selections (no `valid_until`) permitted? Default absent interval | Operator | Effective-time rule cannot be finalised | PR #17 05 open (a) |
| A-06 | Effect of a pinned record becoming `withdrawn` or `superseded` on an `effective` selection (refuse activation vs selector-decides) | OCS Architect with GCR owner | Revocation semantics and Lane D revalidation inputs undefined | none |
| A-07 | Whether the legacy bridge (3.6 item 4) is wanted at all, or `s03-v1` stays S04-only | Operator | Only affects migration; no blocking elsewhere | D3 |
| A-08 | Mandatory vs optional activation profile existence | Operator | Held/refused semantics for mandatory cannot be specified; frozen S04 stays optional overlay | D7, V5, V6 |
| A-09 | Builder confirmation of F3 (status in digest makes in-place supersession impossible) | Builder-routine | Justification of C2 rests on an unexecuted inference | none |
| A-10 | Retention/archival and erasure authority (who may archive, legal hold) | Operator | `archived` semantics incomplete | V7 |

Dependencies on open S02/PR #17 classifications: any family-specific selection or record approval depends on D1 (the 32 unresolved S02 rows, including W8-091, W3-063, W9-027, W8-014, W6-042 and the 60-versus-300 relationship) being classified; this lane's state machines are family-independent but no family record may reach `approved` while its D1 rows are open. D2 (authentication choice) gates every authenticated transition; this lane assumes only the Lane B interface.

## 6. Risks and unresolved constraints
- The machines are candidates; the ISS review lists them only as "candidate contract requirements", and the ISS S04 fixture itself is a hardcoded synthetic selection (envelope review, mapping table). Nothing here is observed in an implementation beyond the frozen S03/S04 fields in F1-F9.
- COG-REG-SHARED-ADD-01 §§4-5 (cited by crosswalk A3) were not read; this design may diverge from them. Stated lifecycle names in the lane spec and plan §3.1 agree; transition rules are mine.
- F3 is unexecuted; if wrong, the argument for event-derived state weakens but the separation requirement stands.
- Event-log design (C2) adds an authenticated store and a reconciler: real operational surface; no durability, ordering or clock-trust analysis is done here (Lane B/D).
- Revocation freshness is unsolved: a consumer offline from the authority cannot know of revocation. Required-profile behavior is HOLD/REFUSE, which carries an availability cost not quantified.
- Single-effective-per-scope with conflict=REFUSE can deny service on operator error; accepted as the conservative CA05 reading, unvalidated.
- ISS review documents examined target the pre-adoption v1.2 draft (PR #16 head), not the adopted blob; differences not diffed.
- Nothing here is approved, implemented, qualified or deployed; all labels above are the maximum supportable.
