"""R08-S01 spec-conformance cases for contract r08-v1 (docs/r08-s01-contract.md; catalogue docs/r08-s01/qualification-spec.md).

BUILDER-AUTHORED ORACLE PREPARATION, written BLIND to the implementation: only the contract text, `common.CODES`
and `tests/r08_support.py` were used to derive the expected results. This is NOT independent qualification and it is
not DEVELOPER-TESTED evidence about any particular module; the independent Tier 1 qualification lead is not yet
designated. Expectations must not be edited to make a failing case pass: a failure is either a spec ambiguity or an
implementation defect and is reported as a finding.

Where the contract text leaves the observable code ambiguous the case accepts the named alternatives and says so
(`ANY_OF`); such cases are listed in the spec under "Known ambiguities".
"""
import copy
import itertools
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import compose, decision, record, selection, verify  # noqa: E402

KEY, PK = "key-test-1", b"public-key-test-1"
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
DEFAULT = object()


def grant(**over):
    base = dict(consumer_id="consumer-test", tenant="tenant-a", institution="inst-a", authority_domain="domain-a", operation="op-test")
    base.update(over)
    return verify.AuthorityGrant(**base)


def trust(**over):
    base = dict(
        snapshot_id="trust-snap-test-1", version=1, valid_until="2026-12-31T00:00:00Z",
        issuers=(verify.IssuerEntry(key_id=KEY, issuer_id="issuer-test-1", alg="ed25519", public_key=PK, authority=(grant(),)),),
        revoked_key_ids=frozenset(), revoked_selections=frozenset(), min_epochs={},
    )
    base.update(over)
    return verify.TrustSnapshot(**base)


def rec_result(obj=None):
    return record.validate_record_text(r.dumps(obj if obj is not None else r.make_record()))


def parse(statement=None, **env):
    signed = env.pop("signed", True)
    return selection.parse_selection_envelope(r.dumps(r.make_envelope(statement, signed=signed, key_id=env.pop("key_id", KEY), public_key=PK, **env)))


def pipeline(statement=None, record_obj=None, context=CTX, trust_obj=DEFAULT, verifier=DEFAULT, now=DEFAULT, binding=DEFAULT, **env):
    """(code, report). Parse and verify layers are both exercised; the first refusal in either wins (code None = verified)."""
    rec = rec_result(record_obj)
    statement = statement or r.make_statement(record_obj or r.make_record())
    sel = parse(statement, **env)
    if not sel.ok:
        return sel.code, None
    report = verify.verify_selection(
        sel, context, trust() if trust_obj is DEFAULT else trust_obj, r.FakeVerifier() if verifier is DEFAULT else verifier,
        r.NOW if now is DEFAULT else now, rec if binding is DEFAULT else binding)
    return report.code, report


def norm(effective):
    return {k: tuple(sorted(v)) for k, v in effective.items()}


F = c.F1A_FIELDS
LAYERS = ("structural", "integrity", "record_binding", "trust_snapshot", "authenticity", "authority", "scope", "time", "revocation", "epoch")


def reseal(**payload_or_top):
    body = copy.deepcopy(r.make_record())
    body.pop("payload_digest"), body.pop("record_digest")
    body.update(payload_or_top)
    return r.seal_record(body)


def with_payload(**fields):
    body = copy.deepcopy(r.make_record())
    body["payload"].update(fields)
    return r.seal_record(body)


# ---------------------------------------------------------------- QR: records
def test_QR01_valid_record():
    res = rec_result()
    assert res.ok and res.code is None and res.record_digest == r.make_record()["record_digest"]


@pytest.mark.parametrize("fields", [{"allowed_units": []}, {"allowed_actions": []}, {"allowed_adapters": []},
                                    {"allowed_units": [], "allowed_actions": [], "allowed_adapters": []}], ids=["QR02a-units", "QR02b-actions", "QR02c-adapters", "QR02d-all"])
def test_QR02_empty_list_is_valid_deny_all(fields):
    assert rec_result(with_payload(**fields)).ok


