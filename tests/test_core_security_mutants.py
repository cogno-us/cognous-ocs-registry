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


_V1_DOMAIN, _V2_DOMAIN = b"ocs-reg/r08-v1/selection\n", b"ocs-reg/r08-v2/selection\n"


class _V64:
    """Probe-only double. S01: it maps the r08-v2 signing domain onto the v1 one so ONE canonical signature text drives both paths;
    signing-domain separation itself is covered by tests/test_s01_withdrawal_floor_signing.py (this double is not cryptography)."""

    def verify(self, alg, public_key, message, signature):
        if message.startswith(_V2_DOMAIN):
            message = _V1_DOMAIN + message[len(_V2_DOMAIN):]
        return alg == "ed25519" and signature == hashlib.sha512(b"sig|" + public_key + b"|" + message).digest()


def collections_UserString(text):
    import collections
    return collections.UserString(text)


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

    stmt2 = r.make_statement_v2()
    canon2 = base64.b64encode(hashlib.sha512(b"sig|" + key + b"|" + _V1_DOMAIN + c.canonical_bytes(stmt2)).digest()).decode("ascii")
    base2 = alphabet.index(canon2[-3]) & ~15
    odd1 = canon[:-3] + alphabet[base + 1] + "=="

    def run(sig_text, public_key, policy, cv="r08-v1", mutate_env=None):
        if type(cv) is str and cv in ("r08-v2", "malformed"):  # a real r08-v2 selection (v2 statement + parser) for the v2 path
            # the same canonical / non-canonical TEXTS, re-derived for the v2 statement (the probe double maps the v2 domain to v1)
            sig_text = canon2 if sig_text == canon else (canon2[:-3] + alphabet[base2 + 1] + "==" if sig_text == odd1 else sig_text)
            env = r.make_envelope_v2(r.make_statement_v2(), key_id="key-test-1", public_key=b"x", signed=False)
            env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": sig_text}]
            sel = r.parse_v2(r.dumps(env))
        else:
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
    odd = run(canon[:-3] + alphabet[base + 1] + "==", key, None, "r08-v2")
    assert odd.ok is False and odd.detail == "signature is not canonical base64"
    # frozen r08-v1 path: identical to origin/main, a non-canonical spelling that decodes fine still verifies
    assert run(canon[:-3] + alphabet[base + 1] + "==", key, None, "r08-v1").ok is True
    assert run(canon, key, None, "r08-v2").ok is True
    assert run("!!bad!!", key, None).detail == "signature is not valid base64"
    assert run("!!bad!!", key, None, "r08-v2").detail == "signature is not valid base64"
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
    assert run(bad_sig, bad_key, None, "r08-v1", {"contract_version": "r08-v2"}).code == "contract_unsupported"  # S01: cross-version
    assert run(bad_sig, bad_key, None, "r08-v1", {"contract_version": "r08-v1"}).ok is True
    assert run(bad_sig, bad_key, None, "r08-v1", {"contract_version": collections_UserString("r08-v1")}).code == "trust_snapshot_invalid"
    assert run(bad_sig, bad_key, None, "r08-v1", {"contract_version": None}).code == "trust_snapshot_invalid"
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
        selx = r.parse_v2(r.dumps(r.make_envelope_v2(r.make_statement_v2(), key_id="key-test-1", public_key=b"x", signed=False)))
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

    # TOCTOU: admission and verification must use one private snapshot of each entry (mandatory path)
    ident = b"\x01" + b"\x00" * 31
    ident_sig = base64.b64encode(hashlib.sha512(b"sig|" + ident + b"|" + _V1_DOMAIN + c.canonical_bytes(r.make_statement_v2())).digest()).decode("ascii")
    selx = r.parse_v2(r.dumps(dict(
        r.make_envelope_v2(r.make_statement_v2(), key_id="key-test-1", public_key=b"x", signed=False),
        signatures=[{"alg": "ed25519", "key_id": "key-test-1", "signature": ident_sig}])))
    grant2 = mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")

    class Spy(mod.IssuerEntry):
        reads = 0

        def __getattribute__(self, name):
            if name == "public_key":
                Spy.reads += 1
                return key if Spy.reads <= 1 else ident
            return object.__getattribute__(self, name)

    class FlipAlg(str):
        n = 0

        def __eq__(self, other):
            FlipAlg.n += 1
            return False if FlipAlg.n == 1 else str.__eq__(self, other)
        __hash__ = str.__hash__

    for entry in (Spy("key-test-1", "issuer-test-1", "ed25519", key, (grant2,)),
                  mod.IssuerEntry("key-test-1", "issuer-test-1", FlipAlg("ed25519"), ident, (grant2,))):
        Spy.reads = FlipAlg.n = 0
        t = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (entry,))
        rep = mod.verify_selection(selx, ctx, t, _V64(), r.NOW, contract_version="r08-v2")
        assert rep.ok is False and rep.code == "trust_snapshot_invalid", type(entry)
    # exact snapshot type only on the mandatory path
    class SubSnap(mod.TrustSnapshot):
        pass
    sub = SubSnap("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", key, (grant2,)),))
    assert mod.verify_selection(selx, ctx, sub, _V64(), r.NOW, contract_version="r08-v2").detail_code == ka.DETAIL_TRUST_SNAPSHOT_MALFORMED
    # fail toward mandatory for odd envelopes on the legacy argument
    import dataclasses

    class DD(dict):
        pass
    badsel = selection.parse_selection_envelope("not json")
    assert badsel.ok is False and badsel.envelope is None
    legacy_trust = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                     (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", b"placeholder", (grant2,)),))
    assert mod.verify_selection(badsel, ctx, legacy_trust, _V64(), r.NOW).layers["trust_snapshot"] == mod.PASS  # legacy shape kept
    for env in (DD(selx.envelope, contract_version="r08-v2"), DD(selx.envelope), [1], 5):
        forged = dataclasses.replace(selx, envelope=env)
        assert mod.verify_selection(forged, ctx, mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
            (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", ident, (grant2,)),)), _V64(), r.NOW,
            contract_version="r08-v1").code == "trust_snapshot_invalid", type(env)


def _fields_probe(mod):
    """Systematic exact-type / single-read coverage of every field read on the mandatory path."""
    import dataclasses
    import datetime
    ka = _load("key_admission")
    ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    key = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    stmt = r.make_statement_v2()
    sig = base64.b64encode(hashlib.sha512(b"sig|" + key + b"|" + _V1_DOMAIN + r.signing_input_v2(stmt)[len(_V2_DOMAIN):]).digest()).decode("ascii")
    env = r.make_envelope_v2(stmt, key_id="key-test-1", public_key=b"x", signed=False)
    env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": sig}]
    base = r.parse_v2(r.dumps(env))
    grant = mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")

    def run(sel=None, context=ctx, now=r.NOW, record=None, trust_obj_override=None, **over):
        if trust_obj_override is not None:
            return mod.verify_selection(sel or base, context, trust_obj_override, _V64(), now, record, contract_version="r08-v2")
        f = dict(snapshot_id="trust-snap-test-1", version=1, valid_until="2026-12-31T00:00:00Z",
                 issuers=(mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", key, (grant,)),))
        f.update(over)
        return mod.verify_selection(sel or base, context, mod.TrustSnapshot(**f), _V64(), now, record, contract_version="r08-v2")

    class Flip(list):
        n = 0

        def __iter__(self):
            Flip.n += 1
            return iter(["key-test-1"]) if Flip.n == 1 else iter([])

    class LInt(int):
        def __lt__(self, o): return False
        def __gt__(self, o): return True
        def __ge__(self, o): return False
        def __le__(self, o): return True

    class SS(str):
        pass

    class DS(dict):
        pass

    class LS(list):
        pass

    class TS(tuple):
        pass

    assert run().ok is True
    assert run(revoked_key_ids=["key-test-1"]).code == "issuer_key_revoked"
    assert run(revoked_key_ids=frozenset({"key-test-1"})).code == "issuer_key_revoked"
    assert run(min_epochs={stmt["selection_id"]: stmt["epoch"] + 1}).code == "selection_epoch_stale"
    assert run(min_epochs=((stmt["selection_id"], stmt["epoch"] + 1),)).code == "selection_epoch_stale"
    assert run(revoked_selections=frozenset({(stmt["selection_id"], stmt["epoch"])})).code == "selection_revoked"
    for over in ({"revoked_key_ids": Flip(["key-test-1"])}, {"revoked_key_ids": [SS("key-test-1")]}, {"revoked_key_ids": TS(("key-test-1",))},
                 {"revoked_selections": [("a", LInt(1))]}, {"revoked_selections": [("a", True)]}, {"revoked_selections": [TS(("a", 1))]},
                 {"min_epochs": {stmt["selection_id"]: LInt(stmt["epoch"] + 5)}}, {"min_epochs": {stmt["selection_id"]: True}},
                 {"min_epochs": {SS(stmt["selection_id"]): 5}}, {"min_epochs": DS({stmt["selection_id"]: 5})},
                 {"version": LInt(1)}, {"version": True}, {"snapshot_id": SS("trust-snap-test-1")},
                 {"valid_until": SS("2026-12-31T00:00:00Z")}, {"issuers": TS(())}):
        Flip.n = 0
        rep = run(**over)
        assert rep.ok is False and rep.code == "trust_snapshot_invalid", over
    ent = mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", key, (grant,))
    assert run(issuers=frozenset({ent})).code == "trust_snapshot_invalid"
    assert run(revoked_selections=TS((("a", 1),))).code == "trust_snapshot_invalid"
    for bad in (LS([1]), TS((1,)), DS(), SS("a"), LInt(1), 1.0, {1: 2}, {SS("k"): 1}, b"x", {1}, object(), [[LS()]]):
        try:
            mod._json_copy(bad)
        except mod._NotSnapshottable:
            pass
        else:
            raise AssertionError(repr(bad))
    import time
    cyc = []
    cyc.append(cyc)
    shared = []
    for _ in range(40):
        shared = [shared, shared]
    twice = [1]
    for bad in (cyc, shared, [twice, twice], [0] * mod.MAX_JSON_NODES, {"a": [[[]] * 3]}, {i: 1 for i in (1,)}):
        t0 = time.monotonic()
        try:
            mod._json_copy(bad)
        except mod._NotSnapshottable:
            pass
        else:
            raise AssertionError("accepted")
        assert time.monotonic() - t0 < 2
    deep = []
    cur = deep
    for _ in range(40):
        nxt = []
        cur.append(nxt)
        cur = nxt
    try:
        mod._json_copy(deep)
    except mod._NotSnapshottable:
        pass
    else:
        raise AssertionError("depth")
    assert mod._json_copy([0] * (mod.MAX_JSON_NODES - 2)) == [0] * (mod.MAX_JSON_NODES - 2)
    assert mod._json_copy({"a": [[1, 2], [3]], "b": {"c": "d"}}) == {"a": [[1, 2], [3]], "b": {"c": "d"}}
    # half-built objects are a typed malformed snapshot / scope refusal, not an internal error
    hb = object.__new__(mod.TrustSnapshot)
    assert run(trust_obj_override=hb).code == "trust_snapshot_invalid"
    assert mod.verify_selection(base, object.__new__(c.ExpectedContext), mod.TrustSnapshot(
        "trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", key, (grant,)),)),
        _V64(), r.NOW, contract_version="r08-v2").code == "selection_scope_mismatch"
    sample = {"a": [1, "x", {"b": None, "c": True}], "d": (1, 2)}
    copied = mod._json_copy(sample)
    assert copied == sample and copied is not sample and copied["a"] is not sample["a"]
    assert mod.verify_selection(base, ctx, type("TS2", (mod.TrustSnapshot,), {})("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", ()),
                                _V64(), r.NOW, contract_version="r08-v2").code == "trust_snapshot_invalid"
    st = dict(base.statement)
    for label, sel in (("stmt dict sub", dataclasses.replace(base, statement=DS(st))),
                       ("nested dict sub", dataclasses.replace(base, statement=dict(st, scope=DS(st["scope"])))),
                       ("nested str sub", dataclasses.replace(base, statement=dict(st, operation=SS(st["operation"])))),
                       ("lying epoch", dataclasses.replace(base, statement=dict(st, epoch=LInt(st["epoch"])))),
                       ("float", dataclasses.replace(base, statement=dict(st, epoch=1.0))),
                       ("digest sub", dataclasses.replace(base, statement_digest=SS(base.statement_digest))),
                       ("sigs list sub", dataclasses.replace(base, signatures=LS(base.signatures))),
                       ("sig entry dict sub", dataclasses.replace(base, signatures=[DS(base.signatures[0])])),
                       ("sig text sub", dataclasses.replace(base, signatures=[dict(base.signatures[0], signature=SS(sig))])),
                       ("ok 1", dataclasses.replace(base, ok=1)), ("ok yes", dataclasses.replace(base, ok="yes"))):
        rep = run(sel)
        assert rep.ok is False and rep.layers["structural"] == "refuse", label
    class CS(c.ExpectedContext):
        pass
    assert run(context=CS("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")).code == "selection_scope_mismatch"
    assert run(context=c.ExpectedContext(SS("consumer-test"), "tenant-a", "inst-a", "domain-a", "op-test")).code == "selection_scope_mismatch"

    class DT(datetime.datetime):
        pass
    n = r.NOW
    assert run(now=DT(n.year, n.month, n.day, n.hour, n.minute, n.second, tzinfo=n.tzinfo)).code == "time_unavailable"

    class FTz(datetime.tzinfo):
        k = 0
        def utcoffset(self, dt):
            FTz.k += 1
            return datetime.timedelta(0) if FTz.k == 1 else datetime.timedelta(days=400)
        def dst(self, dt): return None
        def tzname(self, dt): return "x"
    FTz.k = 0
    assert run(now=datetime.datetime(n.year, n.month, n.day, n.hour, n.minute, n.second, tzinfo=FTz())).ok is True and FTz.k == 1
    rec = r.make_record()
    parsed = __import__("registry_successor.record", fromlist=["x"]).validate_record_text(r.dumps(rec))
    rstmt = r.make_statement_v2(rec, participation="required")
    renv = r.make_envelope_v2(rstmt, key_id="key-test-1", public_key=key, signed=True)
    rsel = r.parse_v2(r.dumps(renv))
    def rrun(rr):
        t = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                              (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", key, (grant,)),))
        return mod.verify_selection(rsel, ctx, t, r.FakeVerifier(), r.NOW, rr, contract_version="r08-v2")
    assert rrun(parsed).ok is True
    for bad in (dataclasses.replace(parsed, record=DS(parsed.record)), dataclasses.replace(parsed, ok=1),
                dataclasses.replace(parsed, record_digest=SS(parsed.record_digest))):
        assert rrun(bad).ok is False
    # FU-2: snapshot-version ingest bound, typed evidence
    for v_ok in (1, 2**53 - 1):
        assert run(version=v_ok).ok is True
    for v_bad in (0, -1, 2**53, 2**60, True, 1.0, "1", None, LInt(1)):
        rep = run(version=v_bad, snapshot_id="bad id")
        assert rep.ok is False and rep.code == "trust_snapshot_invalid", v_bad
        assert (rep.detail_code, rep.detail_stage, rep.detail_member) == ("trust_snapshot_malformed", "ingest", "trust_snapshot_version"), v_bad
    other = run(snapshot_id="bad id")
    assert other.detail_stage is None and other.detail_member is None
    # v2 entry point hardwires the version
    ident = b"\x01" + b"\x00" * 31
    isig0 = base64.b64encode(hashlib.sha512(b"sig|" + ident + b"|" + _V1_DOMAIN + c.canonical_bytes(stmt)).digest()).decode("ascii")
    ienv0 = r.make_envelope_v2(stmt, key_id="key-test-1", public_key=b"x", signed=False)
    ienv0["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": isig0}]
    isel0 = r.parse_v2(r.dumps(ienv0))
    it0 = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", ident, (grant,)),))
    for pol in (None, lambda a, k: True):
        assert mod.verify_selection_v2(isel0, ctx, it0, _V64(), r.NOW, None, pol).code == "trust_snapshot_invalid"
    assert mod.verify_selection_v2(base, ctx, mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (mod.IssuerEntry(
        "key-test-1", "issuer-test-1", "ed25519", key, (grant,)),)), _V64(), r.NOW, None, lambda a, k: False).detail_cause == "policy_refused"
    # L1b
    ident = b"\x01" + b"\x00" * 31
    isig = base64.b64encode(hashlib.sha512(b"sig|" + ident + b"|" + _V1_DOMAIN + c.canonical_bytes(stmt)).digest()).decode("ascii")
    ienv = r.make_envelope_v2(stmt, key_id="key-test-1", public_key=b"x", signed=False)
    ienv["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": isig}]
    isel = r.parse_v2(r.dumps(ienv))
    it = mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z", (mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", ident, (grant,)),))
    for ok in (1, "yes", [1]):
        forged = dataclasses.replace(isel, ok=ok, envelope=None)
        assert mod.verify_selection(forged, ctx, it, _V64(), r.NOW).ok is False, ok
    assert mod._admission_mandatory(dataclasses.replace(isel, ok=None, envelope=None), "r08-v1") is True
    assert mod._admission_mandatory(dataclasses.replace(isel, ok=False, envelope=None), "r08-v1") is False


