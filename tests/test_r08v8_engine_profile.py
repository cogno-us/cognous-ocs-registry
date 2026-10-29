"""The `V8` engine profile and its thin public modules (APPROVED CANDIDATE; BUILDER_TESTED; not independently qualified).

`V8` carries ONLY the three remaining families and does not re-register irreversibility; `V7`, `V6_COMPAT` and `PROFILES` are unchanged (`V7` still registers exactly one
family; its tests are untouched). Registering a family enables no consumer.
"""
import ast
import inspect
import re
from pathlib import Path

import pytest

import r08v8_support as t
from registry_successor import common as c
from registry_successor import v7_families, v8_decision, v8_families, v8_policy_identity
from registry_successor.engine import families_anchor as anc
from registry_successor.engine import families_irreversibility as irr
from registry_successor.engine import families_observation as obs
from registry_successor.engine import identity as identity_e
from registry_successor.engine import profile as profile_e
from registry_successor.engine import profiles
from registry_successor.engine.profile import ContractProfile, FamilyEntry, IdentityRow

V8, V7, V6 = profiles.V8, profiles.V7, profiles.V6_COMPAT
ANC, AGE, TOL = anc.FAMILY_ANCHOR, obs.FAMILY_MAX_AGE, obs.FAMILY_TOLERANCE
ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "registry_successor"


def parts(profile=V8):
    return dict(version=profile.version, selection_signing_domain=profile.selection_signing_domain, effective_policy_domain=profile.effective_policy_domain,
                families=dict(profile.families), identity=dict(profile.identity))


def test_v8_profile_content():
    assert V8.version == "r08-v8" and V8.selection_signing_domain == b"ocs-reg/r08-v8/selection\n" and V8.effective_policy_domain == b"ocs-reg/r08-v8/effective-policy\n"
    assert profiles.CONTRACT_V8 == "r08-v8" and profiles.SELECTION_DOMAIN_V8 == V8.selection_signing_domain and profiles.EFFECTIVE_DOMAIN_V8 == V8.effective_policy_domain
    assert list(V8.families) == [ANC, AGE, TOL] and list(V8.identity) == [ANC, AGE, TOL]
    for fam in (ANC, AGE, TOL):
        entry = V8.families[fam]
        assert entry.schema_revision == 1 and type(entry.schema_revision) is int and entry.spec.enforcing_component == "control-plane"
        assert entry.spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING) and entry.spec.family == fam
        assert V8.identity[fam].version_member == "family_schema_revision" and V8.identity[fam].version_value == 1 and len(V8.identity[fam].members) == 1
        assert V8.identity[fam].members == entry.spec.payload_fields


def test_v8_does_not_reregister_irreversibility_or_any_earlier_family():
    for earlier in (irr.FAMILY_IRREVERSIBILITY, "f5-action-class-revocation-assurance-policy", "f5-terminal-revocation-enablement-policy", "f5-action-class-unreadable-policy",
                    "f5-action-class-age-bounds", "f4-control-plane-age-bounds", "f1abcd-local-execution-limits", "f1ab-local-execution-allowlist", c.FAMILY_F1A,
                    "anchor_deadline_to_inputs", "ObservationPolicy.max_age_seconds", "ObservationPolicy.clock_tolerance_seconds", "unknown-family"):
        assert earlier not in V8.families and v8_families.lookup_v8(earlier) is None
    assert len(V8.families) == 3


def test_v7_and_v6_compat_and_the_profiles_table_are_untouched():
    assert list(V7.families) == [irr.FAMILY_IRREVERSIBILITY] and len(V7.families) == 1
    for new in (ANC, AGE, TOL):
        assert new not in V7.families and v7_families.lookup_v7(new) is None and new not in V6.families
    assert V7.version == "r08-v7" and V7.selection_signing_domain == b"ocs-reg/r08-v7/selection\n" and V7.effective_policy_domain == b"ocs-reg/r08-v7/effective-policy\n"
    assert profiles.PROFILES["r08-v7"] is V7 and profiles.PROFILES["r08-v6"] is V6 and set(profiles.PROFILES) == {"r08-v6", "r08-v7"}
    assert V8 not in profiles.PROFILES.values()


def test_the_shipped_profiles_have_pairwise_distinct_domains_and_versions():
    doms = {p.selection_signing_domain for p in (V6, V7, V8)} | {p.effective_policy_domain for p in (V6, V7, V8)}
    assert len(doms) == 6 and len({V6.version, V7.version, V8.version}) == 3


