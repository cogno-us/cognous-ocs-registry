"""Frozen-baseline protection and cross-version refusal for `r08-v6` (BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v6/frozen_baseline_manifest.json` extends the r08-v5 manifest with the merged r08-v5 modules, contract, tests and vectors (sha256 from
`git show <baseline>:<path>`, baseline = Registry main `e8b572cc669bee668abc88846f7b071a74f13440`; generator in
docs/family-migration/revocation-families/evidence/genman6.py). Nothing frozen, including the whole of r08-v1 .. r08-v5, may change, and no frozen
module may import an r08-v6 module.
"""
import hashlib
import inspect
import json
from pathlib import Path

import pytest

import r08_support as r
import r08v3_support as t3
import r08v4_support as t4
import r08v5_support as t5
import r08v6_support as t
import s01_support as s
from registry_successor import v2_age_bounds, v3_decision, v3_families, v4_decision, v4_families, v5_decision, v5_families, v5_record, v5_selection
from registry_successor import v5_verify, v6_decision, v6_families, v6_record, v6_selection, v6_verify
from registry_successor import verify as v

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v6" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]
V6_MODULES = {"v6_class_revocation_assurance.py", "v6_terminal_revocation.py", "v6_families.py", "v6_record.py", "v6_selection.py", "v6_verify.py",
              "v6_policy_identity.py", "v6_decision.py"}
V6_NAMES = ("v6_class_revocation_assurance", "v6_terminal_revocation", "v6_families", "v6_verify", "v6_decision", "v6_record", "v6_selection",
            "v6_policy_identity")
FAM_RA, FAM_TR = t.FAMILY, t.FAMILY_TR


def test_manifest_shape():
    assert MANIFEST["baseline_commit"] == "e8b572cc669bee668abc88846f7b071a74f13440" and len(FILES) >= 174
    for needed in ("registry_successor/verify.py", "registry_successor/v2_age_bounds.py", "registry_successor/v2_policy_identity.py",
                   "registry_successor/families.py", "registry_successor/v4_f1abcd.py", "registry_successor/v4_verify.py",
                   "registry_successor/v5_class_unreadable.py", "registry_successor/v5_families.py", "registry_successor/v5_verify.py",
                   "registry_successor/v5_policy_identity.py", "registry_successor/v5_decision.py", "registry_successor/v5_record.py",
                   "registry_successor/v5_selection.py", "docs/r08-v2-contract.md", "docs/r08-v4-contract.md", "docs/r08-v5-contract.md",
                   "tests/vectors/r08v4/identity_vectors.json", "tests/vectors/r08v5/identity_vectors.json", "tests/vectors/r08v5/signed_selection_vector.json",
                   "tests/vectors/r08v5/frozen_baseline_manifest.json", "tests/r08v5_support.py", "tests/test_r08v5_decision_path.py",
                   "tests/test_r08v5_frozen_baseline.py", "tests/test_r08v4_decision_path.py"):
        assert needed in FILES, needed
    assert not any("v6_" in p or "r08v6" in p or "r08-v6" in p for p in FILES)


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def test_no_frozen_module_imports_an_r08_v6_module():
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert not any(name in text for name in V6_NAMES), path


def test_v6_modules_are_new_files_only():
    present = {p.name for p in (ROOT / "registry_successor").glob("v6_*.py")}
    assert present == V6_MODULES
    for name in present:
        assert "registry_successor/" + name not in FILES


def test_no_new_reason_code():
    from registry_successor import v2_codes
    assert v6_verify.CODES_V6 is v2_codes.CODES_V2 and v6_decision.CODES is v2_codes.CODES_V2


