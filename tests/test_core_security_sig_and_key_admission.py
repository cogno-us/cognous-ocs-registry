"""Core-security tests: canonical base64 signatures and trust-boundary key admission.

SECURITY-HELD. AI-reviewed only: not an independent cryptographic review and not Tier 1 qualification.
No cryptography library is used. Curve points below come from plain integer arithmetic over the Ed25519 field.
"""
import base64
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import key_admission as ka  # noqa: E402
from registry_successor import selection, verify  # noqa: E402
from registry_successor.canonical_b64 import decode_canonical_base64  # noqa: E402

CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
KEY = "key-test-1"
P = ka.P
D = (-121665 * pow(121666, -1, P)) % P
L = 2**252 + 27742317777372353535851937790883648493


def _add(a, b):
    x1, y1 = a
    x2, y2 = b
    t = D * x1 * x2 * y1 * y2
    return ((x1 * y2 + x2 * y1) * pow(1 + t, -1, P) % P, (y1 * y2 + x1 * x2) * pow(1 - t, -1, P) % P)


def _mul(pt, n):
    acc = (0, 1)
    while n:
        if n & 1:
            acc = _add(acc, pt)
        pt = _add(pt, pt)
        n >>= 1
    return acc


def _enc(pt):
    x, y = pt
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _base():
    y = 4 * pow(5, -1, P) % P
    x2 = (y * y - 1) * pow(D * y * y + 1, -1, P) % P
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * pow(2, (P - 1) // 4, P) % P
    if x & 1:
        x = P - x
    return (x, y)


B = _base()
RFC8032_PUBLIC_KEYS = (  # RFC 8032 section 7.1 test vectors 1 and 2
    bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"),
    bytes.fromhex("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"),
)
SMALL_ORDER_ENCODINGS = tuple(bytes.fromhex(h) for h in (
    "0100000000000000000000000000000000000000000000000000000000000000",
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000080",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
))
LEGIT_KEYS = RFC8032_PUBLIC_KEYS + tuple(_enc(_mul(B, s)) for s in range(1, 41))


# ---------------------------------------------------------------- canonical base64

def _variants(raw: bytes):
    """Every spelling that decode(validate=True) maps to `raw` by varying the unused trailing bits of the last char."""
    canonical = base64.b64encode(raw).decode("ascii")
    pad = len(canonical) - len(canonical.rstrip("="))
    if pad == 0:
        return [canonical]
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    last = canonical.rstrip("=")[-1]
    spare = 4 if pad == 2 else 2
    base = alphabet.index(last) & ~((1 << spare) - 1)
    return [canonical.rstrip("=")[:-1] + alphabet[base + i] + "=" * pad for i in range(1 << spare)]


RAW64 = hashlib.sha512(b"core-security-vector").digest()


def test_sixteen_spellings_decode_to_the_same_64_bytes_under_the_old_rule():
    spellings = _variants(RAW64)
    assert len(set(spellings)) == 16
    assert all(base64.b64decode(s, validate=True) == RAW64 for s in spellings)


def test_only_the_canonical_spelling_is_accepted():
    spellings = _variants(RAW64)
    canonical = base64.b64encode(RAW64).decode("ascii")
    assert [s for s in spellings if decode_canonical_base64(s) is not None] == [canonical]
    assert decode_canonical_base64(canonical) == RAW64


@pytest.mark.parametrize("raw_len", [0, 1, 2, 3, 31, 32, 33, 63, 64, 65])
def test_every_length_has_exactly_one_accepted_spelling(raw_len):
    raw = hashlib.sha512(b"len%d" % raw_len).digest()[:raw_len] if raw_len <= 64 else hashlib.sha512(b"x").digest() + b"y"
    accepted = [s for s in _variants(raw) if decode_canonical_base64(s) is not None]
    assert accepted == [base64.b64encode(raw).decode("ascii")]


@pytest.mark.parametrize("bad", [
    "", " ", "AAAA ", " AAAA", "AA\nAA", "AAAA\n", "AA AA", "AAA", "AAAA=", "AA=A", "A===", "====",
    "AAAA\x00", "ＡAAA", "-_-_", "AB-_", "AAA​",
])
def test_malformed_and_non_standard_text_is_refused(bad):
    if bad == "":
        assert decode_canonical_base64(bad) == b""  # empty text is canonical for empty bytes; length is checked downstream
        return
    assert decode_canonical_base64(bad) is None


@pytest.mark.parametrize("value", [None, 1, 1.5, b"AAAA", bytearray(b"AAAA"), memoryview(b"AAAA"), ["AAAA"], {"a": 1}, True])
def test_non_str_signature_values_are_refused(value):
    assert decode_canonical_base64(value) is None


def test_str_subclass_is_refused():
    class S(str):
        pass
    assert decode_canonical_base64(S("AAAA")) is None


class Sig64Verifier:
    """Accepts exactly one 64-byte signature per message. Test double, not cryptography."""

    def verify(self, alg, public_key, message, signature):
        return alg == "ed25519" and signature == hashlib.sha512(b"sig|" + public_key + b"|" + message).digest()


PK = b"public-key-test-1"


def _signed_selection(signature_text):
    stmt = r.make_statement()
    env = r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=False)
    env["signatures"] = [{"alg": "ed25519", "key_id": KEY, "signature": signature_text}]
    sel = selection.parse_selection_envelope(r.dumps(env))
    return stmt, sel


def _trust(public_key=PK):
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    return verify.TrustSnapshot(
        snapshot_id="trust-snap-test-1", version=1, valid_until="2026-12-31T00:00:00Z",
        issuers=(verify.IssuerEntry(key_id=KEY, issuer_id="issuer-test-1", alg="ed25519", public_key=public_key, authority=(grant,)),))


def _verify(signature_text, **kw):
    from registry_successor.selection import signing_input
    stmt, sel = _signed_selection(signature_text)
    kw.setdefault("contract_version", "r08-v2")  # canonical spelling is enforced on the r08-v2 path only
    return verify.verify_selection(sel, CTX, _trust(kw.pop("public_key", LEGIT_KEYS[0])),
                                   Sig64Verifier(), r.NOW, **kw), signing_input(stmt)


def _canonical_signature():
    from registry_successor.selection import signing_input
    msg = signing_input(r.make_statement())
    raw = hashlib.sha512(b"sig|" + LEGIT_KEYS[0] + b"|" + msg).digest()
    return raw


