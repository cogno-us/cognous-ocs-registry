"""EXT-S1-5 integration tests for Architect Batch 6 rulings 4.3, 4.6, N-10, N-11 and N-12 against the merged contract (Amendment 1).

Covers: the Registry-side `TrustSnapshot` adapter, snapshot version and epoch bounds, duplicate grants by canonical grant identity, typed diagnostic labels that can
never reach a digest, the six-member identity comparison, `verify_carried_binding_digest` ordering, `project_effective_policy_digest`, and the typed INPUT /
DURABLE_STATE stage. Pure; no store, no clock. BUILDER_TESTED, not qualified; digests give integrity, never authentication.
"""
import itertools
import json
import random
from pathlib import Path

import pytest

from registry_successor import v2_policy_identity as m
from registry_successor.verify import AuthorityGrant, IssuerEntry, TrustSnapshot

ROOT = Path(__file__).resolve().parent.parent
V = json.loads((ROOT / "docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json").read_text(encoding="ascii"))
TF001 = V["trust_snapshots"][0]
BV001 = next(v for v in V["valid"] if v["id"] == "BV-001")


def _grant(op):
    return AuthorityGrant("runtime-emulator", "tenant-a", "inst-a", "domain-a", op)


def _snap(**edit):
    base = dict(snapshot_id="snap-example-7", version=7, valid_until="2026-12-01T00:00:00Z",
                issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(range(32)), (_grant("op-audit"), _grant("op-transfer"))),),
                revoked_key_ids=frozenset({"key-old-1"}), revoked_selections=frozenset({("sel-old-1", 2)}), min_epochs={"sel-example-f1ab": 3})
    base.update(edit)
    return TrustSnapshot(**base)


def _refusal(fn, *args, **kw):
    with pytest.raises(m.IdentityRefusal) as info:
        fn(*args, **kw)
    return info.value


# ------------------------------------------------------------------------------------------------------------ adapter
def test_adapter_reproduces_the_contract_fingerprint_from_a_verifier_object():
    assert m.trust_snapshot_fingerprint_from_verified(_snap()) == TF001["expected"]["trust_snapshot_fingerprint"]
    assert m.trust_snapshot_from_verified(_snap()) == m.normalize_snapshot(TF001["input"])


def test_adapter_is_independent_of_collection_order_and_container_type():
    want = TF001["expected"]["trust_snapshot_fingerprint"]
    rnd = random.Random(7)
    grants = [_grant("op-audit"), _grant("op-transfer"), _grant("op-a"), _grant("op-b")]
    base = None
    for _ in range(12):
        rnd.shuffle(grants)
        fp = m.trust_snapshot_fingerprint_from_verified(_snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(range(32)), tuple(grants)),)))
        base = base or fp
        assert fp == base
    for kind in (frozenset, set, tuple, list):
        sn = _snap(revoked_key_ids=kind(["key-old-1"]), revoked_selections=kind([("sel-old-1", 2)]), min_epochs=[("sel-example-f1ab", 3)] if kind is list else {"sel-example-f1ab": 3})
        assert m.trust_snapshot_fingerprint_from_verified(sn) == want, kind
    assert m.trust_snapshot_fingerprint_from_verified(_snap(min_epochs=(("sel-example-f1ab", 3),))) == want
    assert m.trust_snapshot_fingerprint_from_verified(_snap(issuers=[_snap().issuers[0]])) == want


def test_no_snapshot_supplied_is_missing_at_the_typed_input_stage():
    e = _refusal(m.trust_snapshot_from_verified, None)
    assert (e.code, e.stage) == ("trust_snapshot_missing", "INPUT")
    row = m.mapping_row_for(e)
    assert row.evidence_stage == "INPUT" and row.stage_version == "ocs-evidence-stage/1" and row.verdict_class == "UNKNOWN_FAIL_CLOSED"
    assert _refusal(m.trust_snapshot_fingerprint_from_verified, None).code == "trust_snapshot_missing"


def test_the_durable_state_stage_is_a_different_typed_row_under_the_same_code():
    guard = m.verdict_for("trust_snapshot_missing", "DURABLE_STATE")
    verify = m.verdict_for("trust_snapshot_missing", "INPUT")
    assert (verify.evidence_stage, guard.evidence_stage) == ("INPUT", "DURABLE_STATE") and verify.row_id != guard.row_id
    assert verify.registry_code == guard.registry_code == "trust_snapshot_missing"
    assert "scope_key_digest" in guard.evidence_fields and "scope_key_digest" not in verify.evidence_fields  # not presented as one underlying cause
    assert m.EVIDENCE_STAGES == ("INPUT", "DURABLE_STATE")


class _Sub(TrustSnapshot):
    pass


class _SubIssuer(IssuerEntry):
    pass


class _SubGrant(AuthorityGrant):
    pass


