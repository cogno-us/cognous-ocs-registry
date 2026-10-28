"""Frozen-baseline protection and cross-version refusal for `r08-v5` (BUILDER_TESTED; not independently qualified).

`tests/vectors/r08v5/frozen_baseline_manifest.json` extends the r08-v4 manifest with the merged r08-v4 modules, contract, tests and vectors (sha256 from
`git show <baseline>:<path>`, baseline = Registry main `47adfc8f`). Nothing frozen, including the whole of r08-v1 .. r08-v4 and the r08-v2 F5 class-age
family, may change, and no frozen module may import an r08-v5 module.
"""
import hashlib
import inspect
import json
from pathlib import Path

import pytest

import r08_support as r
import r08v3_support as t3
import r08v4_support as t4
import r08v5_support as t
import s01_support as s
from registry_successor import v2_age_bounds, v3_decision, v3_families, v4_decision, v4_families, v4_selection, v4_verify
from registry_successor import v5_decision, v5_selection, v5_verify
from registry_successor import verify as v

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tests" / "vectors" / "r08v5" / "frozen_baseline_manifest.json").read_text())
FILES = MANIFEST["files"]
V5_MODULES = {"v5_class_unreadable.py", "v5_families.py", "v5_record.py", "v5_selection.py", "v5_verify.py", "v5_policy_identity.py", "v5_decision.py"}
V5_NAMES = ("v5_class_unreadable", "v5_families", "v5_verify", "v5_decision", "v5_record", "v5_selection", "v5_policy_identity")


def test_manifest_shape():
    assert len(MANIFEST["baseline_commit"]) == 40 and len(FILES) > 150
    for needed in ("registry_successor/verify.py", "registry_successor/v2_age_bounds.py", "registry_successor/v2_policy_identity.py",
                   "registry_successor/families.py", "registry_successor/v4_f1abcd.py", "registry_successor/v4_verify.py",
                   "registry_successor/v4_policy_identity.py", "docs/r08-v2-contract.md", "docs/r08-v4-contract.md",
                   "tests/vectors/r08v4/identity_vectors.json", "tests/test_r08v4_decision_path.py"):
        assert needed in FILES, needed
    assert not any("v5_" in p or "r08v5" in p or "r08-v5" in p for p in FILES)


@pytest.mark.parametrize("path", sorted(FILES))
def test_frozen_file_is_byte_identical_to_the_baseline(path):
    f = ROOT / path
    assert f.is_file(), "frozen file missing: " + path
    assert hashlib.sha256(f.read_bytes()).hexdigest() == FILES[path], "frozen file changed: " + path


def test_no_frozen_module_imports_an_r08_v5_module():
    for path in FILES:
        if path.endswith(".py") and path.startswith(("registry_", "baseline/")):
            text = (ROOT / path).read_text(encoding="utf-8")
            assert not any(name in text for name in V5_NAMES), path


def test_v5_modules_are_new_files_only():
    present = {p.name for p in (ROOT / "registry_successor").glob("v5_*.py")}
    assert present == V5_MODULES
    for name in present:
        assert "registry_successor/" + name not in FILES


def test_frozen_entry_points_still_refuse_r08_v5():
    from registry_successor import families
    for version in ("r08-v5", "R08-V5"):
        sel = families.table_for_contract_version(version)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
        assert families.lookup_for(version, "f5-action-class-unreadable-policy") is None
        assert not v3_families.table_for_contract_version_v3(version).ok
        assert not v4_families.table_for_contract_version_v4(version).ok
    fam = "f5-action-class-unreadable-policy"
    assert fam not in families.FAMILIES_V2 and fam not in families.FAMILIES
    assert v3_families.lookup_v3(fam) is None and v4_families.lookup_v4(fam) is None


def test_the_r08_v2_f5_class_age_family_is_untouched_and_does_not_carry_the_new_field():
    assert v2_age_bounds.F5_FIELDS == ("class_status_max_age_seconds",)
    assert v2_age_bounds.f5_payload_validator({"class_status_max_age_seconds": {"class-a": 30}, "class_on_unreadable": {"class-a": "refuse"}}) == "field_unknown"
    assert v2_age_bounds.f5_payload_validator({"class_on_unreadable": {"class-a": "refuse"}}) == "field_unknown"


# ---- cross-version / cross-family
pytestmark_backend = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")


