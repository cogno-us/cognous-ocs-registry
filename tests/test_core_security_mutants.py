"""Mutation checks for the core-security guards (SECURITY-HELD, AI-reviewed only).

Each mutant is a one-line source edit of a guard, loaded as a throwaway module. A guard counts as exercised only if
the probe for its module fails (or the module cannot even be checked) under the mutant. The unmutated source must
pass the same probe, so a green run here means every listed mutant was killed.
"""
import base64
import hashlib
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import selection  # noqa: E402
from registry_successor import verify as verify_mod  # noqa: E402

PKG = Path(__file__).resolve().parent.parent / "registry_successor"
P = 2**255 - 19


def _load(name, edits=()):
    src = (PKG / f"{name}.py").read_text(encoding="utf-8")
    for old, new in edits:
        assert src.count(old) == 1, (name, old)
        src = src.replace(old, new)
    mod = types.ModuleType(f"registry_successor._mut_{name}")
    mod.__package__ = "registry_successor"
    exec(compile(src, f"<mutant {name}>", "exec"), mod.__dict__)
    return mod


# ------------------------------------------------------------------ probes

def _b64_probe(mod):
    raw = hashlib.sha512(b"mutant-probe").digest()
    canon = base64.b64encode(raw).decode("ascii")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    base = alphabet.index(canon[-3]) & ~15
    variants = [canon[:-3] + alphabet[base + i] + "==" for i in range(16)]
    assert [v for v in variants if mod.decode_canonical_base64(v) is not None] == [canon]
    assert mod.decode_canonical_base64(canon) == raw
    for bad in ("AAAA\n", " AAAA", "AAA", "AAAA=", "-_-_", "AA\nAA"):
        assert mod.decode_canonical_base64(bad) is None
    for bad in (b"AAAA", None, 5, bytearray(b"AAAA")):
        assert mod.decode_canonical_base64(bad) is None

    class S(str):
        pass
    assert mod.decode_canonical_base64(S("AAAA")) is None


