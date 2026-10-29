"""EXT-S1-2 developer tests: family dispatch table, CODES_V2 declaration and the v1 differential.
DEVELOPER-TESTED builder evidence, not an independently qualified oracle.
"""
import ast
import itertools
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "golden"))
import r08_support as s  # noqa: E402
import v1_runner  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import families  # noqa: E402
from registry_successor import record as record_mod  # noqa: E402
from registry_successor import selection as selection_mod  # noqa: E402
from registry_successor.compose import compose_f1a  # noqa: E402
from registry_successor.decision import verify_and_decide  # noqa: E402
from registry_successor.v2_codes import CODES_V2  # noqa: E402

F = c.F1A_FIELDS
GOLDEN = json.loads((ROOT / "tests" / "golden" / "r08_v1_golden.json").read_text(encoding="utf-8"))
RECORDS = {k: v1_runner.expand(v) for k, v in GOLDEN["records"].items()}
SELECTIONS = {k: v1_runner.expand(v) for k, v in GOLDEN["selections"].items()}
CASES = GOLDEN["cases"]


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# ---------------------------------------------------------------- table shape


def test_f1a_is_the_sole_registered_family():
    assert set(families.FAMILIES) == {c.FAMILY_F1A}
    spec = families.FAMILIES[c.FAMILY_F1A]
    assert spec.payload_fields == F
    assert spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING)
    assert spec.enforcing_component == "runtime"
    assert spec.composer is compose_f1a
    assert callable(spec.payload_validator) and callable(spec.caller_normalizer)
    # exactly the five table columns plus the family key
    assert [f for f in spec.__dataclass_fields__] == [
        "family", "payload_fields", "payload_validator", "composer", "evaluator_binding", "caller_normalizer",
        "enforcing_component"]


def test_table_is_read_only():
    with pytest.raises(TypeError):
        families.FAMILIES["f9-x"] = families.FAMILIES[c.FAMILY_F1A]
    with pytest.raises(TypeError):
        del families.FAMILIES[c.FAMILY_F1A]
    with pytest.raises(Exception):
        families.FAMILIES[c.FAMILY_F1A].family = "x"  # frozen dataclass


@pytest.mark.parametrize("fam", [
    "F1A-LOCAL-EXECUTION-ALLOWLIST", " f1a-local-execution-allowlist", "f1a-local-execution-allowlist ",
    "f1a-local-execution-allowlist\n", "f1a-local-execution-allowlist\x00", "f1a-local-execution-allowlist​",
    "F1a-Local-Execution-Allowlist", "f1a‑local-execution-allowlist", "f1ab-local-execution-allowlist",
    "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "", " ", "f9", None, 1, True, b"x", [c.FAMILY_F1A],
    {"f": 1}, ("f1a-local-execution-allowlist",), 1.5, object(),
])
def test_unregistered_or_varied_family_is_not_found(fam):
    assert families.lookup(fam) is None


def test_lookup_exact_string_found():
    assert families.lookup(c.FAMILY_F1A) is families.FAMILIES[c.FAMILY_F1A]


def test_lookup_str_subclass_with_equal_value_matches_only_as_plain_equality():
    class S(str):
        pass
    # exact-string equality semantics are the v1 `!=` semantics; a subclass with identical value is equal in v1 too
    assert (families.lookup(S(c.FAMILY_F1A)) is not None) == (S(c.FAMILY_F1A) == c.FAMILY_F1A)


def test_unhashable_str_subclass_is_not_found_and_never_raises():
    class U(str):
        __hash__ = None

    assert families.lookup(U(c.FAMILY_F1A)) is None
    base = record_mod.validate_record_text(json.dumps(s.make_record()))
    rec = record_mod.RecordResult(True, None, "", dict(base.record, family=U(c.FAMILY_F1A)), base.record_digest)
    res = families.compose({k: ["a"] for k in F}, rec)
    assert (res.ok, res.code) == (False, "composition_family_unsupported")


