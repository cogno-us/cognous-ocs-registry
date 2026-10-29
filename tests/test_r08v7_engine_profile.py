"""The parameterised engine itself: profile validation and immutability, no hardwired contract, no mutable global, no drift from the frozen v6
orchestration, and a third (test-only) profile proving the engine is generic (BUILDER_TESTED; not independently qualified)."""
import ast
import collections
import dataclasses
import inspect
import re
import textwrap
import types
from pathlib import Path

import pytest

import r08_support as r
import r08v7_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import v2_codes
from registry_successor import v6_decision, v6_families, v6_verify, v7_decision, v7_families, v7_policy_identity
from registry_successor.engine import decide as decide_e
from registry_successor.engine import families_irreversibility as irr
from registry_successor.engine import identity as identity_e
from registry_successor.engine import profile as profile_e
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e
from registry_successor.engine import selection as selection_e
from registry_successor.engine import verify as verify_e
from registry_successor.engine.profile import ContractProfile, FamilyEntry, IdentityRow

ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "registry_successor" / "engine"
ENGINE_FILES = sorted(ENGINE_DIR.glob("*.py"))
V7, V6 = profiles.V7, profiles.V6_COMPAT
IRR = irr.FAMILY_IRREVERSIBILITY


def parts(profile=V7):
    return dict(version=profile.version, selection_signing_domain=profile.selection_signing_domain, effective_policy_domain=profile.effective_policy_domain,
                families=dict(profile.families), identity=dict(profile.identity))


# ---------------------------------------------------------------- shipped profiles
def test_v7_profile_content():
    assert V7.version == "r08-v7" and V7.selection_signing_domain == b"ocs-reg/r08-v7/selection\n" and V7.effective_policy_domain == b"ocs-reg/r08-v7/effective-policy\n"
    assert list(V7.families) == [IRR] and list(V7.identity) == [IRR]
    entry = V7.families[IRR]
    assert entry.schema_revision == 1 and type(entry.schema_revision) is int and entry.spec.enforcing_component == "control-plane"
    assert entry.spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING)
    assert entry.spec.payload_validator is irr.payload_validator and entry.spec.composer is irr.compose_irreversibility and entry.spec.caller_normalizer is irr.normalize_caller
    assert V7.identity[IRR].version_member == "family_schema_revision" and V7.identity[IRR].version_value == 1


def test_the_blocked_families_are_not_registered():
    for blocked in ("anchor_deadline_to_inputs", "f5-anchor-deadline-to-inputs-policy", "ObservationPolicy.max_age_seconds", "ObservationPolicy.clock_tolerance_seconds",
                    "f5-observation-max-age-policy", "f5-observation-clock-tolerance-policy"):
        assert blocked not in V7.families and v7_families.lookup_v7(blocked) is None
    assert len(V7.families) == 1


def test_v6_compat_is_built_from_the_existing_v6_tables_without_copying_them():
    assert V6.version == "r08-v6" and list(V6.families) == list(v6_families.FAMILIES_V6)
    for family, spec in v6_families.FAMILIES_V6.items():
        assert V6.families[family].spec is spec and V6.families[family].schema_revision is None
        row = V6.identity[family]
        assert row.version_member == "family_version" and row.version_value == "v6"


def test_the_two_shipped_profiles_have_distinct_domains_and_versions():
    assert len({V7.selection_signing_domain, V7.effective_policy_domain, V6.selection_signing_domain, V6.effective_policy_domain}) == 4
    assert profiles.PROFILES["r08-v7"] is V7 and profiles.PROFILES["r08-v6"] is V6 and set(profiles.PROFILES) == {"r08-v6", "r08-v7"}