def _bad_snapshots():
    good = _snap()
    iss = good.issuers[0]
    yield "a dict", {"snapshot_id": "x"}
    yield "a str", "snapshot"
    yield "an int", 0
    yield "an object", object()
    yield "a subclass of TrustSnapshot", _Sub(**{f: getattr(good, f) for f in good.__dataclass_fields__})
    yield "a subclass of IssuerEntry", _snap(issuers=(_SubIssuer("key-example-1", "issuer-a", "ed25519", bytes(32), (_grant("op-a"),)),))
    yield "a subclass of AuthorityGrant", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(32), (_SubGrant("a", "b", "c", "d", "e"),)),))
    yield "a bad snapshot id", _snap(snapshot_id="bad id")
    yield "a bad valid_until", _snap(valid_until="soon")
    yield "version 0", _snap(version=0)
    yield "version bool", _snap(version=True)
    yield "version 2^53", _snap(version=2 ** 53)
    yield "public key str", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", "00", (_grant("op-a"),)),))
    yield "public key empty", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", b"", (_grant("op-a"),)),))
    yield "public key bytearray", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytearray(32), (_grant("op-a"),)),))
    yield "grant star token", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(32), (AuthorityGrant("a", "b", "c", "d", "*"),)),))
    yield "grant tuple not a grant", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(32), (("a", "b", "c", "d", "e"),)),))
    yield "authority a set", _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(32), {_grant("op-a")}),))
    yield "issuers a set", _snap(issuers={iss})
    yield "duplicate issuer key", _snap(issuers=(iss, iss))
    yield "revoked key not str", _snap(revoked_key_ids=frozenset({1}))
    yield "revoked pair list", _snap(revoked_selections=frozenset({("a", 1)}) | {("b", 1, 2)})
    yield "revoked epoch 0", _snap(revoked_selections=frozenset({("a", 0)}))
    yield "revoked epoch negative", _snap(revoked_selections=frozenset({("a", -1)}))
    yield "revoked epoch bool", _snap(revoked_selections=frozenset({("a", True)}))
    yield "revoked epoch over range", _snap(revoked_selections=frozenset({("a", 2147483648)}))
    yield "revoked epoch huge", _snap(revoked_selections=frozenset({("a", 10 ** 5000)}))
    yield "floor 0", _snap(min_epochs={"a": 0})
    yield "floor over range", _snap(min_epochs={"a": 2147483648})
    yield "floor bool", _snap(min_epochs={"a": True})
    yield "duplicate floor id", _snap(min_epochs=(("a", 1), ("a", 2)))
    yield "min_epochs a str", _snap(min_epochs="x")
    yield "repeated revoked key (list)", _snap(revoked_key_ids=["k", "k"])
    yield "repeated revoked pair (list)", _snap(revoked_selections=[("a", 1), ("a", 1)])


@pytest.mark.parametrize("label,obj", list(_bad_snapshots()), ids=[x[0] for x in _bad_snapshots()])
def test_malformed_or_foreign_input_is_invalid_never_missing_and_never_misread(label, obj):
    e = _refusal(m.trust_snapshot_fingerprint_from_verified, obj)
    assert e.code == "trust_snapshot_invalid", (label, e.code)  # N-11: definitive malformed input is the invalid-input refusal, never `trust_snapshot_missing`
    assert m.mapping_row_for(e).verdict_class == "REFUSE"


def test_a_hostile_object_never_escapes_and_is_never_formatted():
    class Bomb:
        def __getattribute__(self, name):
            raise RuntimeError("touched " + name)

        def __repr__(self):
            raise AssertionError("formatted")

    assert _refusal(m.trust_snapshot_from_verified, Bomb()).code == "trust_snapshot_invalid"
    sn = _snap()
    object.__setattr__(sn, "issuers", Bomb())
    assert _refusal(m.trust_snapshot_from_verified, sn).code == "trust_snapshot_invalid"


def test_the_adapter_is_stricter_than_the_verifier_in_exactly_the_documented_places_and_never_looser():
    from registry_successor import verify
    for label, obj in _bad_snapshots():
        if verify._normalize_trust(obj) is None:
            with pytest.raises(m.IdentityRefusal):
                m.trust_snapshot_from_verified(obj)  # a snapshot the verifier refuses is never fingerprinted
    # the verifier accepts these, the adapter refuses them (ruling 4.6: strict positive epochs in the declared range, version at most 2^53 - 1, no repeated grant)
    for obj in (_snap(version=2 ** 53), _snap(revoked_selections=frozenset({("a", 0)})), _snap(min_epochs={"a": 2147483648}),
                _snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(32), (_grant("op-a"), _grant("op-a"))),))):
        assert verify._normalize_trust(obj) is not None
        assert _refusal(m.trust_snapshot_from_verified, obj).code == "trust_snapshot_invalid"


# ------------------------------------------------------------------------------------------------------------ bounds
@pytest.mark.parametrize("version,ok", [(1, True), (2, True), (2 ** 31, True), (2 ** 53 - 1, True), (0, False), (-1, False), (2 ** 53, False), (10 ** 20, False), (True, False), (1.0, False), ("1", False), (None, False)])
def test_snapshot_version_is_a_strict_int_in_1_to_2_53_minus_1(version, ok):
    sn = json.loads(json.dumps(TF001["input"]))
    sn["version"] = version
    if ok:
        assert m.trust_snapshot_fingerprint(sn).startswith("sha256:")
        assert m.project_snapshot_version(version) == version
    else:
        assert _refusal(m.trust_snapshot_fingerprint, sn).code == "trust_snapshot_invalid"
        assert _refusal(m.project_snapshot_version, version).stage == "projection"


def test_the_snapshot_version_bound_is_not_a_freshness_bound():
    sn = json.loads(json.dumps(TF001["input"]))
    fps = set()
    for v in (1, 7, 2 ** 40, 2 ** 53 - 1):
        sn["version"] = v
        fps.add(m.trust_snapshot_fingerprint(sn))
    assert len(fps) == 4  # no age, clock or recency is consulted: every in-range value is a distinct, accepted representation


@pytest.mark.parametrize("epoch,ok", [(1, True), (2147483647, True), (0, False), (-1, False), (2147483648, False), (2 ** 53, False), (10 ** 20 - 1, False), (True, False), (False, False), ("1", False), (1.5, False)])
def test_revoked_epoch_and_floor_are_strict_positive_ints_in_the_selection_epoch_range(epoch, ok):
    for field, pair in (("revoked_selections", ["a", epoch]), ("min_epochs", ["a", epoch])):
        sn = json.loads(json.dumps(TF001["input"]))
        sn[field] = [pair]
        if ok:
            assert m.trust_snapshot_fingerprint(sn).startswith("sha256:")
        else:
            assert _refusal(m.trust_snapshot_fingerprint, sn).code == "trust_snapshot_invalid", (field, epoch)


