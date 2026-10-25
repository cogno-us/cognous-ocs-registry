# R08-S01 Lane E: Ed25519 verifier reuse assessment (read-only)

Purpose: compare the Ed25519 verification capabilities that already exist in the OCS stack, and recommend the smallest safe reuse path for selection-statement verification in `registry_successor/`. This is a read-only source assessment. It creates no key, trust root, issuer or infrastructure, selects no operator issuer, and changes no other repository.

Architectural preparation only. Unqualified. No operational authentication, trust root or approved pin exists. Cryptographic authenticity is not policy authorization.

## 1. Sources and exact revisions

| Source | Revision | Read |
|---|---|---|
| BitRep / Evidence Attestation: `cogno-us/cognous-evidence-attestation` | `981036c315856c71207984797b0c4e48d3b3921d` | `utils/verification.py`, `utils/trust.py`, `models/verification.py`, `docs/VERIFICATION_CONTRACT_V1.md`, `docs/AUTHORITY_DIGEST_CUSTODY_PROFILE_V1.md`, `requirements.in`/lock |
| ODES: `cogno-us/open-decision-evidence-standard` | `1a5e1d300250d832e611633f0bf8f762e398c0ec` | `src/odes/signatures.py`, `pyproject.toml` |
| Control Plane: `cogno-us/cognous-control-plane` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `src/agent_control_plane/runtime_authority.py` (`validate_evidence`, `producer_keys`), `src/agent_control_plane/rule_revision.py` header, `pyproject.toml` |
| Registry | branch `implementation/r08-s01-foundation`; `registry_successor/verify.py` (injected `SignatureVerifier`), `requirements-s01.lock.txt`, venv `/tmp/claude-0/venv` | verified below |

Observation: an anonymous clone of `cogno-us/BitRep` and of `cogno-us/cognous-evidence-attestation` both returned `981036c...` with identical file listings, and the hub lock records `981036c...` for the attestation repository (`docs/source-provenance.md`, per `docs/r08-preparation/02-authentication-and-custody.md`). I treat them as the same source; I did not establish why (rename, mirror or other); `gh api` for both repositories was refused for this session (HTTP 403), so repository metadata was not inspected.

Not inspected: upstream test suites were not run; no network trust distribution, deployment or service code beyond the files above; the Index and Governed Exchange; `cognous-iss-core` (access-limited); independent cryptographic review of any of these verifiers (none seen). Control Plane pin `0a41faa9` was not diffed (head `7a4bcd40` only).

## 2. Findings from source [EXISTING unless stated]

| Capability | BitRep v1 verifier (`981036c`) | ODES `signatures.py` (`1a5e1d3`) | Control Plane `validate_evidence` (`7a4bcd4`) |
|---|---|---|---|
| Primitive and library | Ed25519 via pyca `cryptography` (`utils/verification.py:5-6, 69-71`) | Ed25519 via pyca `cryptography`, imported lazily, optional extra (`signatures.py:3, 68-75`; `pyproject.toml:17-18`) | Ed25519 via pyca `cryptography`, imported at call (`runtime_authority.py:216-218`; extra at `pyproject.toml:17`) |
| Canonical statement verification | Domain prefix `BitRep attestation v1\n` + sorted compact ASCII JSON of a strict model (`verification.py:11-18`) | DSSE v1 pre-authentication encoding over canonical package bytes (`signatures.py:7-16, 82-93`) | Canonical bytes of an exact-field statement (`runtime_authority.py:197-218`) |
| Trusted-key handling | Operator snapshot `TrustRegistry`, keys by `(issuer, key_id)`, base64 raw 32 bytes, validated strictly (`trust.py:32-62`); loaded from an env-named local file, fail-closed (`trust.py:69-76`) | Keys only from recipient `trusted_keys`; the algorithm belongs to the key, not the envelope (`signatures.py:18-20, 62-63`) | Host-configured `producer_keys` hex map; evidence cannot select keys (`runtime_authority.py:150-156, 212`) |
| Signature integrity | Exact 64-byte, canonical-base64 signature check before verify (`verification.py:65-73`) | Detached envelope; payload recomputed; mismatch refused (`signatures.py:14-16`) | Raw hex signature; any exception maps to `evidence_signature_invalid` (`:216-221`) |
| Audience and scope | `audience` must equal snapshot audience (`verification.py:46-47`); no scope or operation fields | None in the verifier; recipient policy is outside it | Checks `institution_id`, `authority_domain`, `tenant_id` of the statement against context (`:225-237`) |
| Key revocation | `revoked_at`; revocation rejects even backdated statements (`verification.py:52-54`) | `revoked` flag on a trusted key, `key_revoked` (`signatures.py:181-183`) | None in this path |
| Trust-snapshot versioning | `registry_version: bitrep-trust/1`, `published_at`/`valid_until`, `fingerprint()` over the snapshot (`trust.py:50-66`; `verification.py:28-29`) | None (a list, no version or interval) | None (`catalogue_version` is on the profile, not a key snapshot) |
| Expiry | Key and statement windows; no skew allowance (`verification.py:55-64`) | None; states no trusted signing time (`signatures.py:22-25`) | None in the verifier |
| Deterministic refusal | Closed reason set returned as a result; `TrustUnavailable` raised when the snapshot is not current (`verification.py:29, 42-73`) | Closed codes `REASON_CODES` and statuses pass/fail/unsupported/unavailable (`signatures.py:41-55, 116-118`); missing library gives `unavailable`, never pass (`:3-5, 245-250`) | Closed `evidence_*` codes; missing library gives `evidence_verifier_unavailable` (`:218-219`) |
| Offline and synthetic testing | Ephemeral synthetic keys in tests; a public synthetic fixture (`VERIFICATION_CONTRACT_V1.md:85-87`; `tests/`) | Detached-signature tests use generated keys (`tests/test_detached_signature.py`); not run | Synthetic keys in `tests/test_runtime_authority.py`; not run |
| Anti-rollback | None: snapshot is read each time; "anti-rollback snapshot distribution" is listed as not implemented (`AUTHORITY_DIGEST_CUSTODY_PROFILE_V1.md:114`; `VERIFICATION_CONTRACT_V1.md:47`) | None | None |
| Assurance claim | `issuer_signature_only` (`verification.py:39`) | "authenticates origin only" (`signatures.py:22-25, 57-58`) | Origin plus statement binding; no authority claim |

