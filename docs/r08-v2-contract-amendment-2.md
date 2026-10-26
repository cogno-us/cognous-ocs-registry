# R08 contract `r08-v2`: Amendment 2 (canonical base64 signature spelling; versioned addendum)

Status: **AMENDMENT 2 to [`docs/r08-v2-contract.md`](r08-v2-contract.md), a versioned addendum, effective on merge of this file.** It is read on top of the frozen text together with [Amendment 1](r08-v2-contract-amendment-1.md). It is **not** an edit of any hash-pinned historical contract, and it is **not** applied to the pinned contract text: the pinned files stay byte-identical and a reader applies this addendum on top of them. Documentation plus golden vectors only; the behaviour it describes is the one implemented by `registry_successor/canonical_b64.py` and the r08-v2 verification path (PR #34). RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD. Nothing here is "qualified".

Authorization: the Architect authorized a narrow versioned contract amendment, without editing any hash-pinned historical contract, stating the canonical base64 spelling of `r08-v2` signature envelopes, with positive and negative golden vectors.

## 0. Frozen records stay frozen

| Frozen file | git blob (`git hash-object`) | sha256 |
|---|---|---|
| `docs/r08-v2-contract.md` | `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f` | `64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01` |
| `docs/r08-s01-contract.md` (`r08-v1`, section 3 "standard base64 text") | `d8cf632a5f1ba09c38cfb95cecd84e7b4a7e0452` | `da24154e85d803c6c904d650ddad3dda2ef9f7283f37506e7bbae984d16e5541` |

`tests/test_r08_v2_canonical_base64_vectors.py` recomputes these two values and the vector-file hash. If a frozen file ever changes, that test fails and this addendum must be re-anchored by a new amendment, never by silent edit.

## 1. Supersession table

| # | Frozen anchor | Frozen text (verbatim excerpt, tested as a substring) | Clarification (this addendum) |
|---|---|---|---|
| B-1 | `r08-v1` contract section 3, envelope shape (`d8cf632a`) | `signature` standard base64 text | For **`r08-v2` signature envelopes** the text is the canonical spelling of section 2. For `r08-v1` the sentence is unchanged and means the plain standard-library `validate=True` rule (section 4). |

## 2. Canonical spelling rule (r08-v2)

A `signature` string of an `r08-v2` signature envelope is valid **only if it is exactly the canonical RFC 4648 section 4 encoding of the bytes it decodes to**:

1. standard alphabet only: `A-Z a-z 0-9 + /` (no URL-safe `-` `_`, no other alphabet, no character outside the alphabet, no non-ASCII look-alike);
2. padding `=` **required** where the byte length is not a multiple of three, **no omitted padding** and **no excess padding** (no extra `=`, no padding inside the text);
3. **no whitespace** of any kind and no line break, leading, trailing or embedded;
4. **canonical pad bits**: the unused low bits of the final data character are zero (a 64-byte signature has 16 textual spellings that decode to the same bytes; exactly one is canonical);
5. verification is **strict decode followed by a byte-identical canonical re-encoding**: decode with strict (`validate=True`) semantics, re-encode the decoded bytes, and require the re-encoded text to equal the input text exactly;
6. any other textual representation of identical signature bytes is **rejected** (`signature_invalid`, detail `signature is not canonical base64` when strict decoding succeeds, `signature is not valid base64` when it does not). Input is never normalized, trimmed or repaired; a non-`str` value (including `bytes` and `str` subclasses) is rejected.

The rule decides spelling only. It does not decide the signature length or whether the signature verifies, and it adds no reason code (`signature_invalid` is an existing code).

## 3. Scope

- Applies to `r08-v2` signature envelopes: the r08-v2 verification path (`verify_selection_v2` / `verify_and_decide_v2`, or any call with `contract_version` other than the exact string `r08-v1`).
- Applies to the evaluated signature. The `signatures` array is outside the signed statement, so a non-canonical sibling next to a verifying canonical signature is ignored (success is "any trusted signer verifies"); this addendum does not change that and does not make the whole envelope text unique.

## 4. `r08-v1` is frozen and unchanged

The `r08-v1` path keeps the plain `base64.b64decode(..., validate=True)` rule. A non-canonical spelling that decoded and verified before still does. The vectors below are also run against the `r08-v1` path to prove it.

## 5. Golden vectors

Data file: `tests/vectors/r08_v2_canonical_base64_vectors.json` (format `r08-v2-canonical-base64-vectors/1`; NOT under `tests/golden`, which is the frozen r08-v1 corpus). sha256 `5882926c0cb68f700c64cabae96b11740e2d704962a3649d5e71340d7620e636`, pinned by the test. 205 vectors: 12 positive (canonical spellings of 1, 2, 3, 4, 5, 31, 32, 33, 63, 64, 65 and 96 bytes) and 193 negative (every alternate pad-bits spelling, missing padding, excess padding, whitespace and line breaks in every position, URL-safe alphabet, characters outside the alphabet, a fullwidth look-alike, padding inside the text, control characters). 76 of the negatives are accepted by the standard-library strict decoder, which is why they matter. The file was generated once by a throwaway script that uses the standard-library encoder, not by repository code.

`tests/test_r08_v2_canonical_base64_vectors.py` runs every vector (1) against `canonical_b64.decode_canonical_base64`, (2) through the r08-v2 path with a verifier double that accepts every signature, so any refusal is caused by spelling alone, and (3) against the `r08-v1` path, which must accept exactly what the standard-library strict decoder accepts.

## 6. What this addendum does not do

It does not edit `docs/r08-v2-contract.md`, `docs/r08-s01-contract.md` or Amendment 1; it does not add a reason code; it does not introduce a v2 envelope parser; it does not claim that the pinned contract text now contains this rule. It is a versioned addendum to be read with the contract.