def test_overlong_integers_are_never_coerced_or_collapsed_into_one_fingerprint():
    outs = set()
    for bad in (10 ** 20, 10 ** 21, 10 ** 5000, -10 ** 20):
        sn = json.loads(json.dumps(TF001["input"]))
        sn["revoked_selections"] = [["a", bad]]
        e = _refusal(m.trust_snapshot_fingerprint, sn)
        assert e.code == "trust_snapshot_invalid"
        outs.add(e.code)
    loaded = m.load_document('{"x": 100000000000000000000, "y": 100000000000000000001}')
    assert isinstance(loaded["x"], m.OutOfRangeInteger) and loaded["x"] != loaded["y"]  # distinct literals stay distinct, never an int
    assert _refusal(m.canonical_json_bytes, loaded["x"]).code == "field_invalid"


def test_the_snapshot_node_ceiling_is_input_too_large_and_below_it_nothing_is_lost():
    assert m.MAX_SNAPSHOT_NODES == 1048576
    old = m.MAX_SNAPSHOT_NODES
    try:
        m.MAX_SNAPSHOT_NODES = 40
        sn = json.loads(json.dumps(TF001["input"]))
        sn["revoked_key_ids"] = ["k%d" % i for i in range(100)]
        e = _refusal(m.trust_snapshot_fingerprint, sn)
        assert e.code == "input_too_large"
        assert m.mapping_row_for(e).registry_code == "input_too_large"
    finally:
        m.MAX_SNAPSHOT_NODES = old


# ------------------------------------------------------------------------------------------------------------ grants
def _fp_with(grants):
    return m.trust_snapshot_fingerprint_from_verified(_snap(issuers=(IssuerEntry("key-example-1", "issuer-a", "ed25519", bytes(range(32)), tuple(grants)),)))


def test_duplicate_grants_refuse_by_canonical_identity_and_distinct_grants_never_do():
    assert _refusal(_fp_with, [_grant("op-a"), _grant("op-a")]).code == "trust_snapshot_invalid"  # the same canonical grant identity twice in one issuer
    one_off = [AuthorityGrant("c", "t", "i", "d", "o"), AuthorityGrant("c", "t", "i", "d", "o2")]
    for field in range(5):  # grants differing in exactly one of the five tokens are distinct
        g2 = list(("c", "t", "i", "d", "o"))
        g2[field] = g2[field] + "x"
        assert _fp_with([AuthorityGrant("c", "t", "i", "d", "o"), AuthorityGrant(*g2)]).startswith("sha256:"), field
    many = [AuthorityGrant("c%d" % i, "t", "i", "d", "o") for i in range(50)]
    assert _fp_with(many) == _fp_with(list(reversed(many)))  # many distinct grants under one issuer are accepted, in any order
    assert _fp_with(one_off).startswith("sha256:")


def test_the_same_grant_under_two_issuers_is_two_issuers_not_a_duplicate():
    a = IssuerEntry("key-a", "issuer-a", "ed25519", bytes(range(32)), (_grant("op-a"),))
    b = IssuerEntry("key-b", "issuer-b", "ed25519", bytes(range(1, 33)), (_grant("op-a"),))
    assert m.trust_snapshot_fingerprint_from_verified(_snap(issuers=(a, b))).startswith("sha256:")
    assert _refusal(m.trust_snapshot_fingerprint_from_verified, _snap(issuers=(a, a))).code == "trust_snapshot_invalid"  # a repeated issuer key id is
    # a different grant list changes the fingerprint: a grant is part of the identity
    assert m.trust_snapshot_fingerprint_from_verified(_snap(issuers=(a,))) != m.trust_snapshot_fingerprint_from_verified(_snap(issuers=(a, b)))


# ------------------------------------------------------------------------------------------------------------ labels
def test_diagnostic_labels_are_typed_and_can_never_enter_a_digest_or_a_document():
    for label in (m.NON_STRING_KEY, m.AMBIGUOUS_STRING_KEY):
        assert type(label) is m.DiagnosticLabel and isinstance(label, str)
        for fn in (m.canonical_json_bytes, m.plain_digest):
            assert _refusal(fn, label).code == "field_type_invalid"
            assert _refusal(fn, {"a": label}).code == "field_type_invalid"
            assert _refusal(fn, [label]).code == "field_type_invalid"
        good = json.loads(BV001["input_json"])
        for member in ("record_id", "selection_id", "family", "consumer_id", "operation", "record_digest", "activation_ref"):
            assert _refusal(m.validate_binding, {**good, member: label}).code == "field_type_invalid", member
        sn = json.loads(json.dumps(TF001["input"]))
        sn["snapshot_id"] = label
        assert _refusal(m.trust_snapshot_fingerprint, sn).code == "trust_snapshot_invalid"
        assert _refusal(m.project_scope, {"tenant": label, "institution": "i", "authority_domain": "d"}).stage == "projection"


def test_the_refusal_member_for_a_bad_key_is_the_typed_label_and_a_real_key_with_the_same_text_is_not():
    good = json.loads(BV001["input_json"])
    bad = dict(good)
    bad[1] = "x"
    e = _refusal(m.validate_binding, bad)
    assert e.code == "field_unknown" and e.member == m.NON_STRING_KEY and type(e.member) is m.DiagnosticLabel
    real = {**good, str(m.NON_STRING_KEY): 1}
    e2 = _refusal(m.validate_binding, real)
    assert e2.code == "field_unknown" and e2.member == str(m.NON_STRING_KEY) and type(e2.member) is str  # an ordinary document key stays a plain member path
    pair = chr(0xD83D) + chr(0xDE00)
    e3 = _refusal(m.validate_binding, {**good, pair: 1})
    assert e3.member == m.AMBIGUOUS_STRING_KEY and type(e3.member) is m.DiagnosticLabel


