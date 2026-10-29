"""Differential proof that the parameterised engine under `V6_COMPAT` is the frozen `r08-v6` contract (BUILDER_TESTED; not independently qualified).

For every input of a deterministic corpus (the pinned `tests/vectors/r08v6` vectors, the real signed v6 vectors, one-at-a-time hostile variations of
every argument of the decision path, and a seeded random sample of combinations) the engine must return EXACTLY the frozen v6 entry point's value:
equal decisions (same class, same fields), equal verification reports (layers, codes, details), equal parse and validation results, equal digests and
equal identity refusals. This is the compatibility adapter: it changes no frozen semantics. Cross-version documents (v1..v7) refuse
`contract_unsupported` or `family_unsupported` at every entry point with no fallback or upgrade.
"""
import copy
import datetime
import itertools
import json
import random
from pathlib import Path

import pytest

import r08_support as r
import r08v3_support as t3
import r08v4_support as t4
import r08v5_support as t5
import r08v6_support as t6
import r08v7_support as t7
import s01_support as s
from registry_successor import common as c
from registry_successor import v5_decision, v6_class_revocation_assurance as ra, v6_decision, v6_families, v6_policy_identity as v6pi
from registry_successor import v6_record, v6_selection, v6_terminal_revocation as trv, v6_verify, v7_decision
from registry_successor import verify as v
from registry_successor.engine import decide as decide_e
from registry_successor.engine import identity as identity_e
from registry_successor.engine import profile as profile_e
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e
from registry_successor.engine import selection as selection_e
from registry_successor.engine import verify as verify_e

