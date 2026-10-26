"""Worker B follow-ups: (F4) claim-shape-first order of `verify_carried_binding_digest`; (FU-1) the r08-v2 family modules decide token validity by the frozen
Unicode 15.1.0 table, identically on every host. BUILDER_TESTED, not qualified."""
import json
from pathlib import Path

import pytest

from registry_successor import common as common_mod
from registry_successor import v2_age_bounds as ab
from registry_successor import v2_f1ab as f1
from registry_successor import v2_policy_identity as m

ROOT = Path(__file__).resolve().parent.parent
V = json.loads((ROOT / "docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json").read_text(encoding="ascii"))
BV001 = next(v for v in V["valid"] if v["id"] == "BV-001")
DIGEST_A = "sha256:" + "a" * 64
BAD_DIGESTS = ("sha256:" + "E" * 64, "sha256:short", "e" * 64, "", None, 7, b"sha256:" + b"0" * 64, "sha256:" + "0" * 63 + "٠")


def _b():
    return m.parse_binding(BV001["input_json"])


def _row(b, **edit):
    r = {"scope_key": m.scope_key_digest(m.scope_key_from_binding(b))}
    r.update({k: b[k] for k in m.POLICY_IDENTITY_MEMBER_VALUES if k != "scope_key"})
    r.update(edit)
    return r


def _code(fn, *a):
    with pytest.raises(m.IdentityRefusal) as info:
        fn(*a)
    return info.value


# ---------------------------------------------------------------------------------------------------------------- F4 order
@pytest.mark.parametrize("bad", BAD_DIGESTS, ids=lambda x: repr(x)[:20])
def test_malformed_carried_digest_is_claim_shape_whatever_the_identity_or_store(bad):
    b = _b()
    rows = {
        "match": _row(b),
        "cross_selection": _row(b, selection_id="sel-other", selection_epoch=b["selection_epoch"] + 5),
        "cross_scope": _row(b, scope_key=DIGEST_A, selection_epoch=b["selection_epoch"] + 5),
        "stale": _row(b, selection_epoch=b["selection_epoch"] + 1),
        "ahead": _row(b, selection_epoch=b["selection_epoch"] - 1, selection_digest=DIGEST_A),
        "unknown_store": {},
        "unknown_store_none_like": "not a row",
        "no_row": None,
    }
    for name, row in rows.items():
        e = _code(m.verify_carried_binding_digest, b, bad, row)
        assert e.code == "field_invalid" and e.member is None and "observed_value_class" in e.evidence, name


def test_malformed_carried_digest_after_claim_type_and_members_but_before_the_version():
    b = _b()
    # (1) type and required members first
    assert _code(m.verify_carried_binding_digest, b, "bad", None).code == "field_invalid"
    assert _code(m.verify_carried_binding_digest, {k: v for k, v in b.items() if k != "activation_ref"}, "bad", _row(b)).code == "field_missing"
    assert _code(m.verify_carried_binding_digest, {**b, "extra": 1}, "bad", _row(b)).code == "field_unknown"
    assert _code(m.verify_carried_binding_digest, {**b, "activation_ref": None}, "bad", _row(b)).code == "field_type_invalid"
    assert _code(m.verify_carried_binding_digest, [], "bad", _row(b)).code == "field_type_invalid"
    # (2) before (3): a wrong version AND a malformed digest is the digest (member None), a wrong version with a good digest is binding_profile
    wrong = {**b, "binding_profile": "ocs-policy-binding/2"}
    e = _code(m.verify_carried_binding_digest, wrong, "bad", _row(b))
    assert (e.code, e.member) == ("field_invalid", None)
    e = _code(m.verify_carried_binding_digest, wrong, m.checked_binding_digest(b), _row(b))
    assert (e.code, e.member) == ("field_invalid", "binding_profile")


