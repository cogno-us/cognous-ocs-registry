"""EXT-S1-5 guard amendment (Architect Batch 6 ruling 4.4): negative regression coverage.

The old guards keep protecting `r08-v1` and unsupported-version behaviour; they are narrowed only where a successor semantic is registered under `r08-v2` (the
revision-2 vocabulary in `v2_codes.py`, the one successor identity module, and the explicit revision-2 path in `decision.py`). The withdrawal and snapshot-floor
mappings stay absent until their owning contracts and evaluators exist. Source is read as text/AST; nothing is imported by path. BUILDER_TESTED, not qualified.
"""
import ast
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from registry_successor import common as c
from registry_successor import decision
from registry_successor import families
from registry_successor import v2_policy_identity as m
from registry_successor.v2_codes import CODES_V2_REV2

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "registry_successor"
NEW = ("not_activated", "policy_identity_mismatch", "store_unknown")
V2_ONLY = ("selection_withdrawn", "trust_snapshot_version_stale")
V1_MODULES = ("common.py", "record.py", "selection.py", "verify.py", "compose.py", "families.py")


def _string_constants(path):
    return [n.value for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


@pytest.mark.parametrize("name", V1_MODULES)
def test_v1_modules_never_mention_a_revision_2_or_v2_only_code(name):
    consts = _string_constants(PKG / name)
    for code in NEW + V2_ONLY:
        assert code not in consts, (name, code)
        assert not re.search(r"\b%s\b" % code, (PKG / name).read_text(encoding="utf-8")), (name, code)


def test_decision_py_names_the_revision_2_codes_only_in_its_one_explicit_tuple():
    tree = ast.parse((PKG / "decision.py").read_text(encoding="utf-8"))
    hits = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in NEW + V2_ONLY]
    assigns = [n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "REV2_CODES" for t in n.targets)]
    assert len(assigns) == 1
    inside = {id(x) for x in ast.walk(assigns[0]) if isinstance(x, ast.Constant)}
    assert hits and all(id(h) in inside for h in hits), "a revision-2 code appears outside REV2_CODES"
    assert {h.value for h in hits} == set(NEW) and not {h.value for h in hits} & set(V2_ONLY)
    assert decision.REV2_CODES == NEW


def test_v1_remap_paths_are_unchanged_a_revision_2_code_never_survives_the_v1_decision():
    """A revision-2 code handed to the v1 decision path is rewritten exactly as before (Amendment 1 6.7(e) items 2 and 5: only the explicit revision-2 path routes them)."""
    for code in NEW + V2_ONLY:
        report = SimpleNamespace(ok=False, code=code)
        for participation in ("required", "optional"):
            d = decision._decide_verified(participation, {}, None, report)
            assert d.code == "selection_missing" and d.code in c.CODES, (code, participation)
            assert d.kind in ("required_policy_unavailable", "overlay_not_applied") and d.operationally_authorized is False
        rec_bad = SimpleNamespace(ok=False, code=code)
        ok_report = SimpleNamespace(ok=True, participation="required", layers={"record_binding": "pass"}, bound_record_digest=None)
        d = decision._decide_verified("required", {}, rec_bad, ok_report)
        assert d.code == "composition_record_invalid" and d.code in c.CODES


def test_no_v1_entry_point_emits_a_revision_2_code_for_hostile_or_missing_input():
    for args in (("required", {}, None, None, None, None, None, None), ("optional", {}, "", "", None, None, None, None), ("bogus", {}, "x", "y", None, None, None, None)):
        d = decision.verify_and_decide(*args)
        assert d.code in c.CODES and d.code not in NEW + V2_ONLY and d.operationally_authorized is False


@pytest.mark.parametrize("bad", ("r08-v2-reasons/2", "r08-v2.1", "r08-v3", "", None, 2, b"r08-v2"))
def test_unsupported_versions_still_refuse_contract_unsupported(bad):
    sel = families.table_for_contract_version(bad)
    assert sel.ok is False and sel.code == "contract_unsupported" and sel.table is None


@pytest.mark.parametrize("code", NEW)
@pytest.mark.parametrize("participation", ("required", "optional"))
def test_refusal_rev2_is_never_an_optional_fallback_and_never_remaps(code, participation):
    d = decision.refusal_rev2(participation, code, "x")
    assert (d.kind, d.code, d.effective, d.caller_unchanged, d.deny_all, d.operationally_authorized) == ("required_policy_unavailable", code, None, False, False, False)
    assert d.kind != "overlay_not_applied"


@pytest.mark.parametrize("bad", ("selection_missing", "selection_withdrawn", "trust_snapshot_version_stale", "field_invalid", "", "x", None, 1, b"store_unknown", ["store_unknown"]))
def test_refusal_rev2_accepts_only_the_three_additive_codes(bad):
    with pytest.raises(ValueError) as info:
        decision.refusal_rev2("required", bad)
    assert str(info.value) == "not a revision-2 additive code"  # a fixed message: the offending object is never formatted


@pytest.mark.parametrize("bad", (None, "", "REQUIRED", "required ", 0, ["required"]))
def test_refusal_rev2_with_a_bad_participation_is_a_revision_1_refusal(bad):
    d = decision.refusal_rev2(bad, "store_unknown")
    assert d.code == "participation_mismatch" and d.code in c.CODES and d.kind == "required_policy_unavailable" and d.effective is None


def test_refusal_rev2_with_a_hostile_participation_never_runs_its_eq_or_hash():
    class Boom:
        def __eq__(self, other):
            raise RuntimeError("hostile __eq__")

        __hash__ = None

    class BoomStr(str):
        def __eq__(self, other):
            raise RuntimeError("hostile str __eq__")

        __hash__ = str.__hash__

    class Liar(str):
        def __eq__(self, other):
            return True

        __hash__ = str.__hash__

    for bad in (Boom(), BoomStr("required"), Liar("nope")):
        d = decision.refusal_rev2(bad, "store_unknown")
        assert d.code == "participation_mismatch" and d.kind == "required_policy_unavailable" and d.operationally_authorized is False


def test_withdrawal_and_snapshot_floor_mappings_are_not_introduced_here():
    """Ruling 4.4: introduced only when their owning contracts and codes are available. The codes are declared (CODES_V2) but no evaluator and no owning contract
    implementation exist in this package, so the identity module has no row and no behaviour for them."""
    src = (PKG / "v2_policy_identity.py").read_text(encoding="utf-8")
    for code in V2_ONLY:
        assert code not in src
        assert code not in {r.registry_code for r in m.REFUSAL_MAPPING}
        assert code in m.UNMAPPED_CODES
    for ids in ("MP-selection_withdrawn", "MP-trust_snapshot_version_stale"):
        assert ids not in m.MAPPING_BY_ID


def test_revision_2_symbol_has_one_definition_and_the_identity_module_only_imports_it():
    defs = []
    for path in sorted(PKG.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "CODES_V2_REV2" for t in node.targets):
                defs.append(path.name)
    assert defs == ["v2_codes.py"]
    assert m.CODES_V2_REV2 is CODES_V2_REV2