def test_non_string_and_ambiguous_keys_refuse_before_any_projection_or_digest():
    pair = chr(0xD83D) + chr(0xDE00)
    for payload in ({1: 2}, {"a": 1, 2: 3}, {pair: 1}, {(1, 2): 1}, {None: 1}):
        assert _refusal(m.plain_digest, payload).code == "field_unknown"
        assert _refusal(m.project_effective_policy_digest, "f4-control-plane-age-bounds", payload).code in ("field_unknown", "field_type_invalid")
        assert _refusal(m.canonical_json_bytes, payload).code == "field_unknown"


# ------------------------------------------------------------------------------------------------------------ identity
def _binding():
    return m.parse_binding(BV001["input_json"])


def _row(b=None, **edit):
    b = b or _binding()
    row = {"scope_key": m.scope_key_digest(m.scope_key_from_binding(b))}
    row.update({k: b[k] for k in m.POLICY_IDENTITY_MEMBER_VALUES if k != "scope_key"})
    row.update(edit)
    return row


def test_a_matching_row_returns_the_binding_digest_and_ignores_the_caller_dependent_effective_digest():
    b = _binding()
    assert m.compare_binding_identity(b, _row(b)) == m.checked_binding_digest(b)
    other = {**b, "effective_policy_digest": "sha256:" + "0" * 64}
    assert m.compare_binding_identity(other, _row(b)) == m.checked_binding_digest(other)  # contract 7.4: effective_policy_digest is never compared with durable state


DIGEST_A, DIGEST_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64


@pytest.mark.parametrize("member,value", [("selection_id", "sel-other"), ("scope_key", DIGEST_A), ("selection_digest", DIGEST_A), ("record_id", "rec-other"), ("record_version", 99),
                                          ("record_digest", DIGEST_A), ("activation_ref", DIGEST_B)])
def test_each_differing_member_is_a_policy_identity_mismatch_naming_it(member, value):
    b = _binding()
    row = _row(b, **{member: value})
    e = _refusal(m.compare_binding_identity, b, row)
    assert (e.code, e.member) == ("policy_identity_mismatch", member)
    row_map = m.mapping_row_for(e)
    assert row_map.verdict_class == "REFUSE" and row_map.registry_code == "policy_identity_mismatch" and member.replace("scope_key", "scope_key_digest") in row_map.evidence_fields


def test_a_differing_claim_scope_member_is_found_through_the_scope_key():
    b = _binding()
    for edit in ({"consumer_id": "other-consumer"}, {"operation": "other-op"}, {"scope": {**b["scope"], "tenant": "tenant-z"}}, {"scope": {**b["scope"], "institution": "inst-z"}},
                 {"scope": {**b["scope"], "authority_domain": "dom-z"}}):
        e = _refusal(m.compare_binding_identity, {**b, **edit}, _row(b))
        assert (e.code, e.member) == ("policy_identity_mismatch", "scope_key"), edit
    e = _refusal(m.compare_binding_identity, {**b, "selection_id": "sel-moved"}, _row(b))
    assert e.member == "selection_id"  # reported as itself, not as the scope key that also contains it


def test_a_claim_epoch_behind_the_row_is_stale_ahead_is_a_mismatch_and_stale_takes_precedence():
    b = _binding()
    behind = _row(b, selection_epoch=b["selection_epoch"] + 1)
    e = _refusal(m.compare_binding_identity, b, behind)
    assert e.code == "selection_epoch_stale" and e.member == "selection_epoch"
    assert dict(e.evidence) == {"selection_epoch": b["selection_epoch"], "high_water_epoch": b["selection_epoch"] + 1}
    assert m.mapping_row_for(e).verdict_class == "REFUSE_STALE"
    ahead = _row(b, selection_epoch=b["selection_epoch"] - 1)
    e = _refusal(m.compare_binding_identity, b, ahead)
    assert (e.code, e.member) == ("policy_identity_mismatch", "selection_epoch")
    both = _row(b, selection_epoch=b["selection_epoch"] + 1, selection_digest=DIGEST_A, record_id="rec-other")
    assert _refusal(m.compare_binding_identity, b, both).code == "selection_epoch_stale"  # a definitively stale epoch is never a generic identity mismatch


def test_epochs_of_a_different_row_are_not_comparable_so_cross_row_claims_are_mismatches_never_stale():
    """Review S-1: a claim for another selection id or scope key is not this row's claim, so its epoch (higher or lower) never makes it stale."""
    b = _binding()
    for edit_row in ({"selection_id": "sel-other"}, {"scope_key": DIGEST_A}, {"selection_id": "sel-other", "scope_key": DIGEST_A}):
        for delta in (-1, +1, +10):
            row = _row(b, **edit_row, selection_epoch=b["selection_epoch"] + delta)
            e = _refusal(m.compare_binding_identity, b, row)
            assert e.code == "policy_identity_mismatch", (edit_row, delta)
            assert e.member == ("selection_id" if "selection_id" in edit_row else "scope_key")
            assert m.mapping_row_for(e).verdict_class == "REFUSE"
    # the same claim against its OWN row (same scope key and selection id) with a higher row epoch is still definitively stale
    own = _row(b, selection_epoch=b["selection_epoch"] + 1)
    e = _refusal(m.compare_binding_identity, b, own)
    assert e.code == "selection_epoch_stale" and m.mapping_row_for(e).verdict_class == "REFUSE_STALE"
    # a claim from a moved selection id carrying a LOWER epoch than the row is a mismatch too (the mismatch is the cause, not the epoch)
    moved = {**b, "selection_id": "sel-moved", "selection_epoch": 1}
    assert _refusal(m.compare_binding_identity, moved, _row(b, selection_epoch=5)).code == "policy_identity_mismatch"
    # and through the ordered digest check
    assert _refusal(m.verify_carried_binding_digest, b, m.checked_binding_digest(b), _row(b, selection_id="sel-other", selection_epoch=b["selection_epoch"] + 1)).code == "policy_identity_mismatch"