def test_frozen_entry_points_still_refuse_r08_v6():
    from registry_successor import families
    for version in ("r08-v6", "R08-V6"):
        sel = families.table_for_contract_version(version)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
        for fam in (FAM_RA, FAM_TR):
            assert families.lookup_for(version, fam) is None
        assert not v3_families.table_for_contract_version_v3(version).ok
        assert not v4_families.table_for_contract_version_v4(version).ok
        assert not v5_families.table_for_contract_version_v5(version).ok
    for fam in (FAM_RA, FAM_TR):
        assert fam not in families.FAMILIES_V2 and fam not in families.FAMILIES
        assert v3_families.lookup_v3(fam) is None and v4_families.lookup_v4(fam) is None and v5_families.lookup_v5(fam) is None
    assert set(v6_families.FAMILIES_V6) == {FAM_RA, FAM_TR}
    assert v5_families.lookup_v5("f5-action-class-unreadable-policy") is not None and v6_families.lookup_v6("f5-action-class-unreadable-policy") is None


def test_earlier_tables_are_unchanged_by_the_new_families():
    assert set(v5_families.FAMILIES_V5) == {"f5-action-class-unreadable-policy"}
    assert v2_age_bounds.F5_FIELDS == ("class_status_max_age_seconds",)
    for fld in ("class_requires_revocation_assurance", "terminal_revocation"):
        assert v2_age_bounds.f5_payload_validator({"class_status_max_age_seconds": {"class-a": 30}, fld: {"class-a": "required"}}) == "field_unknown"


# ---- cross-version / cross-family
pytestmark_backend = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")


def _refused_with(d, code):
    return d.kind == "required_policy_unavailable" and d.code == code and d.effective is None