def test_pipeline_accepts_only_the_canonical_signature_spelling():
    raw = _canonical_signature()
    results = []
    for text in _variants(raw):
        report, _ = _verify(text)
        results.append((text == base64.b64encode(raw).decode("ascii"), report.layers["authenticity"], report.code, report.detail))
    verified = [x for x in results if x[1] == verify.PASS]
    assert len(verified) == 1 and verified[0][0] is True
    refused = [x for x in results if x[0] is False]
    assert len(refused) == 15
    assert all(x[1] == verify.REFUSE and x[2] == "signature_invalid" and x[3] == "signature is not canonical base64" for x in refused)


def test_non_base64_text_keeps_its_existing_distinct_detail():
    report, _ = _verify("!!not base64!!")
    assert (report.code, report.detail) == ("signature_invalid", "signature is not valid base64")


def test_wrong_but_canonical_signature_still_says_does_not_verify():
    report, _ = _verify(base64.b64encode(hashlib.sha512(b"other").digest()).decode("ascii"))
    assert (report.code, report.detail) == ("signature_invalid", "signature does not verify")


def test_no_reason_code_was_added():
    assert len(c.CODES) == 46


# ---------------------------------------------------------------- key admission

def test_legitimate_keys_pass_the_builtin_check():
    assert len(LEGIT_KEYS) == 42
    assert all(ka.inspect_ed25519_key(k) is None for k in LEGIT_KEYS)
    assert all(ka.builtin_key_admission("ed25519", k) is True for k in LEGIT_KEYS)


