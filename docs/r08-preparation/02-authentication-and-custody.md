# R08-PREP Lane B: Authentication, Authority Custody and Provenance Architecture

Purpose: design the minimum credible mechanism by which a future OCS consumer can tell (a) who produced a policy record, (b) who authorized its selection for one exact consumer and scope, (c) that the manifest, record and evaluator it holds are the ones authorized, and (d) how that authority is pinned, revoked, rotated, rolled forward, audited and recovered. It evaluates which existing OCS components can supply those functions before proposing anything new. Lifecycle states are Lane A's; consumer wiring is Lane C's.

**Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.**

**Architect disposition applied (PR #18 review; Architect ruling, not operator-approved):** authentication uses an asymmetric authenticated statement and an independently trusted selection authority; preferred direction is reuse of the existing OCS evidence-attestation or ODES Ed25519 verification contract, subject to a bounded fitness and compatibility assessment; no fourth cryptographic system; a signature is not authorization. Trust-root custody, issuer enrollment, signing-key ownership, key ceremony, trust-snapshot distribution and key rotation are **not adopted** by the ruling: they need an operator-approved R09 mechanism. D2 ruling (R07): pin-only integrity is insufficient as a general authorization mechanism; the S04 pin-only profile stays a frozen, optional-overlay limitation. Where this document names BitRep, ODES or Control Plane facilities, none is declared qualified; each is a reuse candidate for assessment.

Author lane: B. Date: 2026-10-25. Reviewed claims are labelled [EXISTING], [DEV-TESTED], [QUALIFIED], [PROPOSAL], [APPROVED], [PRODUCTION]. No [QUALIFIED] or [PRODUCTION] claim appears here because none was established for any custody component.

## 1. Sources and revisions examined

| Source | Revision | Used for |
|---|---|---|
| Registry repo `cogno-us/cognous-ocs-registry` | `main` `eb850c8d303961d099a123534121aeac280b242b` (rev-parse confirmed) | `docs/trust-limitations.md` T1-T14, `docs/s03-contract.md`, `docs/s04-implementation.md`, `registry_records/*.manifest.json`, `docs/decisions/2026-10-24-s04-preconditions-and-authorization.md` (P1/P2), plan v1.2 §§3.1, 3.3, R09/R10/R16/R17, crosswalk A1-A10 |
| PR #17 (merged `e3f5bbc32f957a10822a15a1b642e48c63d428e9`) `docs/registry-schema-analysis/08-open-architectural-decisions.md`; PR #13 merged `e20504df8d2c8ddf8b3944c0dabb0dcf5f1009b6` | Merged source evidence with provisional classifications (originally read at PR head `bdfb2b72...`); D2, D3, V1, V3 and the recorded Architect R07 rulings (cross-referenced only) |
| Control Plane `cognous-control-plane` | clone head `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `rule_revision.py`, `runtime_authority.py`, `bounded.py` (policy status read), `signing.py`, `witness.py`, `docs/threat-model-lite.md`, `docs/runtime-authority-profile.md` |
| Execution Runtime | clone head `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | `engine/revocation_closeout.py`, `engine/local_authority_effect.py` (grant revision binding) |
| ODES `open-decision-evidence-standard` | `1a5e1d300250d832e611633f0bf8f762e398c0ec` | `src/odes/signatures.py`, `contracts/rule-revision`, `authority-lineage`, `witness-digest`, `non-broadening-delegation`, `index-evidence-registry` READMEs |
| Evidence Attestation (BitRep) `cogno-us/cognous-evidence-attestation` | `981036c315856c71207984797b0c4e48d3b3921d` (shallow clone head; equals the hub lock pin recorded in `docs/source-provenance.md`) | `docs/VERIFICATION_CONTRACT_V1.md`, `docs/AUTHORITY_DIGEST_CUSTODY_PROFILE_V1.md`, `docs/trust-v1.schema.json`, `profiles/authority_digest_custody.py`, README known limits |
| Evidence Registry (The Index) `cogno-us/cognous-evidence-registry` | `b2485998b88256c2b322493800d1fba076814cbd` (clone head; equals lock pin) | README only |
| Hub `cogno-us/cognous-open-control-stack` | `51c579a3208149922649a31a6eb041106a4121c3` (clone head; lock text at lines 143 and 151 names the two repositories above) | `component-lock.json` names only |
| Action Manifest | `fa170815ef96a54c233d0dd9da821b60debabf8b` | README (digest/binding, "declaration is not permission") |
| Governed Exchange | `7f7569b02666b99669a9fca61117ca1f4bce5f0d` | grep-level only |
| Stack qualification | `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` | `suites/` listing, `outside-holder/README.md` |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | actual text of EP1-EP7, CA01-CA23, "How the articles work together", ADOPTION.md |

Repository names for the two lock components were taken from the hub `component-lock.json` (repository fields), not guessed. `gh api orgs/cogno-us/repos` was refused by the session proxy (HTTP 403, "sessions are bound to their configured repositories"), so the org listing was not obtained. Both repositories cloned anonymously over HTTPS.

Pin differences: S01/S02 pinned Runtime `ec728da6` and Control Plane `0a41faa9`. Control Plane files above were read at `7a4bcd40`, a later head, and **were not diffed against `0a41faa9`**. Any statement here about `rule_revision.py`, `witness.py` or `validate_evidence` describes `7a4bcd40` only. Consequence: the S01 baseline tuple may not contain them (not established). The Index README names BitRep `5b5077da...` as its qualification pin, which differs from the lock's `981036c3`; not reconciled.

**Not inspected:** COG-REG-SHARED-ADD-01 (unavailable; cited only through plan v1.2 and the crosswalk); `cognous-iss-core` (access-limited); the Index and Governed Exchange source code (README or grep only); BitRep `utils/` and `models/` source beyond file sizes; test execution of any component (no suite was run by this lane); `cognous-institutional-governance`, `replay_bundle`, `governance_evidence_pack`, `verifier`, `prp`, `research_intelligence`, `tfa`; S02 classification IDs W8-091, W3-063, W9-027, W8-014, W6-042 (none read). The ISS review documents were not read for this lane.

## 2. Findings from source

### 2.1 Frozen registry trust model

- [EXISTING] S03 digests give integrity only: a record altered and re-digested still validates (case L1; `docs/s03-contract.md` §3; T2). S03 states "CA18 requires authenticated policy data. S03 provides no authentication."
- [EXISTING] S04's authentication is a single SHA-256 pin: `TrustConfig.manifest_sha256` is the hash of exact manifest bytes, supplied by trusted invocation and never read from record, manifest or repository (`docs/s04-implementation.md` §2; T4). The manifest binds record id, selected version, `record_digest`, `file_sha256`, evaluator id/binding and Runtime blob/sha256; `latest_known_version` comes from the manifest, not the record (P2). The consumer is stdlib-only and has no key, signature, scope, epoch, expiry or revocation concept (T9).
- [DEV-TESTED] S04 negative battery `tests/test_s04_overlay.py` covers re-digested record, wrong digest, manifest replacement, wrong version, wrong Runtime/evaluator, missing selection, consumer exception. Copilot-reviewed, not independently qualified (T10). Only case R09 tests substitution against an unchanged pin (T4).
- [EXISTING] Pin custody is a *named gap*: "Whoever holds the pin holds the trust decision"; the S05 harness plays operator; T8 says no approved activation pin exists. The candidate manifest digest `sha256:948ab4f4...2791` is not a pin.
- [EXISTING] Excluded by P1/T1: compromised host admin or root, compromised interpreter, malicious trusted maintainer, malicious build infrastructure, anyone controlling the selection mechanism. T5: the consumer hashes the evaluator file on disk, not the loaded code object. T6: `record_source` is unverified.
- Contradiction check: P1 says "Do not introduce signatures, key management ... production authentication infrastructure" for S04. That bound applied to S04 only; plan v1.2 §3.3-binding and R09 now require trust roots, key lifecycle and signed or equivalent custody "before active Runtime adoption". Not a contradiction, but R09 must obtain a new operator decision; P1 cannot be read as permitting or forbidding it.

### 2.2 Existing components against the required functions

| Function | Best existing candidate | What exists | What does not |
|---|---|---|---|
| Content integrity | S03 canonical form; S04 `file_sha256` | [EXISTING] canonical JSON digest, file digest | Not authentication |
| Origin authentication (key-based) | BitRep v1 verifier: Ed25519 over a strict statement, `audience`, operator-held trust snapshot (`published_at`, `valid_until`, per-key `valid_from/valid_until/revoked_at`); result `issuer_signature_only` | [EXISTING] contract and schema in `docs/`; README marks the v1 verification interface "selected" in the lock | [DEV-TESTED] only per its own docs (not run here). README known limits: issuer enrollment, secure time, snapshot distribution and **anti-rollback are deployment work**; verification is against the current snapshot only (no as-of historical verification); results are not signed receipts |
| | ODES `signatures.py`: DSSE-v1 PAE, Ed25519, keys only from recipient `trusted_keys` (algorithm belongs to the key, `revoked` flag), reasons `key_not_trusted`, `key_revoked`, `signature_invalid`; absent `cryptography` yields `unavailable`, never pass | [EXISTING] | Stated boundary: authenticates origin only; no trusted timestamp; "a key that is trusted today does not prove authority at a past decision time" |
| | Control Plane `validate_evidence`: raw Ed25519 over canonical statement, `producer_keys` supplied by trusted host config, statement checked for `institution_id`, `authority_domain`, `tenant_id` | [EXISTING] a working tenant- and institution-bound statement check | Built for validation-record evidence, not policy selection; `runtime-authority-profile.md` says it does "not implement key custody, key-status distribution or institutional adoption" |
| | Control Plane `signing.py` | [EXISTING] HMAC-SHA256 over replay bundles with one shared secret | Symmetric: any verifier can forge. Unsuitable as origin or authority authentication across parties |
| Authority vs integrity, independent adoption | CP `rule_revision.py` (opt-in `rule-revision/0.1`; ODES `contracts/rule-revision`, draft) | [EXISTING] append-only revision rows; a digest counts as adopted only when a row names a configured signer different from the reviser; `from_digest` chain; refused attempts retained; `resolve_rule` yields `adopted` only if the observed digest equals the signed adopted digest; `verified_through` levels; unadopted policy digest yields `policy_status_unknown` and holds the decision (`bounded.py` L2466-2474) | Its own docstring: signer and reviser are "asserted names ... nothing here authenticates who supplied them"; the store is plain JSON with "no keyed integrity check"; "visibility to an honest reader, not tamper evidence". Therefore **it models the authority/integrity separation but does not by itself authenticate** |
| Selection pin binding to custody + epoch + interval + witness | BitRep Authority Digest Custody Profile v1 (`profiles/authority_digest_custody.py`) | [EXISTING] publisher signs a claim `{authority_kind policy\|grant, authority_id, authority_epoch, authority_digest, effective_from/until, observed_at, publisher_ref, witness_ref}`; a separate witness signs a commitment to the publisher statement and snapshot fingerprint; checks run fail-closed in a fixed order (epoch, id, interval, exact bytes digest, publisher attestation, witness independence including no shared keys, witness not backdated); result `non_authorizing_digest_custody`. [DEV-TESTED] synthetic tests listed in its doc (editor rewrites bytes+digest; forged issuer; revoked key; stale snapshot; wrong epoch; expired interval; wrong id) | Status "proposed, optional" (not the lock-selected interface). No tenant/scope field in the claim. Independence checks are "conservative synthetic checks, not proof of organizational independence". Not a timestamp authority or transparency log. Needs `cryptography` and pydantic, whereas S04 is stdlib-only |
| Revocation at decision/effect time | CP `PolicyStatus {ref, version, digest, status active\|superseded\|unknown, observed_at, institution_id, authority_domain, tenant_id}` read via a host resolver with `status_max_age_seconds`; reasons `policy_tenant_mismatch`, `policy_superseded`, `policy_version_changed`, `policy_status_stale_or_future`; `TerminalRevocationProfile` makes revocation of `(grant_id, revision)` terminal; Runtime `local_authority_effect.py` binds `grant_revision` into the effect claim | [EXISTING]; Runtime revocation closeout records `in_doubt` honestly | These govern grants/policy refs the Control Plane already knows. Terminal-revocation memory is "this control plane's own record store: ... no keyed integrity check". No selection object exists |
| Anti-rollback / outside-held audit | CP `witness.py` (`witness-digest/0.1`); `suites/outside-holder` | [EXISTING] hash chain over ledgers, held by someone other than the store writer; real location "must be somewhere the store writer cannot write" (owner default: signed tag in the hub repo). [DEV-TESTED] `tests/test_witness.py` exists; `suites/outside-holder` in the qualification repo (not run here) | Visibility only; "NOT tamper evidence against the witness holder"; rows after the last digest are `unwitnessed_rows`; covers list-valued ledgers only |
| Hash-linked authority lineage | ODES `authority-lineage` | [EXISTING as draft contract] hop hash chain grant to delegation to effect | Draft, "not implemented anywhere today" per its README; `non-broadening-delegation` unsupported by the Control Plane (`delegation_profile_unsupported`) |
| Evidence ledger | Index (The Index) | README: claim/evidence ledger on a local chain; "does not show ... that an institution permits an action"; no production deployment | **Not a policy store.** Adopting it as a selection ledger would create the "authority ledger" v1.2 R16 says not to introduce without justification. Not recommended; source not inspected |
| Action Manifest, Governed Exchange, Runtime | | [EXISTING] README states a manifest/digest/matching proposal "is never an authorization token"; no key custody | No custody mechanism to reuse |

Net finding: [EXISTING] the stack already contains an Ed25519 trust-snapshot verifier with revocation (BitRep), a two-party custody profile with epoch and interval (BitRep custody profile), a digest-adoption/refusal model (rule-revision), a tenant-bound decision-time status read (PolicyStatus) and an outside-held witness chain. **No single component provides a signed selection with consumer and tenant scope plus anti-rollback.** The composition below is [PROPOSAL].

## 3. Threat model (candidate, for R09; amends nothing frozen)

| Threat (plan v1.2 §3.3-threat-model list) | In scope for the candidate? | Control and residual |
|---|---|---|
| Untrusted policy/record input | Yes | S03 validation plus selection binding; unchanged |
| Unauthorized repository changes (PR merge, force-push, branch edit) | Yes, as a *content* threat | Repository state confers no authority; only a verified signed selection does. Residual: a repository writer who also holds a selection key |
| Compromised selection or storage (store rewritten, digest rewritten with it) | Yes for storage; **no** for a compromised selection *signer key* | Key-based signature verified against a consumer-held trust snapshot; storage compromise cannot mint signatures. Signer-key compromise is handled by revocation and recovery (§4.9), not prevented |
| Stale or revoked authority | Yes | Epoch floor, effective interval, status freshness, terminal revocation (§4.6-4.7) |
| Cross-tenant substitution | Yes | Scope tuple signed and compared (§4.4). S04 has none today (T9) |
| Runtime tampering (loaded code, T5) | **Excluded** unless the operator approves a separate control | Hashing on-disk source does not defend a modified loaded object. See B-09 |
| Infrastructure compromise (host admin, root, interpreter, build/supply chain) | **Excluded** (P1/T1 carried forward) | No claim. The trust snapshot and `TrustConfig` live on that host |
| Insider roles | Partly | Role separation (§4.2) and "self-signed refused", but one human or one agent holding several keys defeats it; independence is organizational, not provable by code |
| Unavailable dependencies (snapshot, clock, status resolver, witness) | Yes | Fail-closed *to the profile's own refusal semantics* (§4.10); never to permit |
| Replay of a valid selection or statement | Yes | §4.6 |
| Malicious or mistaken trusted operator | **Excluded** | The operator is the root of authority |

Stated exclusions: no claim against root on the consumer host, a compromised interpreter, the holder of the trust-root configuration, a colluding selection signer plus witness, or loss of both. Secure time is an operator assumption (BitRep README: "supplied by the operator").

## 4. Candidate design [PROPOSAL]

### 4.0 Architect ruling on the verifier contract (Architect ruling, not operator-approved; phase R08/R09)
A selection is accepted only if verification establishes **all** of: (1) trusted issuer identity; (2) issuer authority for the exact operation and scope; (3) audience/consumer binding; (4) exact selection digest; (5) record and evaluator revision binding; (6) tenant/institution applicability; (7) selection epoch; (8) effective interval; (9) revocation and supersession status; (10) trust-root version; (11) current trusted time; and (12) unavailable verification refuses (fail-closed to the profile's own refusal semantics). Record approval and selection authorization are distinct authorities. One individual may hold several roles only under an explicit operator-approved separation-of-duties policy. The mapping of these twelve properties to sections 4.3-4.10 is candidate design; the fitness assessment of BitRep (v1 verifier and custody profile), ODES DSSE and the Control Plane `producer_keys` pattern is not yet performed and no outcome is presumed.

### 4.1 Separation that must be preserved

| Question | Answered by | Never answered by |
|---|---|---|
| Are these bytes unchanged? (content integrity) | digest and canonical form | signature, PR merge |
| Who produced them? (origin) | signature under a consumer-trusted key | `authored_by`, `record_source`, commit path |
| Who authorized this exact use? (authority) | a selection statement from an authority role distinct from author and approver | record `status`, digest, repository presence, the selection's own bytes without a trusted signer |
| Is it authorized *now* for *this consumer and scope*? | epoch floor, interval, scope equality, revocation status read | any of the above alone |
| Did this effect or admission happen under it? | evidence row (Lane C/OCS-owned) | the selection |

A valid digest is not authorization. A valid signature authenticates origin of those bytes, not truth, adoption or authority at decision time (ODES `BOUNDARY`; BitRep `issuer_signature_only`). The trust decision is therefore taken *twice*: key trust (does the consumer trust this key for this role?) and authority (is this key authorized to select for this scope?).

### 4.2 Roles and trust roots (consumer-owned)

Four roles (record approval and selection authorization are distinct authorities per section 4.0), each a distinct key set in the consumer's trust configuration: **record author** (informational; may be unsigned), **record approver** (signs approval statements; Lane A lifecycle 1), **selection authority** (signs selection and revocation statements), **witness** (signs custody commitments; must not share an issuer or key with the selection authority, per the BitRep custody checks). Rules: the consumer's `TrustConfig` successor carries the role-to-key-snapshot mapping, supplied only by the operator's trusted channel, never from a record, manifest or repository, extending the S04 pin custody. `selection_authority != record_approver` unless the operator approves an explicit separation-of-duties policy permitting it (B-04). Self-signed rows are refused, mirroring `self_signed_revision_row`.

### 4.3 Selection statement

One immutable signed object per selection revision. Required content (all fields inside the signed bytes):

`selection_id`; `epoch` (positive integer, strictly increasing per `selection_id`); exact `record_id`, `record_version`, `record_digest`, `file_sha256` (the S04 binding retained); `manifest` content digest if a separate manifest is kept; evaluator id, binding and Runtime source blob/sha256 (S04 retained); **consumer identity** (audience); **scope tuple** `{tenant_id, institution_id, authority_domain, operation/profile}`; `effective_from/until`; `supersedes` (digest of the previous selection revision); `revocation_ref`; `participation` (declared optional|mandatory, semantics owned by Lane C and the operator); `non_authorizing: true` (a selection is not an OCS execution grant or GCR admission).

Authentication form (candidate, composition of existing parts; direction per section 4.0, subject to the fitness assessment; ODES Ed25519 is equally eligible and no outcome is presumed): a BitRep v1 statement with `statement_type` `registry_selection` (new value; BitRep owner decision), `subject` `selection_id`, `audience` the consumer identity, `content_digest` the SHA-256 of the canonical selection bytes, plus a witness commitment under the Authority Digest Custody Profile. Because the custody claim has no scope field, scope and consumer are carried in the signed selection bytes and **compared by the consumer to its own configuration**; they are not trusted merely because the signature verifies. Alternative: ODES DSSE (B-01). The ODES DSSE and BitRep verifiers use different formats; choose one, do not add a third.

Binding of manifest to record: the signed selection commits to `file_sha256` and `record_digest`; the consumer verifies those against the bytes it read (S04 behavior unchanged). Binding of selection to consumer and scope: audience equality and scope-tuple equality, mirroring `evidence_subject_mismatch` and `policy_tenant_mismatch` semantics. A tenant mismatch, or a tenant-less consumer receiving a tenant-scoped selection, refuses (mirrors `tenant_proposal_required`).

### 4.4 Trust-root configuration

Trust roots are `TrustConfig`-class inputs: per-role BitRep trust snapshots (or ODES `trusted_keys`), the consumer identity, scope, `min_epoch` per `selection_id`, and snapshot max age. Delivery is by the operator or deployment mechanism outside the registry repository. Required properties: not derivable from record, manifest or repo; atomic replacement; bounded snapshot lifetime (`valid_until`); no default trusted issuer (BitRep already has none). Enrollment of issuers, secure time and distribution are *operational procedures with a named owner*, not code in this repository (B-02). Whether trust roots are held in an HSM/KMS is not decided; no claim is made.

### 4.5 Version pinning and `latest`

Exact `(record_id, record_version, record_digest)` only. `latest_known_version` is the selection's version (P2, retained). Directory enumeration, newest-wins and "highest epoch among files" are prohibited. A newer epoch for one `(selection_id, scope)` takes effect only through the explicit, attributable, approved selection-decision (supersession) event of document 01 §3.3-binding; a higher epoch alone never authorizes supersession and it is never chosen because it is newer. Documents 01 and 02 now agree on this. Two verified selections that would both be effective for the same scope at one evaluation time refuse for both (`selection_epoch_conflict`), as in document 01 §3.3-binding. The epoch floor (`min_epoch`) only rejects epochs below it. The final conflict rule remains subject to A-03.

### 4.6 Replay and rollback

- Rollback of authority is refused by the floor: a selection with `epoch < min_epoch` refuses (`selection_epoch_stale`); a trust snapshot with `published_at` older than the consumer's recorded floor refuses. Selecting an older record is allowed only as a *new, higher* epoch whose `supersedes` names the previous revision (rollback is a forward epoch). Whether S03's `version_not_latest` and its `supersedes`-by-`record_version - 1` rule tolerate selecting an older record version is a Lane A and PR #17 D3 question (B-07).
- Anti-rollback state: **minimal option** keeps the floor in the trusted configuration, raised by operator config change (stateless consumer, S04-compatible). **Heavier option** keeps a consumer-side durable high-water mark: that is new mutable state (B-05). The stack already says anti-rollback is "deployment work"; this lane does not claim it is solved.
- Replay of a captured valid selection inside its interval is *idempotent*, not an attack on selection; its protection is audience, scope and interval. Replay at the operation level is the operation-identity concern of Lane C and OCS. Recording a selection digest does not prove transaction-time authorization (v1.2).

### 4.7 Revocation and expiry

Three mechanisms, kept separate: (a) key revocation via `revoked_at` in the trust snapshot (BitRep rejects `key_revoked` conservatively, which also invalidates earlier statements from that key, so key compromise forces re-issuance at a new epoch); (b) selection revocation as a signed statement `registry_selection_revocation` naming `(selection_id, epoch)`; terminal for that epoch, a higher epoch is the way back (pattern of `TerminalRevocationProfile`, adopting its stated limitation that unobserved revocations cannot be remembered); (c) interval expiry. The consumer reads selection status through a host-injected resolver with a bounded `status_max_age`, in the style of `PolicyStatus`; unknown, stale or future status refuses. The staleness bound value is not proposed here: freshness semantics depend on the unresolved 60-versus-300 relationship (T13) if MSOP uses that value.

### 4.8 Key rotation

Rotation is a trust-snapshot operation: add the new key with `valid_from`, publish a snapshot containing both, move signers, expire or revoke the old key. Because BitRep verifies only against the current snapshot (no as-of verification), **historical selections cannot be re-verified after their key leaves the snapshot**; audit therefore retains the verified statement bytes, the snapshot fingerprint and the verification result *at decision time* (§4.9). Rotation of the pin (S04 manifest hash) is subsumed by a new selection epoch. A rotation ceremony, quorum and offline storage are operator procedures (B-02).

### 4.9 Auditability and evidence

Per admission or refusal, retain: selection digest, epoch, signer `key_id`, trust-snapshot `published_at` and fingerprint, verification result and reason, record digest/version, evaluator and Runtime pins, scope, evaluation time and source of time, and the refusal reason from a closed set. Candidate carriers: CP `rule_identity` rows (`verified_through` levels: `none`, `revision_row_present`, `signer_independent_and_configured`, `digest_matches_signed_revision`), which the ODES journal draft revision 2 declares as optional members per `contracts/rule-revision/README.md`; plus a `witness-digest/0.1` chain held outside the store writer's control for tamper visibility. Selection and revocation history is append-only and negative findings (refusals, revocations, withdrawn selections) are retained with their original bytes. A correction is a linked successor.

### 4.10 Failure and refusal behavior

All candidate refusals are closed-set codes (names are proposals): `trust_config_missing`, `trust_snapshot_stale_or_future`, `key_untrusted`, `key_revoked`, `signature_invalid`, `selection_audience_mismatch`, `selection_scope_mismatch`, `selection_epoch_stale`, `selection_epoch_conflict`, `selection_not_current`, `selection_revoked`, `selection_status_unknown`, `witness_missing_or_not_independent`, `record_binding_mismatch`, `evaluator_binding_mismatch`, `role_separation_violation`. Meaning is fixed by participation profile and is Lane C's: in an **optional overlay** (frozen S04) refusal means "overlay not applied", caller policy unchanged, never "denied" and never evidence of compliance; in a **mandatory profile** (needs a successor contract and independently qualified consumer) refusal is HOLD/DENY. A missing snapshot, clock, resolver or witness is a refusal and never a permit or "not applicable" (CA05).

Recovery paths: snapshot or witness outage resolves by restoring the dependency or by operator re-configuration, never by caching an old verdict past `status_max_age`. Selection-key compromise: revoke the key in the snapshot, issue a new epoch signed by a new key, re-baseline `min_epoch`, retain the old evidence. Lost keys: operator ceremony, no auto-recovery. Backup or restore of trust configuration restoring an older snapshot is a rollback and must be rejected by the floor.

### 4.11 Prohibited behaviors

A consumer must not: infer authority from record status, a digest, PR merge, repository presence or a bare signature; read a pin, key, epoch floor, scope or `latest` from a record, manifest or directory; accept a statement whose audience or scope it did not configure; accept a self-signed approval or selection; select the newest record automatically; treat a selection as an OCS grant or GCR admission; accept an unverifiable `record_source` as provenance; treat a witness chain as protection against the witness holder; continue after `key_revoked` using cached success; or silently fall back to the caller or a default when a *mandatory* profile fails. The registry never mints authority, rewrites canonical state or bypasses revocation.

### 4.12 Is new infrastructure necessary?

Not demonstrated. No new database, signing service or authority ledger is proposed. The functions that **existing components do not meet** are: (i) a durable anti-rollback floor (stateless config floor is a workable minimum; durable store is optional new state); (ii) scope/tenant carried inside a custody claim (convention in signed bytes works without changing BitRep; a profile field would be a BitRep-owner change); (iii) issuer enrollment, key ceremony, secure time and snapshot distribution (operational, not software); (iv) an externally held witness location. Each is a decision for the operator (Section 6), not a builder choice. Reuse costs: BitRep and ODES signatures need `cryptography`; the S04 consumer is stdlib-only, so an authenticated consumer changes the dependency and T1 supply-chain surface (B-10).

### 4.13 Interfaces expected from other lanes

- From Lane A: lifecycle events (record approval, publication, supersession; selection approval, withdrawal, revocation) expressed as statements whose type, subject and signer role this document can authenticate; the meaning of "withdrawn" versus "revoked".
- From Lane C: the `TrustConfig` successor shape, the status-read resolver, where in the Control Plane (`policy_versions`/`PolicyStatus`) and Runtime (`grant_revision` binding) the selection identity enters, commit-boundary revalidation, and mandatory/optional semantics. This lane supplies only the verification result and refusal reason.

## 5. Constitutional and plan mapping

Text read at pin `1c2e920f`. ADOPTION.md says publication or merge "does **not** by itself establish adoption"; formal adoption by the registry program is **not inferred** here (the S03 to S06 decision records cite the pin as their reference, nothing more).

| Source | Text relied on | Applied |
|---|---|---|
| CA18 | "Version, authenticate and review governance-critical policy and rule changes; protect established mandatory invariants against configuration override." Prohibited: "Treat unreviewed settings or evaluator changes as governing authority ... or introduce an unaccountable decision path." | Whole lane; mandatory floors stay in code |
| §3 "Policy integrity, failure semantics and security" | "If data and evaluator logic are separated, preserve completeness, authenticity, unambiguous applicability, defined failure treatment and authorized activation." | §4.3, §4.10 |
| Principles crosswalk text (custody) | "A signed or hashed artifact may substantiate provenance; it does not alone establish correctness or legitimate authority." | §4.1 |
| CA01-03, CA19 paragraph | "A local demonstration, signed artifact or successful merge does not itself establish organizational adoption." | §4.11 |
| CA05 | "Fail Closed Without Inventing Policy ... Prohibited: invent a cause, grant, floor, deadline, mapping or default." | §4.10 (unknown semantics refuse; no invented staleness bound) |
| EP4 / CA06 | "Preserve the source, ancestry, transformations, decisions, negative findings and supersession relationships"; CA06 "Retain ... rejected alternatives, objections, adverse findings and supersession" | §4.9 negative-evidence and append-only history |
| "Documentation, operational records and historical custody" | "Preserve original bytes and identities for failures and negative findings; use linked successors. Missing freshness evidence establishes no freshness. Required checks that are missing, disabled, unsupported or unavailable cannot become PASS" | §4.7, §4.9, §4.10 |
| CA20 | "Bind delegated work to actor, role, domain, action, context, time, limits and accountable issuer." | §4.2-4.3 scope, role, interval |
| CA04, CA23, EP7 | "Machine assistance or a passing test cannot certify itself." Independence "wherever required" | Role separation (§4.2); the S04 Copilot exception does not extend (P3 text) |
| CA14, Tier 1 | Authority, trust, authentication and negative-evidence custody are Tier 1 | Focused independent review before activation (R09 gate) |

Plan v1.2 mapping: §3.1 selection object (identity, epoch, tenant/scope, interval, revocation reference, exact pins) = §4.3; §3.3-binding threat-model paragraph = §3; R09 tasks (trusted activation configuration, immutable approved selection manifests/pins/epochs, anti-rollback, selection revocation, key/identity management or approved equivalent, recovery) = §§4.2-4.10; R09 exit negatives (forged, altered, replayed, cross-tenant, expired, superseded, revoked, source substitution, stale cache, missing custody, rollback) are the acceptance targets for §4.10; R17 key compromise/rotation and loaded-code custody = §4.8 and B-09; R16 "no global authority ledger" = §4.12. Crosswalk: A2 (authority separation), A3 (separate lifecycles), A5 (atomic effective-policy binding, scope clarification), A10 (independent qualification). COG-REG-SHARED-ADD-01 was not read; shared-envelope conventions are Lane D/E territory.

## 6. Decisions raised

| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| B-01 | Authentication primitive. **RULED in direction (Architect ruling, not operator-approved):** asymmetric authenticated statement; prefer reuse of the OCS evidence-attestation or ODES Ed25519 contract; no fourth system; pin-only not general authorization. Remaining: bounded fitness/compatibility assessment of BitRep, ODES, CP `producer_keys`, and the choice | OCS Architect (verifier contract); independent security reviewer (qualification) | R09 cannot specify verification, tests or dependency footprint until the assessment concludes | D2 (ruled), V1 |
| B-02 | Owner and procedure for trust-root custody, issuer enrollment, signing-key ownership, key ceremony, secure time, trust-snapshot distribution, key rotation and storage (HSM/KMS or not). **NOT adopted by the Architect ruling**; needs an operator-approved R09 mechanism | Operator | No trust root exists; R09 activation gate cannot be met; T8 stays open | D2 |
| B-03 | Whether records themselves need origin signatures, or whether authority via signed selection suffices (the ruling requires record approval and selection authorization to be distinct authorities; record-signature need still open) | OCS Architect | Determines who signs approval statements and what Lane A lifecycle events require | D2, D3, V3 |
| B-04 | Role separation. **RULED in principle (Architect ruling):** distinct authorities; one individual in several roles only under an explicit operator-approved separation-of-duties policy. Remaining: the policy itself, witness role and any waiver | Operator | "Independently authorized selection" (v1.2) is unenforceable until the policy exists | D2 |
| B-05 | Anti-rollback state: configuration floor only, or consumer-side durable high-water mark | OCS Architect | Rollback tests (R09 exit) cannot be written; durable state adds new mutable state needing its own custody | none |
| B-06 | Add scope/tenant to the BitRep custody claim, or carry it in signed selection bytes (convention) | OCS Architect with BitRep owner | Cross-tenant substitution protection depends on it; a profile change touches another component | V1 |
| B-07 | Whether a selection may name an older record version (rollback as forward epoch) and how S03 `version_not_latest`/`supersedes` interact | OCS Architect with Lane A | Rollback and recovery procedures undefined; successor schema needed | D3 |
| B-08 | Status freshness bound and revocation distribution latency (value, resolver, clock source) | Operator | Revocation window is unbounded until set; depends on the open 60-versus-300 and unresolved S02 classifications if freshness families join MSOP | none |
| B-09 | Loaded-code integrity (T5): accept exclusion, or approve a verify-then-load-same-bytes control and deployment custody for Runtime | Operator, Independent qualifier | Without it, an "authenticated" selection can drive tampered evaluator code; R17 loaded-code checks have no target | none |
| B-10 | Dependency profile: allow `cryptography`/pydantic in the consumer or in a separate verifier component | Builder-routine, OCS Architect | S04 stdlib-only invariant and T1 supply-chain assumptions change | none |
| B-11 | External witness location and holder (signed tag in hub repo is the stated owner default for `witness-digest`) | Operator | Tamper visibility against the store writer is unavailable | none |
| B-12 | Independent security review scope of authority-bearing paths before activation (G2) and qualifier identity | Operator | Gate G2 and R09 exit cannot close; Copilot review was scoped to S04 only | none |

No decision is made by this document beyond recording the Architect rulings above; none is operator-approved.

## 7. Risks and unresolved constraints

- Selected-versus-proposed mismatch: only BitRep v1 verification is "selected" in the lock; the custody profile this design leans on is "proposed, optional". The design may need the BitRep owner to adopt it. Not established that it is stable.
- Control Plane facts (`rule_revision`, `witness`, `validate_evidence`) come from `7a4bcd40`, not from the S01 pin `0a41faa9`; availability at the baseline tuple is unverified. No test suite was run by this lane, so every [DEV-TESTED] label rests on the component's own documentation and test files existing, not on a reproduced pass.
- The rule-revision model authenticates nothing by itself; reusing its resolution logic without a keyed proof would repeat the S03 L1 flaw at a higher layer.
- Conservative key revocation invalidates every statement of a revoked key, so one compromise forces mass re-selection; consequence for operations not measured.
- No as-of verification: post-hoc audit depends on retained decision-time evidence, so retention policy matters (Constitution preservation vs privacy and retention limits).
- Independence checks (distinct issuers and keys) are synthetic; one actor can hold all roles. Code cannot prove organizational independence (CA04/CA23).
- The witness gives visibility, not protection against its own holder.
- Single-host consumers: trust snapshot and `TrustConfig` share the host with the evaluator; T1/P1 exclusions remain, and the design does not narrow them. Attackers with root defeat it by construction.
- Depends on open decisions, not settled here: PR #17 D2, D3, V1, V3; S02 unresolved classifications (none used directly); the 60-versus-300 relationship (affects any freshness bound, B-08); MSOP (v1.2 §3.4) not adopted, so which families and tenants must be scoped is unknown.
- Not inspected: shared addendum COG-REG-SHARED-ADD-01; Index and Governed Exchange source; BitRep source internals; GCR review documents. Cross-domain custody (GCR holds its own selection authority; matched digests transfer nothing) is stated as a requirement, not designed.
- Nothing here is implemented, approved, activated or qualified; no pin is approved (T8).
