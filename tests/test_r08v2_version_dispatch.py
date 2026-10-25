"""EXT-S1-3 tests: selection of the family table by `contract_version`. BUILDER_TESTED, not independently qualified."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import families  # noqa: E402
from registry_successor import record as record_mod  # noqa: E402
from registry_successor import v2_f1ab as f  # noqa: E402

V1, V2 = "r08-v1", "r08-v2"


class StrSub(str):
    pass


class EvilStr(str):
    def __eq__(self, o):
        return True

    __hash__ = str.__hash__


def pl():
    return {"allowed_actions": ["a"], "allowed_adapters": ["x"], "allowed_units": ["u"], "allowed_institutions": ["i"],
            "allowed_authority_domains": ["d"]}


def cl():
    return {"allowed_actions": ["a", "b"], "allowed_adapters": ["x"], "allowed_units": ["u"], "allowed_institutions": ["i"],
            "allowed_authority_domains": ["d"]}


def rec(family, payload):
    body = dict(s.make_record(), family=family, payload=payload)
    return record_mod.RecordResult(True, None, "", body, body["record_digest"])


def test_version_strings_are_the_repo_strings():
    assert families.CONTRACT_V1 == c.CONTRACT_VERSION == V1 and families.CONTRACT_V2 == V2


def test_each_version_selects_only_its_table():
    a, b = families.table_for_contract_version(V1), families.table_for_contract_version(V2)
    assert (a.ok, a.code, a.table, a.version) == (True, None, families.FAMILIES, V1)
    assert (b.ok, b.code, b.table, b.version) == (True, None, families.FAMILIES_V2, V2)
    assert a.table is not b.table and f.FAMILY_F1AB not in a.table and f.FAMILY_F1AB in b.table


@pytest.mark.parametrize("v", [None, b"r08-v1", b"r08-v2", "R08-V1", "R08-V2", "r08-V2", " r08-v1", "r08-v2 ", "r08-v2\n", "\tr08-v1",
                               "r08-v3", "r08-v0", "r08-v", "r08", "", 1, 2, 1.0, True, ["r08-v1"], ("r08-v2",), {"r08-v1"},
                               StrSub(V1), StrSub(V2), EvilStr("x"), EvilStr(V1), object(), "r08‑v1", "r08-v1\x00"])
def test_unknown_or_malformed_versions_refuse_without_a_table(v):
    r = families.table_for_contract_version(v)
    assert (r.ok, r.code, r.table, r.version) == (False, "contract_unsupported", None, None)
    assert r.code in c.CODES
    assert families.lookup_for(v, c.FAMILY_F1A) is None
    assert families.lookup_for(v, f.FAMILY_F1AB) is None
    res = families.compose_for(v, cl(), rec(c.FAMILY_F1A, {k: ["a"] for k in c.F1A_FIELDS}))
    assert (res.ok, res.code, res.effective) == (False, "contract_unsupported", None)
    res = families.compose_for(v, cl(), rec(f.FAMILY_F1AB, pl()))
    assert (res.ok, res.code, res.effective) == (False, "contract_unsupported", None)


def test_lookup_for_is_version_specific():
    assert families.lookup_for(V1, c.FAMILY_F1A) is families.FAMILIES[c.FAMILY_F1A]
    assert families.lookup_for(V2, c.FAMILY_F1A) is families.FAMILIES_V2[c.FAMILY_F1A]
    assert families.lookup_for(V1, f.FAMILY_F1AB) is None
    assert families.lookup_for(V2, f.FAMILY_F1AB) is families.FAMILIES_V2[f.FAMILY_F1AB]
    for bad in (None, 3, b"f1ab"):
        assert families.lookup_for(V2, bad) is None


def test_f1ab_under_v1_refuses_family_unsupported_golden_consistent():
    body = s.seal_record({**s.make_record(), "family": f.FAMILY_F1AB, "payload": pl()})
    import json
    res = record_mod.validate_record_text(json.dumps(body))
    assert (res.ok, res.code) == (False, "family_unsupported")
    r = families.compose_for(V1, cl(), rec(f.FAMILY_F1AB, pl()))
    assert (r.ok, r.code, r.effective) == (False, "composition_family_unsupported", None)


def test_f1ab_under_v2_composes_all_five_fields_and_empty_set_denies():
    r = families.compose_for(V2, cl(), rec(f.FAMILY_F1AB, pl()))
    assert r.ok and set(r.effective) == set(f.F1AB_FIELDS) and r.effective["allowed_actions"] == ("a",)
    r = families.compose_for(V2, cl(), rec(f.FAMILY_F1AB, {**pl(), "allowed_units": []}))
    assert r.ok and r.effective["allowed_units"] == ()


def test_v1_shaped_f1a_payload_under_v2_is_the_existing_v2_f1a_path():
    r1 = rec(c.FAMILY_F1A, {k: ["a"] for k in c.F1A_FIELDS})
    caller = {k: ["a", "b"] for k in c.F1A_FIELDS}
    v2 = families.compose_for(V2, caller, r1)
    assert v2 == families.compose_v2(caller, r1) == families.compose(caller, r1) == families.compose_for(V1, caller, r1)
    assert v2.ok and set(v2.effective) == set(c.F1A_FIELDS)
    # three-key payload is never reinterpreted as five-key f1ab: a different family string is a different family
    r2 = families.compose_for(V2, cl(), rec(f.FAMILY_F1AB, {k: ["a"] for k in c.F1A_FIELDS}))
    assert not r2.ok and r2.effective is None


def test_no_implicit_upgrade_or_downgrade():
    # f1ab never reachable from v1 selection; v1 table never mutated by v2 selection
    families.table_for_contract_version(V2)
    assert set(families.FAMILIES) == {c.FAMILY_F1A}
    assert not families.compose_for(V1, cl(), rec(f.FAMILY_F1AB, pl())).ok
    # an unsupported version never falls back to either table
    assert not families.compose_for("r08-v3", cl(), rec(c.FAMILY_F1A, {k: ["a"] for k in c.F1A_FIELDS})).ok
    # v1 entry points still reject a v2 contract_version record
    body = s.seal_record({**s.make_record(), "contract_version": V2})
    import json
    assert record_mod.validate_record_text(json.dumps(body)).code == "contract_unsupported"


def test_required_policy_refusal_never_returns_caller_policy():
    for v in (V1, V2, "r08-v3", None):
        r = families.compose_for(v, cl(), rec("f9-unknown", pl()))
        assert not r.ok and r.effective is None