def test_well_formed_digest_keeps_the_order_store_then_row_key_then_stale_then_members_then_digest():
    b = _b()
    good, wrong = m.checked_binding_digest(b), "sha256:" + "0" * 64
    assert _code(m.verify_carried_binding_digest, b, wrong, {}).code == "store_unknown"  # unknown state: HOLD path unchanged, before the digest compare
    assert _code(m.verify_carried_binding_digest, b, wrong, _row(b, selection_id="sel-x", selection_epoch=b["selection_epoch"] + 5)).code == "policy_identity_mismatch"
    assert _code(m.verify_carried_binding_digest, b, wrong, _row(b, selection_epoch=b["selection_epoch"] + 1)).code == "selection_epoch_stale"
    assert _code(m.verify_carried_binding_digest, b, wrong, _row(b, record_digest=DIGEST_A)).code == "policy_identity_mismatch"
    assert _code(m.verify_carried_binding_digest, b, wrong, _row(b)).code == "digest_mismatch"  # PINNED GD-002/GD-003: not policy_identity_mismatch (reported)
    assert m.verify_carried_binding_digest(b, good, _row(b)) == good
    assert m.verify_carried_binding_digest(b, good) == good


# ---------------------------------------------------------------------------------------------------------------- FU-1
TU = V["token_unicode"]["vectors"]


def _text(v):
    return "".join(chr(int(cp, 16)) for cp in v["code_points"]) * v.get("repeat", 1)


def _poison(monkeypatch):
    import unicodedata

    def boom(*a, **k):
        raise AssertionError("host Unicode database consulted")
    monkeypatch.setattr(unicodedata, "category", boom)
    monkeypatch.setattr(common_mod, "valid_token", boom)


def _f1ab_payload(tok):
    return {k: ([tok] if i == 0 else []) for i, k in enumerate(f1.F1AB_FIELDS)}


@pytest.mark.parametrize("vec", TU, ids=lambda v: v["id"])
def test_family_validators_follow_the_frozen_table_with_the_host_database_poisoned(vec, monkeypatch):
    _poison(monkeypatch)
    t, want = _text(vec), vec["expected"]["valid"]
    assert (f1.payload_validator(_f1ab_payload(t)) is None) is want
    assert (f1.normalize_caller(_f1ab_payload(t)) is not None) is want
    assert (ab.f5_payload_validator({ab.F5_FIELD: {t: 5}}) is None) is want
    assert (ab.normalize_caller_f5({ab.F5_FIELD: {t: 5}}) is not None) is want


@pytest.mark.parametrize("host", ("older", "newer", "same"))
def test_older_and_newer_host_cases_decide_identically(host, monkeypatch):
    """Emulated hosts: an older host calls U+2EBF0 (CJK Ext I, assigned in 15.1) unassigned; a newer host calls U+088F (Cn in 15.1) assigned. The frozen table
    decides for the v2 family modules regardless: U+2EBF0 accepted, U+088F refused."""
    import unicodedata
    real = unicodedata.category

    def cat(ch):
        if host == "older" and ord(ch) == 0x2EBF0:
            return "Cn"
        if host == "newer" and ord(ch) == 0x088F:
            return "Lo"
        return real(ch)
    monkeypatch.setattr(unicodedata, "category", cat)
    accepted, refused = chr(0x2EBF0), chr(0x088F)
    for tok, want in ((accepted, True), (refused, False)):
        assert (f1.payload_validator(_f1ab_payload(tok)) is None) is want, (host, hex(ord(tok)))
        assert (f1.normalize_caller(_f1ab_payload(tok)) is not None) is want
        assert (ab.f5_payload_validator({ab.F5_FIELD: {tok: 5}}) is None) is want
        assert (ab.normalize_caller_f5({ab.F5_FIELD: {tok: 5}}) is not None) is want
    # the unchanged r08-v1 validator IS host dependent (golden: it is not routed through the frozen table)
    assert common_mod.valid_token(accepted) is (host != "older")
    assert common_mod.valid_token(refused) is (host == "newer")


def test_v1_paths_are_unchanged():
    import hashlib
    assert hashlib.sha256((ROOT / "registry_successor/common.py").read_bytes()).hexdigest() == "f87c0f1c51785df32f1ad60b77096258729e45cca6586a696533d63ad28aece2"
    from registry_successor import compose
    assert compose.normalize_caller({k: ["transférer"] for k in common_mod.F1A_FIELDS}) is not None  # the v1 F1a composer still uses the shipped validator
