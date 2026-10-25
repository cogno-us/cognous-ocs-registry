"""Deterministic builder of the r08-v1 golden corpus INPUTS (EXT-S1-2). Test support only.

`build()` returns (records, selections, cases): records and selections map ids to raw text; cases are JSON-able dicts for
v1_runner.execute. Run by capture_v1_goldens.py ONCE against the unrefactored head; the stored file is then the source of
truth, so later edits of this builder never silently change what the replay checks.
"""
import copy
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r08_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402

F = c.F1A_FIELDS
CTX = ["consumer-test", "tenant-a", "inst-a", "domain-a", "op-test"]
GRANT = ["consumer-test", "tenant-a", "inst-a", "domain-a", "op-test"]
KEY = "public-key-test-1"
NOW = "2026-10-25T12:00:00Z"
CALLER = {"allowed_actions": ["read-file", "write-file"], "allowed_adapters": ["local-fs", "s3"],
          "allowed_units": ["unit-b", "unit-c"]}


def trust_spec(**over):
    base = {"snapshot_id": "snapshot-1", "version": 1, "valid_until": "2026-10-27T00:00:00Z",
            "issuers": [{"key_id": "key-test-1", "issuer_id": "issuer-test-1", "alg": "ed25519", "public_key": KEY,
                         "authority": [GRANT]}],
            "revoked_key_ids": [], "revoked_selections": [], "min_epochs": []}
    base.update(over)
    return base


def txt(obj):
    return json.dumps(obj, sort_keys=True)


def reseal(body):
    try:
        return s.seal_record(body)
    except Exception:  # structurally broken body: keep as-is (a shape code is reached before any digest check)
        return copy.deepcopy(body)