def _decision_probe(mod):
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"],
              "allowed_units": ["unit-a", "unit-b", "unit-c"]}
    rec = r.make_record()
    rec2 = r.make_record_v2()  # V01a: the v2 entry takes r08-v2 records only; `rec` stays for the frozen v1 entry
    ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    grant = verify_mod.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    trust = verify_mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                     (verify_mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", b"public-key-test-1", (grant,)),))
    for part in ("required", "optional"):
        sel1 = r.dumps(r.make_envelope(r.make_statement(rec, participation=part), signed=True))
        sel = r.dumps(r.make_envelope_v2(r.make_statement_v2(rec2, participation=part), signed=True))
        legacy = mod.verify_and_decide(part, caller, r.dumps(rec), sel1, ctx, trust, r.FakeVerifier(), r.NOW)
        assert legacy.code is None and not hasattr(legacy, "detail_code")
        # the legacy entry forwards its contract_version and key_admission: an r08-v1 selection labelled r08-v2 is the wrong contract (S01)
        assert mod.verify_and_decide(part, caller, r.dumps(rec), sel1, ctx, trust, r.FakeVerifier(), r.NOW,
                                     contract_version="r08-v2").code == "contract_unsupported"
        assert mod.verify_and_decide(part, caller, r.dumps(rec), sel1, ctx, trust, r.FakeVerifier(), r.NOW,
                                     key_admission=lambda a, k: False).code == "trust_snapshot_invalid"
        for policy in (None, lambda a, k: True):
            d = mod.verify_and_decide_v2(part, caller, r.dumps(rec2), sel, ctx, trust, r.FakeVerifier(), r.NOW, key_admission=policy)
            assert d.code == "trust_snapshot_invalid" and d.detail_code == "key_admission_invalid" and d.detail_cause == "key_length"
            assert d.kind == ("required_policy_unavailable" if part == "required" else "overlay_not_applied")
            assert d.operationally_authorized is False
        good = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        gtrust = verify_mod.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                          (verify_mod.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", good, (grant,)),))
        gsel = r.dumps(r.make_envelope_v2(r.make_statement_v2(rec2, participation=part), public_key=good, signed=True))
        ok = mod.verify_and_decide_v2(part, caller, r.dumps(rec2), gsel, ctx, gtrust, r.FakeVerifier(), r.NOW)
        assert ok.code is None
        no = mod.verify_and_decide_v2(part, caller, r.dumps(rec2), gsel, ctx, gtrust, r.FakeVerifier(), r.NOW,
                                      key_admission=lambda a, k: False)
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
        "canonical_b64_on_legacy_path": [("raw = decode_canonical_base64(text)  # r08-v2 only", "raw = decode_canonical_base64(text) if True else None  # r08-v2 only"),
                                         ("            if canonical_b64:\n", "            if True:\n")],
        "canonical_b64_never": [("            if canonical_b64:\n", "            if False:\n")],
        "v2_gate_dropped": [("    if wrong_contract and getattr(selection, \"ok\", False) is True:", "    if False and getattr(selection, \"ok\", False) is True:")],
        "authenticity_not_given_mandatory": [("_authenticity(statement, selection, trust, verifier, mandatory, v2)", "_authenticity(statement, selection, trust, verifier, False, v2)")],
        "entry_not_private_copy": [("        entry = _private_entry(raw)", "        entry = raw if type(raw) is IssuerEntry else None")],
        "exact_entry_type_dropped": [("    if type(entry) is not IssuerEntry:\n        return None\n    key_id", "    key_id")],
        "exact_alg_type_dropped": [("or type(alg) is not str:\n        return None\n    if type(authority)", ":\n        return None\n    if type(authority)")],
        "exact_snapshot_type_dropped": [("    if type(trust) is not TrustSnapshot:\n        return None\n    snapshot_id,", "    snapshot_id,")],
        "envelope_non_dict_legacy": [("return envelope is not None or getattr(selection, \"ok\", False) is not False", "return False")],
        "envelope_okless_none_mandatory": [("return envelope is not None or getattr(selection, \"ok\", False) is not False", "return True")],
        "legacy_equality_only": [("type(contract_version) is not str or contract_version != LEGACY_CONTRACT", "contract_version != LEGACY_CONTRACT")],
        "legacy_isinstance_str": [("type(contract_version) is not str or", "not isinstance(contract_version, str) or")],
        "junk_key_left_to_normalizer": [("if entry is None or not c.valid_token(entry.key_id)", "if entry is None or type(entry.public_key) is not bytes or not c.valid_token(entry.key_id)")],
        "junk_key_check_dropped": [("    if mandatory and cause is None and (type(entry.public_key) is not bytes or not entry.public_key):", "    if False:")],
        "junk_key_type_label_swapped": [('cause = "key_type" if type(entry.public_key) is not bytes else "key_length"', 'cause = "key_length"')],
        "mandatory_ignores_envelope_v2": [("return type(declared) is not str or declared != LEGACY_CONTRACT", "return False")],
        "envelope_equality_only": [("return type(declared) is not str or declared != LEGACY_CONTRACT", "return declared == V2_CONTRACT")],
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
    "verify_fields": (_fields_probe, {
        "revoked_keys_not_exact": [("    keys = _exact_items(revoked_key_ids)\n", "    keys = tuple(revoked_key_ids) if isinstance(revoked_key_ids, (list, tuple, set, frozenset)) else None\n")],
        "revoked_key_item_type_dropped": [("    if keys is None or any(type(k) is not str for k in keys):", "    if keys is None:")],
        "revoked_selections_not_exact": [("    sels = _exact_items(revoked_selections)\n", "    sels = tuple(revoked_selections) if isinstance(revoked_selections, (list, tuple, set, frozenset)) else None\n")],
        "revoked_selection_item_type_dropped": [("type(item) is tuple and len(item) == 2 and type(item[0]) is str and type(item[1]) is int", "len(item) == 2")],
        "floor_type_dropped": [("or type(floor) is not int or floor < 1", "or floor < 1")],
        "min_epochs_mapping_allowed": [("    if type(min_epochs) is dict:", "    if isinstance(min_epochs, dict):")],
        "min_epochs_key_type_dropped": [("if type(sid) is not str or type(floor)", "if type(floor)")],
        "version_type_dropped": [("    if type(version) is not int or not 1 <= version <= MAX_SNAPSHOT_VERSION:", "    if version < 1:")],
        "version_upper_bound_dropped": [("not 1 <= version <= MAX_SNAPSHOT_VERSION", "version < 1")],
        "version_upper_bound_off_by_one": [("not 1 <= version <= MAX_SNAPSHOT_VERSION:  # ingest", "not 1 <= version < MAX_SNAPSHOT_VERSION:  # ingest")],
        "version_bound_too_high": [("MAX_SNAPSHOT_VERSION = 2**53 - 1", "MAX_SNAPSHOT_VERSION = 2**60")],
        "version_ingest_untyped": [("return _IngestRefusal(\"ingest\", \"trust_snapshot_version\")", "return None")],
        "ingest_stage_dropped": [("(DETAIL_TRUST_SNAPSHOT_MALFORMED, None, ingest.stage, ingest.member))", "(DETAIL_TRUST_SNAPSHOT_MALFORMED, None))")],
        "v2_entry_not_v2_mode": [("now, record, key_admission, V2_CONTRACT, True,\n", "now, record, key_admission, V2_CONTRACT, False,\n")],
        "v2_entry_drops_policy": [("now, record, key_admission, V2_CONTRACT, True,\n", "now, record, None, V2_CONTRACT, True,\n")],
        "v2_domain_dropped": [("v2_sel.signing_input_v2(statement) if v2 else", "sel_mod.signing_input(statement) if v2 else")],
        "snapshot_id_type_dropped": [("    if type(snapshot_id) is not str or not c.valid_token(snapshot_id):", "    if not c.valid_token(snapshot_id):")],
        "valid_until_type_dropped": [("    if type(valid_until) is not str:\n        return None\n", "")],
        "issuers_container_loose": [("_exact_items(issuers_in) if type(issuers_in) in (list, tuple) else None", "_exact_items(issuers_in)")],
        "exact_snapshot_type_dropped2": [("    if type(trust) is not TrustSnapshot:\n        return None\n    snapshot_id,", "    snapshot_id,")],
        "selection_privatization_dropped": [("        selection, record, context = _private_selection(selection), _private_record(record), _private_context(context)", "        record, context = _private_record(record), _private_context(context)")],
        "record_privatization_dropped": [("        selection, record, context = _private_selection(selection), _private_record(record), _private_context(context)", "        selection, context = _private_selection(selection), _private_context(context)")],
        "context_privatization_dropped": [("        selection, record, context = _private_selection(selection), _private_record(record), _private_context(context)", "        selection, record = _private_selection(selection), _private_record(record)")],
        "now_privatization_dropped": [("        when = _private_now(now)", "        when = _aware(now)")],
        "selection_ok_loose": [("    if ok is not True:\n        return sel_mod.SelectionResult(False, code", "    if not ok:\n        return sel_mod.SelectionResult(False, code")],
        "json_copy_container_subclass": [("    if t is dict or t is list or t is tuple:", "    if isinstance(value, (dict, list, tuple)):")],
        "json_cycle_check_dropped": [("        if id(value) in state[\"seen\"]:\n            raise _NotSnapshottable()\n", "")],
        "json_seen_never_recorded": [("        state[\"seen\"].add(id(value))\n", "")],
        "json_node_budget_dropped": [("    if state[\"nodes\"] > MAX_JSON_NODES or depth > 32:", "    if depth > 32:")],
        "json_node_budget_off": [("state[\"nodes\"] > MAX_JSON_NODES", "state[\"nodes\"] > MAX_JSON_NODES * 100")],
        "json_depth_dropped": [("    if state[\"nodes\"] > MAX_JSON_NODES or depth > 32:", "    if state[\"nodes\"] > MAX_JSON_NODES:")],
        "half_built_trust_not_caught": [("        try:\n            return _private_trust(trust)", "        if True:\n            return _private_trust(trust)"), ("        except Exception:  # e.g. a half-built object: typed as a malformed snapshot, fail closed\n            return None", "")],
        "json_copy_str_subclass": [("    if t is str or t is bool or value is None:", "    if isinstance(value, str) or t is bool or value is None:")],
        "json_copy_int_subclass": [("    if t is int:\n        return int(value)", "    if isinstance(value, int):\n        return value")],
        "json_copy_float_allowed": [("    raise _NotSnapshottable()\n\n\ndef _exact_items", "    if t is float:\n        return value\n    raise _NotSnapshottable()\n\n\ndef _exact_items")],
        "json_key_type_dropped": [("                if type(k) is not str:\n                    raise _NotSnapshottable()\n", "")],
        "digest_type_dropped": [("        if type(digest) is not str or type(statement) is not dict", "        if type(statement) is not dict")],
        "record_ok_loose": [("        if getattr(record, \"ok\", False) is not True:\n            return refused", "        if not getattr(record, \"ok\", False):\n            return refused")],
        "record_digest_type_dropped": [("        if type(body) is not dict or type(digest) is not str:", "        if type(body) is not dict:")],
        "context_type_loose": [("    if type(context) is not ExpectedContext:\n        return None", "    if not isinstance(context, ExpectedContext):\n        return None")],
        "context_member_type_dropped": [("    if any(type(m) is not str for m in members):\n        return None\n    return ExpectedContext", "    return ExpectedContext")],
        "now_type_loose": [("    if type(now) is not datetime.datetime:\n        return None", "    if not isinstance(now, datetime.datetime):\n        return None")],
        "now_reads_offset_twice": [("        return (now.replace(tzinfo=None) - offset)", "        return (now.replace(tzinfo=None) - now.utcoffset())")],
        "ok_truthy_legacy": [("getattr(selection, \"ok\", False) is not False", "bool(getattr(selection, \"ok\", False))")],
    }),
    "decision": (_decision_probe, {
        "contract_version_not_forwarded": [("rec, key_admission, contract_version)", "rec, key_admission)")],
        "key_admission_not_forwarded": [("rec, key_admission, contract_version)", "rec, None, contract_version)")],
        "typed_detail_dropped": [("                     if type(dc) is str else None)", "                     if False else None)")],
        "typed_cause_dropped": [("typed = ((dc, cause if type(cause) is str else None) +", "typed = ((dc, None) +")],
    }),
}

CASES = [(mod, name) for mod, (_, ms) in MUTANTS.items() for name in ms]


@pytest.mark.parametrize("mod", list(MUTANTS))
def test_unmutated_source_passes_its_probe(mod):
    probe = MUTANTS[mod][0]
    probe(_load('verify' if mod == 'verify_fields' else mod))


@pytest.mark.parametrize("mod,name", CASES)
def test_mutant_is_killed(mod, name):
    probe, mutants = MUTANTS[mod]
    try:
        mutated = _load('verify' if mod == 'verify_fields' else mod, mutants[name])
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