def _drop(field):
    body = copy.deepcopy(r.make_record())
    del body["payload"][field]
    return r.seal_record(body)


RECORD_REFUSALS = [
    ("QR03-missing-field", _drop("allowed_units"), {"field_missing"}),
    ("QR04-unknown-payload-field", with_payload(allowed_extra=["x"]), {"field_unknown"}),
    ("QR05-unknown-top-field", reseal(extra="x"), {"field_unknown"}),
    ("QR06-status-field-absent-by-design", reseal(status="active"), {"field_unknown"}),
    ("QR07-contract-version", reseal(contract_version="s03-v1"), {"contract_unsupported"}),
    ("QR08-kind", reseal(kind="selection"), {"kind_unsupported"}),
    ("QR09-family", reseal(family="f1b-other"), {"family_unsupported"}),
    ("QR10-unsorted", with_payload(allowed_units=["unit-b", "unit-a"]), {"field_invalid"}),
    ("QR11-duplicates", with_payload(allowed_units=["unit-a", "unit-a"]), {"field_invalid"}),
    ("QR12-wildcard", with_payload(allowed_units=["unit-*"]), {"field_invalid"}),
    ("QR13-too-many", with_payload(allowed_units=sorted("u%04d" % i for i in range(257))), {"field_invalid"}),
    ("QR14-entry-too-long", with_payload(allowed_units=["u" * 129]), {"field_invalid"}),
    ("QR15-control-char", with_payload(allowed_units=["a\x01b"]), {"field_invalid"}),
    ("QR16-space-char", with_payload(allowed_units=["a b"]), {"field_invalid"}),
    ("QR17-empty-entry", with_payload(allowed_units=[""]), {"field_invalid"}),
    ("QR18-list-not-list", with_payload(allowed_units="unit-a"), {"field_type_invalid"}),
    ("QR19-non-authorizing-false", reseal(non_authorizing=False), {"field_invalid"}),
    ("QR20-evaluator-id", reseal(evaluator={**r.EVALUATOR, "evaluator_id": "other.evaluator"}), {"evaluator_unsupported"}),
    ("QR21-evaluator-binding", reseal(evaluator={**r.EVALUATOR, "binding": "dynamic-script"}), {"evaluator_unsupported"}),
    ("QR22-version-zero", reseal(record_version=0), {"field_invalid"}),
    ("QR23-version-bool", reseal(record_version=True), {"field_type_invalid", "field_invalid"}),
    ("QR24-supersedes-higher-version", reseal(supersedes={"record_id": "f1a-test-record", "record_version": 5, "record_digest": "sha256:" + "0" * 64}), {"supersession_invalid"}),
    ("QR25-supersedes-other-id", reseal(supersedes={"record_id": "f1a-other-record", "record_version": 1, "record_digest": "sha256:" + "0" * 64}), {"supersession_invalid"}),
    ("QR26-bad-timestamp", reseal(provenance={"decision_ref": "decision-test-1", "authored_at": "2026-10-25", "authored_by": "x"}), {"field_invalid"}),
]


@pytest.mark.parametrize("obj,codes", [(o, k) for _, o, k in RECORD_REFUSALS], ids=[i for i, _, _ in RECORD_REFUSALS])
def test_QR_refusals(obj, codes):
    res = rec_result(obj)
    assert not res.ok and res.code in codes


def test_QR27_digest_mismatch_payload_and_record():
    body = r.make_record()
    body["payload"]["allowed_units"] = ["unit-a"]
    assert rec_result(body).code == "digest_mismatch"
    body = r.make_record()
    body["record_digest"] = "sha256:" + "1" * 64
    assert rec_result(body).code == "digest_mismatch"


def test_QR28_integrity_is_not_authentication():
    forged = with_payload(allowed_units=["unit-evil"])  # re-sealed by an attacker: a valid digest, no authority
    res = rec_result(forged)
    assert res.ok and not hasattr(res, "authenticated")


