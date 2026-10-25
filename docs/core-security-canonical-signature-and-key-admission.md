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

## 3. Evidence

- 85 behavioural tests and 37 mutation checks (`tests/test_core_security_*.py`): 16 non-canonical spellings through the full
  verifier pipeline, the 8 small-order encodings, 38 aliases, junk and wrong-type keys, 42 legitimate keys (RFC 8032 vectors 1
  and 2 plus 40 derived by plain integer arithmetic), 40 source mutants killed, one documented equivalent mutant pinned.
- Limits: no real Ed25519 library is used in these tests; point arithmetic is a test-local transcription; only CPython.
