# Core verifier hardening: canonical signature text and key admission

Status: SECURITY-HELD. BUILDER_TESTED. AI-reviewed only (not independent cryptographic review, not Tier 1). Not merged until
Architect security review. Trust-root activation remains held. Authority: Architect Batch 6 ruling 11, separate from PR #26.

## 1. Canonical base64 signature text

Contract `docs/r08-s01-contract.md` section 3 says only "standard base64 text". It does not state the canonical spelling,
so this PR adopts the plain reading: RFC 4648 section 4, padding present, no whitespace or line breaks, unused trailing
bits zero. Implemented by decode then re-encode and compare (`registry_successor/canonical_b64.py`).

Why: `base64.b64decode(..., validate=True)` accepts 16 spellings of every 64-byte signature (the last character carries
four unused bits). That is a second spelling of the same signed envelope.

Behaviour change: a signature spelled any way but canonical now refuses `signature_invalid` with detail
`signature is not canonical base64`. Undecodable text keeps `signature is not valid base64`; a canonical signature that
fails verification keeps `signature does not verify`. No reason code is added (CODES stays 46). Non-`str` signature values
(including `bytes`) now refuse; parsed envelopes only ever carry `str`. The v1 golden corpus is unchanged and passes.

Open question for the Architect: the contract text should state the canonical spelling explicitly. This PR does not edit the
hash-pinned contract file.

## 2. Key admission at the trust boundary

`verify_selection(..., key_admission=None)` takes an optional policy `(alg, public_key) -> bool`, applied to every issuer key
when the trust snapshot is admitted. A refused key makes the snapshot `trust_snapshot_invalid` (existing code) with a detail
naming the cause and key id, and authenticity is not evaluated. A policy that raises, or returns anything but exactly `True`,
refuses.

Default `None` keeps the legacy behaviour: existing fixtures use non-32-byte placeholder keys and the frozen v1 vectors must
not change. A production caller must pass a policy. Whether the default should become mandatory for `r08-v2` is an open
Architect question.

`registry_successor/key_admission.py` provides `builtin_key_admission` (pure standard library). It DOES refuse: non-`bytes`,
length other than 32, any encoding whose y coordinate is not below p (all 38 non-canonical y aliases and everything above),
and any encoding whose y is one of the five small-order values for either sign bit (the eight canonical small-order encodings,
including the identity, plus the non-canonical x = 0 sign-bit spellings).

It does NOT refuse: a y that is not on the curve, or a point outside the prime-order subgroup. Mixed-order keys (A plus a
small-order point) pass this built-in check; a test pins that limitation. The Ed25519 adapter's stricter
`acceptable_public_key` (PR #26, unmerged) is meant to be composed in with `compose_key_admission`. Until a subgroup-validating policy or
verifier is in place, mixed-order keys and signatures made with them MAY be accepted; PR #26 reports libsodium's signature check
alone accepting mixed-order cases. This PR does not close that gap.

### 2a. Behaviour notes (documented, not changed)

- **The built-in Ed25519 check always runs.** Whenever any `key_admission` policy is supplied, `inspect_ed25519_key` is applied
  to every ed25519 issuer key in addition to the policy, and a refusal by either refuses the snapshot. A custom policy can
  therefore only tighten admission; it cannot relax the built-in check (for example to admit test keys). Pinned by a test.
- **Ordering.** An admission refusal outranks `time_unavailable` and `trust_snapshot_expired`: a bad key with an expired snapshot
  reports `trust_snapshot_invalid`.
- **Every issuer is checked.** All issuers in the snapshot are checked, including revoked and non-signing ones, so one bad key
  blocks the whole snapshot. This is fail-closed and intended. Pinned by a test and a mutant.
- **Non-ed25519 algorithms.** `builtin_key_admission` returns `True` for them because the verifier never verifies them
  (`_authenticity` treats any non-ed25519 algorithm as not good); admission is therefore irrelevant to them.
- **Detail is not surfaced by the decision layer.** `verify_and_decide` drops the report detail for every code (pre-existing),
  so callers of that entrypoint see only `trust_snapshot_invalid`.

### 2b. Envelope-level spelling is not unique

Canonical spelling applies to the signature that is evaluated. The `signatures` array is outside the signed statement, so an
envelope that carries a canonical signature that verifies plus a non-canonical sibling signature is accepted: the sibling is
ignored because success is "any trusted signer verifies". The non-canonical entry alone is refused. The canonical rule
therefore does not make the whole envelope text unique. Behaviour is unchanged by this PR. If whole-envelope uniqueness is
wanted, a separate decision would reject any non-canonical supported-algorithm signature for a trusted key even when another
verifies.

### 2c. OPEN GATE for Architect decision (not implemented here)

`key_admission` defaults to `None`, so a caller that omits it gets no admission at all on the single public entrypoint
`verify_and_decide` (a small-order key is then refused only generically at signature time). Before any trust-root activation:
1. admission must be mandatory on the r08-v2 path, or default to `builtin_key_admission` there (the v1 path stays legacy,
   because v1 fixtures use placeholder keys); and
2. a subgroup-validating check (the PR #26 adapter's `acceptable_public_key`, or equivalent) must be composed in with
   `compose_key_admission`.
Trust-root activation stays held until both are decided and implemented.

## 3. Evidence

- 85 behavioural tests and 37 mutation checks (`tests/test_core_security_*.py`): 16 non-canonical spellings through the full
  verifier pipeline, the 8 small-order encodings, 38 aliases, junk and wrong-type keys, 42 legitimate keys (RFC 8032 vectors 1
  and 2 plus 40 derived by plain integer arithmetic), 40 source mutants killed, one documented equivalent mutant pinned.
- Limits: no real Ed25519 library is used in these tests; point arithmetic is a test-local transcription; only CPython.