def test_small_order_table_matches_independent_arithmetic():
    torsion = set()
    t = None
    for y in range(2, 200):
        x2 = (y * y - 1) * pow(D * y * y + 1, -1, P) % P
        x = pow(x2, (P + 3) // 8, P)
        if (x * x - x2) % P:
            x = x * pow(2, (P - 1) // 4, P) % P
        if (x * x - x2) % P:
            continue
        t = _mul((x, y), L)
        q = t
        for _ in range(8):
            torsion.add(_enc(q))
            q = _add(q, t)
        if len(torsion) == 8:
            break
    assert torsion == set(SMALL_ORDER_ENCODINGS)


@pytest.mark.parametrize("enc", SMALL_ORDER_ENCODINGS)
def test_each_of_the_eight_small_order_encodings_is_refused(enc):
    assert ka.inspect_ed25519_key(enc) == "key_small_order"
    assert ka.builtin_key_admission("ed25519", enc) is False


def test_the_identity_key_is_refused():
    assert ka.inspect_ed25519_key(b"\x01" + b"\x00" * 31) == "key_small_order"


def test_x_zero_sign_bit_spellings_of_identity_and_order_two_are_refused():
    assert ka.inspect_ed25519_key(bytes.fromhex("01" + "00" * 30 + "80")) == "key_small_order"
    assert ka.inspect_ed25519_key(bytes.fromhex("ec" + "ff" * 30 + "ff")) == "key_small_order"


def test_all_thirty_eight_non_canonical_y_aliases_are_refused():
    refused = 0
    for y in range(19):
        for sign in (0, 1):
            enc = (y + P | (sign << 255)).to_bytes(32, "little")
            assert ka.inspect_ed25519_key(enc) == "key_non_canonical_y", (y, sign)
            refused += 1
    assert refused == 38


def test_y_equal_to_p_and_the_top_of_the_range_are_refused():
    for y in (P, P + 1, 2**255 - 1):
        for sign in (0, 1):
            assert ka.inspect_ed25519_key((y | (sign << 255)).to_bytes(32, "little")) == "key_non_canonical_y"


def test_largest_canonical_y_is_not_refused_as_non_canonical():
    assert ka.inspect_ed25519_key((P - 2).to_bytes(32, "little")) is None


@pytest.mark.parametrize("n", [0, 1, 7, 31, 33, 64])
def test_wrong_length_keys_are_refused(n):
    assert ka.inspect_ed25519_key(b"\x07" * n) == "key_length"


@pytest.mark.parametrize("value", [None, "a" * 32, bytearray(32), memoryview(bytes(32)), 5, [1] * 32])
def test_wrong_type_keys_are_refused(value):
    assert ka.inspect_ed25519_key(value) == "key_type"


def test_bytes_subclass_is_refused():
    class K(bytes):
        pass
    assert ka.inspect_ed25519_key(K(LEGIT_KEYS[0])) == "key_type"


def test_documented_limitation_a_mixed_order_key_passes_the_builtin_check():
    """The built-in check is not subgroup validation. A + small-order point is mixed order and is NOT refused here."""
    a = _mul(B, 5)
    t = _mul(B, 1)  # placeholder replaced below
    # an order-8 point: clear the prime-order part of a point of unknown order
    for y in range(2, 200):
        x2 = (y * y - 1) * pow(D * y * y + 1, -1, P) % P
        x = pow(x2, (P + 3) // 8, P)
        if (x * x - x2) % P:
            x = x * pow(2, (P - 1) // 4, P) % P
        if (x * x - x2) % P:
            continue
        torsion = _mul((x, y), L)
        if torsion != (0, 1) and _mul(torsion, 4) != (0, 1):
            t = torsion
            break
    mixed = _enc(_add(a, t))
    assert mixed not in LEGIT_KEYS
    assert ka.inspect_ed25519_key(mixed) is None


def test_other_algorithms_are_not_judged_by_the_builtin_policy():
    assert ka.builtin_key_admission("future-alg", b"x") is True


def test_compose_requires_every_policy_to_return_exactly_true():
    yes, no = (lambda a, k: True), (lambda a, k: False)
    assert ka.compose_key_admission(yes, yes)("ed25519", b"k") is True
    assert ka.compose_key_admission(yes, no)("ed25519", b"k") is False
    assert ka.compose_key_admission(lambda a, k: 1)("ed25519", b"k") is False
    assert ka.compose_key_admission(lambda a, k: None)("ed25519", b"k") is False
    assert ka.compose_key_admission(lambda a, k: (_ for _ in ()).throw(RuntimeError("x")))("ed25519", b"k") is False
    assert ka.compose_key_admission()("ed25519", b"k") is True


def _good_signature_for(public_key):
    from registry_successor.selection import signing_input
    msg = signing_input(r.make_statement())
    return base64.b64encode(hashlib.sha512(b"sig|" + public_key + b"|" + msg).digest()).decode("ascii")


def _admit(public_key, policy):
    stmt = r.make_statement()
    env = r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=False)
    env["signatures"] = [{"alg": "ed25519", "key_id": KEY, "signature": _good_signature_for(public_key)}]
    sel = selection.parse_selection_envelope(r.dumps(env))
    return verify.verify_selection(sel, CTX, _trust(public_key), Sig64Verifier(), r.NOW, key_admission=policy)


@pytest.mark.parametrize("bad_key,cause", [
    (b"\x01" + b"\x00" * 31, "key_small_order"),
    (b"1234567", "key_length"),
    ((P).to_bytes(32, "little"), "key_non_canonical_y"),
    (SMALL_ORDER_ENCODINGS[2], "key_small_order"),
])
def test_admission_refuses_the_snapshot_with_the_precise_cause(bad_key, cause):
    report = _admit(bad_key, ka.builtin_key_admission)
    assert report.ok is False and report.code == "trust_snapshot_invalid"
    assert report.layers["trust_snapshot"] == verify.REFUSE and report.layers["authenticity"] == verify.NOT_EVALUATED
    assert cause in report.detail and KEY in report.detail
    assert report.authenticated is False


def test_admission_lets_a_legitimate_key_through_to_normal_verification():
    for key in LEGIT_KEYS[:5]:
        report = _admit(key, ka.builtin_key_admission)
        assert report.ok is True and report.authenticated is True, report.detail


def test_default_is_the_legacy_behaviour_even_for_a_bad_key():
    report = _admit(b"\x01" + b"\x00" * 31, None)
    assert report.ok is True  # legacy: identity key is not refused at the trust boundary when no policy is passed


def test_a_custom_policy_can_refuse_a_key_the_builtin_accepts():
    refuse_all = ka.compose_key_admission(ka.builtin_key_admission, lambda a, k: False)
    report = _admit(LEGIT_KEYS[0], refuse_all)
    assert report.code == "trust_snapshot_invalid" and "policy_refused" in report.detail


def test_a_policy_that_raises_or_returns_non_true_fails_closed():
    def boom(a, k):
        raise RuntimeError("boom")
    assert _admit(LEGIT_KEYS[0], boom).code == "trust_snapshot_invalid"
    assert _admit(LEGIT_KEYS[0], lambda a, k: 1).code == "trust_snapshot_invalid"
    assert _admit(LEGIT_KEYS[0], lambda a, k: None).code == "trust_snapshot_invalid"


def test_malformed_snapshot_still_reports_the_existing_malformed_detail():
    report = verify.verify_selection(_signed_selection("AAAA")[1], CTX, "not a snapshot", Sig64Verifier(), r.NOW,
                                     key_admission=ka.builtin_key_admission)
    assert report.code == "trust_snapshot_invalid" and report.detail == "trust snapshot is malformed"


def test_missing_snapshot_still_reports_missing():
    report = verify.verify_selection(_signed_selection("AAAA")[1], CTX, None, Sig64Verifier(), r.NOW,
                                     key_admission=ka.builtin_key_admission)
    assert report.code == "trust_snapshot_missing"


def test_admission_failure_precedes_expiry_and_missing_time():
    t = _trust(b"1234567")
    sel = _signed_selection("AAAA")[1]
    late = r.NOW.replace(year=2030)
    assert verify.verify_selection(sel, CTX, t, Sig64Verifier(), late, key_admission=ka.builtin_key_admission).code == "trust_snapshot_invalid"
    assert verify.verify_selection(sel, CTX, t, Sig64Verifier(), None, key_admission=ka.builtin_key_admission).code == "trust_snapshot_invalid"
    assert verify.verify_selection(sel, CTX, t, Sig64Verifier(), late).code == "trust_snapshot_expired"


def test_decision_pipeline_forwards_key_admission_policy():
    from registry_successor import decision
    seen = []

    def policy(alg, key):
        seen.append((alg, key))
        return False

    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    stmt = r.make_statement(rec, participation="required")
    sel_text = r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=True))
    args = ("required", caller, r.dumps(rec), sel_text, CTX, _trust(), r.FakeVerifier(), r.NOW)
    assert decision.verify_and_decide(*args).kind == "applied"
    d = decision.verify_and_decide(*args, key_admission=policy)
    assert seen == [("ed25519", PK)]
    assert d.kind != "applied" and d.code == "trust_snapshot_invalid"


def test_revoked_nonsigning_issuer_bad_key_still_blocks_snapshot():
    from registry_successor.selection import signing_input
    good = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    trust = verify.TrustSnapshot(
        snapshot_id="trust-snap-test-1", version=1, valid_until="2026-12-31T00:00:00Z",
        issuers=(verify.IssuerEntry(KEY, "issuer-test-1", "ed25519", good, (grant,)),
                 verify.IssuerEntry("key-test-2", "issuer-test-2", "ed25519", b"\x01" + b"\x00" * 31, (grant,))),
        revoked_key_ids=frozenset({"key-test-2"}))
    raw = hashlib.sha512(b"sig|" + good + b"|" + signing_input(r.make_statement())).digest()
    _stmt, sel = _signed_selection(base64.b64encode(raw).decode("ascii"))
    assert verify.verify_selection(sel, CTX, trust, Sig64Verifier(), r.NOW).ok is True
    report = verify.verify_selection(sel, CTX, trust, Sig64Verifier(), r.NOW, key_admission=ka.builtin_key_admission)
    assert report.code == "trust_snapshot_invalid" and "key-test-2" in report.detail


def test_custom_policy_cannot_relax_the_builtin_ed25519_check():
    report, _ = _verify(base64.b64encode(_canonical_signature()).decode("ascii"), public_key=b"\x01" + b"\x00" * 31,
                        key_admission=lambda a, k: True, contract_version="r08-v1")
    assert report.code == "trust_snapshot_invalid" and "key_small_order" in report.detail


def test_admission_refusal_outranks_snapshot_expiry():
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    bad = b"\x01" + b"\x00" * 31
    expired = verify.TrustSnapshot("trust-snap-test-1", 1, "2000-01-01T00:00:00Z",
                                   (verify.IssuerEntry(KEY, "issuer-test-1", "ed25519", bad, (grant,)),))
    _stmt, sel = _signed_selection(base64.b64encode(_canonical_signature()).decode("ascii"))
    assert verify.verify_selection(sel, CTX, expired, Sig64Verifier(), r.NOW).code == "trust_snapshot_expired"
    refused = verify.verify_selection(sel, CTX, expired, Sig64Verifier(), r.NOW, key_admission=ka.builtin_key_admission)
    assert refused.code == "trust_snapshot_invalid"


def test_non_ed25519_algorithms_are_passed_through_by_the_builtin_policy():
    assert ka.builtin_key_admission("rsa", b"short") is True


# ---------------------------------------------------------------- mandatory admission on the r08-v2 path (Architect ruling B/C)

V2 = "r08-v2"
IDENTITY = b"\x01" + b"\x00" * 31
BAD_KEYS = (
    [(k, "key_small_order") for k in SMALL_ORDER_ENCODINGS]
    + [(P.to_bytes(32, "little"), "key_non_canonical_y"), ((2**255 - 1).to_bytes(32, "little"), "key_non_canonical_y"),
       ((P + 1 | (1 << 255)).to_bytes(32, "little"), "key_non_canonical_y")]
    + [(b"\x07" * n, "key_length") for n in (1, 16, 31, 33, 64)]
)
CALLBACKS = {"omitted": None, "always_true": lambda a, k: True, "builtin": ka.builtin_key_admission,
             "composed_builtin": ka.compose_key_admission(ka.builtin_key_admission)}


def _v2(public_key, policy, contract_version=V2):
    stmt = r.make_statement()
    env = r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=False)
    env["signatures"] = [{"alg": "ed25519", "key_id": KEY, "signature": _good_signature_for(public_key)}]
    sel = selection.parse_selection_envelope(r.dumps(env))
    return verify.verify_selection(sel, CTX, _trust(public_key), Sig64Verifier(), r.NOW,
                                   key_admission=policy, contract_version=contract_version)