# ---------------------------------------------------------------- immutability and validation
def test_profile_is_frozen_and_its_tables_are_immutable_views():
    with pytest.raises(dataclasses.FrozenInstanceError):
        V7.version = "r08-v9"
    with pytest.raises(dataclasses.FrozenInstanceError):
        V7.families = {}
    with pytest.raises(TypeError):
        V7.families[IRR] = V7.families[IRR]
    with pytest.raises(TypeError):
        V7.identity["x"] = V7.identity[IRR]
    with pytest.raises(TypeError):
        V7.specs["x"] = None
    with pytest.raises(dataclasses.FrozenInstanceError):
        V7.families[IRR].schema_revision = 2
    with pytest.raises(dataclasses.FrozenInstanceError):
        V7.identity[IRR].version_value = 2
    assert isinstance(V7.families, types.MappingProxyType) and isinstance(V7.identity, types.MappingProxyType)


def test_a_profile_copies_its_inputs_so_later_mutation_of_the_source_dicts_changes_nothing():
    p = parts()
    prof = ContractProfile(**p)
    p["families"].clear()
    p["identity"].clear()
    assert list(prof.families) == [IRR] and list(prof.identity) == [IRR]


@pytest.mark.parametrize("field,value", [
    ("version", "r08 v9"), ("version", ""), ("version", b"r08-v9"), ("version", None), ("version", "r08-v6"),  # domains carry r08-v7, version mismatch
    ("selection_signing_domain", b"ocs-reg/r08-v7/selection"), ("selection_signing_domain", "ocs-reg/r08-v7/selection\n"),
    ("selection_signing_domain", b"ocs-reg/r08-v6/selection\n"), ("effective_policy_domain", b"ocs-reg/r08-v7/selection\n"),
    ("effective_policy_domain", b"ocs-reg/r08-v6/effective-policy\n"), ("effective_policy_domain", None),
    ("families", {}), ("families", None), ("identity", {}), ("identity", None)])
def test_invalid_profile_construction_is_refused(field, value):
    p = parts()
    p[field] = value
    with pytest.raises(ValueError):
        ContractProfile(**p)


def test_profile_rejects_inconsistent_family_and_identity_tables():
    p = parts()
    # key / spec family mismatch
    spec_other = V6.families["f5-terminal-revocation-enablement-policy"]
    bad = parts()
    bad["families"] = {IRR: spec_other}
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    # revision mismatch between entry and identity row
    bad = parts()
    bad["families"] = {IRR: FamilyEntry(V7.families[IRR].spec, 2)}
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    for rev in (0, -1, True, "1", None, 1.0):
        bad = parts()
        bad["families"] = {IRR: FamilyEntry(V7.families[IRR].spec, rev)}
        bad["identity"] = {IRR: dataclasses.replace(V7.identity[IRR], version_value=rev)}
        with pytest.raises(ValueError):
            ContractProfile(**bad)
    # a tag row must not carry a revision and a revision row must not carry a tag
    bad = parts()
    bad["identity"] = {IRR: dataclasses.replace(V7.identity[IRR], version_member="family_version", version_value="v7")}
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    bad = parts(V6)
    bad["families"] = {k: FamilyEntry(e.spec, 1) for k, e in V6.families.items()}
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    bad = parts()
    bad["identity"] = {IRR: dataclasses.replace(V7.identity[IRR], version_member="other")}
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    # identity row members must equal the spec's payload fields; kind must be known; a family key mismatch
    for change in ({"members": ("other",)}, {"kind": "map"}, {"family": "x"}, {"is_value": None}):
        bad = parts()
        bad["identity"] = {IRR: dataclasses.replace(V7.identity[IRR], **change)}
        with pytest.raises(ValueError):
            ContractProfile(**bad)
    # key order of the two tables must agree
    bad = parts(V6)
    bad["identity"] = dict(reversed(list(V6.identity.items())))
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    assert ContractProfile(**p).specs == V7.specs  # a well-formed profile is accepted