def build():
    records, selections, cases = {}, {}, []

    def add_record(rid, text):
        records[rid] = text
        return rid

    def add_sel(sid, text):
        selections[sid] = text
        return sid

    base = s.make_record()

    # ---------------- record corpus ----------------
    rec_variants = {"base": txt(base)}
    for i in range(8):  # payload variants incl. explicit deny-all combinations
        p = {f: (["x-" + f[8:]] if (i >> k) & 1 else []) for k, f in enumerate(F)}
        rec_variants["payload-%d" % i] = txt(reseal({**base, "payload": p}))
    for name, fam in [("fam-upper", c.FAMILY_F1A.upper()), ("fam-lead-space", " " + c.FAMILY_F1A),
                      ("fam-trail-space", c.FAMILY_F1A + " "), ("fam-trail-nl", c.FAMILY_F1A + "\n"),
                      ("fam-title", c.FAMILY_F1A.title()), ("fam-f1ab", "f1ab-local-execution-allowlist"),
                      ("fam-f4", "f4-control-plane-age-bounds"), ("fam-f5", "f5-action-class-age-bounds"),
                      ("fam-empty", ""), ("fam-num", 1), ("fam-null", None), ("fam-list", [c.FAMILY_F1A]),
                      ("fam-nbsp", c.FAMILY_F1A.replace("-", "‑", 1)), ("fam-zw", c.FAMILY_F1A + "​"),
                      ("fam-unknown", "f9-unknown")]:
        rec_variants[name] = txt(reseal({**base, "family": fam}))
    for k in ("contract_version", "kind"):
        for name, val in [("wrong", "other"), ("v2", "r08-v2"), ("num", 1), ("null", None), ("upper", "R08-V1")]:
            rec_variants["%s-%s" % (k, name)] = txt(reseal({**base, k: val}))
    for k in list(base):
        if k in ("payload_digest", "record_digest"):
            continue
        b = copy.deepcopy(base)
        del b[k]
        rec_variants["missing-" + k] = txt(reseal(b))
    for k in list(base):
        if k in ("payload_digest", "record_digest"):
            continue
        for tname, val in (("str", "s"), ("int", 3), ("list", []), ("null", None), ("bool", True)):
            b = copy.deepcopy(base)
            b[k] = val
            rec_variants["type-%s-%s" % (k, tname)] = txt(reseal(b))
    rec_variants["extra-top"] = txt(reseal({**base, "zzz": 1}))
    for sub in ("evaluator", "source", "payload", "provenance"):
        b = copy.deepcopy(base)
        b[sub]["zzz"] = "x"
        rec_variants["extra-" + sub] = txt(reseal(b))
        b = copy.deepcopy(base)
        b[sub] = {}
        rec_variants["emptyobj-" + sub] = txt(reseal(b))
    rec_variants["payload-missing-actions"] = txt(reseal({**base, "payload": {k: base["payload"][k] for k in F[1:]}}))
    rec_variants["payload-extra-amount"] = txt(reseal({**base, "payload": {**base["payload"], "max_amount": ["1"]}}))
    for name, val in [("unsorted", ["b", "a"]), ("dup", ["a", "a"]), ("wild", ["*"]), ("wild-embedded", ["a*"]),
                      ("empty-str", [""]), ("long", ["x" * 129]), ("ok-long", ["x" * 128]), ("ctrl", ["a\tb"]),
                      ("space", ["a b"]), ("nonstr", [1]), ("notlist", "a"), ("nfc", ["é"]),
                      ("nfd", ["é"]), ("nonbmp", ["\U0001f600"]), ("big", ["e%03d" % i for i in range(257)]),
                      ("max", ["e%03d" % i for i in range(256)]), ("null", None), ("nested", [["a"]])]:
        rec_variants["payload-" + name] = txt(reseal({**base, "payload": {**base["payload"], "allowed_actions": val}}))
    ev = base["evaluator"]
    for name, val in [("id", {**ev, "evaluator_id": "other"}), ("binding", {**ev, "binding": "other"}),
                      ("blob", {**ev, "source_blob_id": "xyz"}), ("sha", {**ev, "source_sha256": "sha256:AB"}),
                      ("type", {**ev, "evaluator_id": 3})]:
        rec_variants["evaluator-" + name] = txt(reseal({**base, "evaluator": val}))
    for name, val in [("id-upper", "Abc-record"), ("id-short", "ab"), ("id-long", "a" * 65), ("id-ok64", "a" * 64),
                      ("ver0", 0), ("ver-neg", -1), ("ver-max", 2**31 - 1), ("ver-over", 2**31),
                      ("ver-bool", True)]:
        key = "record_id" if name.startswith("id") else "record_version"
        rec_variants["rv-" + name] = txt(reseal({**base, key: val}))
    rec_variants["nonauth-false"] = txt(reseal({**base, "non_authorizing": False}))
    rec_variants["nonauth-str"] = txt(reseal({**base, "non_authorizing": "true"}))
    sup = {"record_id": "f1a-test-record", "record_version": 1, "record_digest": s.SHA}
    rec_variants["sup-ok"] = txt(reseal({**base, "record_version": 2, "supersedes": sup}))
    rec_variants["sup-same-version"] = txt(reseal({**base, "supersedes": sup}))
    rec_variants["sup-other-id"] = txt(reseal({**base, "record_version": 2, "supersedes": {**sup, "record_id": "other-id"}}))
    rec_variants["sup-bad-digest"] = txt(reseal({**base, "record_version": 2, "supersedes": {**sup, "record_digest": "x"}}))
    rec_variants["sup-extra"] = txt(reseal({**base, "record_version": 2, "supersedes": {**sup, "z": 1}}))
    rec_variants["sup-str"] = txt(reseal({**base, "record_version": 2, "supersedes": "x"}))
    for name, prov in [("ts-bad", {**base["provenance"], "authored_at": "2026-10-25"}),
                       ("ts-offset", {**base["provenance"], "authored_at": "2026-10-25T00:00:00+00:00"}),
                       ("ts-month13", {**base["provenance"], "authored_at": "2026-13-25T00:00:00Z"}),
                       ("by-star", {**base["provenance"], "authored_by": "a*b"}),
                       ("by-uni", {**base["provenance"], "authored_by": "andré"})]:
        rec_variants["prov-" + name] = txt(reseal({**base, "provenance": prov}))
    b = copy.deepcopy(base)
    b["payload_digest"] = "sha256:" + "0" * 64
    rec_variants["digest-payload-bad"] = txt(b)
    b = copy.deepcopy(base)
    b["record_digest"] = "sha256:" + "0" * 64
    rec_variants["digest-record-bad"] = txt(b)
    b = copy.deepcopy(base)
    b["payload"]["allowed_units"] = ["tampered"]
    rec_variants["digest-tampered-payload"] = txt(b)
    rec_variants["digest-upper"] = txt({**base, "record_digest": base["record_digest"].upper()})
    rec_variants["compact-json"] = json.dumps(base, separators=(",", ":"))
    rec_variants["pretty-json"] = json.dumps(base, indent=2)
    rec_variants["unicode-escaped"] = json.dumps(reseal({**base, "provenance": {**base["provenance"], "authored_by": "café"}}))
    # text-level
    raw_text = {
        "text-empty": "", "text-ws": "   ", "text-null-json": "null", "text-list": "[]", "text-str": '"x"', "text-int": "1",
        "text-malformed": "{", "text-trailing": txt(base) + "x", "text-dupkey": '{"kind":"record","kind":"record"}',
        "text-float": '{"a":1.5}', "text-exp": '{"a":1e3}', "text-nan": '{"a":NaN}', "text-inf": '{"a":Infinity}',
        "text-negzero": '{"a":-0}', "text-deep": "[" * 20 + "]" * 20, "text-deeper": {"wrap": ["[", "]", 100000]},
        "text-depth8": '{"a":{"a":{"a":{"a":{"a":{"a":{"a":1}}}}}}}', "text-depth9": '{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":1}}}}}}}}',
        "text-large": {"pad": 70000, "text": txt(base)}, "text-surrogate": '{"a":"\\ud800"}', "text-bom": "﻿" + txt(base),
        "text-bigint": '{"a":' + "9" * 40 + "}",
    }
    rec_variants.update(raw_text)
    for rid, t in rec_variants.items():
        add_record(rid, t)
        cases.append({"kind": "record", "record": rid})
    for name, val in [("none", None), ("bytes", b"x"), ("int", 1), ("list", []), ("dict", {})]:
        cases.append({"kind": "record", "text": val if not isinstance(val, bytes) else None, "_note": "non-text " + name})

    # ---------------- selection corpus ----------------
    stmt0 = s.make_statement(base)

    def mk(rec=None, **over):
        b = copy.deepcopy(s.make_statement(rec or base))
        b.update(over)
        return b

    sel_variants = {"base": txt(s.make_envelope(stmt0)), "optional": txt(s.make_envelope(mk(base, participation="optional")))}

    def env_for(stmt, **kw):
        return txt(s.make_envelope(stmt, **kw))

    for name, fam in [("fam-upper", c.FAMILY_F1A.upper()), ("fam-space", c.FAMILY_F1A + " "), ("fam-lead", " " + c.FAMILY_F1A),
                      ("fam-f1ab", "f1ab-local-execution-allowlist"), ("fam-f4", "f4-control-plane-age-bounds"),
                      ("fam-empty", ""), ("fam-null", None), ("fam-num", 7), ("fam-unknown", "f9-x")]:
        sel_variants[name] = env_for(mk(base, family=fam))
    for k in list(stmt0):
        b = copy.deepcopy(stmt0)
        del b[k]
        sel_variants["missing-" + k] = env_for(b)
        for tname, val in (("str", "s"), ("int", 3), ("list", []), ("null", None), ("bool", True), ("dict", {})):
            b = copy.deepcopy(stmt0)
            b[k] = val
            sel_variants["type-%s-%s" % (k, tname)] = env_for(b)
    b = copy.deepcopy(stmt0)
    b["zzz"] = 1
    sel_variants["extra-stmt"] = env_for(b)
    for sub in ("scope", "record", "evaluator", "effective"):
        b = copy.deepcopy(stmt0)
        b[sub]["zzz"] = "x"
        sel_variants["extra-" + sub] = env_for(b)
    for name, over in [("epoch0", {"epoch": 0}), ("epoch-neg", {"epoch": -1}), ("epoch-max", {"epoch": 2**31 - 1}),
                       ("epoch-over", {"epoch": 2**31}), ("epoch-bool", {"epoch": True}), ("epoch2", {"epoch": 2}),
                       ("epoch3", {"epoch": 3}),
                       ("part-bad", {"participation": "Required"}), ("part-null", {"participation": None}),
                       ("id-upper", {"selection_id": "Sel-A"}), ("id-short", {"selection_id": "ab"}),
                       ("op-other", {"operation": "op-other"}), ("consumer-other", {"consumer_id": "consumer-x"}),
                       ("scope-tenant", {"scope": {**stmt0["scope"], "tenant": "tenant-z"}}),
                       ("scope-inst", {"scope": {**stmt0["scope"], "institution": "inst-z"}}),
                       ("scope-domain", {"scope": {**stmt0["scope"], "authority_domain": "domain-z"}}),
                       ("scope-star", {"scope": {**stmt0["scope"], "tenant": "*"}}),
                       ("scope-uni", {"scope": {**stmt0["scope"], "tenant": "ténant"}}),
                       ("scope-ctrl", {"scope": {**stmt0["scope"], "tenant": "a\u0000b"}}),
                       ("scope-space", {"scope": {**stmt0["scope"], "tenant": "a b"}}),
                       ("eff-inverted", {"effective": {"valid_from": "2026-10-26T00:00:00Z", "valid_until": "2026-10-25T00:00:00Z"}}),
                       ("eff-equal", {"effective": {"valid_from": "2026-10-25T00:00:00Z", "valid_until": "2026-10-25T00:00:00Z"}}),
                       ("eff-future", {"effective": {"valid_from": "2026-10-26T00:00:00Z", "valid_until": "2026-10-27T00:00:00Z"}}),
                       ("eff-past", {"effective": {"valid_from": "2026-10-23T00:00:00Z", "valid_until": "2026-10-24T00:00:00Z"}}),
                       ("eff-ends-now", {"effective": {"valid_from": "2026-10-25T00:00:00Z", "valid_until": NOW}}),
                       ("eff-starts-now", {"effective": {"valid_from": NOW, "valid_until": "2026-10-26T00:00:00Z"}}),
                       ("eff-badts", {"effective": {"valid_from": "x", "valid_until": "2026-10-26T00:00:00Z"}}),
                       ("issued-bad", {"issued_at": "yesterday"}),
                       ("ev-other", {"evaluator": {**s.EVALUATOR, "evaluator_id": "other"}}),
                       ("ev-blob", {"evaluator": {**s.EVALUATOR, "source_blob_id": "0" * 40}}),
                       ("rev-bad", {"revocation_ref": "Bad Ref"}), ("sel-ref-bad", {"selector_ref": ""}),
                       ("pin-id", {"record": {**stmt0["record"], "record_id": "other-record"}}),
                       ("pin-ver", {"record": {**stmt0["record"], "record_version": 2}}),
                       ("pin-digest", {"record": {**stmt0["record"], "record_digest": "sha256:" + "1" * 64}}),
                       ("pin-digest-bad", {"record": {**stmt0["record"], "record_digest": "nope"}}),
                       ("kind-other", {"kind": "revocation"})]:
        sel_variants["s-" + name] = env_for(mk(**over))
    sup_ok = {"selection_id": "sel-test-1", "epoch": 1, "statement_digest": s.SHA, "decision_ref": "decision-test-1"}
    for name, over in [("sup-ok", {"epoch": 2, "supersedes": sup_ok}),
                       ("sup-same-epoch", {"epoch": 1, "supersedes": sup_ok}),
                       ("sup-higher", {"epoch": 2, "supersedes": {**sup_ok, "epoch": 3}}),
                       ("sup-other-id", {"epoch": 2, "supersedes": {**sup_ok, "selection_id": "sel-other"}}),
                       ("sup-bad-digest", {"epoch": 2, "supersedes": {**sup_ok, "statement_digest": "x"}}),
                       ("sup-bad-ref", {"epoch": 2, "supersedes": {**sup_ok, "decision_ref": "Bad Ref"}}),
                       ("sup-extra", {"epoch": 2, "supersedes": {**sup_ok, "z": 1}}),
                       ("sup-str", {"epoch": 2, "supersedes": "x"})]:
        sel_variants["s-" + name] = env_for(mk(**over))
    # chain: epoch1 (base) <- epoch2 supersedes epoch1 exactly
    from registry_successor.common import digest as dg
    s1 = mk(base)
    s2 = mk(base, epoch=2, supersedes={"selection_id": "sel-test-1", "epoch": 1, "statement_digest": dg(s1),
                                                      "decision_ref": "decision-test-1"})
    s3 = mk(base, epoch=3, supersedes={"selection_id": "sel-test-1", "epoch": 2, "statement_digest": dg(s2),
                                                      "decision_ref": "decision-test-1"})
    s2_nolink = mk(base, epoch=2)
    s_other_id = mk(base, selection_id="sel-test-2", epoch=1)
    sel_variants["chain-1"], sel_variants["chain-2"], sel_variants["chain-3"] = env_for(s1), env_for(s2), env_for(s3)
    sel_variants["chain-2-nolink"], sel_variants["other-id"] = env_for(s2_nolink), env_for(s_other_id)
    sel_variants["chain-1-optional"] = env_for(mk(base, participation="optional"))
    # envelope-level
    e = s.make_envelope(stmt0)
    for k in list(e):
        b = copy.deepcopy(e)
        del b[k]
        sel_variants["env-missing-" + k] = txt(b)
        for tname, val in (("str", "s"), ("int", 3), ("null", None), ("list", []), ("dict", {})):
            b = copy.deepcopy(e)
            b[k] = val
            sel_variants["env-type-%s-%s" % (k, tname)] = txt(b)
    sel_variants["env-extra"] = txt({**e, "zzz": 1})
    sel_variants["env-cv-v2"] = txt({**e, "contract_version": "r08-v2"})
    sel_variants["env-kind-other"] = txt({**e, "kind": "record"})
    sel_variants["env-digest-bad"] = txt({**e, "statement_digest": "sha256:" + "0" * 64})
    sel_variants["env-digest-upper"] = txt({**e, "statement_digest": e["statement_digest"].upper()})
    sel_variants["unsigned"] = env_for(stmt0, signed=False)
    sel_variants["sig-wrong-key"] = env_for(stmt0, key_id="key-test-9")
    sel_variants["sig-wrong-pub"] = env_for(stmt0, public_key=b"other-public-key")
    sel_variants["sig-alg-other"] = txt({**e, "signatures": [{**e["signatures"][0], "alg": "rsa"}]})
    sel_variants["sig-garbage"] = txt({**e, "signatures": [{**e["signatures"][0], "signature": "!!!notbase64"}]})
    sel_variants["sig-empty-str"] = txt({**e, "signatures": [{**e["signatures"][0], "signature": ""}]})
    sel_variants["sig-long"] = txt({**e, "signatures": [{**e["signatures"][0], "signature": "A" * 1025}]})
    sel_variants["sig-extra"] = txt({**e, "signatures": [{**e["signatures"][0], "z": "1"}]})
    sel_variants["sig-nine"] = txt({**e, "signatures": [e["signatures"][0]] * 9})
    sel_variants["sig-eight"] = txt({**e, "signatures": [e["signatures"][0]] * 8})
    sel_variants["sig-bad-then-good"] = txt({**e, "signatures": [{**e["signatures"][0], "key_id": "key-test-9"}, e["signatures"][0]]})
    sel_variants["sig-nonlist"] = txt({**e, "signatures": "x"})
    sel_variants["v1-domain-misuse"] = txt({**e, "signatures": [{**e["signatures"][0], "signature": s.fake_signature(
        KEY.encode(), b"ocs-reg/r08-v2/selection\n" + c.canonical_bytes(stmt0))}]})
    sel_variants["text-malformed"] = "{"
    sel_variants["text-empty"] = ""
    sel_variants["text-dupkey"] = '{"kind":"a","kind":"b"}'
    sel_variants["text-float"] = '{"a":1.5}'
    sel_variants["text-large"] = {"pad": 70000, "text": txt(e)}
    sel_variants["pretty"] = json.dumps(e, indent=2)
    for sid, t in sel_variants.items():
        add_sel(sid, t)
        cases.append({"kind": "selection", "selection": sid})
    for name, val in [("none", None), ("int", 1), ("list", [])]:
        cases.append({"kind": "selection", "text": val, "_note": "non-text " + name})

    # ---------------- verify grid (selection x record binding) ----------------
    def vcase(sel, rec, ctx=CTX, trust=None, verifier="fake", now=NOW):
        cases.append({"kind": "verify", "selection": sel, "record": rec, "context": ctx,
                      "trust": trust_spec() if trust is None else (None if trust == "none" else trust),
                      "verifier": verifier, "now": now})

    for sid in sorted(sel_variants):
        vcase(sid, "base")
        vcase(sid, None)
    for rid in sorted(rec_variants):
        vcase("base", rid)
    vcase("base", "base", ctx=None)
    vcase("base", "base", ctx="junk")
    for i in range(5):
        ctx = list(CTX)
        ctx[i] = ctx[i] + "-x"
        vcase("base", "base", ctx=ctx)
    for name, tr in [("none", "none"), ("junk", "junk"), ("expired", trust_spec(valid_until="2026-10-25T12:00:00Z")),
                     ("expired-before", trust_spec(valid_until="2026-10-25T11:59:59Z")),
                     ("ok-1s", trust_spec(valid_until="2026-10-25T12:00:01Z")),
                     ("badts", trust_spec(valid_until="soon")), ("ver0", trust_spec(version=0)),
                     ("verbool", trust_spec(version=True)),
                     ("revkey", trust_spec(revoked_key_ids=["key-test-1"])),
                     ("revsel", trust_spec(revoked_selections=[["sel-test-1", 1]])),
                     ("revsel-other-epoch", trust_spec(revoked_selections=[["sel-test-1", 2]])),
                     ("floor-above", trust_spec(min_epochs=[["sel-test-1", 2]])),
                     ("floor-equal", trust_spec(min_epochs=[["sel-test-1", 1]])),
                     ("floor-other", trust_spec(min_epochs=[["sel-other", 9]])),
                     ("floor-zero", trust_spec(min_epochs=[["sel-test-1", 0]])),
                     ("floor-dup", trust_spec(min_epochs=[["sel-test-1", 1], ["sel-test-1", 2]])),
                     ("no-issuers", trust_spec(issuers=[])),
                     ("no-grants", trust_spec(issuers=[{"key_id": "key-test-1", "issuer_id": "issuer-test-1", "alg": "ed25519", "public_key": KEY, "authority": []}])),
                     ("grant-other", trust_spec(issuers=[{"key_id": "key-test-1", "issuer_id": "issuer-test-1", "alg": "ed25519", "public_key": KEY, "authority": [["consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"]]}])),
                     ("alg-other", trust_spec(issuers=[{"key_id": "key-test-1", "issuer_id": "issuer-test-1", "alg": "rsa", "public_key": KEY, "authority": [GRANT]}])),
                     ("wrong-pub", trust_spec(issuers=[{"key_id": "key-test-1", "issuer_id": "issuer-test-1", "alg": "ed25519", "public_key": "zzz", "authority": [GRANT]}])),
                     ("dup-key", trust_spec(issuers=[trust_spec()["issuers"][0]] * 2)),
                     ("empty-pub", trust_spec(issuers=[{"key_id": "key-test-1", "issuer_id": "issuer-test-1", "alg": "ed25519", "public_key": "", "authority": [GRANT]}]))]:
        vcase("base", "base", trust=tr)
    for name in ("none", "reject", "raises", "truthy", "junk"):
        vcase("base", "base", verifier=None if name == "none" else name)
    for now in (None, "naive", "plus1", "string", "2026-10-24T23:59:59Z", "2026-10-25T00:00:00Z",
                "2026-10-25T23:59:59Z", "2026-10-26T00:00:00Z", "2026-10-27T00:00:00Z", "2026-10-28T00:00:00Z"):
        vcase("base", "base", now=now)

    # ---------------- decide grid ----------------
    callers = {
        "plain": {"kind": "json", "value": CALLER},
        "set": {"kind": "set", "value": CALLER},
        "tuple": {"kind": "tuple", "value": CALLER},
        "disjoint": {"kind": "json", "value": {k: ["zz-none"] for k in F}},
        "empty-dim": {"kind": "json", "value": {**CALLER, "allowed_units": []}},
        "all-empty": {"kind": "json", "value": {k: [] for k in F}},
        "superset": {"kind": "json", "value": {"allowed_actions": ["read-file", "write-file"], "allowed_adapters": ["local-fs", "s3"], "allowed_units": ["unit-a", "unit-b", "unit-c"]}},
        "missing-field": {"kind": "json", "value": {k: CALLER[k] for k in F[:2]}},
        "extra-field": {"kind": "json", "value": {**CALLER, "max_amount": ["1"]}},
        "str-field": {"kind": "json", "value": {**CALLER, "allowed_units": "unit-a"}},
        "bad-token": {"kind": "json", "value": {**CALLER, "allowed_units": ["a*"]}},
        "nonstr-token": {"kind": "json", "value": {**CALLER, "allowed_units": [1]}},
        "unsorted-dup": {"kind": "json", "value": {**CALLER, "allowed_units": ["unit-c", "unit-b", "unit-b"]}},
        "wildcard-star": {"kind": "json", "value": {**CALLER, "allowed_actions": ["*"]}},
        "none": None, "str": {"kind": "json", "value": "x"}, "list": {"kind": "json", "value": []},
    }

    def dcase(part, caller, rec, sel, **kw):
        cases.append({"kind": "decide", "participation": part, "caller": callers[caller] if isinstance(caller, str) else caller,
                      "record": rec, "selection": sel, "context": kw.get("ctx", CTX),
                      "trust": trust_spec() if kw.get("trust") is None else (None if kw["trust"] == "none" else kw["trust"]),
                      "verifier": kw.get("verifier", "fake"), "now": kw.get("now", NOW)})

    for part in ("required", "optional", "Required", "", None, 1, "both"):
        for cname in callers:
            dcase(part, cname, "base", "base")
            dcase(part, cname, "base", "optional")
    for part in ("required", "optional"):
        for sid in sorted(sel_variants):
            dcase(part, "plain", "base", sid)
        for rid in sorted(rec_variants):
            dcase(part, "plain", rid, "base")
            dcase(part, "plain", rid, "optional")
        dcase(part, "plain", None, "base")
        dcase(part, "plain", "base", None)
        dcase(part, "plain", None, None)
        cases.append({"kind": "decide", "participation": part, "caller": callers["plain"], "record": None,
                      "record_text": 5, "selection": "base", "context": CTX, "trust": trust_spec(), "verifier": "fake", "now": NOW})
        cases.append({"kind": "decide", "participation": part, "caller": callers["plain"], "record": "base",
                      "selection": None, "selection_text": 5, "context": CTX, "trust": trust_spec(), "verifier": "fake", "now": NOW})
        for ctxname, ctx in (("none", None), ("junk", "junk"), ("wrong-op", CTX[:4] + ["op-x"])):
            dcase(part, "plain", "base", "base", ctx=ctx)
        for tr in ("none", "junk", trust_spec(valid_until="2026-10-25T12:00:00Z"), trust_spec(revoked_key_ids=["key-test-1"]),
                   trust_spec(revoked_selections=[["sel-test-1", 1]]), trust_spec(min_epochs=[["sel-test-1", 2]]),
                   trust_spec(issuers=[])):
            dcase(part, "plain", "base", "base", trust=tr)
            dcase(part, "plain", "base", "optional", trust=tr)
        for vf in (None, "reject", "raises", "truthy", "junk"):
            dcase(part, "plain", "base", "base", verifier=vf)
        for now in (None, "naive", "string", "2026-10-26T00:00:00Z", "2026-10-24T00:00:00Z"):
            dcase(part, "plain", "base", "base", now=now)
    # pairing mismatches: selection pins base record; supply other valid records
    for rid in ("payload-0", "payload-1", "payload-7", "rv-ver-max", "sup-ok", "compact-json", "pretty-json"):
        for part in ("required", "optional"):
            dcase(part, "plain", rid, "base")
            dcase(part, "plain", rid, "optional")
    # alt: valid selections pinning alternative records
    for i in (0, 1, 3, 7):
        rb = json.loads(rec_variants["payload-%d" % i])
        st = mk(rb)
        add_sel("pin-payload-%d" % i, env_for(st))
        add_sel("pin-payload-%d-opt" % i, env_for(mk(rb, participation="optional")))
        for part in ("required", "optional"):
            for cname in ("plain", "superset", "disjoint", "set", "tuple", "empty-dim"):
                dcase(part, cname, "payload-%d" % i, "pin-payload-%d" % i)
                dcase(part, cname, "payload-%d" % i, "pin-payload-%d-opt" % i)

    # ---------------- compose grid ----------------
    for rid in sorted(rec_variants):
        if rid.startswith("text-"):
            continue
        for cname in ("plain", "set", "tuple", "disjoint", "empty-dim", "all-empty", "superset", "missing-field", "none", "bad-token"):
            cases.append({"kind": "compose", "record": rid, "caller": callers[cname]})
    for op in ("union", "Intersection", "", None, 1):
        cases.append({"kind": "compose", "record": "base", "caller": callers["plain"], "operator": op})
        cases.append({"kind": "compose", "record": "payload-0", "caller": callers["plain"], "operator": op})
    # exhaustive 3x3 per-dimension grid
    grid_vals = [[], ["a-1"], ["a-1", "a-2"]]
    n = 0
    for pv in itertools.product(range(3), repeat=3):
        for cv in itertools.product(range(3), repeat=3):
            rid = "grid-r-%d%d%d" % pv
            if rid not in records:
                p = {f: grid_vals[pv[k]] for k, f in enumerate(F)}
                add_record(rid, txt(reseal({**base, "payload": p})))
            cases.append({"kind": "compose", "record": rid,
                          "caller": {"kind": "json", "value": {f: grid_vals[cv[k]] for k, f in enumerate(F)}}})
            n += 1

    # compose on hand-built record results (reaches composition_* codes the text path cannot)
    for shape in ("ok", "not-ok", "none", "bare"):
        cases.append({"kind": "compose_raw", "record": "base", "shape": shape, "mutate": [], "caller": callers["plain"]})
    for name, mut in [("fam-x", [[["family"], "f1ab-local-execution-allowlist"]]), ("fam-upper", [[["family"], c.FAMILY_F1A.upper()]]),
                      ("fam-space", [[["family"], c.FAMILY_F1A + " "]]), ("fam-none", [[["family"], None]]),
                      ("fam-del", [[["family"], "__delete__"]]),
                      ("payload-del", [[["payload"], "__delete__"]]), ("payload-str", [[["payload"], "x"]]),
                      ("payload-extra", [[["payload", "max_amount"], ["1"]]]), ("payload-field-del", [[["payload", "allowed_units"], "__delete__"]]),
                      ("payload-unsorted", [[["payload", "allowed_units"], ["b", "a"]]]), ("payload-wild", [[["payload", "allowed_units"], ["*"]]]),
                      ("payload-nonlist", [[["payload", "allowed_units"], "unit-a"]]), ("payload-none", [[["payload", "allowed_units"], None]])]:
        for cname in ("plain", "none"):
            cases.append({"kind": "compose_raw", "record": "base", "shape": "ok", "mutate": mut, "caller": callers[cname]})
    cases.append({"kind": "resolve_authoritative"})
    cases.append({"kind": "resolve_authoritative", "args": [1, 2], "kwargs": {"a": 3}})

    # ---------------- resolve ----------------
    r_cases = [["chain-1"], ["chain-2"], ["chain-1", "chain-2"], ["chain-1", "chain-2", "chain-3"], ["chain-3", "chain-1"],
               ["chain-1", "chain-2-nolink"], ["base", "other-id"], ["base", "base"], ["chain-1", "chain-3"],
               ["unsigned", "base"], ["env-digest-bad", "base"], [], ["s-eff-past"], ["s-eff-future", "base"],
               ["chain-1", "chain-2", "other-id"], ["optional", "base"], ["s-scope-tenant"], ["s-op-other", "base"]]
    for sels in r_cases:
        for now in (NOW, None, "naive", "2026-10-26T00:00:00Z"):
            cases.append({"kind": "resolve", "selections": sels, "context": CTX, "now": now})
    cases.append({"kind": "resolve", "selections": ["base"], "context": None, "now": NOW})
    cases.append({"kind": "resolve", "selections": ["base"], "context": "junk", "now": NOW})
    return records, selections, cases