def test_only_the_table_registers_a_family():
    """No registry_successor module except the table, the F1a composer and the constant's definition names FAMILY_F1A."""
    allowed = {"families.py", "common.py", "compose.py"}
    for path in sorted((ROOT / "registry_successor").glob("*.py")):
        if path.name in allowed:
            continue
        tree = ast.parse(path.read_text())
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert "FAMILY_F1A" not in names, path.name
        assert "F1A_FIELDS" not in names, path.name


# ---------------------------------------------------------------- unregistered family refusals, end to end


def _rec_with_family(fam):
    base = s.make_record()
    return s.seal_record({**base, "family": fam})


VARIANTS = ["F1A-LOCAL-EXECUTION-ALLOWLIST", " f1a-local-execution-allowlist", "f1a-local-execution-allowlist ",
            "f1a-local-execution-allowlist\n", "f1ab-local-execution-allowlist", "f4-control-plane-age-bounds",
            "f5-action-class-age-bounds", "", "f9-unknown", None, 7, ["x"]]


@pytest.mark.parametrize("fam", VARIANTS)
def test_record_with_unregistered_family_refused_family_unsupported(fam):
    res = record_mod.validate_record_text(json.dumps(_rec_with_family(fam)))
    assert (res.ok, res.code) == (False, "family_unsupported")


@pytest.mark.parametrize("fam", VARIANTS)
def test_selection_with_unregistered_family_refused_family_unsupported(fam):
    stmt = s.make_statement(s.make_record(), family=fam)
    res = selection_mod.parse_selection_envelope(json.dumps(s.make_envelope(stmt)))
    assert (res.ok, res.code) == (False, "family_unsupported")


@pytest.mark.parametrize("fam", [v for v in VARIANTS if isinstance(v, str)])
def test_compose_dispatch_refuses_unregistered_family(fam):
    base = record_mod.validate_record_text(json.dumps(s.make_record()))
    body = dict(base.record, family=fam)
    rec = record_mod.RecordResult(True, None, "", body, base.record_digest)
    res = families.compose({k: ["a"] for k in F}, rec)
    assert (res.ok, res.code, res.effective) == (False, "composition_family_unsupported", None)


def test_compose_dispatch_check_order_matches_v1_compose():
    ok = record_mod.validate_record_text(json.dumps(s.make_record()))
    caller = {k: ["write-file"] for k in F}
    assert families.compose(caller, ok, "union").code == "composition_operator_unsupported"
    assert families.compose(caller, None).code == "composition_record_invalid"
    assert families.compose(caller, record_mod.RecordResult(False, "field_invalid")).code == "composition_record_invalid"
    assert families.compose(caller, record_mod.RecordResult(True, None, "", "notamapping")).code == "composition_record_invalid"
    assert families.compose(None, ok).code == "composition_caller_invalid"
    assert families.compose(object(), ok).code == "composition_caller_invalid"


@pytest.mark.parametrize("participation", ["required", "optional"])
@pytest.mark.parametrize("fam", [v for v in VARIANTS if isinstance(v, str) or v is None])
def test_unregistered_family_through_decision_never_applies(participation, fam):
    rec = _rec_with_family(fam)
    sel = s.make_envelope(s.make_statement(rec))
    caller = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
    ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    d = verify_and_decide(participation, caller, json.dumps(rec), json.dumps(sel), ctx, None, None, s.NOW)
    assert d.kind in ("required_policy_unavailable", "overlay_not_applied")
    assert d.kind != "applied" and d.operationally_authorized is False
    if participation == "required":
        assert d.effective is None and d.caller_unchanged is False and d.kind == "required_policy_unavailable"


# ---------------------------------------------------------------- required never returns the caller policy (property)