def test_profile_rejects_wrongly_typed_table_members():
    spec = V7.families[IRR].spec
    bad = parts()
    bad["families"] = {IRR: spec}  # a bare FamilySpec is not a FamilyEntry
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    bad = parts()
    bad["families"] = {IRR: FamilyEntry(spec, True)}  # a bool is not a revision, even when the identity row says 1
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    bad = parts()
    bad["families"] = {IRR: FamilyEntry(dataclasses.replace(spec, family="other-family"), 1)}  # the spec must be registered under its own family id
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    bad = parts()
    bad["families"] = {"other-family": V7.families[IRR]}
    bad["identity"] = {"other-family": dataclasses.replace(V7.identity[IRR], family="other-family")}
    with pytest.raises(ValueError):
        ContractProfile(**bad)
    bad = parts()
    bad["identity"] = {IRR: V7.identity[IRR].version_value}
    with pytest.raises(ValueError):
        ContractProfile(**bad)


def test_the_dispatch_itself_enforces_record_validity_operator_and_family_even_for_a_composer_that_does_not():
    """A family composer that never re-checks its input must still be refused by the engine's own dispatch (defence in depth)."""
    from registry_successor.compose import CompositionResult
    spec = V7.families[IRR].spec
    lax = dataclasses.replace(spec, composer=lambda caller, record, operator: CompositionResult(True, None, "", {t.FIELD: {"class-a": "no_change"}}, False, ()))
    px = ContractProfile("r08-v9", b"ocs-reg/r08-v9/selection\n", b"ocs-reg/r08-v9/effective-policy\n", {IRR: FamilyEntry(lax, 1)}, V7.identity)
    good_body = {"family": IRR, "payload": t.payload()}
    ok_rec = type("R", (), {"ok": True, "record": good_body})()
    assert profile_e.compose(px, t.caller(), ok_rec).ok  # the lax composer is reached for a valid request
    assert profile_e.compose(px, t.caller(), type("R", (), {"ok": 1, "record": good_body})()).code == "composition_record_invalid"
    assert profile_e.compose(px, t.caller(), type("R", (), {"ok": "yes", "record": good_body})()).code == "composition_record_invalid"
    assert profile_e.compose(px, t.caller(), type("R", (), {"ok": True, "record": [good_body]})()).code == "composition_record_invalid"
    assert profile_e.compose(px, t.caller(), type("R", (), {"ok": True, "record": {"family": "other", "payload": {}}})()).code == "composition_family_unsupported"
    for op in ("union", "", None, 1, "Intersection"):
        assert profile_e.compose(px, t.caller(), ok_rec, op).code == "composition_operator_unsupported"
    assert profile_e.compose_for(px, "r08-v9", t.caller(), ok_rec).ok
    assert profile_e.compose_for(px, "r08-v7", t.caller(), ok_rec).code == "contract_unsupported"


def test_engine_entry_points_accept_exactly_a_contract_profile():
    class Sub(ContractProfile):
        pass
    fake = Sub(**parts())
    for bad in (None, "r08-v7", {"version": "r08-v7"}, object(), fake, V7.version):
        for fn, args in ((selection_e.parse_selection_envelope, ("{}",)), (record_e.validate_record_text, ("{}",)),
                         (selection_e.signing_input, ({},)), (verify_e.verify_selection, (None, None, None, None, None)),
                         (decide_e.verify_and_decide, ("required", {}, "{}", "{}", None, None, None, None)),
                         (decide_e.decide_verified, ("required", {}, None, None)), (identity_e.effective_policy_digest, (IRR, {})),
                         (identity_e.validate_effective_payload, (IRR, {})), (identity_e.registered_family_version, (IRR, "r08-v7")),
                         (identity_e.effective_preimage, (IRR, {})), (identity_e.deny_all_dimensions, (IRR, {})), (identity_e.effective_digest_of_preimage, ({},))):
            with pytest.raises(TypeError):
                fn(bad, *args)


# ---------------------------------------------------------------- structure of the engine package
def _module_tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _docstring_ids(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def test_no_engine_module_but_profiles_names_a_contract_version_or_domain_in_code():
    for path in ENGINE_FILES:
        if path.name == "profiles.py":
            continue
        tree = _module_tree(path)
        docs = _docstring_ids(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and id(node) not in docs:
                text = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
                assert not re.search(r"r08-v\d|ocs-reg/", text), (path.name, text)


def test_engine_has_no_global_statement_and_no_mutable_module_global():
    for path in ENGINE_FILES:
        tree = _module_tree(path)
        assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Global, ast.Nonlocal))], path.name
    for module in (profile_e, profiles, selection_e, record_e, verify_e, decide_e, identity_e, irr):
        for name, value in vars(module).items():
            if name.startswith("__"):
                continue
            assert not isinstance(value, (list, dict, set, bytearray)), (module.__name__, name, type(value))