@pytest.mark.parametrize("policy_name", list(CALLBACKS))
@pytest.mark.parametrize("bad_key,cause", BAD_KEYS)
def test_v2_path_refuses_bad_keys_whatever_the_callback_says(bad_key, cause, policy_name):
    report = _v2(bad_key, CALLBACKS[policy_name])
    assert report.ok is False and report.code == "trust_snapshot_invalid"
    assert report.layers["trust_snapshot"] == verify.REFUSE and report.layers["authenticity"] == verify.NOT_EVALUATED
    assert report.authenticated is False
    assert report.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID and report.detail_cause == cause


def test_the_identity_key_is_refused_on_v2_even_with_a_permissive_callback():
    report = _v2(IDENTITY, lambda a, k: True)
    assert report.code == "trust_snapshot_invalid" and report.detail_cause == "key_small_order"
    assert report.ok is False and report.authenticated is False


@pytest.mark.parametrize("version", [V2, "r08-v3", "", None, 2, b"r08-v1", "R08-V1", "r08-v1 "])
def test_every_path_but_exact_legacy_v1_is_mandatory(version):
    assert _v2(IDENTITY, None, version).code == "trust_snapshot_invalid"


def test_the_legacy_path_is_unchanged_without_a_callback():
    assert _v2(IDENTITY, None, "r08-v1").ok is True
    assert not hasattr(_v2(IDENTITY, None, "r08-v1"), "detail_code")


def test_an_envelope_that_says_r08_v2_selects_the_mandatory_path_even_on_the_legacy_argument():
    import dataclasses
    stmt, sel = _signed_selection(_good_signature_for(IDENTITY))
    v2sel = dataclasses.replace(sel, envelope={**sel.envelope, "contract_version": V2})
    t = _trust(IDENTITY)
    assert verify.verify_selection(sel, CTX, t, Sig64Verifier(), r.NOW).ok is True
    assert verify.verify_selection(v2sel, CTX, t, Sig64Verifier(), r.NOW).code == "trust_snapshot_invalid"


@pytest.mark.parametrize("policy_name", list(CALLBACKS))
def test_v2_valid_keys_and_valid_signatures_still_pass(policy_name):
    for key in LEGIT_KEYS[:6]:
        report = _v2(key, CALLBACKS[policy_name])
        assert report.ok is True and report.authenticated is True, (key.hex(), report.detail)
        assert type(report) is verify.VerificationReport


def test_a_callback_can_further_restrict_on_v2_with_a_distinct_cause():
    report = _v2(LEGIT_KEYS[0], lambda a, k: False)
    assert report.code == "trust_snapshot_invalid" and report.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID
    assert report.detail_cause == "policy_refused"
    assert _v2(LEGIT_KEYS[0], lambda a, k: 1).detail_cause == "policy_refused"

    def boom(a, k):
        raise RuntimeError("x")
    assert _v2(LEGIT_KEYS[0], boom).detail_cause == "policy_refused"


def test_invalid_key_admission_is_distinguishable_from_a_malformed_snapshot_without_a_new_reason_code():
    sel = _signed_selection("AAAA")[1]
    malformed = verify.verify_selection(sel, CTX, "not a snapshot", Sig64Verifier(), r.NOW, contract_version=V2)
    bad_key = _v2(IDENTITY, None)
    assert malformed.code == bad_key.code == "trust_snapshot_invalid"
    assert malformed.detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED and bad_key.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID
    assert malformed.detail_code != bad_key.detail_code
    assert len(c.CODES) == 46 and "key_admission_invalid" not in c.CODES
    # the frozen r08-v1 serialized shape: a malformed snapshot there is a plain report with no typed fields
    legacy = verify.verify_selection(sel, CTX, "not a snapshot", Sig64Verifier(), r.NOW)
    assert type(legacy) is verify.VerificationReport and legacy.code == "trust_snapshot_invalid"


def test_admission_precedes_expiry_and_time_on_v2_without_any_callback():
    sel = _signed_selection(_good_signature_for(IDENTITY))[1]
    t = _trust(IDENTITY)
    assert verify.verify_selection(sel, CTX, t, Sig64Verifier(), r.NOW.replace(year=2030), contract_version=V2).code == "trust_snapshot_invalid"
    assert verify.verify_selection(sel, CTX, t, Sig64Verifier(), None, contract_version=V2).code == "trust_snapshot_invalid"


def test_decision_pipeline_negative_key_admission_on_v2_never_applies_and_never_returns_the_caller_policy_for_required():
    from registry_successor import decision
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    for participation in ("required", "optional"):
        stmt = r.make_statement(rec, participation=participation)
        for key in (IDENTITY, SMALL_ORDER_ENCODINGS[3], b"short"):
            sel_text = r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=key, signed=True))
            for policy in (None, lambda a, k: True):
                d = decision.verify_and_decide(participation, caller, r.dumps(rec), sel_text, CTX, _trust(key),
                                               r.FakeVerifier(), r.NOW, key_admission=policy, contract_version=V2)
                assert d.code == "trust_snapshot_invalid" and d.operationally_authorized is False
                assert d.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID
                assert d.kind == ("required_policy_unavailable" if participation == "required" else "overlay_not_applied")
                assert (d.effective is None) if participation == "required" else (d.caller_unchanged is True)
            legacy = decision.verify_and_decide(participation, caller, r.dumps(rec), sel_text, CTX, _trust(key),
                                                r.FakeVerifier(), r.NOW)
            assert not hasattr(legacy, "detail_code")  # the legacy r08-v1 decision keeps its frozen shape