def test_the_v8_specs_are_the_family_module_functions_not_copies():
    assert V8.families[ANC].spec.composer is anc.compose_anchor and V8.families[ANC].spec.payload_validator is anc.payload_validator
    assert V8.families[AGE].spec.composer is obs.compose_max_age and V8.families[TOL].spec.composer is obs.compose_tolerance
    assert V8.identity[AGE].is_value is obs.is_max_age and V8.identity[TOL].is_value is obs.is_tolerance and V8.identity[ANC].is_value is anc.is_value


def test_profile_is_frozen_and_its_tables_are_immutable_views():
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        V8.version = "r08-v9"
    with pytest.raises(TypeError):
        V8.families[ANC] = V8.families[ANC]
    with pytest.raises(TypeError):
        V8.identity[ANC] = V8.identity[ANC]


def test_scalar_int_rows_are_validated_at_construction():
    p = parts()
    ContractProfile(**p)  # control: the unmodified parts construct
    row = V8.identity[AGE]
    for bad in (IdentityRow(AGE, "scalar-int", (obs.MAX_AGE_FIELD, obs.TOLERANCE_FIELD), row.is_value, row.version_member, 1),
                IdentityRow(AGE, "scalar-int", (obs.TOLERANCE_FIELD,), row.is_value, row.version_member, 1),
                IdentityRow(AGE, "scalar-int", row.members, None, row.version_member, 1),
                IdentityRow(AGE, "scalar-int", row.members, row.is_value, row.version_member, 2),
                IdentityRow(AGE, "scalar-int", row.members, row.is_value, "family_version", "v8"),
                IdentityRow(AGE, "scalar-float", row.members, row.is_value, row.version_member, 1),
                IdentityRow(TOL, "scalar-int", row.members, row.is_value, row.version_member, 1)):
        q = parts()
        q["identity"] = dict(q["identity"], **{AGE: bad})
        with pytest.raises(ValueError):
            ContractProfile(**q)


def test_the_scalar_int_identity_branch_is_selected_by_the_row_kind_only():
    """A scalar-int row with the enum vocabulary refuses a string by type; a scalar-enum row refuses an int by type (the kinds do not leak into each other)."""
    assert identity_e.validate_effective_payload(V8, AGE, {obs.MAX_AGE_FIELD: 60}) == {obs.MAX_AGE_FIELD: 60}
    assert identity_e.validate_effective_payload(V8, ANC, {anc.ANCHOR_FIELD: "anchor"}) == {anc.ANCHOR_FIELD: "anchor"}
    with pytest.raises(identity_e.IdentityRefusal) as e:
        identity_e.validate_effective_payload(V8, ANC, {anc.ANCHOR_FIELD: 60})
    assert (e.value.code, e.value.member) == ("field_type_invalid", anc.ANCHOR_FIELD)
    with pytest.raises(identity_e.IdentityRefusal) as e:
        identity_e.validate_effective_payload(V8, AGE, {obs.MAX_AGE_FIELD: "anchor"})
    assert (e.value.code, e.value.member) == ("field_type_invalid", obs.MAX_AGE_FIELD)


def test_the_v8_table_dispatches_by_exact_string_and_the_contract_version():
    assert set(v8_families.FAMILIES_V8) == {ANC, AGE, TOL} and v8_families.CONTRACT_V8 == "r08-v8"
    for bad in ("F5-OBSERVATION-MAX-AGE-POLICY", " f5-observation-max-age-policy", None, 1, ["x"], "f5-action-class-irreversibility-policy", ANC + "\n"):
        assert v8_families.lookup_v8(bad) is None
    assert v8_families.table_for_contract_version_v8("r08-v8").ok
    for v in ("r08-v7", "r08-v6", "r08-v5", "r08-v2", "R08-V8", "r08-v8 ", None, 8, b"r08-v8"):
        sel = v8_families.table_for_contract_version_v8(v)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
    assert not v8_families.compose_for_v8("r08-v7", t.caller(AGE), None).ok


def test_the_dispatch_enforces_operator_record_validity_and_family():
    from registry_successor.record import RecordResult
    rec = t.record(family=AGE)
    ok = RecordResult(True, None, "", rec, rec["record_digest"])
    assert v8_families.compose_v8(t.caller(AGE), ok).ok
    assert v8_families.compose_v8(t.caller(AGE), ok, "union").code == "composition_operator_unsupported"
    assert v8_families.compose_v8(t.caller(AGE), RecordResult(False, "field_invalid", "", None, None)).code == "composition_record_invalid"
    other = dict(rec, family=irr.FAMILY_IRREVERSIBILITY)
    assert v8_families.compose_v8(t.caller(AGE), RecordResult(True, None, "", other, "x")).code == "composition_family_unsupported"
    assert v8_families.compose_for_v8("r08-v8", t.caller(AGE), ok).ok