def test_QR29_parse_level_refusals():
    text = r.dumps(r.make_record())
    assert record.validate_record_text(text.replace('"record_version": 1', '"record_version": 1, "record_version": 2')).code == "json_duplicate_key"
    assert record.validate_record_text("x" * 70000).code == "input_too_large"
    assert record.validate_record_text("{not json").code == "json_malformed"
    assert record.validate_record_text(b"{}").code == "input_not_text"
    assert record.validate_record_text(text.replace('"record_version": 1', '"record_version": 1.5')).code == "json_number_unsupported"
    assert record.validate_record_text("[" * 9 + "1" + "]" * 9).code == "json_nesting_too_deep"
    assert record.validate_record_text('{"a":"\ud800"}').code == "input_not_text"


def test_QR30_corrupted_source_bytes():
    text = r.dumps(r.make_record())
    assert record.validate_record_text(text.replace("unit-b", "unit-c", 1)).code == "digest_mismatch"  # stays sorted, so only the digest layer can fail
    assert record.validate_record_text(text[:-5]).code == "json_malformed"


# ---------------------------------------------------------------- QS: selection structure
def test_QS01_valid_selection_parses():
    res = parse()
    assert res.ok and res.statement["selection_id"] == "sel-test-1" and res.statement_digest == r.make_envelope()["statement_digest"]


def _stmt_without(field):
    s = r.make_statement()
    del s[field]
    return s


SELECTION_REFUSALS = [
    ("QS02-unknown-statement-field", r.make_statement(extra="x"), {}, {"field_unknown"}),
    ("QS03-missing-statement-field", _stmt_without("operation"), {}, {"field_missing"}),
    ("QS04-epoch-zero", r.make_statement(epoch=0), {}, {"field_invalid"}),
    ("QS05-epoch-bool", r.make_statement(epoch=True), {}, {"field_type_invalid", "field_invalid"}),
    ("QS06-bad-participation", r.make_statement(participation="maybe"), {}, {"field_invalid"}),
    ("QS07-inverted-interval", r.make_statement(effective={"valid_from": "2026-10-26T00:00:00Z", "valid_until": "2026-10-25T00:00:00Z"}), {}, {"field_invalid"}),
    ("QS08-equal-interval", r.make_statement(effective={"valid_from": "2026-10-25T00:00:00Z", "valid_until": "2026-10-25T00:00:00Z"}), {}, {"field_invalid"}),
    ("QS09-perpetual-null", r.make_statement(effective={"valid_from": "2026-10-25T00:00:00Z", "valid_until": None}), {}, {"field_type_invalid", "field_invalid"}),
    ("QS10-missing-valid-until", r.make_statement(effective={"valid_from": "2026-10-25T00:00:00Z"}), {}, {"field_missing"}),
    ("QS11-bad-timestamp", r.make_statement(effective={"valid_from": "2026-10-25 00:00:00", "valid_until": "2026-10-26T00:00:00Z"}), {}, {"field_invalid"}),
    ("QS12-wildcard-scope", r.make_statement(scope={"tenant": "*", "institution": "inst-a", "authority_domain": "domain-a"}), {}, {"field_invalid"}),
    ("QS13-supersedes-no-decision-ref", r.make_statement(epoch=2, supersedes={"selection_id": "sel-test-1", "epoch": 1, "statement_digest": "sha256:" + "0" * 64}), {}, {"selection_supersession_invalid"}),  # expectation changed after spec clarification (contract section 3a), see qualification-spec ambiguity 10
    ("QS14-supersedes-not-lower", r.make_statement(epoch=2, supersedes={"selection_id": "sel-test-1", "epoch": 2, "statement_digest": "sha256:" + "0" * 64, "decision_ref": "decision-x1"}), {}, {"selection_supersession_invalid", "field_invalid"}),
    ("QS15-supersedes-other-id", r.make_statement(epoch=2, supersedes={"selection_id": "sel-other-1", "epoch": 1, "statement_digest": "sha256:" + "0" * 64, "decision_ref": "decision-x1"}), {}, {"selection_supersession_invalid", "field_invalid"}),
    ("QS16-family", r.make_statement(family="f1b-other"), {}, {"family_unsupported"}),
    ("QS17-envelope-contract", r.make_statement(), {"contract_version": "s04-v1"}, {"contract_unsupported"}),
    ("QS18-envelope-kind", r.make_statement(), {"kind": "record"}, {"kind_unsupported"}),
    ("QS19-envelope-unknown-field", r.make_statement(), {"extra": 1}, {"field_unknown"}),
]