def test_decision_pipeline_ordinary_v2_caller_with_a_valid_key_is_still_applied():
    from registry_successor import decision
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    stmt = r.make_statement(rec, participation="required")
    key = LEGIT_KEYS[0]
    sel_text = r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=key, signed=True))
    for policy in (None, ka.builtin_key_admission):
        d = decision.verify_and_decide("required", caller, r.dumps(rec), sel_text, CTX, _trust(key), r.FakeVerifier(),
                                       r.NOW, key_admission=policy, contract_version=V2)
        assert d.kind == "applied" and d.code is None, (d.code, d.detail)
        assert type(d) is decision.PolicyDecision
    legacy = decision.verify_and_decide("required", caller, r.dumps(rec), sel_text, CTX, _trust(key), r.FakeVerifier(), r.NOW)
    assert legacy.kind == "applied"


def test_decision_pipeline_forwards_contract_version_to_the_verifier():
    from registry_successor import decision
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    stmt = r.make_statement(rec, participation="required")
    sel_text = r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=True))
    args = ("required", caller, r.dumps(rec), sel_text, CTX, _trust(), r.FakeVerifier(), r.NOW)
    assert decision.verify_and_decide(*args).kind == "applied"                       # legacy placeholder key
    d = decision.verify_and_decide(*args, contract_version=V2)                       # PK is 17 bytes: key_length
    assert d.code == "trust_snapshot_invalid" and d.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID
    assert d.detail_cause == "key_length"


def test_equal_but_non_str_contract_versions_take_the_mandatory_path():
    import collections

    class StrSub(str):
        pass
    for odd in (collections.UserString("r08-v1"), StrSub("r08-v1"), b"r08-v1"):
        report = _v2(IDENTITY, None, odd)
        assert report.code == "trust_snapshot_invalid" and report.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID, odd
    assert _v2(IDENTITY, None, "r08-v1").ok is True  # the exact legacy str still behaves as before


@pytest.mark.parametrize("junk,cause", [(b"", "key_length"), (None, "key_type"), ("a" * 32, "key_type"),
                                         (bytearray(32), "key_type"), (5, "key_type")])
def test_empty_and_wrong_type_keys_are_admission_failures_on_v2_not_malformed(junk, cause):
    for policy in (None, lambda a, k: True):
        report = verify.verify_selection(
            _signed_selection("AAAA")[1], CTX, _trust(junk), Sig64Verifier(), r.NOW, key_admission=policy, contract_version=V2)
        assert report.code == "trust_snapshot_invalid"
        assert report.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID and report.detail_cause == cause
    legacy = verify.verify_selection(_signed_selection("AAAA")[1], CTX, _trust(junk), Sig64Verifier(), r.NOW)
    assert legacy.code == "trust_snapshot_invalid" and legacy.detail == "trust snapshot is malformed"
    assert type(legacy) is verify.VerificationReport


@pytest.mark.parametrize("junk,cause", [(b"", "key_length"), (None, "key_type"), ("a" * 32, "key_type")])
def test_decision_pipeline_reports_junk_keys_as_key_admission_invalid_on_v2(junk, cause):
    from registry_successor import decision
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    for part in ("required", "optional"):
        sel = r.dumps(r.make_envelope(r.make_statement(rec, participation=part), key_id=KEY, public_key=PK, signed=True))
        d = decision.verify_and_decide(part, caller, r.dumps(rec), sel, CTX, _trust(junk), r.FakeVerifier(), r.NOW,
                                       contract_version=V2)
        assert d.code == "trust_snapshot_invalid" and d.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID
        assert d.detail_cause == cause and d.operationally_authorized is False
        legacy = decision.verify_and_decide(part, caller, r.dumps(rec), sel, CTX, _trust(junk), r.FakeVerifier(), r.NOW)
        assert legacy.code == "trust_snapshot_invalid" and not hasattr(legacy, "detail_code")


class _EqLiar:
    """Instance that tries to pass as the legacy version by coercion: __eq__, __str__, __hash__ and __class__ all lie."""
    __class__ = str  # type() is unaffected by this

    def __eq__(self, other):
        return other == "r08-v1" or other is self

    def __ne__(self, other):
        return False

    def __str__(self):
        return "r08-v1"

    def __hash__(self):
        return hash("r08-v1")


def _contract_version_cases():
    import collections

    class StrSub(str):
        pass

    class StrSubLiar(str):
        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False
        __hash__ = str.__hash__
    return [("exact r08-v2", "r08-v2"), ("UserString r08-v2", collections.UserString("r08-v2")),
            ("str subclass r08-v2", StrSub("r08-v2")), ("bytes r08-v2", b"r08-v2"), ("None", None),
            ("UserString r08-v1", collections.UserString("r08-v1")), ("str subclass r08-v1", StrSub("r08-v1")),
            ("bytes r08-v1", b"r08-v1"), ("__eq__ liar str subclass", StrSubLiar("anything")), ("__eq__/__str__ liar instance", _EqLiar()),
            ("int", 1), ("empty", "")]


@pytest.mark.parametrize("label,version", _contract_version_cases(), ids=[x[0] for x in _contract_version_cases()])
@pytest.mark.parametrize("policy_name", ["omitted", "always_true"])
def test_every_contract_version_but_the_exact_legacy_str_is_mandatory(label, version, policy_name):
    from registry_successor import decision  # noqa: F401
    assert verify._admission_mandatory(None, version) is True
    report = _v2(IDENTITY, CALLBACKS[policy_name], version)
    assert report.ok is False and report.code == "trust_snapshot_invalid" and report.detail_cause == "key_small_order"
    assert _v2(LEGIT_KEYS[0], CALLBACKS[policy_name], version).ok is True  # ordinary callers still pass


def test_envelope_declared_v2_beats_a_legacy_argument_and_odd_envelope_values_are_mandatory():
    import collections
    import dataclasses
    _stmt, sel = _signed_selection(_good_signature_for(IDENTITY))
    t = _trust(IDENTITY)
    for declared in (V2, collections.UserString("r08-v1"), b"r08-v1", None, 1, _EqLiar()):
        forged = dataclasses.replace(sel, envelope={**sel.envelope, "contract_version": declared})
        assert verify._admission_mandatory(forged, "r08-v1") is True, declared
        assert verify.verify_selection(forged, CTX, t, Sig64Verifier(), r.NOW, contract_version="r08-v1").code == "trust_snapshot_invalid"
        assert verify.verify_selection(forged, CTX, t, Sig64Verifier(), r.NOW, key_admission=lambda a, k: True).code == "trust_snapshot_invalid"
    assert verify._admission_mandatory(sel, "r08-v1") is False  # the single legacy skip: exact-str v1 argument AND exact-str v1 envelope
    assert verify._admission_mandatory(None, "r08-v1") is False