def test_engine_entry_points_still_accept_exactly_a_contract_profile():
    for bad in (None, "r08-v8", dict(parts()), object()):
        with pytest.raises(TypeError):
            identity_e.effective_policy_digest(bad, AGE, {obs.MAX_AGE_FIELD: 60})


# ---------------------------------------------------------------- structure
def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _docstring_ids(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def test_the_public_v8_modules_are_thin_bindings_to_the_engine():
    for module, names in ((v8_decision, ["verify_and_decide_v8"]), (v8_families, ["lookup_v8", "table_for_contract_version_v8", "compose_v8", "compose_for_v8"]),
                          (v8_policy_identity, ["registered_family_version", "validate_effective_payload", "deny_all_dimensions", "effective_preimage",
                                                "effective_digest_of_preimage", "effective_policy_digest"])):
        tree = ast.parse(inspect.getsource(module))
        for name in names:
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            body = [n for n in fn.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
            assert len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Call), (module.__name__, name)
            assert not [n for n in ast.walk(fn) if isinstance(n, (ast.If, ast.Try, ast.For, ast.While, ast.BoolOp))], (module.__name__, name)
            assert "_profiles.V8" in ast.unparse(fn) and "V7" not in ast.unparse(fn) and "V6" not in ast.unparse(fn)


def test_the_public_v8_entry_points_take_no_contract_version_in_the_decision():
    assert "contract_version" not in inspect.signature(v8_decision.verify_and_decide_v8).parameters
    assert inspect.signature(v8_policy_identity.effective_policy_digest).parameters["contract_version"].default == "r08-v8"


def test_the_new_engine_modules_name_no_contract_version_or_domain_in_code():
    for name in ("families_anchor.py", "families_observation.py"):
        tree = _tree(PKG / "engine" / name)
        docs = _docstring_ids(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and id(node) not in docs:
                text = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
                assert not re.search(r"r08-v\d|ocs-reg/", text), (name, text)


def test_the_engine_files_other_than_the_two_additive_edits_are_unchanged_in_content_shape():
    """`profile.py` gains only the `scalar-int` kind; `identity.py` gains only the `scalar-int` branch (the existing branches are the manifest-checked baseline)."""
    ident = (PKG / "engine" / "identity.py").read_text(encoding="utf-8")
    assert ident.count('elif row.kind == "scalar-int":') == 1 and ident.count('if row.kind == "classmap-enum":') == 1 and ident.count("# scalar-enum") == 1
    assert profile_e.KINDS == ("classmap-enum", "scalar-enum", "scalar-int")


def test_public_family_id_constants_match_the_profile_table_and_expose_the_binding_fields():
    """D-06 binding entries need {family_id, contract_version, family_schema_revision, effective_policy_digest}; all four are reachable from the public v8 modules."""
    from registry_successor import v8_families as vf, v8_policy_identity as vi
    assert vf.FAMILY_IDS_V8 == ("f5-anchor-deadline-to-inputs-policy", "f5-observation-max-age-policy", "f5-observation-clock-tolerance-policy")
    assert tuple(vf.FAMILIES_V8) == vf.FAMILY_IDS_V8 and vf.CONTRACT_V8 == vi.CONTRACT_VERSION == "r08-v8"
    assert (vf.FAMILY_ANCHOR_V8, vf.FAMILY_OBSERVATION_MAX_AGE_V8, vf.FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8) == vf.FAMILY_IDS_V8
    sample = {vf.FAMILY_IDS_V8[0]: {"anchor_deadline_to_inputs": "anchor"}, vf.FAMILY_IDS_V8[1]: {"observation_max_age_seconds": 60},
              vf.FAMILY_IDS_V8[2]: {"observation_clock_tolerance_seconds": 0}}
    for fid in vf.FAMILY_IDS_V8:
        rev = vi.registered_family_version(fid, vf.CONTRACT_V8)
        dig = vi.effective_policy_digest(fid, sample[fid])
        assert type(rev) is int and rev == 1 and dig.startswith("sha256:") and len(dig) == 71