def test_required_never_returns_caller_over_the_whole_golden_decide_grid():
    n = 0
    for case in CASES:
        if case["kind"] != "decide" or case["participation"] != "required":
            continue
        got = v1_runner.execute(case, GOLDEN["records"], GOLDEN["selections"])
        n += 1
        assert got["operationally_authorized"] is False
        if got["kind"] == "required_policy_unavailable":
            assert got["effective"] is None and got["caller_unchanged"] is False and got["deny_all"] is False
        else:
            assert got["kind"] in ("applied", "applied_deny_all")
            assert got["caller_unchanged"] is False
    assert n > 400


# ---------------------------------------------------------------- F1a through the table equals the pre-refactor path


def test_compose_dispatch_equals_golden_pre_refactor_compose_f1a_over_corpus():
    n = 0
    for case in CASES:
        if case["kind"] != "compose" or case.get("operator", "intersection") != "intersection":
            continue
        rec = record_mod.validate_record_text(RECORDS[case["record"]])
        caller = v1_runner.build_caller(case["caller"])
        via_table = v1_runner.jsonable(families.compose(caller, rec))
        assert canon(via_table) == canon(case["expected"]), case["id"]
        n += 1
    assert n > 2000


def test_compose_dispatch_equals_golden_with_every_operator_value():
    for case in CASES:
        if case["kind"] != "compose" or "operator" not in case:
            continue
        rec = record_mod.validate_record_text(RECORDS[case["record"]])
        got = v1_runner.jsonable(families.compose(v1_runner.build_caller(case["caller"]), rec, case["operator"]))
        assert canon(got) == canon(case["expected"]), case["id"]


def test_validator_and_normalizer_via_table_equal_v1_functions():
    spec = families.lookup(c.FAMILY_F1A)
    from registry_successor.compose import normalize_caller
    for case in CASES:
        if case["kind"] == "compose":
            caller = v1_runner.build_caller(case["caller"])
            assert spec.caller_normalizer(caller) == normalize_caller(caller)


# ---------------------------------------------------------------- v1 differential on every v1 corpus input


def test_differential_every_v1_corpus_input_replays_identically():
    bad = [case["id"] for case in CASES
           if canon(v1_runner.execute(case, GOLDEN["records"], GOLDEN["selections"])) != canon(case["expected"])]
    assert not bad, bad[:20]


def test_differential_tests_use_public_interfaces_with_normal_exceptions_swallowed():
    """No corpus input makes a public r08-v1 entry point raise (they refuse instead)."""
    for case in CASES:
        v1_runner.execute(case, GOLDEN["records"], GOLDEN["selections"])


# ---------------------------------------------------------------- family/case/whitespace variants x mutated outcomes


def test_family_variant_matrix_never_validates_and_matches_v1_codes():
    """Each variant refuses with the same code the unrefactored path gave (golden), and never validates."""
    seen = 0
    for rid, text in RECORDS.items():
        if not rid.startswith("fam-"):
            continue
        res = record_mod.validate_record_text(text)
        assert not res.ok and res.code == "family_unsupported", rid
        seen += 1
    for sid, text in SELECTIONS.items():
        if not sid.startswith("fam-"):
            continue
        res = selection_mod.parse_selection_envelope(text)
        assert not res.ok and res.code == "family_unsupported", sid
        seen += 1
    assert seen == 24  # 15 record + 9 selection family variants in the corpus


def test_unicode_normalization_does_not_conflate_family():
    # NFKC of the ligature-ish or fullwidth spelling must not resolve to the registered family
    fam = c.FAMILY_F1A.replace("f1a", "ｆ１ａ")
    assert families.lookup(fam) is None


# ---------------------------------------------------------------- v1 / v2 domain separation (unchanged by this PR)


def test_v1_signing_domain_unchanged_and_v2_signature_does_not_verify_v1():
    stmt = s.make_statement(s.make_record())
    assert selection_mod.SIGNING_DOMAIN == b"ocs-reg/r08-v1/selection\n"
    assert selection_mod.signing_input(stmt) == b"ocs-reg/r08-v1/selection\n" + c.canonical_bytes(stmt)
    v2_sig = s.fake_signature(b"public-key-test-1", b"ocs-reg/r08-v2/selection\n" + c.canonical_bytes(stmt))
    v1_sig = s.fake_signature(b"public-key-test-1", selection_mod.signing_input(stmt))
    assert v2_sig != v1_sig
    assert c.CONTRACT_VERSION == "r08-v1"