def test_the_only_non_mandatory_path_is_exact_str_r08_v1_argument_with_an_exact_str_r08_v1_envelope():
    _stmt, sel = _signed_selection("AAAA")
    non_mandatory = [(sel, "r08-v1"), (None, "r08-v1")]
    for version in [x[1] for x in _contract_version_cases()] + ["r08-v1"]:
        for selection_obj in (sel, None):
            expected_legacy = (selection_obj, version) in non_mandatory and type(version) is str
            assert verify._admission_mandatory(selection_obj, version) is (not expected_legacy)


# ---------------------------------------------------------------- independent-review round (M2, M3, L1)

def _ident_selection():
    _stmt, sel = _signed_selection(_good_signature_for(IDENTITY))
    return sel


def test_m2_stateful_entry_cannot_show_admission_a_good_key_and_the_verifier_the_identity_key():
    sel = _ident_selection()
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")

    class Spy(verify.IssuerEntry):
        reads = 0

        def __getattribute__(self, name):
            if name == "public_key":
                Spy.reads += 1
                return LEGIT_KEYS[0] if Spy.reads <= 1 else IDENTITY
            return object.__getattribute__(self, name)

    for cut in range(1, 6):
        Spy.reads = 0
        entry = Spy(KEY, "issuer-test-1", "ed25519", LEGIT_KEYS[0], (grant,))
        t = verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (entry,))
        seen = []

        class V:
            def verify(self, alg, pk, m, s):
                seen.append(pk)
                return Sig64Verifier().verify(alg, pk, m, s)
        report = verify.verify_selection(sel, CTX, t, V(), r.NOW, contract_version=V2)
        assert report.ok is False and report.code == "trust_snapshot_invalid" and IDENTITY not in seen


def test_m2_stateful_str_subclass_alg_cannot_flip_between_admission_and_verification():
    class FlipAlg(str):
        n = 0

        def __eq__(self, other):
            FlipAlg.n += 1
            return False if FlipAlg.n == 1 else str.__eq__(self, other)
        __hash__ = str.__hash__
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    FlipAlg.n = 0
    t = verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                             (verify.IssuerEntry(KEY, "issuer-test-1", FlipAlg("ed25519"), IDENTITY, (grant,)),))
    report = verify.verify_selection(_ident_selection(), CTX, t, Sig64Verifier(), r.NOW, contract_version=V2)
    assert report.ok is False and report.code == "trust_snapshot_invalid"