@pytestmark_backend
def test_v5_selection_and_record_are_refused_by_v4_and_the_reverse():
    rec5, ad = t.record(), t.ev.Ed25519Verifier()
    d = v4_decision.verify_and_decide_v4("required", t4.caller(), r.dumps(rec5), t.selection_text(rec5), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"
    rec4 = t4.record()
    d = v5_decision.verify_and_decide_v5("required", t.caller(), r.dumps(rec4), t4.selection_text(rec4), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"
    rec3 = t3.record()
    d = v5_decision.verify_and_decide_v5("required", t.caller(), r.dumps(rec3), t3.selection_text(rec3), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"
    d = v3_decision.verify_and_decide_v3("required", t3.caller(), r.dumps(rec5), t.selection_text(rec5), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"


@pytestmark_backend
def test_v5_record_is_refused_by_the_v1_and_v2_entry_points():
    from registry_successor import decision, record as record_mod, selection as s1
    from registry_successor.v2_selection import parse_selection_envelope_v2
    rec = t.record()
    sel = t.selection_text(rec)
    assert decision.validate_record_text_v2(r.dumps(rec)).code == "contract_unsupported"
    assert record_mod.validate_record_text(r.dumps(rec)).code == "contract_unsupported"
    assert parse_selection_envelope_v2(sel).code == "contract_unsupported"
    assert s1.parse_selection_envelope(sel).code == "contract_unsupported"
    ad = t.ev.Ed25519Verifier()
    d2 = decision.verify_and_decide_v2("required", {"class_status_max_age_seconds": {"class-a": 30}}, r.dumps(rec), sel, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d2.kind == "required_policy_unavailable" and d2.effective is None


@pytestmark_backend
@pytest.mark.parametrize("contract", ["r08-v4", "r08-v3", "r08-v2", "r08-v1", "R08-V5", ""])
def test_wrong_contract_envelope_refuses(contract):
    rec = t.record()
    d = t.decide(rec=rec, sel=t.selection_text(rec, contract=contract))
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"


@pytestmark_backend
def test_a_v5_age_family_record_inside_a_v5_envelope_is_refused():
    rec = t.record(family="f5-action-class-age-bounds", payload={"class_status_max_age_seconds": {"class-a": 30}})
    sel = r.dumps(t.envelope(r.make_statement_v2(rec, family="f5-action-class-age-bounds")))
    d = t.decide(rec=rec, sel=sel)
    assert d.kind == "required_policy_unavailable" and d.code in ("family_unsupported", "composition_family_unsupported")


@pytestmark_backend
def test_the_v5_verifier_takes_no_contract_version_and_rejects_a_foreign_envelope_object():
    assert "contract_version" not in inspect.signature(v5_verify.verify_selection_v5).parameters
    stmt = t.statement(t.record())
    foreign = type("P", (), {"ok": True, "code": None, "envelope": {"contract_version": "r08-v2"}, "statement": stmt,
                             "statement_digest": __import__("registry_successor.common", fromlist=["digest"]).digest(stmt), "signatures": []})()
    rep = v5_verify.verify_selection_v5(foreign, s.CTX, s.trust(pub=t.PK), t.ev.Ed25519Verifier(), r.NOW, None)
    assert rep.ok is False and rep.code == "contract_unsupported"


# ---- parity: the v5 orchestration is the v4 orchestration with only the version, table and domain changed
def _norm(src, tag):
    return src.replace("v" + tag, "vN").replace("V" + tag, "VN").replace("r08-v" + tag, "r08-vN")


def test_v5_verify_orchestration_is_the_v4_orchestration_modulo_version_names():
    a, b = inspect.getsource(v4_verify._verify_v4), inspect.getsource(v5_verify._verify_v5)
    assert _norm(a, "4").replace("_verify_vN", "_verify") == _norm(b, "5").replace("_verify_vN", "_verify")
    a, b = inspect.getsource(v4_verify._authenticity_v4), inspect.getsource(v5_verify._authenticity_v5)
    assert _norm(a, "4").replace("_authenticity_vN", "_a") == _norm(b, "5").replace("_authenticity_vN", "_a")


def test_v5_decision_orchestration_is_the_v4_orchestration_modulo_version_names_and_the_optional_normalizer():
    a, b = inspect.getsource(v4_decision._decide_verified), inspect.getsource(v5_decision._decide_verified)
    assert _norm(a, "4").replace("_decide_verifiedN", "_d") == _norm(b, "5").replace("_decide_verifiedN", "_d")
    a, b = inspect.getsource(v4_decision.verify_and_decide_v4), inspect.getsource(v5_decision.verify_and_decide_v5)
    assert _norm(a, "4").replace("verify_and_decide_vN", "_d") == _norm(b, "5").replace("verify_and_decide_vN", "_d")


def test_v5_selection_statement_shape_and_layers_are_the_v4_ones():
    assert v5_selection.STATEMENT_FIELDS_V5 == v4_selection.STATEMENT_FIELDS_V4
    assert v5_verify.LAYERS_V5 == v4_verify.LAYERS_V4 == v.LAYERS_V2
    assert v5_verify.CODES_V5 == v4_verify.CODES_V4