@pytest.mark.parametrize("stmt,env,codes", [(s, e, k) for _, s, e, k in SELECTION_REFUSALS], ids=[i for i, _, _, _ in SELECTION_REFUSALS])
def test_QS_refusals(stmt, env, codes):
    code, _ = pipeline(stmt, **env)
    assert code in codes


def test_QS20_statement_digest_mismatch():
    code, _ = pipeline(r.make_statement(), statement_digest="sha256:" + "0" * 64)
    assert code == "digest_mismatch"


def test_QS21_text_level_refusals():
    text = r.dumps(r.make_envelope())
    assert selection.parse_selection_envelope(text.replace('"epoch": 1', '"epoch": 1, "epoch": 2')).code == "json_duplicate_key"
    assert selection.parse_selection_envelope("x" * 70000).code == "input_too_large"
    assert selection.parse_selection_envelope(None).code == "input_not_text"
    assert selection.parse_selection_envelope(text[:-7]).code == "json_malformed"
    assert selection.parse_selection_envelope(text.replace('"epoch": 1', '"epoch": 1.0')).code == "json_number_unsupported"


# ---------------------------------------------------------------- QV: verification layers
def test_QV01_technically_verified_but_not_operationally_authorized():
    code, rep = pipeline()
    assert code is None and rep.ok and rep.authenticated
    assert rep.operationally_authorized is False
    assert set(rep.layers) == set(LAYERS) and all(v == "pass" for v in rep.layers.values())


def test_QV02_digest_match_is_not_authentication():
    code, rep = pipeline(verifier=None)
    assert code == "verifier_unavailable" and not rep.ok and not rep.authenticated and rep.operationally_authorized is False
    code, rep = pipeline(signed=False)
    assert code == "signature_missing" and not rep.authenticated


def test_QV03_unavailable_trust_root_and_time():
    assert pipeline(trust_obj=None)[0] == "trust_snapshot_missing"
    assert pipeline(now=None)[0] == "time_unavailable"
    assert pipeline(trust_obj=trust(valid_until="2026-10-25T11:59:59Z"))[0] == "trust_snapshot_expired"


def test_QV04_untrusted_issuer_and_key():
    assert pipeline(trust_obj=trust(issuers=()))[0] == "issuer_untrusted"
    assert pipeline(key_id="key-unknown-9")[0] == "issuer_untrusted"
    assert pipeline(trust_obj=trust(revoked_key_ids=frozenset({KEY})))[0] == "issuer_key_revoked"


def test_QV05_invalid_signature_and_algorithm():
    env = r.make_envelope()
    env["signatures"][0]["signature"] = r.fake_signature(PK, b"another message")
    sel = selection.parse_selection_envelope(r.dumps(env))
    assert verify.verify_selection(sel, CTX, trust(), r.FakeVerifier(), r.NOW, rec_result()).code == "signature_invalid"
    env["signatures"][0]["signature"] = "!!not-base64!!"
    sel = selection.parse_selection_envelope(r.dumps(env))
    res = verify.verify_selection(sel, CTX, trust(), r.FakeVerifier(), r.NOW, rec_result()) if sel.ok else sel
    assert not res.ok and res.code in {"signature_invalid", "field_invalid"}
    env = r.make_envelope()
    env["signatures"][0]["alg"] = "rsa"
    sel = selection.parse_selection_envelope(r.dumps(env))
    res = verify.verify_selection(sel, CTX, trust(), r.FakeVerifier(), r.NOW, rec_result()) if sel.ok else sel
    assert not res.ok and res.code in {"signature_algorithm_unsupported", "field_invalid"}