def test_engine_has_no_executable_rules_no_eval_exec_and_no_io():
    banned_names = {"eval", "exec", "compile", "open", "__import__", "getattr_static"}
    banned_imports = {"subprocess", "socket", "os", "pickle", "importlib", "ctypes", "marshal", "http", "urllib"}
    for path in ENGINE_FILES:
        tree = _module_tree(path)
        called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert not called & banned_names, (path.name, called & banned_names)
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        assert not imported & banned_imports, (path.name, imported & banned_imports)
        assert "control_plane" not in path.read_text(encoding="utf-8").replace("control-plane", "")


def test_engine_emits_only_codes_of_the_closed_v2_vocabulary():
    position = {"_refuse": 0, "_no": 0, "mark": 1, "_refusal": 3}  # index of the reason-code argument
    emitted = set()
    for path in ENGINE_FILES:
        for node in ast.walk(_module_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else None
            if name in position and len(node.args) > position[name] and not any(isinstance(a, ast.Starred) for a in node.args[:position[name] + 1]):
                arg = node.args[position[name]]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    emitted.add(arg.value)
    assert len(emitted) >= 25, emitted
    from registry_successor.v2_codes import CODES_V2_REV2
    assert emitted <= set(CODES_V2_REV2), emitted - set(CODES_V2_REV2)
    assert verify_e.CODES is v2_codes.CODES_V2 and decide_e.CODES is v2_codes.CODES_V2 and verify_e.LAYERS == v6_verify.LAYERS_V6


def test_the_public_v7_modules_are_thin_bindings_to_the_engine():
    for module, names in ((v7_decision, ["verify_and_decide_v7"]), (v7_families, ["lookup_v7", "table_for_contract_version_v7", "compose_v7", "compose_for_v7"]),
                          (v7_policy_identity, ["registered_family_version", "validate_effective_payload", "deny_all_dimensions", "effective_preimage",
                                                "effective_digest_of_preimage", "effective_policy_digest"])):
        tree = ast.parse(inspect.getsource(module))
        for name in names:
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            body = [n for n in fn.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
            assert len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Call), (module.__name__, name)
            assert not [n for n in ast.walk(fn) if isinstance(n, (ast.If, ast.Try, ast.For, ast.While, ast.BoolOp))], (module.__name__, name)


def test_the_public_v7_entry_points_are_bound_to_the_v7_profile_and_take_no_contract_version():
    assert "contract_version" not in inspect.signature(v7_decision.verify_and_decide_v7).parameters
    assert list(inspect.signature(v7_decision.verify_and_decide_v7).parameters) == list(inspect.signature(v6_decision.verify_and_decide_v6).parameters)
    assert "contract_version" not in inspect.signature(verify_e.verify_selection).parameters
    assert "contract_version" not in inspect.signature(decide_e.verify_and_decide).parameters
    assert v7_families.FAMILIES_V7 == V7.specs and v7_families.CONTRACT_V7 == "r08-v7"
    assert v7_policy_identity.IDENTITY_FAMILIES is V7.identity


# ---------------------------------------------------------------- no drift from the frozen v6 orchestration
def _string_constants(fn):
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    docs = _docstring_ids(tree)
    return collections.Counter(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs)


def _call_names(fn):
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    return collections.Counter(ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call))