def test_m2_mandatory_path_accepts_exact_types_only_for_snapshot_entry_and_grant():
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")

    class SubSnap(verify.TrustSnapshot):
        pass

    class SubEntry(verify.IssuerEntry):
        pass

    class SubGrant(verify.AuthorityGrant):
        pass

    class SubStr(str):
        pass
    sel = _signed_selection(_good_signature_for(LEGIT_KEYS[0]))[1]
    good = verify.IssuerEntry(KEY, "issuer-test-1", "ed25519", LEGIT_KEYS[0], (grant,))
    assert verify.verify_selection(sel, CTX, verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (good,)),
                                   Sig64Verifier(), r.NOW, contract_version=V2).ok is True
    cases = [SubSnap("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (good,)),
             verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                  (SubEntry(KEY, "issuer-test-1", "ed25519", LEGIT_KEYS[0], (grant,)),)),
             verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                  (verify.IssuerEntry(KEY, "issuer-test-1", "ed25519", LEGIT_KEYS[0],
                                                      (SubGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test"),)),)),
             verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                  (verify.IssuerEntry(SubStr(KEY), "issuer-test-1", "ed25519", LEGIT_KEYS[0], (grant,)),))]
    for t in cases:
        report = verify.verify_selection(sel, CTX, t, Sig64Verifier(), r.NOW, contract_version=V2)
        assert report.ok is False and report.code == "trust_snapshot_invalid"
        assert report.detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED


def test_m3_legacy_r08_v1_path_keeps_noncanonical_base64_exactly_as_origin_main():
    """Golden-style: on the frozen legacy path the outcome equals the plain stdlib rule (origin/main behaviour); only r08-v2 is canonical."""
    from registry_successor.selection import signing_input
    key = LEGIT_KEYS[0]
    raw = hashlib.sha512(b"sig|" + key + b"|" + signing_input(r.make_statement())).digest()
    texts = _variants(raw) + [base64.b64encode(raw).decode("ascii") + "\n", " " + base64.b64encode(raw).decode("ascii"),
                              base64.b64encode(raw).decode("ascii").replace("+", "-"), base64.b64encode(raw).decode("ascii")[:-2],
                              base64.b64encode(raw).decode("ascii") + "=", "!!not base64!!"]
    canonical = base64.b64encode(raw).decode("ascii")
    for text in texts:
        try:
            decoded = base64.b64decode(text, validate=True)
            expected_legacy = (True, None) if decoded == raw else (False, "signature does not verify")
        except Exception:
            expected_legacy = (False, "signature is not valid base64")
        rep = verify.verify_selection(_signed_selection(text)[1], CTX, _trust(key), Sig64Verifier(), r.NOW)
        assert (rep.ok, None if rep.ok else rep.detail) == expected_legacy, repr(text)
        assert rep.ok == (rep.code is None) and type(rep) is verify.VerificationReport
        strict = verify.verify_selection(_signed_selection(text)[1], CTX, _trust(key), Sig64Verifier(), r.NOW, contract_version=V2)
        assert strict.ok is (text == canonical), repr(text)
    assert sum(verify.verify_selection(_signed_selection(t)[1], CTX, _trust(key), Sig64Verifier(), r.NOW).ok for t in _variants(raw)) == 16


def test_l1_non_exact_dict_envelopes_take_the_mandatory_path():
    import dataclasses

    class DD(dict):
        pass
    _stmt, sel = _signed_selection(_good_signature_for(IDENTITY))
    t = _trust(IDENTITY)
    for env in (DD({**sel.envelope, "contract_version": V2}), DD(sel.envelope), [sel.envelope], "r08-v1", 7):
        forged = dataclasses.replace(sel, envelope=env)
        assert verify._admission_mandatory(forged, "r08-v1") is True, type(env)
        for kw in ({}, {"contract_version": "r08-v1"}, {"key_admission": lambda a, k: True}):
            assert verify.verify_selection(forged, CTX, t, Sig64Verifier(), r.NOW, **kw).code == "trust_snapshot_invalid"
    # an invalid selection with no envelope keeps the frozen legacy shape (golden corpus compatibility)
    bad = selection.parse_selection_envelope("not json")
    assert bad.ok is False and verify._admission_mandatory(bad, "r08-v1") is False
    # envelope with the version member missing or odd on an ok selection is mandatory
    for decl in (None, 1, b"r08-v1"):
        forged = dataclasses.replace(sel, envelope={**sel.envelope, "contract_version": decl})
        assert verify._admission_mandatory(forged, "r08-v1") is True


def test_m1_envelope_declared_v2_forces_mandatory_even_when_the_argument_is_omitted():
    import dataclasses
    _stmt, sel = _signed_selection(_good_signature_for(IDENTITY))
    forged = dataclasses.replace(sel, envelope={**sel.envelope, "contract_version": V2})
    assert verify.verify_selection(forged, CTX, _trust(IDENTITY), Sig64Verifier(), r.NOW).code == "trust_snapshot_invalid"
    # residual risk (documented, not changed): a v2 caller handing over an envelope that DECLARES r08-v1 and omitting the argument is legacy
    assert verify.verify_selection(sel, CTX, _trust(IDENTITY), Sig64Verifier(), r.NOW).ok is True


# ---------------------------------------------------------------- systematic exact-type / single-read coverage (round 2)

def _v2_run(*, selection_obj=None, trust_obj=None, context=None, now=None, record=None, **trust_over):
    """A fully valid r08-v2 verification with one field replaced; returns the report."""
    key = LEGIT_KEYS[0]
    sel = selection_obj if selection_obj is not None else _signed_selection(_good_signature_for(key))[1]
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    fields = dict(snapshot_id="trust-snap-test-1", version=1, valid_until="2026-12-31T00:00:00Z",
                  issuers=(verify.IssuerEntry(KEY, "issuer-test-1", "ed25519", key, (grant,)),))
    fields.update(trust_over)
    t = trust_obj if trust_obj is not None else verify.TrustSnapshot(**fields)
    return verify.verify_selection(sel, context or CTX, t, Sig64Verifier(), now or r.NOW, record, contract_version=V2)


class _FlipList(list):
    """Reports the revoked key on the first pass and nothing on later passes."""
    n = 0

    def __iter__(self):
        _FlipList.n += 1
        return iter([KEY]) if _FlipList.n == 1 else iter([])


class _LyingInt(int):
    def __lt__(self, other):
        return False

    def __gt__(self, other):
        return True

    def __ge__(self, other):
        return False

    def __le__(self, other):
        return True


class _StrSub(str):
    pass


class _TupleSub(tuple):
    pass


def test_baseline_field_probe_is_ok():
    assert _v2_run().ok is True


@pytest.mark.parametrize("over,expected_code", [
    ({"revoked_key_ids": [KEY]}, "issuer_key_revoked"),
    ({"revoked_key_ids": (KEY,)}, "issuer_key_revoked"),
    ({"revoked_key_ids": frozenset({KEY})}, "issuer_key_revoked"),
    ({"revoked_selections": frozenset({("sel-test-1", 1)})}, None),   # exact containers accepted (code depends on fixture ids)
    ({"min_epochs": {"sel-test-1": 5}}, "selection_epoch_stale"),
    ({"min_epochs": (("sel-test-1", 5),)}, "selection_epoch_stale"),
])
def test_exact_containers_are_honoured_on_the_mandatory_path(over, expected_code):
    rep = _v2_run(**over)
    if expected_code is not None:
        assert rep.ok is False and rep.code == expected_code


def _stateful_cases():
    flip = _FlipList([KEY])
    return [
        ("stateful revoked_key_ids list subclass", {"revoked_key_ids": flip}),
        ("revoked_key_ids dict", {"revoked_key_ids": {KEY: 1}}),
        ("revoked_key_ids with str subclass", {"revoked_key_ids": [_StrSub(KEY)]}),
        ("revoked_key_ids tuple subclass", {"revoked_key_ids": _TupleSub((KEY,))}),
        ("revoked_selections tuple-subclass item", {"revoked_selections": [_TupleSub(("sel-test-1", 1))]}),
        ("revoked_selections lying int epoch", {"revoked_selections": [("sel-test-1", _LyingInt(1))]}),
        ("revoked_selections bool epoch", {"revoked_selections": [("sel-test-1", True)]}),
        ("min_epochs lying int floor", {"min_epochs": {"sel-test-1": _LyingInt(5)}}),
        ("min_epochs bool floor", {"min_epochs": {"sel-test-1": True}}),
        ("min_epochs mapping subclass", {"min_epochs": type("M", (dict,), {})({"sel-test-1": 5})}),
        ("min_epochs str-subclass key", {"min_epochs": {_StrSub("sel-test-1"): 5}}),
        ("version lying int", {"version": _LyingInt(1)}),
        ("version bool", {"version": True}),
        ("snapshot_id str subclass", {"snapshot_id": _StrSub("trust-snap-test-1")}),
        ("valid_until str subclass", {"valid_until": _StrSub("2026-12-31T00:00:00Z")}),
        ("issuers tuple subclass", {"issuers": _TupleSub(())}),
    ]


@pytest.mark.parametrize("label,over", _stateful_cases(), ids=[x[0] for x in _stateful_cases()])
def test_every_trust_snapshot_field_refuses_subclasses_and_lying_objects_on_the_mandatory_path(label, over):
    _FlipList.n = 0
    rep = _v2_run(**over)
    assert rep.ok is False and rep.code == "trust_snapshot_invalid" and rep.detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED, label


class _DictSub(dict):
    pass


class _ListSub(list):
    pass


def _selection_cases():
    base = _signed_selection(_good_signature_for(LEGIT_KEYS[0]))[1]
    import dataclasses

    def repl(**kw):
        return dataclasses.replace(base, **kw)
    stmt = dict(base.statement)
    flips = {"n": 0}

    class FlipDict(dict):
        def get(self, k, d=None):
            flips["n"] += 1
            return dict.get(self, k, d) if flips["n"] < 3 else "other"
    return [
        ("statement dict subclass", repl(statement=_DictSub(stmt))),
        ("statement stateful get", repl(statement=FlipDict(stmt))),
        ("statement nested dict subclass", repl(statement=dict(stmt, scope=_DictSub(stmt["scope"])))),
        ("statement nested str subclass", repl(statement=dict(stmt, operation=_StrSub(stmt["operation"])))),
        ("statement nested lying int epoch", repl(statement=dict(stmt, epoch=_LyingInt(stmt["epoch"])))),
        ("statement float", repl(statement=dict(stmt, epoch=1.0))),
        ("statement_digest str subclass", repl(statement_digest=_StrSub(base.statement_digest))),
        ("signatures list subclass", repl(signatures=_ListSub(base.signatures))),
        ("signature entry dict subclass", repl(signatures=[_DictSub(base.signatures[0])])),
        ("signature text str subclass", repl(signatures=[dict(base.signatures[0], signature=_StrSub(base.signatures[0]["signature"]))])),
        ("ok is 1", repl(ok=1)),
        ("ok is 'yes'", repl(ok="yes")),
        ("ok is a list", repl(ok=[1])),
    ]


@pytest.mark.parametrize("label,sel", _selection_cases(), ids=[x[0] for x in _selection_cases()])
def test_every_selection_field_must_be_exact_data_on_the_mandatory_path(label, sel):
    rep = _v2_run(selection_obj=sel)
    assert rep.ok is False and rep.authenticated is False, label
    assert rep.layers["structural"] == verify.REFUSE, label


def test_context_and_now_and_record_are_exact_typed_single_read_copies_on_the_mandatory_path():
    import datetime

    class CtxSub(c.ExpectedContext):
        pass

    class DT(datetime.datetime):
        pass

    class FlipTz(datetime.tzinfo):
        n = 0

        def utcoffset(self, dt):
            FlipTz.n += 1
            return datetime.timedelta(0) if FlipTz.n == 1 else datetime.timedelta(days=400)

        def dst(self, dt):
            return None

        def tzname(self, dt):
            return "x"
    assert _v2_run(context=CtxSub("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")).code == "selection_scope_mismatch"
    assert _v2_run(context=c.ExpectedContext(_StrSub("consumer-test"), "tenant-a", "inst-a", "domain-a", "op-test")).code == "selection_scope_mismatch"
    n = r.NOW
    sub_now = DT(n.year, n.month, n.day, n.hour, n.minute, n.second, tzinfo=n.tzinfo)
    assert _v2_run(now=sub_now).code == "time_unavailable"
    FlipTz.n = 0
    flip_now = datetime.datetime(n.year, n.month, n.day, n.hour, n.minute, n.second, tzinfo=FlipTz())
    assert _v2_run(now=flip_now).ok is True      # utcoffset read once (1st value 0) -> same instant as intended
    assert FlipTz.n == 1
    # record result: subclass dict / str digest / stateful ok are refused as an invalid record
    rec = r.make_record()
    parsed = __import__("registry_successor.record", fromlist=["x"]).validate_record_text(r.dumps(rec))
    stmt = r.make_statement(rec, participation="required")
    sel = selection.parse_selection_envelope(r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=LEGIT_KEYS[0], signed=True)))
    import dataclasses
    for bad in (dataclasses.replace(parsed, record=_DictSub(parsed.record)), dataclasses.replace(parsed, ok=1),
                dataclasses.replace(parsed, record_digest=_StrSub(parsed.record_digest))):
        rep = verify.verify_selection(sel, CTX, _trust(LEGIT_KEYS[0]), r.FakeVerifier(), r.NOW, bad, contract_version=V2)
        assert rep.ok is False and rep.layers["record_binding"] == verify.REFUSE
    good = verify.verify_selection(sel, CTX, _trust(LEGIT_KEYS[0]), r.FakeVerifier(), r.NOW, parsed, contract_version=V2)
    assert good.ok is True and good.layers["record_binding"] == verify.PASS