def _key_probe(mod):
    small = ["01" + "00" * 31, "ec" + "ff" * 30 + "7f", "00" * 32, "00" * 31 + "80",
             "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
             "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
             "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
             "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa"]
    for h in small:
        assert mod.inspect_ed25519_key(bytes.fromhex(h)) == "key_small_order", h
    for y in range(19):
        for sign in (0, 1):
            assert mod.inspect_ed25519_key((y + P | (sign << 255)).to_bytes(32, "little")) == "key_non_canonical_y"
    assert mod.inspect_ed25519_key(P.to_bytes(32, "little")) == "key_non_canonical_y"
    assert mod.inspect_ed25519_key((2**255 - 1).to_bytes(32, "little")) == "key_non_canonical_y"
    assert mod.inspect_ed25519_key(bytes.fromhex("01" + "00" * 30 + "80")) == "key_small_order"
    assert mod.inspect_ed25519_key(bytes.fromhex("ec" + "ff" * 30 + "ff")) == "key_small_order"
    for n in (0, 1, 7, 31, 33):
        assert mod.inspect_ed25519_key(b"\x07" * n) == "key_length"
    for v in (None, "a" * 32, bytearray(32), 5):
        assert mod.inspect_ed25519_key(v) == "key_type"

    class K(bytes):
        pass
    assert mod.inspect_ed25519_key(K(bytes(range(1, 33)))) == "key_type"
    assert mod.inspect_ed25519_key(bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")) is None
    assert mod.inspect_ed25519_key((P - 2).to_bytes(32, "little")) is None
    assert mod.builtin_key_admission("ed25519", bytes(32)) is False
    assert mod.builtin_key_admission("future", b"x") is True
    yes, no = (lambda a, k: True), (lambda a, k: False)
    assert mod.compose_key_admission(yes, yes)("e", b"k") is True
    assert mod.compose_key_admission(yes, no)("e", b"k") is False
    assert mod.compose_key_admission(lambda a, k: 1)("e", b"k") is False
    assert mod.compose_key_admission(lambda a, k: (_ for _ in ()).throw(RuntimeError()))("e", b"k") is False


class _V64:
    def verify(self, alg, public_key, message, signature):
        return alg == "ed25519" and signature == hashlib.sha512(b"sig|" + public_key + b"|" + message).digest()


def _verify_probe(mod):
    from registry_successor.selection import signing_input
    ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    stmt = r.make_statement()
    msg = signing_input(stmt)
    key = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    raw = hashlib.sha512(b"sig|" + key + b"|" + msg).digest()
    canon = base64.b64encode(raw).decode("ascii")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    base = alphabet.index(canon[-3]) & ~15

    def run(sig_text, public_key, policy, cv="r08-v1", mutate_env=None):
        env = r.make_envelope(stmt, key_id="key-test-1", public_key=b"x", signed=False)
        env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": sig_text}]
        sel = selection.parse_selection_envelope(r.dumps(env))
        if mutate_env:
            import dataclasses
            sel = dataclasses.replace(sel, envelope={**sel.envelope, **mutate_env})
        grant = mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
        trust = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                  (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", public_key, (grant,)),))
        if cv == "malformed":
            trust = "not a snapshot"
            cv = "r08-v2"
        return mod.verify_selection(sel, ctx, trust, _V64(), r.NOW, key_admission=policy, contract_version=cv)

    good = run(canon, key, None)
    assert good.ok is True
    odd = run(canon[:-3] + alphabet[base + 1] + "==", key, None)
    assert odd.ok is False and odd.detail == "signature is not canonical base64"
    assert run("!!bad!!", key, None).detail == "signature is not valid base64"
    from registry_successor import key_admission as ka
    bad_key = b"\x01" + b"\x00" * 31
    raw_bad = hashlib.sha512(b"sig|" + bad_key + b"|" + msg).digest()
    refused = run(base64.b64encode(raw_bad).decode("ascii"), bad_key, ka.builtin_key_admission)
    assert refused.code == "trust_snapshot_invalid" and "key_small_order" in refused.detail
    assert refused.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID
    assert run(base64.b64encode(raw_bad).decode("ascii"), bad_key, None).ok is True
    assert run(canon, key, ka.builtin_key_admission).ok is True
    # r08-v2 path: admission is MANDATORY; omitted or permissive callbacks cannot bypass the built-in check
    bad_sig = base64.b64encode(raw_bad).decode("ascii")
    for policy in (None, lambda a, k: True, ka.builtin_key_admission):
        v2 = run(bad_sig, bad_key, policy, "r08-v2")
        assert v2.ok is False and v2.code == "trust_snapshot_invalid", policy
        assert v2.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID and v2.detail_cause == "key_small_order"
    assert run(bad_sig, bad_key, None, "not-a-version").code == "trust_snapshot_invalid"
    assert run(bad_sig, bad_key, None, None).code == "trust_snapshot_invalid"
    assert run(bad_sig, bad_key, None, "r08-v1", {"contract_version": "r08-v2"}).code == "trust_snapshot_invalid"
    assert run(bad_sig, bad_key, None, "r08-v1", {"contract_version": "r08-v1"}).ok is True
    assert run(canon, key, None, "r08-v2").ok is True
    assert run(canon, key, lambda a, k: True, "r08-v2").ok is True
    stricter = run(canon, key, lambda a, k: False, "r08-v2")
    assert stricter.code == "trust_snapshot_invalid" and stricter.detail_cause == "policy_refused"
    assert run(canon, key, lambda a, k: (_ for _ in ()).throw(RuntimeError()), "r08-v2").detail_cause == "policy_refused"
    import collections
    class StrSub(str):
        pass
    for odd in (collections.UserString("r08-v1"), StrSub("r08-v1"), b"r08-v1"):
        assert run(bad_sig, bad_key, None, odd).code == "trust_snapshot_invalid", odd
    for junk, cause in ((b"", "key_length"), (None, "key_type"), ("a" * 32, "key_type"), (bytearray(32), "key_type")):
        jr = run(canon, junk, None, "r08-v2")
        assert jr.code == "trust_snapshot_invalid" and jr.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID and jr.detail_cause == cause, junk
        assert run(canon, junk, None).detail == "trust snapshot is malformed"  # legacy normalization untouched
    grant = mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    for junk, cause in ((b"", "key_length"), (None, "key_type")):
        other = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                  (mod.IssuerEntry("key-test-1", "issuer-test-1", "future-alg", junk, (grant,)),))
        selx = selection.parse_selection_envelope(r.dumps(r.make_envelope(stmt, key_id="key-test-1", public_key=b"x", signed=False)))
        o = mod.verify_selection(selx, ctx, other, _V64(), r.NOW, contract_version="r08-v2")
        assert o.code == "trust_snapshot_invalid" and o.detail_code == ka.DETAIL_KEY_ADMISSION_INVALID and o.detail_cause == cause
    mal = run(canon, key, None, "malformed")
    assert mal.code == "trust_snapshot_invalid" and mal.detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED
    assert mal.detail_code != ka.DETAIL_KEY_ADMISSION_INVALID
    legacy_mal = mod.verify_selection(selection.parse_selection_envelope(r.dumps(
        r.make_envelope(stmt, key_id="key-test-1", public_key=b"x", signed=False))), ctx, "x", _V64(), r.NOW)
    assert type(legacy_mal) is mod.VerificationReport  # frozen r08-v1 serialized shape: no extra fields
    assert run(canon, key, lambda a, k: 1).code == "trust_snapshot_invalid"
    assert run(canon, key, lambda a, k: (_ for _ in ()).throw(RuntimeError())).code == "trust_snapshot_invalid"
    custom = run(canon, key, lambda a, k: False)
    assert custom.code == "trust_snapshot_invalid" and "policy_refused" in custom.detail
    # every issuer is checked: admitted first key, refused second key that did not sign
    env = r.make_envelope(stmt, key_id="key-test-1", public_key=b"x", signed=False)
    env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": canon}]
    sel = selection.parse_selection_envelope(r.dumps(env))
    grant = mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    two = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (
        mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", key, (grant,)),
        mod.IssuerEntry("key-test-2", "issuer-test-2", "ed25519", bad_key, (grant,))))
    second = mod.verify_selection(sel, ctx, two, _V64(), r.NOW, key_admission=ka.builtin_key_admission)
    assert second.code == "trust_snapshot_invalid" and "key-test-2" in second.detail
    assert mod.verify_selection(sel, ctx, two, _V64(), r.NOW).ok is True
    # a revoked, non-signing issuer's bad key still blocks the snapshot
    revoked = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", two.issuers,
                                revoked_key_ids=frozenset({"key-test-2"}))
    rv = mod.verify_selection(sel, ctx, revoked, _V64(), r.NOW, key_admission=ka.builtin_key_admission)
    assert rv.code == "trust_snapshot_invalid" and "key-test-2" in rv.detail