def test_engine_verification_carries_exactly_the_v6_layers_codes_and_details():
    """Every string literal (layer name, reason code, detail text, mapping key) of the frozen v6 orchestration appears in the engine's, with the same
    multiplicity; the only differences are the version-specific literals."""
    for engine_fn, frozen_fn, only_frozen, only_engine in (
            (verify_e._verify, v6_verify._verify_v6, {"statement is not a valid r08-v6 statement": 1},
             {"statement is not a valid statement of the profile's contract": 1}),
            (verify_e._authenticity, v6_verify._authenticity_v6, {}, {})):
        a, b = _string_constants(engine_fn), _string_constants(frozen_fn)
        assert (a - b) == collections.Counter(only_engine), a - b
        assert (b - a) == collections.Counter(only_frozen), b - a


def test_engine_decision_carries_exactly_the_v6_codes_and_details():
    for engine_fn, frozen_fn in ((decide_e.decide_verified, v6_decision._decide_verified), (decide_e._refusal, v6_decision._refusal)):
        a, b = _string_constants(engine_fn), _string_constants(frozen_fn)
        assert a == b, (a - b, b - a)
    a, b = _string_constants(decide_e.verify_and_decide), _string_constants(v6_decision.verify_and_decide_v6)
    assert a == b, (a - b, b - a)


def test_engine_selection_and_record_carry_exactly_the_v6_codes():
    from registry_successor import v6_record, v6_selection
    assert _string_constants(selection_e.statement_code) == _string_constants(v6_selection._statement_code_v6)
    assert _string_constants(selection_e._parse) == _string_constants(v6_selection._parse)
    assert _string_constants(record_e.validate_record_text) == _string_constants(v6_record.validate_record_text_v6)


def test_engine_calls_the_same_shared_helpers_as_the_frozen_orchestration():
    a, b = _call_names(verify_e._verify), _call_names(v6_verify._verify_v6)
    assert collections.Counter({k: v for k, v in a.items() if k.startswith(("v.", "c.", "mark", "getattr", "isinstance"))}) == \
        collections.Counter({k: v for k, v in b.items() if k.startswith(("v.", "c.", "mark", "getattr", "isinstance"))})


# ---------------------------------------------------------------- the engine is generic: a third test-only profile
PX = ContractProfile("r08-v9", b"ocs-reg/r08-v9/selection\n", b"ocs-reg/r08-v9/effective-policy\n", V7.families, V7.identity)
X_DOMAIN = PX.selection_signing_domain


def x_record(**over):
    return t.record(contract_version="r08-v9", **over)


def x_decide(profile, rec_text, sel_text, caller=None):
    ad = t.ev.Ed25519Verifier()
    return decide_e.verify_and_decide(profile, "required", caller or t.caller(), rec_text, sel_text, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)


@pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed")
def test_a_third_profile_runs_on_the_same_engine_and_is_isolated_from_the_others():
    rec = x_record()
    sel = t.selection_text(rec, domain=X_DOMAIN, contract="r08-v9")
    d = x_decide(PX, r.dumps(rec), sel)
    assert d.kind == "applied" and d.effective == {t.FIELD: {"class-a": "irreversible", "class-b": "irreversible", "class-c": "irreversible"}}
    # the same documents under the other profiles refuse; their documents under this one refuse; signatures do not cross domains
    for other in (V7, V6):
        assert x_decide(other, r.dumps(rec), sel).code == "contract_unsupported"
    rec7 = t.record()
    assert x_decide(PX, r.dumps(rec7), t.selection_text(rec7)).code == "contract_unsupported"
    wrong_domain = t.selection_text(rec, domain=t.V7_DOMAIN, contract="r08-v9")
    assert x_decide(PX, r.dumps(rec), wrong_domain).code == "signature_invalid"
    # identity is domain separated and the preimage names the profile's version
    eff = {t.FIELD: {"class-a": "irreversible"}}
    assert identity_e.effective_policy_digest(PX, IRR, eff) != identity_e.effective_policy_digest(V7, IRR, eff)
    assert identity_e.effective_preimage(PX, IRR, eff)["contract_version"] == "r08-v9"
    with pytest.raises(identity_e.IdentityRefusal) as e:
        identity_e.effective_policy_digest(PX, IRR, eff, "r08-v7")
    assert e.value.code == "contract_unsupported"