def test_QV06_issuer_authority_is_exact():
    for over in ({"consumer_id": "consumer-x1"}, {"tenant": "tenant-b"}, {"institution": "inst-b"}, {"authority_domain": "domain-b"}, {"operation": "op-other"}):
        issuers = (verify.IssuerEntry(key_id=KEY, issuer_id="issuer-test-1", alg="ed25519", public_key=PK, authority=(grant(**over),)),)
        assert pipeline(trust_obj=trust(issuers=issuers))[0] == "issuer_not_authorized", over
    assert pipeline(trust_obj=trust(issuers=(verify.IssuerEntry(key_id=KEY, issuer_id="issuer-test-1", alg="ed25519", public_key=PK, authority=()),)))[0] == "issuer_not_authorized"


@pytest.mark.parametrize("ctx,code", [
    (c.ExpectedContext("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch"),
], ids=["QV07a-consumer", "QV07b-tenant", "QV07c-institution", "QV07d-authority-domain", "QV07e-operation"])
def test_QV07_scope_mismatch(ctx, code):
    got, rep = pipeline(context=ctx)
    assert got == code and not rep.ok


@pytest.mark.parametrize("hour_offset,code", [(-1, "selection_not_yet_effective"), (0, None), (86399, None), (86400, "selection_expired"), (86401, "selection_expired")],
                         ids=["QV08a-1s-before-from", "QV08b-at-from", "QV08c-1s-before-until", "QV08d-at-until", "QV08e-after-until"])
def test_QV08_exact_boundary_instants(hour_offset, code):
    import datetime
    start = datetime.datetime(2026, 10, 25, 0, 0, 0, tzinfo=datetime.timezone.utc)
    now = start + datetime.timedelta(seconds=hour_offset)
    assert pipeline(now=now)[0] == code


def test_QV09_stale_epoch_floor():
    assert pipeline(trust_obj=trust(min_epochs={"sel-test-1": 2}))[0] == "selection_epoch_stale"
    assert pipeline(trust_obj=trust(min_epochs={"sel-test-1": 1}))[0] is None


def test_QV10_revoked_selection():
    assert pipeline(trust_obj=trust(revoked_selections=frozenset({("sel-test-1", 1)})))[0] == "selection_revoked"
    assert pipeline(trust_obj=trust(revoked_selections=frozenset({("sel-test-1", 2)})))[0] is None


def test_QV11_record_binding():
    base = r.make_record()
    sel_stmt = r.make_statement(base)
    other_version = r.make_record(record_version=2)
    assert pipeline(sel_stmt, record_obj=other_version)[0] == "record_identity_mismatch"
    other_id = r.make_record(record_id="f1a-other-record")
    assert pipeline(sel_stmt, record_obj=other_id)[0] == "record_identity_mismatch"
    other_payload = with_payload(allowed_units=["unit-a"])
    assert pipeline(sel_stmt, record_obj=other_payload)[0] == "record_digest_mismatch"
    other_eval = r.make_record(evaluator={**r.EVALUATOR, "source_blob_id": "0" * 40})
    stmt = r.make_statement(other_eval, evaluator=dict(r.EVALUATOR))
    assert pipeline(stmt, record_obj=other_eval)[0] == "evaluator_mismatch"


def test_QV12_failed_parse_never_verifies():
    bad = selection.parse_selection_envelope("{")
    rep = verify.verify_selection(bad, CTX, trust(), r.FakeVerifier(), r.NOW, rec_result())
    assert not rep.ok and rep.operationally_authorized is False


# ---------------------------------------------------------------- QC: effective selection / conflicts
def sel_with(**over):
    return parse(r.make_statement(**over))


def test_QC01_empty_and_foreign_context():
    assert selection.resolve_effective([], CTX, r.NOW).code == "selection_missing"
    other = sel_with(scope={"tenant": "tenant-z", "institution": "inst-a", "authority_domain": "domain-a"})
    assert selection.resolve_effective([other], CTX, r.NOW).code == "selection_missing"


def test_QC02_two_selections_conflict():
    a, b = sel_with(), sel_with(selection_id="sel-test-2")
    res = selection.resolve_effective([a, b], CTX, r.NOW)
    assert not res.ok and res.code == "selection_conflict"


def test_QC03_higher_epoch_alone_does_not_supersede():
    res = selection.resolve_effective([sel_with(), sel_with(epoch=2)], CTX, r.NOW)
    assert not res.ok and res.code == "selection_conflict"


def test_QC04_explicit_supersession_resolves():
    old = sel_with()
    new = sel_with(epoch=2, supersedes={"selection_id": "sel-test-1", "epoch": 1, "statement_digest": old.statement_digest, "decision_ref": "decision-approve-2"})
    res = selection.resolve_effective([old, new], CTX, r.NOW)
    assert res.ok and res.selected.statement["epoch"] == 2


def test_QC05_supersession_with_wrong_digest_refuses():
    old = sel_with()
    new = sel_with(epoch=2, supersedes={"selection_id": "sel-test-1", "epoch": 1, "statement_digest": "sha256:" + "0" * 64, "decision_ref": "decision-approve-2"})
    res = selection.resolve_effective([old, new], CTX, r.NOW)
    assert not res.ok and res.code in {"selection_supersession_invalid", "selection_conflict"}


def test_QC06_out_of_window_selection_is_not_effective():
    expired = sel_with(effective={"valid_from": "2026-10-20T00:00:00Z", "valid_until": "2026-10-21T00:00:00Z"})
    res = selection.resolve_effective([expired, sel_with(selection_id="sel-test-2")], CTX, r.NOW)
    assert res.ok and res.selected.statement["selection_id"] == "sel-test-2"


# ---------------------------------------------------------------- QD: composition and deny-all
CALLER = {"allowed_actions": ["read-file", "write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a", "unit-c"]}


def test_QD01_intersection():
    res = compose.compose_f1a(CALLER, rec_result())
    assert res.ok and norm(res.effective) == {"allowed_actions": ("write-file",), "allowed_adapters": ("local-fs",), "allowed_units": ("unit-a",)}
    assert not res.deny_all and not res.deny_all_fields


@pytest.mark.parametrize("field", F)
def test_QD02_empty_intersection_is_valid_deny_all(field):
    caller = dict(CALLER)
    caller[field] = ["zzz-not-in-record"]
    res = compose.compose_f1a(caller, rec_result())
    assert res.ok and res.deny_all and field in res.deny_all_fields and norm(res.effective)[field] == ()


def test_QD03_registry_empty_list_is_deny_all():
    res = compose.compose_f1a(CALLER, rec_result(with_payload(allowed_units=[])))
    assert res.ok and res.deny_all and res.deny_all_fields == ("allowed_units",)


def test_QD04_never_widens_over_a_full_grid():
    universe = ["unit-a", "unit-b", "unit-c"]
    subsets = [list(s) for n in range(4) for s in itertools.combinations(universe, n)]
    for caller_units, reg_units in itertools.product(subsets, subsets):
        caller = dict(CALLER, allowed_units=caller_units)
        res = compose.compose_f1a(caller, rec_result(with_payload(allowed_units=reg_units)))
        assert res.ok
        got = set(norm(res.effective)["allowed_units"])
        assert got == set(caller_units) & set(reg_units) and got <= set(caller_units) and got <= set(reg_units)


def test_QD05_unsupported_operator_and_family():
    for op in ("union", "latest", "", "newest"):
        assert compose.compose_f1a(CALLER, rec_result(), operator=op).code == "composition_operator_unsupported", op
    body = copy.deepcopy(r.make_record())
    body["family"] = "f1b-other"
    foreign = SimpleNamespace(ok=True, code=None, detail="", record=body, record_digest=body["record_digest"])
    res = compose.compose_f1a(CALLER, foreign)
    assert not res.ok and res.code in {"composition_family_unsupported", "composition_record_invalid"}


def test_QD06_invalid_record_and_caller():
    assert compose.compose_f1a(CALLER, rec_result(reseal(extra="x"))).code == "composition_record_invalid"
    for bad in ({"allowed_actions": ["a"], "allowed_adapters": ["b"]},
                dict(CALLER, extra=["x"]),
                dict(CALLER, allowed_units="unit-a"),
                dict(CALLER, allowed_units=[1, 2]),
                None):
        assert compose.compose_f1a(bad, rec_result()).code == "composition_caller_invalid"


# ---------------------------------------------------------------- QP: per-operation outcomes, no silent fallback
# A1 amendment: decisions go through the single verify_and_decide entrypoint; there is no public report-taking interface.
def vd(participation, caller=CALLER, record_obj=None, statement=DEFAULT, record_text=DEFAULT, trust_obj=DEFAULT,
       verifier=DEFAULT, now=DEFAULT, signed=True):
    record_obj = record_obj if record_obj is not None else r.make_record()
    stmt = r.make_statement(record_obj, participation=participation) if statement is DEFAULT else statement
    sel_text = None if stmt is None else r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=signed))
    return decision.verify_and_decide(
        participation, caller, r.dumps(record_obj) if record_text is DEFAULT else record_text, sel_text, CTX,
        trust() if trust_obj is DEFAULT else trust_obj, r.FakeVerifier() if verifier is DEFAULT else verifier,
        r.NOW if now is DEFAULT else now)


