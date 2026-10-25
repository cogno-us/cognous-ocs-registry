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

    def run(sig_text, public_key, policy):
        env = r.make_envelope(stmt, key_id="key-test-1", public_key=b"x", signed=False)
        env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": sig_text}]
        sel = selection.parse_selection_envelope(r.dumps(env))
        grant = mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
        trust = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                  (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", public_key, (grant,)),))
        return mod.verify_selection(sel, ctx, trust, _V64(), r.NOW, key_admission=policy)

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
    assert run(base64.b64encode(raw_bad).decode("ascii"), bad_key, None).ok is True
    assert run(canon, key, ka.builtin_key_admission).ok is True
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
        "drop_admission_branch": [("    elif admission_detail is not None:\n        mark(\"trust_snapshot\", \"trust_snapshot_invalid\", admission_detail)\n", "")],
        "admission_ignored": [("    if key_admission is None:\n        return None\n    for key_id", "    return None\n    for key_id")],
        "admission_none_means_builtin": [("    if key_admission is None:\n        return None\n", "    if key_admission is None:\n        key_admission = lambda a, k: True\n")],
        "admission_skips_revoked": [("    for key_id, (entry, _grants) in trust[\"issuers\"].items():\n        cause", "    for key_id, (entry, _grants) in trust[\"issuers\"].items():\n        if key_id in trust[\"revoked_keys\"]:\n            continue\n        cause")],
        "policy_truthy_accepted": [("admitted = key_admission(entry.alg, entry.public_key) is True", "admitted = bool(key_admission(entry.alg, entry.public_key))")],
        "policy_exception_admits": [("        except Exception:\n            admitted = False", "        except Exception:\n            admitted = True")],
        "drop_builtin_cause": [("cause = inspect_ed25519_key(entry.public_key) if entry.alg == SUPPORTED_ALG else None", "cause = None")],
        "cause_not_in_detail": [("({cause or 'policy_refused'}; key_id={key_id})", "(refused; key_id={key_id})")],
        "admission_only_first_issuer": [("    for key_id, (entry, _grants) in trust[\"issuers\"].items():", "    for key_id, (entry, _grants) in list(trust[\"issuers\"].items())[:1]:")],
        "admission_passed_not_threaded": [("return _verify(selection, context, trust, verifier, now, record, key_admission)", "return _verify(selection, context, trust, verifier, now, record, None)")],
    }),
}

CASES = [(mod, name) for mod, (_, ms) in MUTANTS.items() for name in ms]


@pytest.mark.parametrize("mod", list(MUTANTS))
def test_unmutated_source_passes_its_probe(mod):
    probe = MUTANTS[mod][0]
    probe(_load(mod) if mod != "verify" else _load("verify"))


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