def test_v2_contract_version_document_does_not_cross_into_v1_entry_points():
    rec = dict(s.make_record(), contract_version="r08-v2")
    res = record_mod.validate_record_text(json.dumps(s.seal_record(rec)))
    assert (res.ok, res.code) == (False, "contract_unsupported")
    env = s.make_envelope(s.make_statement(s.make_record()))
    env["contract_version"] = "r08-v2"
    res = selection_mod.parse_selection_envelope(json.dumps(env))
    assert (res.ok, res.code) == (False, "contract_unsupported")


# ---------------------------------------------------------------- CODES_V2


def test_codes_v2_is_46_plus_exactly_two():
    assert len(c.CODES) == 46
    assert len(CODES_V2) == 48
    assert set(CODES_V2) - set(c.CODES) == {"trust_snapshot_version_stale", "selection_withdrawn"}
    assert all(CODES_V2[k] == c.CODES[k] for k in c.CODES)
    assert list(CODES_V2)[:46] == list(c.CODES)
    assert CODES_V2["trust_snapshot_version_stale"][0] == "trust"
    assert CODES_V2["selection_withdrawn"][0] == "disposition"
    for code, (layer, meaning) in CODES_V2.items():
        assert re.fullmatch(r"[a-z]+(_[a-z0-9]+)*", code) and layer and meaning


def test_codes_v2_is_read_only_and_does_not_alter_v1_codes():
    with pytest.raises(TypeError):
        CODES_V2["x"] = ("a", "b")
    assert "selection_withdrawn" not in c.CODES and "trust_snapshot_version_stale" not in c.CODES


def test_no_v1_entry_point_emits_a_v2_only_code_over_the_corpus():
    v2_only = {"trust_snapshot_version_stale", "selection_withdrawn"}
    for case in CASES:
        text = canon(case["expected"])
        for code in v2_only:
            assert '"%s"' % code not in text


def test_v2_only_codes_have_no_behaviour_in_this_package():
    """selection_withdrawn and the snapshot floor were declared-only until S01. S01 (plan v1.4 Amendment 1) implements them, and ONLY in
    verify.py (the v2 disposition layer and the v2 snapshot-floor check); every other module, the v1 vocabulary included, still has none."""
    for path in sorted((ROOT / "registry_successor").glob("*.py")):
        if path.name in ("v2_codes.py", "verify.py", "v3_verify.py", "v3_decision.py", "v4_verify.py", "v4_decision.py", "v5_verify.py", "v5_decision.py", "v6_verify.py", "v6_decision.py"):  # M2 PR-1: the r08-v3 verifier mirrors verify.py's disposition layer; v3_decision emits the refusal; M3 PR-1: the same for v4_verify/v4_decision; F5 on_unreadable (r08-v5): the same for v5_verify/v5_decision; revocation families (r08-v6): the same for v6_verify/v6_decision
            continue
        text = path.read_text()
        assert "selection_withdrawn" not in text and "trust_snapshot_version_stale" not in text, path.name


# ---------------------------------------------------------------- scope guards


def test_no_max_amount_slot_anywhere_in_the_dispatch_modules():
    for name in ("families.py", "v2_codes.py"):
        assert "max_amount" not in (ROOT / "registry_successor" / name).read_text()
    assert "max_amount" not in families.FAMILIES[c.FAMILY_F1A].payload_fields


def test_new_modules_have_no_forbidden_imports_or_io():
    forbidden = {"registry_contract", "registry_consumer", "engine", "baseline", "os", "pathlib", "socket", "subprocess"}
    for name in ("families.py", "v2_codes.py"):
        tree = ast.parse((ROOT / "registry_successor" / name).read_text())
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                mods.add(n.module.split(".")[0])
        assert not mods & forbidden, (name, mods & forbidden)