def test_a_48_code_consumer_fails_closed_on_each_revision_2_code():
    """Amendment 1 6.7(d), simulated: a consumer holding only the revision-1 table (`CODES_V2`, 48) that receives a revision-2 code treats it as UNMAPPED, which
    is a refusal (never success, never an optional fallback, never remapped by text). The real consumer is outside this package; this is its stated rule."""
    from registry_successor.v2_codes import CODES_V2, CODES_V2_REV2

    def rev1_consumer(participation, registry_code):
        if registry_code in CODES_V2:  # known: its own mapping applies (not simulated)
            return "known"
        return "REFUSE_UNMAPPED"  # unknown to a 48-code table: fail closed, whatever the participation, no remap, no fallback

    for code in ("not_activated", "policy_identity_mismatch", "store_unknown"):
        assert code in CODES_V2_REV2 and code not in CODES_V2
        for participation in ("required", "optional"):
            assert rev1_consumer(participation, code) == "REFUSE_UNMAPPED", (code, participation)
    # the Registry's own revision-1 mapping surface agrees: the 48-code outcome map and the revision-1 table know none of the three
    import json
    base = json.loads((ROOT / "docs/p1-extraction-plan/data/ld02-outcome-map.json").read_text(encoding="utf-8"))["codes"]
    assert not {"not_activated", "policy_identity_mismatch", "store_unknown"} & set(base) and len(base) == 48
    # and the v1 decision path never lets one through as a success or an optional overlay
    from registry_successor import decision
    from types import SimpleNamespace
    for code in ("not_activated", "policy_identity_mismatch", "store_unknown"):
        for participation in ("required", "optional"):
            d = decision._decide_verified(participation, {}, None, SimpleNamespace(ok=False, code=code))
            assert d.code == "selection_missing" and d.operationally_authorized is False and d.kind != "applied"


def test_s1_order_row_key_then_epoch_then_remaining_members():
    """S-1 order pins: selection_id is reported before scope_key when both differ (whatever the epoch); a same-row stale epoch wins over every later member;
    a same-row claim epoch AHEAD of the row is a selection_epoch mismatch, reported before selection_digest."""
    b = _binding()
    both = _row(b, selection_epoch=b["selection_epoch"] + 5, selection_id="sel-other", scope_key=DIGEST_A)
    e = _refusal(m.compare_binding_identity, b, both)
    assert (e.code, e.member) == ("policy_identity_mismatch", "selection_id")
    behind = _row(b, selection_epoch=b["selection_epoch"] + 1, selection_digest=DIGEST_A, record_digest=DIGEST_B, activation_ref=DIGEST_B)
    e = _refusal(m.compare_binding_identity, b, behind)
    assert e.code == "selection_epoch_stale" and dict(e.evidence) == {"selection_epoch": b["selection_epoch"], "high_water_epoch": b["selection_epoch"] + 1}
    ahead = _row(b, selection_epoch=b["selection_epoch"] - 1, selection_digest=DIGEST_A)
    e = _refusal(m.compare_binding_identity, b, ahead)
    assert (e.code, e.member) == ("policy_identity_mismatch", "selection_epoch")


def test_one_validated_copy_serves_the_digest_and_the_identity_check():
    """Review (Copilot) 1: a binding mutated by another thread between the digest check and the identity check cannot make the digest of A pass with the
    identity of B. The binding is validated ONCE; both checks read that private copy, so the caller's later mutation changes nothing."""
    b = _binding()
    digest, row = m.checked_binding_digest(b), _row(b)

    real = m.binding_digest
    seen = []

    def spy(doc):
        seen.append(doc)
        b["selection_id"] = "sel-mutated"  # the caller's object changes right after the first (and only) validation
        return real(doc)

    m.binding_digest = spy
    try:
        assert m.verify_carried_binding_digest(b, digest, row) == digest
    finally:
        m.binding_digest = real
    assert seen and all(d["selection_id"] != "sel-mutated" for d in seen)


def test_one_shot_min_epochs_is_refused_not_fingerprinted_as_empty():
    for floors in (iter([("sel-a", 3)]), (x for x in [("sel-a", 3)]), {("sel-a", 3)}, frozenset({("sel-a", 3)}), "ab", None, 5):
        e = _refusal(m.trust_snapshot_from_verified, _snap(min_epochs=floors))
        assert e.code == "trust_snapshot_invalid", floors
        assert _refusal(m.trust_snapshot_fingerprint_from_verified, _snap(min_epochs=floors)).code == "trust_snapshot_invalid"
    for floors in ({"sel-a": 3}, (("sel-a", 3),), [("sel-a", 3)]):
        assert m.trust_snapshot_from_verified(_snap(min_epochs=floors))["min_epochs"] == [["sel-a", 3]]


@pytest.mark.parametrize("code", ("store_unknown", "policy_identity_mismatch", "not_activated", "selection_missing", "trust_snapshot_invalid", "selection_expired"))
def test_projection_effect_for_accepts_only_the_three_projection_codes(code):
    for participation, state, det in (("optional", "permits_optional", "authenticated"), ("optional", "known", "authenticated"), ("required", "known", "n/a")):
        with pytest.raises(ValueError):
            m.projection_effect_for(code, participation, state, det)
    for ok in ("field_invalid", "family_unsupported", "contract_unsupported"):
        assert m.projection_effect_for(ok, "optional", "permits_optional", "unauthenticated")["fallback_permitted"] is False


def test_row_key_with_a_raising_eq_refuses_as_store_unknown_not_an_exception():
    class Evil(str):
        def __eq__(self, other):
            raise RuntimeError("hostile __eq__")

        __hash__ = str.__hash__

    b = _binding()
    row = _row(b)
    row[Evil("selection_id")] = row.pop("selection_id")
    assert _refusal(m.compare_binding_identity, b, row).code == "store_unknown"
    assert _refusal(m.verify_carried_binding_digest, b, m.checked_binding_digest(b), row).code == "store_unknown"