@pytestmark_backend
@pytest.mark.parametrize("family", [FAM_RA, FAM_TR])
def test_v6_selection_and_record_are_refused_by_v5_v4_v3_and_the_reverse(family):
    rec6, ad = t.record(family=family), t.ev.Ed25519Verifier()
    args = (r.dumps(rec6), t.selection_text(rec6), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert _refused_with(v5_decision.verify_and_decide_v5("required", t5.caller(), *args), "contract_unsupported")
    assert _refused_with(v4_decision.verify_and_decide_v4("required", t4.caller(), *args), "contract_unsupported")
    assert _refused_with(v3_decision.verify_and_decide_v3("required", t3.caller(), *args), "contract_unsupported")
    for rec_other, text_other, caller_other in ((t5.record(), t5.selection_text, t5.caller()), (t4.record(), t4.selection_text, t4.caller()),
                                                (t3.record(), t3.selection_text, t3.caller())):
        d = v6_decision.verify_and_decide_v6("required", t.caller(family), r.dumps(rec_other), text_other(rec_other), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
        assert _refused_with(d, "contract_unsupported")
    # a v5 record under a v6 selection and a v6 record under a v5 selection
    rec5 = t5.record()
    # (a v5 record under a v6 selection: the record itself is unsupported at the v6 validator, so the selection cannot bind it)
    d = v6_decision.verify_and_decide_v6("required", t.caller(family), r.dumps(rec5), t.selection_text(rec6), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert _refused_with(d, "composition_record_invalid")
    assert v6_record.validate_record_text_v6(r.dumps(rec5)).code == "contract_unsupported"
    d = v6_decision.verify_and_decide_v6("required", t.caller(family), r.dumps(rec6), t5.selection_text(rec5), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert _refused_with(d, "contract_unsupported")
    d = v5_decision.verify_and_decide_v5("required", t5.caller(), r.dumps(rec6), t5.selection_text(rec5), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert _refused_with(d, "composition_record_invalid")
    assert v5_record.validate_record_text_v5(r.dumps(rec6)).code == "contract_unsupported"


@pytestmark_backend
@pytest.mark.parametrize("family", [FAM_RA, FAM_TR])
def test_v6_record_and_selection_are_refused_by_the_v1_and_v2_entry_points_and_parsers(family):
    from registry_successor import decision, record as record_mod, selection as s1
    from registry_successor.v2_selection import parse_selection_envelope_v2
    rec = t.record(family=family)
    sel = t.selection_text(rec)
    assert decision.validate_record_text_v2(r.dumps(rec)).code == "contract_unsupported"
    assert record_mod.validate_record_text(r.dumps(rec)).code == "contract_unsupported"
    assert parse_selection_envelope_v2(sel).code == "contract_unsupported"
    assert s1.parse_selection_envelope(sel).code == "contract_unsupported"
    from registry_successor import v3_record, v3_selection, v4_record, v4_selection as v4s
    assert v3_record.validate_record_text_v3(r.dumps(rec)).code == "contract_unsupported"
    assert v4_record.validate_record_text_v4(r.dumps(rec)).code == "contract_unsupported"
    assert v5_record.validate_record_text_v5(r.dumps(rec)).code == "contract_unsupported"
    assert v3_selection.parse_selection_envelope_v3(sel).code == "contract_unsupported"
    assert v4s.parse_selection_envelope_v4(sel).code == "contract_unsupported"
    assert v5_selection.parse_selection_envelope_v5(sel).code == "contract_unsupported"
    # and the reverse: older documents at the v6 parsers
    for older in (t5.record(), t4.record(), t3.record(), r.make_record_v2(), r.make_record()):
        assert v6_record.validate_record_text_v6(r.dumps(older)).code == "contract_unsupported"
    assert v6_selection.parse_selection_envelope_v6(t5.selection_text(t5.record())).code == "contract_unsupported"
    assert v6_selection.parse_selection_envelope_v6(t4.selection_text(t4.record())).code == "contract_unsupported"
    ad = t.ev.Ed25519Verifier()
    d2 = decision.verify_and_decide_v2("required", {"class_status_max_age_seconds": {"class-a": 30}}, r.dumps(rec), sel, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d2.kind == "required_policy_unavailable" and d2.effective is None


@pytestmark_backend
@pytest.mark.parametrize("family", [FAM_RA, FAM_TR])
@pytest.mark.parametrize("contract", ["r08-v5", "r08-v4", "r08-v3", "r08-v2", "r08-v1", "R08-V6", "", "r08-v6 "])
def test_wrong_contract_envelope_refuses(family, contract):
    rec = t.record(family=family)
    assert _refused_with(t.decide(rec=rec, sel=t.selection_text(rec, contract=contract)), "contract_unsupported")


@pytestmark_backend
@pytest.mark.parametrize("contract", ["r08-v5", "r08-v4", "r08-v3", "r08-v2", "r08-v1", "r08-v7", "", None, 6])
def test_wrong_contract_record_refuses(contract):
    for family in (FAM_RA, FAM_TR):
        rec = t.record(family=family, contract_version=contract)
        assert v6_record.validate_record_text_v6(r.dumps(rec)).code == "contract_unsupported"
        assert _refused_with(t.decide(rec=rec, sel=t.selection_text(rec)), "composition_record_invalid")


@pytestmark_backend
def test_a_v5_family_or_age_family_record_inside_a_v6_envelope_is_refused():
    rec = t.record(family="f5-action-class-age-bounds", payload={"class_status_max_age_seconds": {"class-a": 30}})
    d = t.decide(rec=rec, sel=r.dumps(t.envelope(r.make_statement_v2(rec, family="f5-action-class-age-bounds"))))
    assert d.kind == "required_policy_unavailable" and d.code == "family_unsupported"
    rec = t.record(family="f5-action-class-unreadable-policy", payload={"class_on_unreadable": {"class-a": "refuse"}})
    d = t.decide(rec=rec, sel=r.dumps(t.envelope(r.make_statement_v2(rec, family="f5-action-class-unreadable-policy"))))
    assert d.kind == "required_policy_unavailable" and d.code == "family_unsupported"


@pytestmark_backend
def test_the_v6_verifier_takes_no_contract_version_and_rejects_a_foreign_envelope_object():
    assert "contract_version" not in inspect.signature(v6_verify.verify_selection_v6).parameters
    assert "contract_version" not in inspect.signature(v6_decision.verify_and_decide_v6).parameters
    for family in (FAM_RA, FAM_TR):
        stmt = t.statement(t.record(family=family))
        digest = __import__("registry_successor.common", fromlist=["digest"]).digest(stmt)
        for foreign_version in ("r08-v2", "r08-v5", None, 6):
            foreign = type("P", (), {"ok": True, "code": None, "envelope": {"contract_version": foreign_version}, "statement": stmt,
                                     "statement_digest": digest, "signatures": []})()
            rep = v6_verify.verify_selection_v6(foreign, s.CTX, s.trust(pub=t.PK), t.ev.Ed25519Verifier(), r.NOW, None)
            assert rep.ok is False and rep.code == "contract_unsupported"


@pytestmark_backend
def test_a_v5_signature_over_a_v6_statement_does_not_verify():
    for family in (FAM_RA, FAM_TR):
        rec = t.record(family=family)
        stmt = t.statement(rec)
        sel = r.dumps(s.envelope(stmt, domain=t.V5_DOMAIN, contract="r08-v6", signature=t.sign(stmt, domain=t.V5_DOMAIN), pub=t.PK))
        assert t.decide(rec=rec, sel=sel).code == "signature_invalid"


# ---- parity: the v6 orchestration is the v5 orchestration with only the version names changed
def _norm(src, tag):
    return src.replace("v" + tag, "vN").replace("V" + tag, "VN").replace("r08-v" + tag, "r08-vN")


def test_v6_verify_orchestration_is_the_v5_orchestration_modulo_version_names():
    a, b = inspect.getsource(v5_verify._verify_v5), inspect.getsource(v6_verify._verify_v6)
    assert _norm(a, "5").replace("_verify_vN", "_verify") == _norm(b, "6").replace("_verify_vN", "_verify")
    a, b = inspect.getsource(v5_verify._authenticity_v5), inspect.getsource(v6_verify._authenticity_v6)
    assert _norm(a, "5").replace("_authenticity_vN", "_a") == _norm(b, "6").replace("_authenticity_vN", "_a")
    a, b = inspect.getsource(v5_verify.verify_selection_v5), inspect.getsource(v6_verify.verify_selection_v6)
    assert _norm(a, "5").replace("verify_selection_vN", "_v") == _norm(b, "6").replace("verify_selection_vN", "_v")


def test_v6_decision_orchestration_is_the_v5_orchestration_modulo_version_names():
    a, b = inspect.getsource(v5_decision._decide_verified), inspect.getsource(v6_decision._decide_verified)
    assert _norm(a, "5").replace("_decide_verifiedN", "_d") == _norm(b, "6").replace("_decide_verifiedN", "_d")
    a, b = inspect.getsource(v5_decision.verify_and_decide_v5), inspect.getsource(v6_decision.verify_and_decide_v6)
    assert _norm(a, "5").replace("verify_and_decide_vN", "_d") == _norm(b, "6").replace("verify_and_decide_vN", "_d")


def test_v6_record_and_selection_are_the_v5_ones_modulo_version_names():
    a, b = inspect.getsource(v5_record.validate_record_text_v5), inspect.getsource(v6_record.validate_record_text_v6)
    assert _norm(a, "5").replace("validate_record_text_vN", "_r") == _norm(b, "6").replace("validate_record_text_vN", "_r")
    for name5, name6 in (("_statement_code_v5", "_statement_code_v6"), ("_parse", "_parse"), ("parse_selection_envelope_v5", "parse_selection_envelope_v6"),
                         ("signing_input_v5", "signing_input_v6")):
        a, b = inspect.getsource(getattr(v5_selection, name5)), inspect.getsource(getattr(v6_selection, name6))
        assert _norm(a, "5").replace(name5, "_f").replace("_parse", "_f") == _norm(b, "6").replace(name6, "_f").replace("_parse", "_f")


def test_v6_selection_statement_shape_and_layers_are_the_v5_ones():
    assert v6_selection.STATEMENT_FIELDS_V6 == v5_selection.STATEMENT_FIELDS_V5
    assert v6_verify.LAYERS_V6 == v5_verify.LAYERS_V5 == v.LAYERS_V2
    assert v6_verify.CODES_V6 == v5_verify.CODES_V5
    assert v6_selection.DISPOSITIONS == v5_selection.DISPOSITIONS