def _decision_probe(mod):
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    grant = verify_mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    trust = verify_mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                     (verify_mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", b"public-key-test-1", (grant,)),))
    for part in ("required", "optional"):
        sel = r.dumps(r.make_envelope(r.make_statement(rec, participation=part), signed=True))
        legacy = mod.verify_and_decide(part, caller, r.dumps(rec), sel, ctx, trust, r.FakeVerifier(), r.NOW)
        assert legacy.code is None and not hasattr(legacy, "detail_code")
        for policy in (None, lambda a, k: True):
            d = mod.verify_and_decide(part, caller, r.dumps(rec), sel, ctx, trust, r.FakeVerifier(), r.NOW,
                                      key_admission=policy, contract_version="r08-v2")
            assert d.code == "trust_snapshot_invalid" and d.detail_code == "key_admission_invalid" and d.detail_cause == "key_length"
            assert d.kind == ("required_policy_unavailable" if part == "required" else "overlay_not_applied")
            assert d.operationally_authorized is False
        good = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        gtrust = verify_mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                          (verify_mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", good, (grant,)),))
        gsel = r.dumps(r.make_envelope(r.make_statement(rec, participation=part), public_key=good, signed=True))
        ok = mod.verify_and_decide(part, caller, r.dumps(rec), gsel, ctx, gtrust, r.FakeVerifier(), r.NOW, contract_version="r08-v2")
        assert ok.code is None
        no = mod.verify_and_decide(part, caller, r.dumps(rec), gsel, ctx, gtrust, r.FakeVerifier(), r.NOW,
                                   key_admission=lambda a, k: False, contract_version="r08-v2")
        assert no.code == "trust_snapshot_invalid" and no.detail_cause == "policy_refused"


MUTANTS = {
    "canonical_b64": (_b64_probe, {
        "drop_reencode_compare": [('    if base64.b64encode(raw).decode("ascii") != text:\n        return None\n', "")],
        "drop_type_check": [("    if type(text) is not str:\n        return None\n", "")],
        "isinstance_type_check": [("type(text) is not str", "not isinstance(text, str)")],
        "return_text_on_mismatch": [('!= text:\n        return None', '!= text:\n        return raw')],
    }),
    "key_admission": (_key_probe, {
        "drop_type_check": [("    if type(public_key) is not bytes:\n        return \"key_type\"\n", "")],
        "isinstance_type_check": [("type(public_key) is not bytes", "not isinstance(public_key, bytes)")],
        "length_check_weakened": [("len(public_key) != 32", "len(public_key) < 1")],
        "length_check_upper_only": [("len(public_key) != 32", "len(public_key) > 32")],
        "drop_canonical_y": [("    if y >= P:\n        return \"key_non_canonical_y\"\n", "")],
        "canonical_y_off_by_one": [("if y >= P:", "if y > P:")],
        "mask_256": [("((1 << 255) - 1)", "((1 << 256) - 1)")],
        "drop_small_order": [("    if y in SMALL_ORDER_Y:\n        return \"key_small_order\"\n", "")],
        "drop_y0": [("SMALL_ORDER_Y = frozenset({\n    0,\n", "SMALL_ORDER_Y = frozenset({\n")],
        "drop_y1": [("    1,\n    P - 1,", "    P - 1,")],
        "drop_ym1": [("    P - 1,\n    0x5fc5", "    0x5fc5")],
        "drop_order8_a": [("    0x5fc536d880238b13933c6d305acdfd5f098eff289f4c345b027b2c28f95e826,\n", "")],
        "drop_order8_b": [("    0x7a03ac9277fdc74ec6cc392cfa53202a0f67100d760b3cba4fd84d3d706a17c7,\n", "")],
        "wrong_p": [("P = 2**255 - 19", "P = 2**255 - 18")],
        "builtin_judges_all_algs": [('    if alg != "ed25519":\n        return True\n', "")],
        "builtin_admits_on_none_wrong": [("return inspect_ed25519_key(public_key) is None", "return inspect_ed25519_key(public_key) is not None")],
        "compose_truthy": [("is not True:\n                    return False", "is False:\n                    return False")],
        "compose_swallow_exception": [("            except Exception:\n                return False", "            except Exception:\n                continue")],
    }),
    "verify": (_verify_probe, {
        "plain_b64decode_for_signature": [("raw = decode_canonical_base64(text)", "raw = base64.b64decode(text, validate=True) if isinstance(text, str) else None")],
        "noncanonical_detail_collapsed": [('"signature is not canonical base64"', '"signature is not valid base64"')],
        "drop_admission_branch": [("    elif admission is not None:\n        mark(\"trust_snapshot\", \"trust_snapshot_invalid\", admission[0], (DETAIL_KEY_ADMISSION_INVALID, admission[1]))\n", "")],
        "admission_ignored": [("    if key_admission is None and not mandatory:\n        return None\n    for key_id", "    return None\n    for key_id")],
        "admission_none_means_builtin": [("    if key_admission is None and not mandatory:\n        return None\n", "    if key_admission is None and not mandatory:\n        key_admission = lambda a, k: True\n")],
        "mandatory_requires_callback": [("    if key_admission is None and not mandatory:", "    if key_admission is None:")],
        "callback_replaces_builtin": [("cause = inspect_ed25519_key(entry.public_key) if entry.alg == SUPPORTED_ALG else None", "cause = inspect_ed25519_key(entry.public_key) if entry.alg == SUPPORTED_ALG and key_admission is None else None")],
        "mandatory_only_for_exact_v2": [("    if type(contract_version) is not str or contract_version != LEGACY_CONTRACT:\n        return True", "    if contract_version == V2_CONTRACT:\n        return True")],
        "legacy_equality_only": [("type(contract_version) is not str or contract_version != LEGACY_CONTRACT", "contract_version != LEGACY_CONTRACT")],
        "legacy_isinstance_str": [("type(contract_version) is not str or", "not isinstance(contract_version, str) or")],
        "junk_key_left_to_normalizer": [("(not mandatory and (not isinstance(entry.public_key, bytes)", "((not isinstance(entry.public_key, bytes)")],
        "junk_key_check_dropped": [("    if mandatory and cause is None and (type(entry.public_key) is not bytes or not entry.public_key):", "    if False:")],
        "junk_key_type_label_swapped": [('cause = "key_type" if type(entry.public_key) is not bytes else "key_length"', 'cause = "key_length"')],
        "mandatory_ignores_envelope_v2": [("selection.envelope.get(\"contract_version\") == V2_CONTRACT", "False")],
        "contract_version_not_threaded": [("record, key_admission, contract_version)", "record, key_admission, LEGACY_CONTRACT)")],
        "malformed_detail_always_typed": [("(DETAIL_TRUST_SNAPSHOT_MALFORMED, None) if mandatory else None", "(DETAIL_TRUST_SNAPSHOT_MALFORMED, None)")],
        "malformed_detail_never_typed": [("(DETAIL_TRUST_SNAPSHOT_MALFORMED, None) if mandatory else None", "None")],
        "typed_detail_swapped": [("(DETAIL_KEY_ADMISSION_INVALID, admission[1]))", "(DETAIL_TRUST_SNAPSHOT_MALFORMED, admission[1]))")],
        "typed_detail_dropped": [("    if not ok and first in typed:", "    if False:")],
        "admission_skips_revoked": [("    for key_id, (entry, _grants) in trust[\"issuers\"].items():\n        cause", "    for key_id, (entry, _grants) in trust[\"issuers\"].items():\n        if key_id in trust[\"revoked_keys\"]:\n            continue\n        cause")],
        "policy_truthy_accepted": [("admitted = key_admission(entry.alg, entry.public_key) is True", "admitted = bool(key_admission(entry.alg, entry.public_key))")],
        "policy_exception_admits": [("            except Exception:\n                admitted = False", "            except Exception:\n                admitted = True")],
        "drop_builtin_cause": [("cause = inspect_ed25519_key(entry.public_key) if entry.alg == SUPPORTED_ALG else None", "cause = None")],
        "cause_not_in_detail": [("({cause}; key_id={key_id})", "(refused; key_id={key_id})")],
        "admission_only_first_issuer": [("    for key_id, (entry, _grants) in trust[\"issuers\"].items():", "    for key_id, (entry, _grants) in list(trust[\"issuers\"].items())[:1]:")],
        "admission_passed_not_threaded": [("record, key_admission, contract_version)\n    except", "record, None, contract_version)\n    except")],
    }),
    "decision": (_decision_probe, {
        "contract_version_not_forwarded": [("rec, key_admission, contract_version)", "rec, key_admission)")],
        "key_admission_not_forwarded": [("rec, key_admission, contract_version)", "rec, None, contract_version)")],
        "typed_detail_dropped": [("typed = (dc, cause if type(cause) is str else None) if type(dc) is str else None", "typed = None")],
        "typed_cause_dropped": [("typed = (dc, cause if type(cause) is str else None) if type(dc) is str else None", "typed = (dc, None) if type(dc) is str else None")],
    }),
}

CASES = [(mod, name) for mod, (_, ms) in MUTANTS.items() for name in ms]


@pytest.mark.parametrize("mod", list(MUTANTS))
def test_unmutated_source_passes_its_probe(mod):
    probe = MUTANTS[mod][0]
    probe(_load(mod))


@pytest.mark.parametrize("mod,name", CASES)
def test_mutant_is_killed(mod, name):
    probe, mutants = MUTANTS[mod]
    try:
        mutated = _load(mod, mutants[name])
    except (AssertionError, SyntaxError, NameError):
        # an edit that no longer matches the source (assert in _load) must fail loudly, not count as killed
        raise
    try:
        probe(mutated)
    except Exception:
        return
    pytest.fail(f"mutant {mod}:{name} survived")


def test_documented_equivalent_mutant_validate_false_behaves_identically():
    """`validate=False` is subsumed by the re-encode comparison (defense in depth), so it cannot be killed by behaviour.

    Pinned by exhaustive comparison over every string of length <= 4 on an alphabet that includes the characters
    validate=True exists to refuse, plus a seeded random battery. If this ever diverges, the mutant stops being
    equivalent and must be moved into MUTANTS.
    """
    import itertools
    import random
    orig = _load("canonical_b64")
    mutant = _load("canonical_b64", [("base64.b64decode(text, validate=True)", "base64.b64decode(text, validate=False)")])
    alphabet = "AZaz09+/=-_ \n\x00\u00e9"
    for n in range(5):
        for tup in itertools.product(alphabet, repeat=n):
            text = "".join(tup)
            assert orig.decode_canonical_base64(text) == mutant.decode_canonical_base64(text), repr(text)
    rng = random.Random(20261025)
    chars = alphabet + "BCDEFGHIJKLMNOPQRSTUVWXY"
    for _ in range(20000):
        text = "".join(rng.choice(chars) for _ in range(rng.randrange(0, 90)))
        assert orig.decode_canonical_base64(text) == mutant.decode_canonical_base64(text), repr(text)