@pytest.mark.parametrize("text,ok", (("1", 1), ("2147483648", 2147483648), ("9007199254740991", 9007199254740991)))
def test_ingest_bound_accepts_the_representation_range(text, ok):
    assert m.trust_snapshot_from_verified(_snap(version=ok))["version"] == ok


@pytest.mark.parametrize("version", (0, -1, 2 ** 53, 10 ** 40, 10 ** 700, 7.0, "7", True, False, None, [7]))
def test_ingest_bound_refuses_before_authority_evaluation(version, monkeypatch):
    """N-10(c) (PR #35 SIB-004..013): refused at ingest as trust_snapshot_invalid, stage ingest, member trust_snapshot_version, before `_normalize_trust`."""
    from registry_successor import verify as vm
    calls = []
    monkeypatch.setattr(vm, "_normalize_trust", lambda t: calls.append(t))
    e = _refusal(m.trust_snapshot_from_verified, _snap(version=version))
    assert (e.code, e.stage, e.member) == ("trust_snapshot_invalid", "ingest", "trust_snapshot_version")
    assert calls == []  # authority evaluation never reached
    assert m.mapping_row_for(e).verdict_class == "REFUSE"
    assert _refusal(m.trust_snapshot_fingerprint_from_verified, _snap(version=version)).stage == "ingest"


def _sib_value(v):
    t = v["text_repeat"][0] * v["text_repeat"][1] if "text_repeat" in v else v["text"]
    rep = v["representation"]
    if rep == "int":
        return (10 ** len(t) - 1) // 9 * int(t[0]) if "text_repeat" in v else int(t)  # repeated-digit literals built arithmetically (no int-string conversion limit)
    return {"float": float, "string": str, "bool": lambda x: x == "true", "null": lambda x: None}[rep](t)


@pytest.mark.parametrize("vec", V["snapshot_version_ingest_bound"]["vectors"], ids=lambda v: v["id"])
def test_sib_vectors_drive_the_ingest_bound(vec, monkeypatch):
    """Merged PR #35 vectors SIB-001..013 against `trust_snapshot_from_verified`: accepted versions reach authority evaluation; every other representation is
    refused at ingest (code, stage and member as the vector states) BEFORE authority evaluation."""
    from registry_successor import verify as vm
    sec, exp = V["snapshot_version_ingest_bound"], vec["expected"]
    value = _sib_value(vec)
    reached = []
    real = vm._normalize_trust
    monkeypatch.setattr(vm, "_normalize_trust", lambda t: (reached.append(1), real(t))[1])
    if exp["result"] == "refuse":
        e = _refusal(m.trust_snapshot_from_verified, _snap(version=value))
        assert (e.code, e.stage, e.member) == (exp["code"], exp["stage"], exp["member"]) == (sec["code"], sec["stage"], sec["member"])
        assert reached == [] and exp["authority_evaluation_reached"] is False
    else:
        assert m.trust_snapshot_from_verified(_snap(version=value))["version"] == int(vec["text"])
        assert reached == [1]


def test_ingest_stage_and_member_are_diagnostic_metadata_never_digest_data():
    """Architect Batch 7: stage `ingest` and member `trust_snapshot_version` are typed diagnostic metadata on the refusal, not canonical digest data."""
    e = _refusal(m.trust_snapshot_from_verified, _snap(version=0))
    row = m.mapping_row_for(e)
    assert "member" in row.evidence_fields and "stage" in row.evidence_fields and "trust_snapshot_version" in row.evidence_fields
    good = m.trust_snapshot_from_verified(_snap())
    assert set(good) == set(m._SNAPSHOT_MEMBERS)  # the normalized snapshot (the fingerprint preimage) has no stage or member
    assert m.trust_snapshot_fingerprint(good) == TF001["expected"]["trust_snapshot_fingerprint"]  # unchanged after a refused ingest in the same process
    pre = m.canonical_json_bytes(good)
    assert b"ingest" not in pre and b'"member"' not in pre and b'"stage"' not in pre
    b = _binding()
    assert m.checked_binding_digest(b) == m.binding_digest(b) and b"ingest" not in m.canonical_binding_bytes(b)


def test_cross_row_substitution_is_the_identity_mismatch_never_stale_after_the_merge():
    b = _binding()
    for edit in ({"selection_id": "sel-other"}, {"scope_key": DIGEST_A}):
        row = _row(b, selection_epoch=b["selection_epoch"] + 9, **edit)
        for fn, args in ((m.compare_binding_identity, (b, row)), (m.verify_carried_binding_digest, (b, "sha256:" + "0" * 64, row))):
            e = _refusal(fn, *args)
            assert e.code == "policy_identity_mismatch" and e.code != "selection_epoch_stale"  # identity before digest too


def test_authoritative_row_is_copied_once_before_validation():
    """Review (Copilot) 1: the caller's row is mutated AFTER validation; the comparison still uses the validated private copy."""
    b = _binding()
    real_ok = m._authoritative_row_ok
    row = _row(b)

    def spy(r):
        ok = real_ok(r)
        row["selection_id"] = "sel-mutated"  # the caller mutates its own dict right after validation
        row["selection_epoch"] = b["selection_epoch"] + 9
        return ok

    m._authoritative_row_ok = spy
    try:
        assert m.compare_binding_identity(b, row) == m.checked_binding_digest(b)  # the copy matched; the later mutation is invisible
    finally:
        m._authoritative_row_ok = real_ok


