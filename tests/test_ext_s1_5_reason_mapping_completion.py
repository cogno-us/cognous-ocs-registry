"""EXT-S1-5 reason-mapping completion over the 51-code revision-2 vocabulary (`r08-v2-reasons/2`, `CODES_V2_REV2`).

Amendment 1 section 6.5 (docs/r08-v2-contract-amendment-1.md) obliges the implementation PR to declare `CODES_V2_REV2` in `v2_codes.py`, add a 51-code outcome map
(the 48-code map stays pinned) and extend the completeness test to all 51. Architect Batch 6 rulings 4.3, 4.7 and N-12 fix the three additive classes. Reads files as text
or JSON; changes nothing. BUILDER_TESTED, not qualified; the Control Plane owner has not ratified the outcome or classification of the three codes.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

from registry_successor import common as c
from registry_successor import v2_policy_identity as m
from registry_successor.v2_codes import CODES_V2, CODES_V2_REV2, REV2_ADDED_CODES

ROOT = Path(__file__).resolve().parent.parent
BASE_MAP_PATH = ROOT / "docs/p1-extraction-plan/data/ld02-outcome-map.json"
REV2_MAP_PATH = ROOT / "docs/p1-extraction-plan/data/ld02-outcome-map-rev2.json"
BASE_MAP = json.loads(BASE_MAP_PATH.read_text(encoding="utf-8"))
REV2_MAP = json.loads(REV2_MAP_PATH.read_text(encoding="utf-8"))
NEW = ("not_activated", "policy_identity_mismatch", "store_unknown")


def _missing(base_codes, added_codes):
    """The completeness rule as a function, so a deletion can be shown to fail it."""
    return set(CODES_V2_REV2) - set(base_codes) - set(added_codes)


def test_revision_2_is_revision_1_plus_exactly_the_three_codes_in_order():
    assert len(c.CODES) == 46 and len(CODES_V2) == 48 and len(CODES_V2_REV2) == 51
    assert list(CODES_V2_REV2)[:46] == list(c.CODES) and list(CODES_V2_REV2)[:48] == list(CODES_V2)
    assert all(CODES_V2_REV2[k] == CODES_V2[k] for k in CODES_V2)
    assert tuple(list(CODES_V2_REV2)[48:]) == NEW and tuple(REV2_ADDED_CODES) == NEW
    assert [CODES_V2_REV2[k][0] for k in NEW] == ["selection", "identity", "trust"]
    assert not set(NEW) & set(CODES_V2) and not set(NEW) & set(c.CODES)
    for code in NEW:
        assert re.fullmatch(r"[a-z]+(_[a-z0-9]+)*", code) and CODES_V2_REV2[code][1]
    with pytest.raises(TypeError):
        CODES_V2_REV2["x"] = ("a", "b")


def test_contract_version_is_never_the_revision_designation():
    from registry_successor import families
    for bad in ("r08-v2-reasons/2", "r08-v2-reasons/1", "r08-v2.1", "r08-v2.2"):
        sel = families.table_for_contract_version(bad)
        assert sel.ok is False and sel.code == "contract_unsupported", bad
    assert families.table_for_contract_version("r08-v2").ok is True and families.table_for_contract_version("r08-v1").ok is True


def test_rev2_outcome_map_inherits_the_pinned_48_and_adds_exactly_three():
    meta = REV2_MAP["meta"]
    assert meta["code_count"] == 51 and meta["vocabulary_revision"] == "r08-v2-reasons/2" and meta["vocabulary_symbol"] == "CODES_V2_REV2"
    assert meta["inherits"]["sha256"] == hashlib.sha256(BASE_MAP_PATH.read_bytes()).hexdigest()  # the 48-code map is the pinned file, byte for byte
    assert meta["inherits"]["code_count"] == 48 and set(BASE_MAP["codes"]) == set(CODES_V2) and len(BASE_MAP["codes"]) == 48
    assert tuple(meta["added_codes_order"]) == NEW and set(REV2_MAP["codes_added"]) == set(NEW)
    assert _missing(BASE_MAP["codes"], REV2_MAP["codes_added"]) == set()
    assert set(BASE_MAP["codes"]) | set(REV2_MAP["codes_added"]) == set(CODES_V2_REV2)
    assert not set(BASE_MAP["codes"]) & set(REV2_MAP["codes_added"])


def test_completeness_fails_for_any_deleted_entry():
    for code in NEW:
        assert _missing(BASE_MAP["codes"], {k: v for k, v in REV2_MAP["codes_added"].items() if k != code}) == {code}
    for code in ("selection_missing", "selection_withdrawn", "trust_snapshot_version_stale"):
        assert _missing({k: v for k, v in BASE_MAP["codes"].items() if k != code}, REV2_MAP["codes_added"]) == {code}


def test_no_entry_can_authorize_an_action():
    for code, entry in {**BASE_MAP["codes"], **REV2_MAP["codes_added"]}.items():
        assert entry["can_authorize_action"] is False, code
    for entry in REV2_MAP["codes_added"].values():
        assert entry["required_behavior"]["policy_returned"] is None and entry["required_behavior"]["caller_policy_returned"] is False


def test_rev2_codes_are_never_an_optional_fallback_in_the_map():
    """N-12: none of the three yields overlay_not_applied under optional participation."""
    for code, entry in REV2_MAP["codes_added"].items():
        opt = entry["optional_behavior"]
        assert opt["overlay_not_applied"] is False and opt["caller_policy_returned"] is False and opt["decision_kind"] == "required_policy_unavailable", code
        assert entry["in_CODES"] is False and entry["in_CODES_V2"] is False and entry["in_CODES_V2_REV2"] is True


def test_classes_follow_the_rulings_and_agree_with_the_module_mapping():
    classes = {code: REV2_MAP["codes_added"][code]["verdict_class"] for code in NEW}
    assert classes == {"not_activated": "REFUSE", "policy_identity_mismatch": "REFUSE", "store_unknown": "UNKNOWN_FAIL_CLOSED"}
    for code in NEW:
        row = m.verdict_for(code)
        assert row.verdict_class == classes[code] and row.decision_kind == "required_policy_unavailable" and row.optional_overlay is False
        assert REV2_MAP["codes_added"][code]["retry_class"] == row.retry
    # ruling 4.7: the Control Plane proposal is NOT a blanket HOLD (definitive invalidity REFUSE, indeterminate HOLD) and carries no deny
    proposed = {code: REV2_MAP["codes_added"][code]["control_plane_f4_f5"]["proposed_outcome"] for code in NEW}
    assert proposed == {"not_activated": "REFUSE", "policy_identity_mismatch": "REFUSE", "store_unknown": "HOLD"}
    assert all(REV2_MAP["codes_added"][c_]["control_plane_f4_f5"]["status"] == "UNRATIFIED_OWNER_RECORD_REQUIRED" for c_ in NEW)
    assert all(REV2_MAP["codes_added"][c_]["control_plane_f4_f5"]["deny_used"] is False for c_ in NEW)


def test_every_revision_2_code_is_mapped_by_the_module_or_owned_elsewhere():
    mapped = {r.registry_code for r in m.REFUSAL_MAPPING}
    assert mapped | set(m.UNMAPPED_CODES) == set(CODES_V2_REV2) and not mapped & set(m.UNMAPPED_CODES)
    for code in m.UNMAPPED_CODES:  # each unmapped code has a full entry in the pinned map: it is owned by another package, not forgotten
        assert code in BASE_MAP["codes"], code
    assert {"selection_withdrawn", "trust_snapshot_version_stale"} <= set(m.UNMAPPED_CODES)  # held back: owning contracts and evaluators are not in this package
    assert set(NEW) <= mapped


def test_policy_identity_mismatch_covers_all_six_members_and_routes_stale_to_its_own_code():
    row = m.verdict_for("policy_identity_mismatch")
    ev = set(row.evidence_fields)
    assert {"scope_key_digest", "selection_id", "selection_epoch", "selection_digest", "record_id", "record_version", "record_digest", "activation_ref", "member"} <= ev
    assert m.POLICY_IDENTITY_MEMBER_SET == ("scope_key", "selection_id", "selection_epoch", "selection_digest", "record", "activation_ref")
    assert m.POLICY_IDENTITY_MEMBER_VALUES == ("scope_key", "selection_id", "selection_epoch", "selection_digest", "record_id", "record_version", "record_digest", "activation_ref")
    stale = m.verdict_for("selection_epoch_stale")
    assert stale.verdict_class == "REFUSE_STALE" and "high_water_epoch" in stale.evidence_fields
    assert "high_water_epoch" in ev  # the mismatch evidence can name the row it differed from