Further findings:
1. All three reuse the same library (pyca `cryptography`); none implements Ed25519 itself. So a registry verifier built on any of them adds no fourth primitive, only a possible dependency.
2. BitRep's `verify_attestation` requires BitRep's own models (`pydantic`, `cryptography`; `requirements.in`), a fixed `AttestationEnvelope` shape (`models/verification.py:13-36`), and integer-epoch times. The registry statement of `docs/r08-s01-contract.md` section 3 has different fields (consumer, scope, operation, epoch, interval, supersession) and ISO timestamps, so it cannot be passed to BitRep unchanged; it would be carried as the signed subject (`content_digest`) of a BitRep statement, which verifies only the issuer signature and snapshot, not consumer, scope or operation. Mapping those stays in the registry layer.
3. The BitRep Authority Digest Custody Profile adds epoch, effective interval and a distinct witness, but states it is "bounded optional proposal" and non-authorizing (`AUTHORITY_DIGEST_CUSTODY_PROFILE_V1.md:3, 13-15`), and its epoch is an externally supplied expectation, not a floor kept by the consumer.
4. [EXISTING] Registry environment: `import cryptography` fails in `/tmp/claude-0/venv` (ModuleNotFoundError, Python 3.13.17). `requirements-s01.lock.txt` is the hash-locked pytest-only set (colorama, iniconfig, packaging, pluggy, pytest). The registry consumer and contract are stdlib-only (trust limitations T1, per `docs/r08-preparation/02-authentication-and-custody.md`).
5. None of the three verifies a registry-shaped selection today, and no operational issuer, key, snapshot or custody procedure exists (trust-limitations T8).

## 3. What adding a dependency would change (decision B-10, open)

Adding `cryptography` to the registry (verifier component or tests) would: add a hash-locked, binary, native-extension package to `requirements-s01.lock.txt` (a lock regeneration that is itself a supply-chain change); end the "stdlib-only, no native code" property that S04's trust assumptions rely on; require an SBOM/licence check (plan R17); and make the registry's authenticity depend on a library version it does not currently pin. It would also make "authenticated" claims depend on an unqualified wiring of that library. This sprint is not authorized to take that decision; it belongs to the Architect with the operator (B-10).

## 4. Recommendation [PROPOSAL]

Smallest safe reuse path for this sprint: **bounded interface plus explicit refusal; no verifier is bundled.**
1. Keep the injected `SignatureVerifier.verify(alg, public_key, message, signature) -> bool` protocol (`registry_successor/verify.py:60-61`). With no verifier supplied, the authenticity layer refuses `verifier_unavailable`; it never falls back to a digest match. This mirrors ODES's missing-library behavior (`unavailable`, not pass) and the Control Plane's `evidence_verifier_unavailable`.
2. Do not import or vendor BitRep, ODES or Control Plane code, and do not add a dependency in R08-S01. A reuse adapter would be a later, separately authorized increment: an adapter that calls pyca `Ed25519PublicKey.from_public_bytes(...).verify(...)` in the same way all three do, kept outside `registry_successor/` core, with the trust-snapshot semantics (versioned snapshot, validity interval, key revocation, no backdating) taken from the BitRep v1 contract rather than redesigned.
3. Carry over BitRep's reviewed semantics as requirements for the registry's `TrustSnapshot`, not as code: audience equals the consumer; revocation rejects regardless of issuance time; the snapshot must be current; key material is never replaced under an existing key id; the algorithm belongs to the trusted key, not the statement.
4. Do not claim cryptographic capability the package lacks: tests use a clearly labelled test double, so developer evidence shows layer separation only, not signature correctness.
5. Anti-rollback remains an open limitation in all three; the registry's `min_epochs`/revoked sets are explicit inputs, and their durable distribution is an R09 operator decision (B-05).

## 5. Decisions for the Architect

| ID | Decision | Owner | Blocking consequence |
|---|---|---|---|
| E-A | Approve adding pyca `cryptography` (hash-locked) to a registry verifier adapter, or keep the verifier injected and external | Architect with operator (B-10) | No real signature check can run inside the registry until decided |
| E-B | Select which verifier is the canonical reuse target: BitRep v1 (snapshot, revocation, expiry), ODES DSSE, or Control Plane `producer_keys` pattern | Architect (B-01) | Trust-snapshot format cannot be fixed beyond the injected interface |
| E-C | Whether selection statements are carried as the BitRep subject (`content_digest`) or verified directly with registry-specific fields | Architect | Scope/operation binding must be done in the registry layer if BitRep is used |
| E-D | Trust-root custody, issuer enrollment, key ceremony, snapshot distribution, rollback protection | Operator (R09; not adopted) | Verification stays technical; no selection is operationally authorized |
| E-E | Independent cryptographic and security review of any adapter | Independent security reviewer | No `QUALIFIED` label for authenticity |