def test_mappingproxy_of_a_one_shot_dict_subclass_keeps_its_floors():
    class OneShot(dict):
        used = False

        def items(self):
            if OneShot.used:
                return iter(())
            OneShot.used = True
            return iter(dict.items(self))

    OneShot.used = False
    snap = _snap(min_epochs=m.MappingProxyType(OneShot({"sel-a": 3})))
    assert m.trust_snapshot_from_verified(snap)["min_epochs"] == [["sel-a", 3]]
    OneShot.used = False
    assert m.trust_snapshot_fingerprint_from_verified(_snap(min_epochs=m.MappingProxyType(OneShot({"sel-a": 3})))) == m.trust_snapshot_fingerprint_from_verified(_snap(min_epochs={"sel-a": 3}))
    assert m.trust_snapshot_fingerprint_from_verified(_snap(min_epochs={"sel-a": 3})) != m.trust_snapshot_fingerprint_from_verified(_snap(min_epochs={}))


def _lists_payload(family, token):
    return {k: ([token] if i == 0 else []) for i, k in enumerate(m.IDENTITY_FAMILIES[family].members)}


def _classmap_payload(family, token):
    return {"class_status_max_age_seconds": {token: 5}}


def _tu_text(vec):
    return "".join(chr(int(cp, 16)) for cp in vec["code_points"]) * vec.get("repeat", 1)


def test_token_table_pin_and_fail_closed():
    import hashlib
    from registry_successor.v2_token_table import TABLE_BYTES
    assert TABLE_BYTES == (ROOT / "docs/ext-implementation/data/ext-s1-5-token-unicode-15.1-excluded-ranges.json").read_bytes()  # the embedded copy is the committed file
    assert hashlib.sha256(TABLE_BYTES).hexdigest() == m.TOKEN_TABLE_SHA256 == V["pins"]["token_unicode_table"]["sha256"]
    starts, ranges = m._load_token_table()
    assert len(ranges) == 713
    for bad in (TABLE_BYTES + b" ", TABLE_BYTES.replace(b'"0000"', b'"0001"', 1), b"", "text", None.__class__):
        with pytest.raises(RuntimeError):
            m._load_token_table(bad)


@pytest.mark.parametrize("vec", V["token_unicode"]["vectors"], ids=lambda v: v["id"])
def test_token_unicode_vectors_drive_both_production_validators_without_the_host_database(vec, monkeypatch):
    """Spec 6.1 / N-13: effective-list entries and F5 class names decide by the pinned table; `unicodedata` is poisoned to prove no dependence."""
    import unicodedata
    def poisoned(*a, **k):
        raise AssertionError("host Unicode database consulted")
    monkeypatch.setattr(unicodedata, "category", poisoned)
    monkeypatch.setattr(m.c, "valid_token", poisoned)
    text, want = _tu_text(vec), vec["expected"]["valid"]
    assert m.frozen_token_valid(text) is want
    from registry_successor.v2_policy_identity import IDENTITY_FAMILIES
    lists_family = next(k for k, r in IDENTITY_FAMILIES.items() if r.kind == "lists")
    classmap_family = next(k for k, r in IDENTITY_FAMILIES.items() if r.kind == "classmap")
    for family, mk in ((lists_family, lambda t: _lists_payload(lists_family, t)), (classmap_family, lambda t: _classmap_payload(classmap_family, t))):
        try:
            m.validate_effective_payload(family, mk(text))
            got = True
        except m.IdentityRefusal as e:
            assert e.code == "field_invalid"
            got = False
        assert got is want, (family, vec["id"])


def _bad_rows():
    b = _binding()
    good = _row(b)
    yield "none", None
    yield "a list", list(good.items())
    yield "a subclass", type("D", (dict,), {})(good)
    yield "empty", {}
    for k in m.POLICY_IDENTITY_MEMBER_VALUES:
        yield "missing " + k, {x: y for x, y in good.items() if x != k}
    yield "extra member", {**good, "high_water_epoch": 3}
    yield "non-str key", {**good, 1: 2}
    yield "epoch bool", {**good, "selection_epoch": True}
    yield "epoch zero", {**good, "selection_epoch": 0}
    yield "epoch over range", {**good, "selection_epoch": 2147483648}
    yield "epoch str", {**good, "selection_epoch": "3"}
    yield "record_version zero", {**good, "record_version": 0}
    yield "bad digest", {**good, "selection_digest": "sha256:xyz"}
    yield "upper digest", {**good, "activation_ref": "sha256:" + "A" * 64}
    yield "null activation_ref", {**good, "activation_ref": None}
    yield "bad id", {**good, "selection_id": "bad id"}
    yield "id subclass", {**good, "record_id": type("S", (str,), {})("rec-x")}


@pytest.mark.parametrize("label,row", list(_bad_rows()), ids=[x[0] for x in _bad_rows()])
def test_an_unusable_durable_row_is_store_unknown_never_a_match_and_never_a_fallback(label, row):
    e = _refusal(m.compare_binding_identity, _binding(), row)
    assert e.code == "store_unknown"
    row_map = m.mapping_row_for(e)
    assert row_map.verdict_class == "UNKNOWN_FAIL_CLOSED" and row_map.optional_overlay is False


def test_a_malformed_binding_is_refused_with_its_own_code_before_the_row_is_looked_at():
    b = _binding()
    assert _refusal(m.compare_binding_identity, {**b, "binding_profile": "ocs-policy-binding/2"}, _row(b)).code == "field_invalid"
    assert _refusal(m.compare_binding_identity, {**b, "selection_epoch": 0}, None).code == "field_invalid"  # the binding is checked first, even with an unusable row
    assert _refusal(m.compare_binding_identity, {k: v for k, v in b.items() if k != "activation_ref"}, _row(b)).code == "field_missing"
    assert _refusal(m.compare_binding_identity, {**b, "extra": 1}, _row(b)).code == "field_unknown"
    assert _refusal(m.compare_binding_identity, {**b, "activation_ref": None}, _row(b)).code == "field_type_invalid"