def test_QP01_applied_and_applied_deny_all():
    d = vd("required")
    assert d.kind == "applied" and norm(d.effective)["allowed_units"] == ("unit-a",)
    d = vd("required", record_obj=with_payload(allowed_units=[]))
    assert d.kind == "applied_deny_all"


def failing_cases():
    return {
        "QP02a-missing-selection": dict(statement=None),
        "QP02b-untrusted": dict(trust_obj=trust(issuers=())),
        "QP02c-revoked": dict(trust_obj=trust(revoked_selections=frozenset({("sel-test-1", 1)}))),
        "QP02d-expired": dict(now=r.NOW.replace(day=27)),
        "QP02e-no-trust-root": dict(trust_obj=None),
        "QP02f-no-verifier": dict(verifier=None),
    }


@pytest.mark.parametrize("name", list(failing_cases()))
def test_QP02_required_never_falls_back_to_caller(name):
    d = vd("required", **failing_cases()[name])
    assert d.kind == "required_policy_unavailable" and d.code in c.CODES
    assert d.effective is None or norm(d.effective) != norm(CALLER)


@pytest.mark.parametrize("name", list(failing_cases()))
def test_QP03_optional_returns_caller_unchanged_and_is_not_denial(name):
    d = vd("optional", **failing_cases()[name])
    assert d.kind == "overlay_not_applied" and d.code in c.CODES
    assert norm(d.effective) == norm(CALLER) and not getattr(d, "deny_all", False)


def test_QP04_missing_selection_code_and_invalid_record():
    assert vd("required", statement=None).code == "selection_missing"
    assert vd("optional", statement=None).code == "selection_missing"
    bad = reseal(extra="x")
    d = vd("required", record_obj=r.make_record(), record_text=r.dumps(bad))
    assert d.kind == "required_policy_unavailable" and d.code in {rec_result(bad).code, "composition_record_invalid"}


def test_QP05_unsupported_composition_in_decision():
    d = vd("required", caller=dict(CALLER, extra=["x"]))
    assert d.kind == "required_policy_unavailable" and d.code == "composition_caller_invalid"
    d = vd("optional", caller=dict(CALLER, extra=["x"]))
    assert d.kind == "overlay_not_applied"


def test_QP06_taxonomy_is_closed():
    for name, kw in failing_cases().items():
        assert vd("required", **kw).code in c.CODES, name