pytestmark = pytest.mark.skipif(not t6.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

P6 = profiles.V6_COMPAT
RA, TR = t6.FAMILY, t6.FAMILY_TR
VEC = Path(__file__).parent / "vectors" / "r08v6"
COUNTS = {"decision": 0, "report": 0, "applied": 0}


def same(a, b):
    assert type(a) is type(b), (type(a), type(b))
    assert a == b, (a, b)


def frozen_decide(*args):
    return v6_decision.verify_and_decide_v6(*args)


def engine_decide(*args):
    return decide_e.verify_and_decide(P6, *args)


# ------------------------------------------------------------------ corpus
def mutate_statement(stmt, how):
    st = copy.deepcopy(stmt)
    if how == "kind":
        st["kind"] = "other"
    elif how == "family":
        st["family"] = "nope"
    elif how == "epoch0":
        st["epoch"] = 0
    elif how == "epoch-str":
        st["epoch"] = "1"
    elif how == "participation":
        st["participation"] = "sometimes"
    elif how == "extra":
        st["extra"] = 1
    elif how == "missing":
        del st["operation"]
    elif how == "scope":
        st["scope"] = dict(st["scope"], tenant="")
    elif how == "interval":
        st["effective"] = dict(st["effective"], valid_from=st["effective"]["valid_until"])
    elif how == "issued":
        st["issued_at"] = "yesterday"
    elif how == "evaluator":
        st["evaluator"] = dict(st["evaluator"], binding="other")
    elif how == "blob":
        st["evaluator"] = dict(st["evaluator"], source_blob_id="xyz")
    elif how == "pin-version":
        st["record"] = dict(st["record"], record_version=0)
    elif how == "pin-digest":
        st["record"] = dict(st["record"], record_digest="sha256:" + "0" * 64)
    elif how == "disposition":
        st["disposition"] = "erase"
    elif how == "disposition-type":
        st["disposition"] = 1
    elif how == "supersedes":
        st["supersedes"] = {"selection_id": "x"}
    elif how == "revocation-ref":
        st["revocation_ref"] = "bad ref"
    elif how == "withdraw-with-record":
        st["disposition"] = "withdraw"
    return st


STATEMENT_MUTATIONS = ["kind", "family", "epoch0", "epoch-str", "participation", "extra", "missing", "scope", "interval", "issued", "evaluator", "blob",
                       "pin-version", "pin-digest", "disposition", "disposition-type", "supersedes", "revocation-ref", "withdraw-with-record"]


def selection_variants(family):
    rec = t6.record(family=family)
    stmt = t6.statement(rec)
    out = {"valid": t6.selection_text(rec)}
    for ver in ("r08-v1", "r08-v2", "r08-v3", "r08-v4", "r08-v5", "r08-v7", "R08-V6", "", "r08-v6 "):
        out["contract:" + ver] = t6.selection_text(rec, contract=ver)
    for name, dom in (("v5", t6.V5_DOMAIN), ("v7", t7.V7_DOMAIN), ("v2", s.V2_DOMAIN), ("v1", s.V1_DOMAIN), ("empty", b"")):
        out["domain:" + name] = t6.selection_text(rec, domain=dom)
    good_sig = t6.sign(stmt)
    for i, noncanon in enumerate((good_sig + "\n", good_sig.replace("=", ""), good_sig[:-4], "!" + good_sig[1:], "", good_sig.lower(), "=" * 88)):
        out["noncanonical-sig:%d" % i] = r.dumps(s.envelope(stmt, domain=t6.V6_DOMAIN, contract="r08-v6", signature=noncanon, pub=t6.PK))
    out["wrong-key"] = t6.selection_text(rec, sk=t6.OTHER_SK)
    out["unsigned"] = r.dumps(s.envelope(stmt, domain=t6.V6_DOMAIN, contract="r08-v6", signed=False))
    out["unknown-key-id"] = r.dumps(s.envelope(stmt, domain=t6.V6_DOMAIN, contract="r08-v6", key_id="key-unknown", signature=t6.sign(stmt), pub=t6.PK))
    out["bad-digest"] = r.dumps(dict(t6.envelope(stmt), statement_digest="sha256:" + "0" * 64))
    out["bad-digest-form"] = r.dumps(dict(t6.envelope(stmt), statement_digest="nope"))
    out["no-alg"] = r.dumps(dict(t6.envelope(stmt), signatures=[{"alg": "rsa", "key_id": s.KEY_ID, "signature": "AAAA"}]))
    wd = s.withdraw_statement(stmt)
    out["withdraw"] = r.dumps(t6.envelope(wd))
    out["withdraw-wrong-key"] = r.dumps(t6.envelope(wd, sk=t6.OTHER_SK))
    out["optional"] = t6.selection_text(rec, participation="optional")
    for how in STATEMENT_MUTATIONS:
        out["stmt:" + how] = r.dumps(t6.envelope(mutate_statement(stmt, how)))
    for name, text in (("empty-obj", "{}"), ("empty", ""), ("not-json", "not json"), ("array", "[]"), ("null", "null"), ("number", "5"),
                       ("dup", '{"a":1,"a":2}'), ("float", '{"epoch": 1.5}'), ("deep", "[" * 50 + "]" * 50), ("big-int", '{"epoch": ' + "9" * 40 + "}")):
        out["text:" + name] = text
    out["none"] = None
    out["bytes"] = b"{}"
    out["int"] = 7
    return out


def record_variants(family):
    rec = t6.record(family=family)
    out = {"valid": r.dumps(rec)}
    for ver in ("r08-v1", "r08-v2", "r08-v3", "r08-v4", "r08-v5", "r08-v7", "R08-V6", "", None, 6):
        out["contract:%s" % (ver,)] = r.dumps(t6.record(family=family, contract_version=ver))
    fld = t6.FIELD if family == RA else t6.TR_FIELD
    pls = ([{}, {fld: {}}, {fld: {"class-a": "x"}}, {fld: {"class-a": 1}}, {fld: {"class-a": True}}, {fld: {"b": "required", "a": "required"}},
            {fld: {"*": "required"}}, {fld: {"class-a": "required"}, "x": 1}, {"terminal_revocation": "on"}, {"class_irreversible": {"class-a": "irreversible"}},
            {fld: []}, {fld: "required"}] if family == RA else
           [{}, {fld: "x"}, {fld: True}, {fld: 1}, {fld: None}, {fld: {"class-a": "on"}}, {fld: "on", "x": 1}, {fld: "ON"}, {"class_requires_revocation_assurance": {"class-a": "required"}}])
    for i, pl in enumerate(pls):
        out["payload:%d" % i] = r.dumps(t6.record(pl, family=family))
    tampered = copy.deepcopy(t6.record(family=family))
    key = next(iter(tampered["payload"]))
    tampered["payload"][key] = {"class-a": "not_required"} if family == RA else "off"
    out["tampered"] = r.dumps(tampered)
    out["resealed"] = r.dumps(r.seal_record(tampered))
    for i, kw in enumerate(({"kind": "selection"}, {"non_authorizing": False}, {"record_version": 0}, {"record_id": "bad id"}, {"family": "f5-action-class-age-bounds"},
                            {"family": "f5-action-class-unreadable-policy"}, {"family": "f5-action-class-irreversibility-policy"}, {"family": 5})):
        out["top:%d" % i] = r.dumps(r.seal_record(dict(rec, **kw)))
    for name, text in (("empty-obj", "{}"), ("not-json", "not json"), ("array", "[]"), ("null", "null"), ("dup", '{"a":1,"a":2}')):
        out["text:" + name] = text
    out["none"] = None
    out["bytes"] = b"{}"
    return out


def trusts():
    return {"ok": s.trust(pub=t6.PK), "revoked-sel": s.trust(pub=t6.PK, revoked_selections=frozenset({("sel-test-1", 1)})),
            "other-sel-revoked": s.trust(pub=t6.PK, revoked_selections=frozenset({("sel-test-1", 2)})), "floor2": s.trust(pub=t6.PK, min_epochs=(("sel-test-1", 2),)),
            "floor1": s.trust(pub=t6.PK, min_epochs=(("sel-test-1", 1),)), "revoked-key": s.trust(pub=t6.PK, revoked_key_ids=frozenset({s.KEY_ID})),
            "expired": s.trust(pub=t6.PK, valid_until="2026-10-25T06:00:00Z"), "edge": s.trust(pub=t6.PK, valid_until="2026-10-25T12:00:00Z"),
            "bad-pub": s.trust(pub=bytes.fromhex("01" + "00" * 31)), "other-pub": s.trust(pub=t6.OTHER_PK), "none": None, "junk": "snapshot", "int": 3,
            "no-grant": v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t6.PK, ()),)),
            "grant-other-op": v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(
                s.KEY_ID, "issuer-test-1", "ed25519", t6.PK, (v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"),)),))}


def contexts():
    E = c.ExpectedContext
    return {"ok": s.CTX, "consumer": E("other", "tenant-a", "inst-a", "domain-a", "op-test"), "tenant": E("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"),
            "inst": E("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"), "domain": E("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"),
            "op": E("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "none": None, "junk": ("consumer-test",)}


def nows():
    utc = datetime.timezone.utc
    return {"ok": r.NOW, "start": datetime.datetime(2026, 10, 25, 0, 0, 0, tzinfo=utc), "before": datetime.datetime(2026, 10, 24, 23, 59, 59, tzinfo=utc),
            "end": datetime.datetime(2026, 10, 26, 0, 0, 0, tzinfo=utc), "late": r.NOW + datetime.timedelta(days=3), "none": None,
            "naive": datetime.datetime(2026, 10, 25, 12, 0, 0), "str": "2026-10-25T12:00:00Z", "int": 5}


def callers(family):
    good = t6.caller(family)
    junk = [None, {}, 5, "x", {"zzz": 1}, {"class-a": "required"}]
    if family == RA:
        extra = [{t6.FIELD: {}}, {t6.FIELD: {"class-a": "x"}}, {t6.FIELD: {"class-a": True}}, {t6.FIELD: {"class-a": "required"}},
                 {t6.FIELD: {"class-a": "not_required", "class-b": "required"}}, {t6.FIELD: {"class-a": "required", "class-b": "required", "class-c": "required"}},
                 {t6.TR_FIELD: "on"}, {t6.FIELD: {"class-a": "required"}, "x": 1}]
    else:
        extra = [{t6.TR_FIELD: "on"}, {t6.TR_FIELD: "off"}, {t6.TR_FIELD: "ON"}, {t6.TR_FIELD: True}, {t6.TR_FIELD: "on", "x": 1}, {t6.FIELD: {"class-a": "required"}}]
    return [good] + junk + extra


def ad():
    return t6.ev.Ed25519Verifier()


def check_decision(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission):
    args = (participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission)
    a, b = frozen_decide(*args), engine_decide(*args)
    same(a, b)
    COUNTS["decision"] += 1
    COUNTS["applied"] += a.kind == "applied"
    return a


def base_args(family):
    verifier = ad()
    rec = t6.record(family=family)
    return dict(participation="required", caller=t6.caller(family), record_text=r.dumps(rec), selection_text=t6.selection_text(rec), context=s.CTX,
                trust=s.trust(pub=t6.PK), verifier=verifier, now=r.NOW, key_admission=verifier.key_admission)


def run_with(base, **over):
    a = dict(base, **over)
    return check_decision(a["participation"], a["caller"], a["record_text"], a["selection_text"], a["context"], a["trust"], a["verifier"], a["now"], a["key_admission"])


@pytest.mark.parametrize("family", [RA, TR])
def test_one_axis_at_a_time_hostile_variations_are_identical(family):
    base = base_args(family)
    first = run_with(base)
    assert first.kind == "applied"
    for name, text in selection_variants(family).items():
        run_with(base, selection_text=text)
    for name, text in record_variants(family).items():
        run_with(base, record_text=text)
    for name, trust in trusts().items():
        run_with(base, trust=trust)
    for name, ctx in contexts().items():
        run_with(base, context=ctx)
    for name, now in nows().items():
        run_with(base, now=now)
    for cal in callers(family):
        run_with(base, caller=cal)
    for part in ("required", "optional", "sometimes", None, 1, b"required"):
        run_with(base, participation=part)
    for verifier in (None, object(), "verifier"):
        run_with(base, verifier=verifier)
    for adm in (None, object()):
        run_with(base, key_admission=adm)
    # optional participation with every selection/record/caller variant: the optional refusal path normalizes with the table's normalizers
    for name, text in selection_variants(family).items():
        run_with(base, participation="optional", selection_text=text)
    for cal in callers(family):
        run_with(base, participation="optional", selection_text="{}", caller=cal)
        run_with(base, participation="optional", caller=cal)


@pytest.mark.parametrize("seed", range(6))
def test_seeded_random_combinations_are_identical(seed):
    rng = random.Random(1000 + seed)
    for _ in range(120):
        family = rng.choice([RA, TR])
        base = base_args(family)
        sv, rv, tv, cv, nv = selection_variants(family), record_variants(family), trusts(), contexts(), nows()
        over = {"selection_text": sv[rng.choice(sorted(sv))], "record_text": rv[rng.choice(sorted(rv))], "trust": tv[rng.choice(sorted(tv))],
                "context": cv[rng.choice(sorted(cv))], "now": nv[rng.choice(sorted(nv))], "caller": rng.choice(callers(family)),
                "participation": rng.choice(["required", "required", "optional", "bad"])}
        for key in rng.sample(sorted(over), rng.randint(1, len(over))):
            base[key] = over[key]
        run_with(base)


def test_the_corpus_is_not_vacuous():
    # runs after the two tests above when the module is run whole; when run alone the counters are filled here
    test_one_axis_at_a_time_hostile_variations_are_identical(RA)
    test_one_axis_at_a_time_hostile_variations_are_identical(TR)
    assert COUNTS["decision"] >= 500 and COUNTS["applied"] >= 20


@pytest.mark.parametrize("family", [RA, TR])
def test_verification_reports_parse_and_validation_results_are_identical(family):
    verifier = ad()
    for rname, rtext in record_variants(family).items():
        same(v6_record.validate_record_text_v6(rtext), record_e.validate_record_text(P6, rtext))
    recs = {k: v6_record.validate_record_text_v6(t) for k, t in record_variants(family).items()}
    for sname, stext in selection_variants(family).items():
        pa, pb = v6_selection.parse_selection_envelope_v6(stext), selection_e.parse_selection_envelope(P6, stext)
        same(pa, pb)
        for rname in ("valid", "tampered", "resealed", "contract:r08-v5", "text:not-json", "top:4", "top:6"):
            rec = recs[rname]
            for tname in ("ok", "revoked-sel", "floor2", "bad-pub", "none", "revoked-key"):
                trust = trusts()[tname]
                a = v6_verify.verify_selection_v6(pa, s.CTX, trust, verifier, r.NOW, rec, verifier.key_admission)
                b = verify_e.verify_selection(P6, pb, s.CTX, trust, verifier, r.NOW, rec, verifier.key_admission)
                same(a, b)
                COUNTS["report"] += 1
    assert COUNTS["report"] > 0
    # snapshot floor keyword arguments
    rec = recs["valid"]
    pa = v6_selection.parse_selection_envelope_v6(selection_variants(family)["valid"])
    for floor in (None, 0, 1, 2, 10 ** 6, -1, "x", True):
        for last in (None, 0, 1, 2, "x"):
            same(v6_verify.verify_selection_v6(pa, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, rec, verifier.key_admission, min_trust_snapshot_version=floor,
                                               last_accepted_snapshot=last),
                 verify_e.verify_selection(P6, pa, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, rec, verifier.key_admission, min_trust_snapshot_version=floor,
                                           last_accepted_snapshot=last))


def test_optional_refusal_normalizes_with_the_first_matching_family_and_keeps_the_sorted_order():
    """The optional-refusal caller normalization is order- and table-sensitive: compare the exact key order, not only dict equality."""
    unsorted_ra = {t6.FIELD: dict(reversed(list({"class-a": "required", "class-b": "not_required", "class-c": "required"}.items())))}
    for family in (RA, TR):
        base = base_args(family)
        for cal in (unsorted_ra, {t6.TR_FIELD: "on"}, {t6.FIELD: {"class-a": "x"}}, {"zzz": 1}, None):
            a = frozen_decide("optional", cal, base["record_text"], "{}", s.CTX, base["trust"], base["verifier"], r.NOW, base["key_admission"])
            b = engine_decide("optional", cal, base["record_text"], "{}", s.CTX, base["trust"], base["verifier"], r.NOW, base["key_admission"])
            same(a, b)
            if a.effective is not None and isinstance(a.effective.get(t6.FIELD), dict):
                assert list(a.effective[t6.FIELD]) == list(b.effective[t6.FIELD])
            if cal is unsorted_ra:
                assert list(b.effective[t6.FIELD]) == ["class-a", "class-b", "class-c"] and b.effective is not cal


def test_hostile_selection_objects_are_identical():
    verifier = ad()
    for family in (RA, TR):
        stmt = t6.statement(t6.record(family=family))
        digest = c.digest(stmt)
        for foreign in ("r08-v2", "r08-v5", "r08-v6", "r08-v7", None, 6):
            for ok in (True, False):
                obj = type("P", (), {"ok": ok, "code": None, "envelope": {"contract_version": foreign}, "statement": stmt, "statement_digest": digest, "signatures": []})()
                same(v6_verify.verify_selection_v6(obj, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, None),
                     verify_e.verify_selection(P6, obj, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, None))
        for obj in (None, object(), "x", 5):
            same(v6_verify.verify_selection_v6(obj, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, None), verify_e.verify_selection(P6, obj, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, None))


def test_signing_input_and_domains_are_identical():
    for family in (RA, TR):
        stmt = t6.statement(t6.record(family=family))
        assert v6_selection.signing_input_v6(stmt) == selection_e.signing_input(P6, stmt)
    assert P6.selection_signing_domain == v6_selection.SIGNING_DOMAIN_V6 == b"ocs-reg/r08-v6/selection\n"
    assert P6.effective_policy_domain == v6pi.EFFECTIVE_PREFIX == b"ocs-reg/r08-v6/effective-policy\n"
    assert P6.version == v6_families.CONTRACT_V6 == "r08-v6"


def test_the_pinned_v6_signed_vectors_decide_identically_and_to_the_pinned_effective_policy():
    vecs = json.loads((VEC / "signed_selection_vector.json").read_text())
    for family, vec in vecs.items():
        d = check_decision("required", t6.caller(family), r.dumps(vec["record"]), json.dumps(vec["envelope"]), s.CTX, s.trust(pub=t6.PK), ad(), r.NOW, ad().key_admission)
        assert d.kind == "applied" and d.effective == vec["effective"]
        assert selection_e.signing_input(P6, vec["statement"]).hex() == vec["signing_input_hex"]


def test_the_pinned_v6_identity_vectors_are_reproduced_by_the_engine():
    vecs = json.loads((VEC / "identity_vectors.json").read_text())
    for vec in vecs["vectors"]:
        assert identity_e.effective_policy_digest(P6, vec["family"], vec["effective"]) == vec["digest"] == v6pi.effective_policy_digest(vec["family"], vec["effective"])
        assert identity_e.effective_preimage(P6, vec["family"], vec["effective"]) == vec["preimage"]


def identity_outcome(fn, *a):
    try:
        return ("ok", fn(*a))
    except Exception as e:  # compare the refusal, never the object identity
        if isinstance(e, v6pi.IdentityRefusal):
            return ("refusal", e.code, e.member, e.stage, dict(e.evidence))
        return ("raised", type(e).__name__)


def test_identity_digests_preimages_and_refusals_are_identical_over_a_hostile_grid():
    class S(str):
        pass
    payloads = [
        {ra.F5RA_FIELD: {"class-a": "required", "class-b": "not_required"}}, {ra.F5RA_FIELD: {"class-a": "required"}}, {ra.F5RA_FIELD: {}},
        {ra.F5RA_FIELD: {"*": "required"}}, {ra.F5RA_FIELD: {"class a": "required"}}, {ra.F5RA_FIELD: {"class-a": 1}}, {ra.F5RA_FIELD: {"class-a": True}},
        {ra.F5RA_FIELD: {"class-a": "Required"}}, {ra.F5RA_FIELD: {"class-a": S("required")}}, {ra.F5RA_FIELD: []}, {ra.F5RA_FIELD: "required"},
        {ra.F5RA_FIELD: {("c%03d" % i): "required" for i in range(257)}}, {ra.F5RA_FIELD: {("c%03d" % i): "required" for i in range(256)}},
        {trv.TR_FIELD: "on"}, {trv.TR_FIELD: "off"}, {trv.TR_FIELD: "ON"}, {trv.TR_FIELD: True}, {trv.TR_FIELD: 1}, {trv.TR_FIELD: None}, {trv.TR_FIELD: {"a": "on"}},
        {trv.TR_FIELD: S("on")}, {}, {"zzz": 1}, dict({trv.TR_FIELD: "on"}, zzz=1), {ra.F5RA_FIELD: {"class-a": "required"}, trv.TR_FIELD: "on"},
        None, [], "x", 5, {1: 2}, {"class_irreversible": {"class-a": "irreversible"}},
    ]
    fams = [RA, TR, "f5-action-class-irreversibility-policy", "f5-action-class-unreadable-policy", "nope", None, 5, S(RA), ""]
    vers = ["r08-v6", "r08-v7", "r08-v5", "r08-v1", "R08-V6", "r08-v6 ", None, b"r08-v6", S("r08-v6"), 6]
    n = 0
    for fam_, pl in itertools.product(fams, payloads):
        assert identity_outcome(v6pi.effective_policy_digest, fam_, pl) == identity_outcome(identity_e.effective_policy_digest, P6, fam_, pl)
        assert identity_outcome(v6pi.effective_preimage, fam_, pl) == identity_outcome(identity_e.effective_preimage, P6, fam_, pl)
        assert identity_outcome(v6pi.validate_effective_payload, fam_, pl) == identity_outcome(identity_e.validate_effective_payload, P6, fam_, pl)
        assert identity_outcome(v6pi.deny_all_dimensions, fam_, pl) == identity_outcome(identity_e.deny_all_dimensions, P6, fam_, pl)
        n += 4
    good = {RA: {ra.F5RA_FIELD: {"class-a": "required"}}, TR: {trv.TR_FIELD: "on"}}
    for fam_, ver in itertools.product(fams, vers):
        pl = good.get(fam_, {})
        assert identity_outcome(v6pi.effective_policy_digest, fam_, pl, ver) == identity_outcome(identity_e.effective_policy_digest, P6, fam_, pl, ver)
        assert identity_outcome(v6pi.registered_family_version, fam_, ver) == identity_outcome(identity_e.registered_family_version, P6, fam_, ver)
        n += 2
    assert n > 600
    pre = v6pi.effective_preimage(RA, good[RA])
    assert v6pi.effective_digest_of_preimage(pre) == identity_e.effective_digest_of_preimage(P6, pre)
    assert pre["family_version"] == "v6" and "family_schema_revision" not in pre


def test_table_dispatch_and_composition_are_identical():
    class S(str):
        pass
    for fam_ in (RA, TR, "x", None, 5, S(RA), [RA], {}):
        a, b = v6_families.lookup_v6(fam_), profile_e.lookup(P6, fam_)
        assert a is b
    for ver in ("r08-v6", "r08-v7", "r08-v5", None, 6, S("r08-v6"), "R08-V6", ""):
        a, b = v6_families.table_for_contract_version_v6(ver), profile_e.table_for_contract_version(P6, ver)
        assert (a.ok, a.code, a.version) == (b.ok, b.code, b.version) and (a.table is None) == (b.table is None)
        if a.ok:
            assert dict(a.table) == dict(b.table)
    recs = {fam_: v6_record.validate_record_text_v6(r.dumps(t6.record(family=fam_))) for fam_ in (RA, TR)}
    bad_recs = [None, object(), type("R", (), {"ok": 1, "record": recs[RA].record})(), type("R", (), {"ok": True, "record": []})(),
                type("R", (), {"ok": True, "record": {"family": S(RA), "payload": t6.payload(RA)}})(),
                type("R", (), {"ok": True, "record": {"family": "f5-action-class-age-bounds", "payload": {}}})(),
                type("R", (), {"ok": True, "record": {"family": RA, "payload": {"x": 1}}})(),
                type("R", (), {"ok": True, "record": {"family": TR, "payload": t6.payload(TR)}})()]
    ops = ["intersection", "union", "", None, S("intersection"), 1]
    n = 0
    for rec in list(recs.values()) + bad_recs:
        for cal in [t6.caller(RA), t6.caller(TR), None, {}, "x", {ra.F5RA_FIELD: {"class-a": "x"}}, {trv.TR_FIELD: "ON"}]:
            for op in ops:
                same(v6_families.compose_v6(cal, rec, op), profile_e.compose(P6, cal, rec, op))
                for ver in ("r08-v6", "r08-v5", S("r08-v6"), None):
                    same(v6_families.compose_for_v6(ver, cal, rec, op), profile_e.compose_for(P6, ver, cal, rec, op))
                    n += 1
    assert n > 1000


# ------------------------------------------------------------------ cross-version
def refused_with(d, *codes):
    return d.kind == "required_policy_unavailable" and d.code in codes and d.effective is None


def docs_by_version():
    """(record, selection_text, caller, decide-function name) for one document of each of v3, v4, v5, v6 (both families) and v7."""
    out = {"v3": (t3.record(), t3.selection_text, t3.caller()), "v4": (t4.record(), t4.selection_text, t4.caller()), "v5": (t5.record(), t5.selection_text, t5.caller()),
           "v6-ra": (t6.record(family=RA), t6.selection_text, t6.caller(RA)), "v6-tr": (t6.record(family=TR), t6.selection_text, t6.caller(TR)),
           "v7": (t7.record(), t7.selection_text, t7.caller())}
    return {k: (rec, sel(rec), cal) for k, (rec, sel, cal) in out.items()}


def entry_points():
    from registry_successor import v3_decision, v4_decision
    return {"v3": v3_decision.verify_and_decide_v3, "v4": v4_decision.verify_and_decide_v4, "v5": v5_decision.verify_and_decide_v5,
            "v6": v6_decision.verify_and_decide_v6, "v6-engine": lambda *a: engine_decide(*a), "v7": v7_decision.verify_and_decide_v7,
            "v7-engine": lambda *a: decide_e.verify_and_decide(profiles.V7, *a)}


OWN = {"v3": {"v3"}, "v4": {"v4"}, "v5": {"v5"}, "v6": {"v6-ra", "v6-tr"}, "v6-engine": {"v6-ra", "v6-tr"}, "v7": {"v7"}, "v7-engine": {"v7"}}


def test_every_document_is_accepted_only_by_its_own_contract_and_refused_everywhere_else():
    verifier = ad()
    docs, eps = docs_by_version(), entry_points()
    applied = 0
    for ep_name, ep in eps.items():
        for doc_name, (rec, sel, cal) in docs.items():
            d = ep("required", cal, r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, verifier.key_admission)
            if doc_name in OWN[ep_name]:
                assert d.kind == "applied", (ep_name, doc_name, d)
                applied += 1
            else:
                assert refused_with(d, "contract_unsupported"), (ep_name, doc_name, d)
                d = ep("optional", cal, r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, verifier.key_admission)
                assert d.kind == "overlay_not_applied" and d.code == "contract_unsupported" and d.caller_unchanged is True
    assert applied == 9  # v3, v4, v5 once each; v6 and v6-engine twice each (two families); v7 and v7-engine once each


def test_a_record_and_a_selection_of_different_contracts_never_combine():
    verifier = ad()
    docs, eps = docs_by_version(), entry_points()
    for ep_name in ("v6", "v6-engine", "v7", "v7-engine"):
        ep = eps[ep_name]
        for rname, (rec, _, cal) in docs.items():
            for sname, (_, sel, _) in docs.items():
                if rname == sname:
                    continue
                d = ep("required", cal, r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, verifier.key_admission)
                assert refused_with(d, "contract_unsupported", "composition_record_invalid", "family_unsupported", "record_identity_mismatch",
                                    "record_digest_mismatch", "evaluator_mismatch"), (ep_name, rname, sname, d)


def test_a_family_of_another_contract_inside_this_contracts_envelope_is_family_unsupported_with_no_fallback():
    verifier = ad()
    irr, ra_fam = "f5-action-class-irreversibility-policy", RA
    # v7 envelope + v7 contract record carrying a v6 family; v6 envelope + record carrying the v7 family
    for ep_name, contract, domain, foreign_fam, rec_support, caller in (
            ("v7", "r08-v7", t7.V7_DOMAIN, ra_fam, t7, t7.caller()), ("v7", "r08-v7", t7.V7_DOMAIN, TR, t7, t7.caller()),
            ("v6", "r08-v6", t6.V6_DOMAIN, irr, t6, t6.caller(RA)), ("v6-engine", "r08-v6", t6.V6_DOMAIN, irr, t6, t6.caller(RA)),
            ("v7-engine", "r08-v7", t7.V7_DOMAIN, ra_fam, t7, t7.caller())):
        rec = rec_support.record(family=foreign_fam)
        stmt = r.make_statement_v2(rec, family=foreign_fam)
        sel = r.dumps(s.envelope(stmt, domain=domain, contract=contract, signature=rec_support.sign(stmt), pub=t6.PK))
        d = entry_points()[ep_name]("required", caller, r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, verifier.key_admission)
        assert refused_with(d, "family_unsupported"), (ep_name, foreign_fam, d)
        d = entry_points()[ep_name]("optional", caller, r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), verifier, r.NOW, verifier.key_admission)
        assert d.kind == "overlay_not_applied" and d.code == "family_unsupported" and d.caller_unchanged is True


def test_a_signature_over_another_contracts_domain_never_verifies_under_this_one():
    verifier = ad()
    for support, ep_name, own_contract in ((t7, "v7", "r08-v7"), (t6, "v6-engine", "r08-v6")):
        fam_ = support.FAMILY
        rec = support.record(family=fam_)
        stmt = support.statement(rec)
        for domain in (t7.V7_DOMAIN, t6.V6_DOMAIN, t6.V5_DOMAIN, s.V2_DOMAIN, s.V1_DOMAIN):
            sel = r.dumps(s.envelope(stmt, domain=domain, contract=own_contract, signature=support.sign(stmt, domain=domain), pub=t6.PK))
            d = entry_points()[ep_name]("required", support.caller() if support is t7 else t6.caller(fam_), r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), verifier,
                                        r.NOW, verifier.key_admission)
            own = t7.V7_DOMAIN if support is t7 else t6.V6_DOMAIN
            assert (d.kind == "applied") == (domain == own), (ep_name, domain, d)
            if domain != own:
                assert refused_with(d, "signature_invalid")


def test_frozen_dispatch_tables_still_refuse_r08_v7_and_no_family_leaks_between_tables():
    from registry_successor import families, v3_families, v4_families, v5_families
    from registry_successor import v7_families
    irr = "f5-action-class-irreversibility-policy"
    sel = families.table_for_contract_version("r08-v7")
    assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
    assert not v3_families.table_for_contract_version_v3("r08-v7").ok and not v4_families.table_for_contract_version_v4("r08-v7").ok
    assert not v5_families.table_for_contract_version_v5("r08-v7").ok and not v6_families.table_for_contract_version_v6("r08-v7").ok
    assert not v7_families.table_for_contract_version_v7("r08-v6").ok
    for lookup in (families.lookup_for, ):
        assert lookup("r08-v7", irr) is None and lookup("r08-v2", irr) is None
    assert v3_families.lookup_v3(irr) is None and v4_families.lookup_v4(irr) is None and v5_families.lookup_v5(irr) is None and v6_families.lookup_v6(irr) is None
    assert v7_families.lookup_v7(RA) is None and v7_families.lookup_v7(TR) is None and v7_families.lookup_v7(irr) is not None
    assert irr not in families.FAMILIES_V2 and irr not in families.FAMILIES