def test_the_six_ruled_members_are_the_declared_v1_binding_and_nothing_is_manufactured():
    b = _binding()
    assert set(m.POLICY_IDENTITY_MEMBER_VALUES) - {"scope_key"} <= set(b)  # every compared value is a member the declared binding version carries
    assert set(m.TOP_MEMBERS) >= set(m.POLICY_IDENTITY_MEMBER_VALUES) - {"scope_key"}
    assert len(m.TOP_MEMBERS) == 15 and "scope_key" not in m.TOP_MEMBERS  # the scope key is derived from the binding, never a 16th member
    assert len(m.POLICY_IDENTITY_MEMBER_SET) == 6 and "record" in m.POLICY_IDENTITY_MEMBER_SET


def test_verify_carried_binding_digest_validates_syntax_version_context_and_identity_before_the_digest_comparison():
    b = _binding()
    good = m.checked_binding_digest(b)
    wrong = "sha256:" + "0" * 64
    # integrity only, no identity (documented): unchanged behaviour
    assert m.verify_carried_binding_digest(b, good) == good
    assert _refusal(m.verify_carried_binding_digest, b, wrong).code == "digest_mismatch"
    # 1. syntax and version first
    assert _refusal(m.verify_carried_binding_digest, {**b, "binding_profile": "ocs-policy-binding/2"}, good, _row(b)).code == "field_invalid"
    assert _refusal(m.verify_carried_binding_digest, {**b, "record_version": "2"}, good, _row(b)).code == "field_type_invalid"
    # 2. then the carried digest's format
    assert _refusal(m.verify_carried_binding_digest, b, "sha256:ZZ", _row(b, selection_id="sel-other")).code == "field_invalid"
    assert _refusal(m.verify_carried_binding_digest, b, None, _row(b)).code == "field_invalid"
    # 3. then identity and context, BEFORE the digest comparison: a wrong digest does not hide an identity refusal, and a right digest does not hide one
    assert _refusal(m.verify_carried_binding_digest, b, wrong, _row(b, activation_ref=DIGEST_B)).code == "policy_identity_mismatch"
    assert _refusal(m.verify_carried_binding_digest, b, good, _row(b, activation_ref=DIGEST_B)).code == "policy_identity_mismatch"
    assert _refusal(m.verify_carried_binding_digest, b, wrong, _row(b, selection_epoch=b["selection_epoch"] + 1)).code == "selection_epoch_stale"
    assert _refusal(m.verify_carried_binding_digest, b, good, {}).code == "store_unknown"
    # 4. only then the comparison
    assert _refusal(m.verify_carried_binding_digest, b, wrong, _row(b)).code == "digest_mismatch"
    assert m.verify_carried_binding_digest(b, good, _row(b)) == good


# ------------------------------------------------------------------------------------------------------------ projection entry
def test_project_effective_policy_digest_validates_version_and_input_at_the_projection_stage():
    fam = "f4-control-plane-age-bounds"
    payload = {"status_max_age_seconds": 1, "approval_max_age_seconds": 2}
    assert m.project_effective_policy_digest(fam, payload) == m.effective_policy_digest(fam, payload)
    for contract in ("r08-v1", "r08-v2.1", "r08-v2-reasons/2", "", "R08-V2"):
        e = _refusal(m.project_effective_policy_digest, fam, payload, contract)
        assert (e.code, e.stage) == ("contract_unsupported", "projection"), contract
    for family in ("f9", "", "f4-control-plane-age-bounds "):
        e = _refusal(m.project_effective_policy_digest, family, payload)
        assert (e.code, e.stage) == ("family_unsupported", "projection"), family
    for contract in (None, 2, b"r08-v2", ["r08-v2"]):  # a non-string version is a type refusal at the shape stage, never a coercion and never a version match
        e = _refusal(m.project_effective_policy_digest, fam, payload, contract)
        assert e.code == "field_type_invalid" and e.stage is None, contract
    for family in (None, 1, b"f4", ["f4"]):
        e = _refusal(m.project_effective_policy_digest, family, payload)
        assert e.code == "field_type_invalid" and e.stage is None, family
    e = _refusal(m.project_effective_policy_digest, fam, {**payload, "status_max_age_seconds": 2 ** 31})
    assert (e.code, e.stage) == ("field_invalid", "projection")
    assert _refusal(m.project_effective_policy_digest, fam, {**payload, "extra": 1}).stage is None  # not a projection kind: shape stage


# ------------------------------------------------------------------------------------------------------------ N-12 (no fallback from a refusal)
def test_an_unknown_store_is_hold_for_every_participation_and_a_refused_projection_is_not_never_activated():
    for participation in ("required", "optional"):
        out = m.projection_effect(participation, "indeterminate", "authenticated")
        assert out["effect_outcome"] == "UNKNOWN_FAIL_CLOSED" and out["fallback_permitted"] is False
        assert out["decision_kind"] != "overlay_not_applied"
    # a refused projection with no authenticated determination never falls back, for any state
    for state in ("permits_optional", "never_activated", "unknown", None, "required"):
        out = m.projection_effect("optional", state, "unauthenticated")
        assert out["fallback_permitted"] is False and out["effect_outcome"] == "REFUSE", state
    # required participation always fails closed, even with a permitting determination
    assert m.projection_effect("required", "permits_optional", "authenticated")["fallback_permitted"] is False


def test_family_and_contract_unsupported_are_definitive_refusals_not_fallback_conditions():
    for code in ("family_unsupported", "contract_unsupported"):
        row = m.verdict_for(code)
        assert row.verdict_class == "REFUSE" and row.optional_overlay is False
        out = m.projection_effect_for(code, "optional", "permits_optional", "unauthenticated")
        assert out["fallback_permitted"] is False and out["effect_outcome"] == "REFUSE"
