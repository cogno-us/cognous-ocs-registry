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
    return verify.verify_selection(sel, CTX, _trust(**({"public_key": kw.pop("public_key")} if "public_key" in kw else {})),
                                   Sig64Verifier(), r.NOW, **kw), signing_input(stmt)


def _canonical_signature():
    from registry_successor.selection import signing_input
    msg = signing_input(r.make_statement())
    raw = hashlib.sha512(b"sig|" + PK + b"|" + msg).digest()
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
