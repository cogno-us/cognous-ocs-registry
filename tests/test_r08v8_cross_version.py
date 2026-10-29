"""Cross-version refusal for `r08-v8` (APPROVED CANDIDATE; BUILDER_TESTED; not independently qualified).

A document of one contract is accepted by that contract's entry point only. v6, v7 and v8 documents (record + signed selection) are run through every other entry point; the
three v8 family ids stay `family_unsupported` under r08-v7 (a v7 document naming them is not applied); irreversibility is `family_unsupported` under r08-v8; a signature made
over one contract's domain never verifies under another's. The `V6_COMPAT` differential (tests/test_r08v7_engine_differential.py) is untouched and still the proof that the
engine equals the frozen r08-v6 contract; here the additive `scalar-int` kind is shown not to alter it.
"""
import pytest

import r08_support as r
import r08v6_support as t6
import r08v7_support as t7
import r08v8_support as t8
import s01_support as s
from registry_successor import decision as d2
from registry_successor import v3_decision, v4_decision, v5_decision, v6_decision, v7_decision, v8_decision
from registry_successor import v7_families, v8_families
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e
from registry_successor.engine import selection as selection_e

pytestmark = pytest.mark.skipif(not t8.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

ENTRIES = {"r08-v2": d2.verify_and_decide_v2, "r08-v3": v3_decision.verify_and_decide_v3, "r08-v4": v4_decision.verify_and_decide_v4,
           "r08-v5": v5_decision.verify_and_decide_v5, "r08-v6": v6_decision.verify_and_decide_v6, "r08-v7": v7_decision.verify_and_decide_v7,
           "r08-v8": v8_decision.verify_and_decide_v8}


def run(entry, cl, rec, sel):
    ad = t8.ev.Ed25519Verifier()
    return ENTRIES[entry]("required", cl, r.dumps(rec), sel, s.CTX, s.trust(pub=t8.PK), ad, r.NOW, ad.key_admission)


def docs():
    out = {}
    for fam in t6.FAMILIES:
        rec = t6.record(family=fam)
        out[("r08-v6", fam)] = (rec, t6.selection_text(rec), t6.caller(fam))
    rec7 = t7.record()
    out[("r08-v7", t7.FAMILY)] = (rec7, t7.selection_text(rec7), t7.caller())
    for fam in t8.FAMILIES:
        rec = t8.record(family=fam)
        out[("r08-v8", fam)] = (rec, t8.selection_text(rec), t8.caller(fam))
    return out


DOCS = docs()


@pytest.mark.parametrize("key", sorted(DOCS))
def test_each_document_is_applied_by_its_own_entry_point_only(key):
    contract, fam = key
    rec, sel, cl = DOCS[key]
    own = run(contract, cl, rec, sel)
    assert own.kind == "applied" and own.operationally_authorized is False
    for entry in ENTRIES:
        if entry == contract:
            continue
        got = run(entry, cl, rec, sel)
        assert got.kind == "required_policy_unavailable" and got.effective is None and got.operationally_authorized is False, (entry, key)
        assert got.code == "contract_unsupported", (entry, key, got.code)


@pytest.mark.parametrize("fam", t8.FAMILIES, ids=["anchor", "max_age", "tolerance"])
def test_v7_still_refuses_the_three_family_ids_in_records_selections_and_decisions(fam):
    rec = t7.record(family=fam, pl=t8.payload(fam))
    assert record_e.validate_record_text(profiles.V7, r.dumps(rec)).code == "family_unsupported"
    stmt = r.make_statement_v2(rec, family=fam)
    text = r.dumps(s.envelope(stmt, domain=t7.V7_DOMAIN, contract="r08-v7", signature=t7.sign(stmt), pub=t7.PK))
    assert selection_e.parse_selection_envelope(profiles.V7, text).code == "family_unsupported"
    d = run("r08-v7", t8.caller(fam), rec, text)
    t7.assert_refused(d, "family_unsupported")
    assert v7_families.lookup_v7(fam) is None and fam not in profiles.V7.families and len(profiles.V7.families) == 1


def test_v8_refuses_irreversibility_in_records_selections_and_decisions():
    rec = t8.record(family=t7.FAMILY, pl=t7.payload())  # irreversibility payload, relabelled r08-v8
    assert record_e.validate_record_text(profiles.V8, r.dumps(rec)).code == "family_unsupported"
    stmt = r.make_statement_v2(rec, family=t7.FAMILY)
    text = r.dumps(s.envelope(stmt, domain=t8.V8_DOMAIN, contract="r08-v8", signature=t8.sign(stmt), pub=t8.PK))
    assert selection_e.parse_selection_envelope(profiles.V8, text).code == "family_unsupported"
    t8.assert_refused(run("r08-v8", t7.caller(), rec, text), "family_unsupported")
    # a genuine v7 irreversibility selection (v7 domain, v7 label) carrying a v7 record is contract_unsupported under v8, and relabelling it r08-v8 fails on the family
    rec7 = t7.record()
    t8.assert_refused(run("r08-v8", t7.caller(), rec7, t7.selection_text(rec7)), "contract_unsupported")
    relabelled = r.dumps(s.envelope(t7.statement(rec7), domain=t7.V7_DOMAIN, contract="r08-v8", signature=t7.sign(t7.statement(rec7)), pub=t7.PK))
    t8.assert_refused(run("r08-v8", t7.caller(), rec7, relabelled), "family_unsupported")
    assert v8_families.lookup_v8(t7.FAMILY) is None


@pytest.mark.parametrize("fam", t8.FAMILIES, ids=["anchor", "max_age", "tolerance"])
def test_a_v8_family_selection_signed_over_another_contracts_domain_never_verifies(fam):
    rec = t8.record(family=fam)
    stmt = t8.statement(rec)
    for domain in (t7.V7_DOMAIN, t6.V6_DOMAIN, t6.V5_DOMAIN, s.V2_DOMAIN, s.V1_DOMAIN):
        sel = r.dumps(s.envelope(stmt, domain=domain, contract="r08-v8", signature=t8.sign(stmt, domain=domain), pub=t8.PK))
        t8.assert_refused(run("r08-v8", t8.caller(fam), rec, sel), "signature_invalid")
    # the v8-signed statement placed in an envelope that declares another contract is not verified at that contract's entry point either
    for contract in ("r08-v7", "r08-v6"):
        sel = r.dumps(s.envelope(stmt, domain=t8.V8_DOMAIN, contract=contract, signature=t8.sign(stmt), pub=t8.PK))
        got = run(contract, t8.caller(fam), rec, sel)
        assert got.kind == "required_policy_unavailable" and got.code in ("contract_unsupported", "family_unsupported")


def test_a_v7_signature_does_not_verify_a_v8_statement_and_the_reverse():
    rec7 = t7.record()
    stmt7 = t7.statement(rec7)
    assert t7.sign(stmt7) != t7.sign(stmt7, domain=t8.V8_DOMAIN)
    rec8 = t8.record(family=t8.ANCHOR)
    stmt8 = t8.statement(rec8)
    assert t8.sign(stmt8) != t8.sign(stmt8, domain=t7.V7_DOMAIN)


def test_the_three_family_records_do_not_validate_under_the_earlier_profiles_and_the_reverse():
    for fam in t8.FAMILIES:
        rec = r.dumps(t8.record(family=fam))
        for prof in (profiles.V7, profiles.V6_COMPAT):
            assert record_e.validate_record_text(prof, rec).code == "contract_unsupported"
    rec7 = r.dumps(t7.record())
    assert record_e.validate_record_text(profiles.V8, rec7).code == "contract_unsupported"
    assert record_e.validate_record_text(profiles.V7, rec7).ok


def test_v8_has_no_fallback_or_implicit_upgrade():
    rec = t8.record(family=t8.MAXAGE)
    sel = t8.selection_text(rec)
    for bad in ("R08-V8", "r08-v8 ", " r08-v8", "r08-v8\n", "r08-v9", "r08-v8.1", "", "r08-v"):
        got = run("r08-v8", t8.caller(t8.MAXAGE), rec, t8.selection_text(rec, contract=bad))
        assert got.kind == "required_policy_unavailable" and got.code == "contract_unsupported", bad
    for bad in ("R08-V8", "r08-v8 ", "r08-v9", ""):
        rec_bad = t8.record(family=t8.MAXAGE, contract=bad)
        assert record_e.validate_record_text(profiles.V8, r.dumps(rec_bad)).code == "contract_unsupported", bad
        got = run("r08-v8", t8.caller(t8.MAXAGE), rec_bad, sel)  # the decision reports a refused record as composition_record_invalid (as r08-v7 does)
        assert got.kind == "required_policy_unavailable" and got.code == "composition_record_invalid" and got.effective is None, bad


def test_v6_compat_engine_decision_equals_the_frozen_v6_entry_point_on_the_v6_vectors():
    """A smoke over the same shape as the merged differential (which remains the full proof): the engine under V6_COMPAT and the frozen v6 agree after the additive
    `scalar-int` kind."""
    from registry_successor.engine import decide as decide_e
    for fam in t6.FAMILIES:
        rec = t6.record(family=fam)
        sel = t6.selection_text(rec)
        ad = t8.ev.Ed25519Verifier()
        args = ("required", t6.caller(fam), r.dumps(rec), sel, s.CTX, s.trust(pub=t6.PK), ad, r.NOW, ad.key_admission)
        assert decide_e.verify_and_decide(profiles.V6_COMPAT, *args) == v6_decision.verify_and_decide_v6(*args)