def test_l1b_truthy_non_true_ok_without_an_envelope_is_mandatory_not_legacy():
    import dataclasses
    base = _signed_selection(_good_signature_for(IDENTITY))[1]
    t = _trust(IDENTITY)
    for ok in (1, "yes", [1], 2.0):
        forged = dataclasses.replace(base, ok=ok, envelope=None)
        assert verify._admission_mandatory(forged, "r08-v1") is True, ok
        assert verify.verify_selection(forged, CTX, t, Sig64Verifier(), r.NOW).ok is False
    for ok in (False, None):
        genuine_shape = dataclasses.replace(base, ok=ok, envelope=None)
        assert verify._admission_mandatory(genuine_shape, "r08-v1") is (ok is not False)
    assert verify._admission_mandatory(selection.parse_selection_envelope("not json"), "r08-v1") is False


# ---------------------------------------------------------------- resource bounds and half-built objects (round 3)

def test_json_copy_refuses_cycles_shared_references_and_over_budget_quickly_but_copies_ordinary_data():
    import time
    cyc = []
    cyc.append(cyc)
    shared = []
    for _ in range(40):
        shared = [shared, shared]
    twice = [1]
    for bad in (cyc, shared, [twice, twice], [0] * verify.MAX_JSON_NODES, {"a": [[[]] * 3]}):
        t0 = time.monotonic()
        with pytest.raises(verify._NotSnapshottable):
            verify._json_copy(bad)
        assert time.monotonic() - t0 < 2
    ordinary = {"a": [[1, 2], [3]], "b": {"c": "d", "e": None, "f": True}, "g": (1, "x")}
    out = verify._json_copy(ordinary)
    assert out == ordinary and out is not ordinary and out["a"] is not ordinary["a"]
    assert verify._json_copy([0] * (verify.MAX_JSON_NODES - 2)) == [0] * (verify.MAX_JSON_NODES - 2)


def test_hostile_selection_content_is_a_structural_refusal_not_a_hang():
    import dataclasses
    import time
    base = _signed_selection(_good_signature_for(LEGIT_KEYS[0]))[1]
    loop = dict(base.statement)
    loop["self"] = loop
    shared = []
    for _ in range(40):
        shared = [shared, shared]
    for stmt in (loop, dict(base.statement, extra=shared), dict(base.statement, extra=[0] * (verify.MAX_JSON_NODES + 1))):
        t0 = time.monotonic()
        rep = _v2_run(selection_obj=dataclasses.replace(base, statement=stmt))
        assert rep.ok is False and rep.layers["structural"] == verify.REFUSE and time.monotonic() - t0 < 2


def test_half_built_objects_are_typed_refusals_on_the_mandatory_path():
    half_trust = object.__new__(verify.TrustSnapshot)
    rep = verify.verify_selection(_signed_selection(_good_signature_for(LEGIT_KEYS[0]))[1], CTX, half_trust, Sig64Verifier(), r.NOW,
                                  contract_version=V2)
    assert rep.code == "trust_snapshot_invalid" and rep.detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED
    half_entry = object.__new__(verify.IssuerEntry)
    t = verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (half_entry,))
    rep = verify.verify_selection(_signed_selection(_good_signature_for(LEGIT_KEYS[0]))[1], CTX, t, Sig64Verifier(), r.NOW,
                                  contract_version=V2)
    assert rep.code == "trust_snapshot_invalid" and rep.detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED
    rep = _v2_run(context=object.__new__(c.ExpectedContext))
    assert rep.code == "selection_scope_mismatch"
