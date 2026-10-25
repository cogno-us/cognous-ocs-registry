"""R08-S01 Lane D developer tests for registry_successor.verify (DEVELOPER-TESTED, not independently qualified).

Uses the FakeVerifier test double from tests/r08_support.py; it is not cryptography.
"""
import copy
import datetime
import sys
import unittest
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import verify as v  # noqa: E402

Sel = namedtuple("Sel", "ok code detail envelope statement statement_digest signatures")
Rec = namedtuple("Rec", "ok code detail record record_digest")
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
GRANT = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
KEY = b"public-key-test-1"
UTC = datetime.timezone.utc


def sel_from(env, ok=True, code=None):
    return Sel(ok, code, "", env, env["statement"], env["statement_digest"], env["signatures"])


def issuer(key_id="key-test-1", key=KEY, grants=(GRANT,), alg="ed25519", issuer_id="issuer-test-1"):
    return v.IssuerEntry(key_id, issuer_id, alg, key, tuple(grants))


def trust(**over):
    base = dict(snapshot_id="snapshot-1", version=1, valid_until="2026-10-27T00:00:00Z", issuers=(issuer(),),
                revoked_key_ids=frozenset(), revoked_selections=frozenset(), min_epochs=())
    base.update(over)
    return v.TrustSnapshot(**base)


def rec_from(record):
    return Rec(True, None, "", record, record["record_digest"])


def run(env=None, ctx=CTX, tr=None, verifier="fake", now=r.NOW, record=None, selection=None):
    env = env or r.make_envelope()
    selection = selection or sel_from(env)
    tr = trust() if tr is None else tr
    verifier = r.FakeVerifier() if verifier == "fake" else verifier
    return v.verify_selection(selection, ctx, tr, verifier, now, record)


class Pass(unittest.TestCase):
    def test_full_pass(self):
        rep = run(record=rec_from(r.make_record()))
        self.assertTrue(rep.ok, rep)
        self.assertIsNone(rep.code)
        self.assertTrue(rep.authenticated)
        self.assertEqual(rep.issuer_id, "issuer-test-1")
        self.assertEqual(set(rep.layers), set(v.LAYERS))
        self.assertTrue(all(x == "pass" for x in rep.layers.values()))

    def test_without_record_binding_not_evaluated(self):
        rep = run()
        self.assertTrue(rep.ok)
        self.assertEqual(rep.layers["record_binding"], "not_evaluated")

    def test_never_operationally_authorized(self):
        self.assertFalse(run().operationally_authorized)
        self.assertFalse(run(verifier=None).operationally_authorized)
        self.assertFalse(run(tr=None, ctx=None).operationally_authorized)

    def test_deterministic(self):
        self.assertEqual(run(), run())


class EachLayer(unittest.TestCase):
    def test_structural(self):
        rep = run(selection=sel_from(r.make_envelope(), ok=False, code="field_missing"))
        self.assertEqual((rep.ok, rep.code, rep.layers["structural"]), (False, "field_missing", "refuse"))
        self.assertEqual(rep.layers["integrity"], "not_evaluated")
        self.assertEqual(rep.layers["trust_snapshot"], "pass")  # independent of the selection

    def test_structural_none(self):
        rep = v.verify_selection(None, CTX, trust(), r.FakeVerifier(), r.NOW)
        self.assertFalse(rep.ok)
        self.assertEqual(rep.layers["structural"], "refuse")

    def test_integrity(self):
        env = r.make_envelope()
        env["statement_digest"] = "sha256:" + "0" * 64
        rep = run(env)
        self.assertEqual((rep.code, rep.layers["integrity"]), ("digest_mismatch", "refuse"))

    def test_record_binding(self):
        rec = r.make_record()
        other = r.make_record(record_version=2)
        self.assertEqual(run(record=rec_from(other)).code, "record_identity_mismatch")
        digest_other = r.make_record(payload={"allowed_actions": ["x-action"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]})
        self.assertEqual(run(record=rec_from(digest_other)).code, "record_digest_mismatch")
        ev = copy.deepcopy(rec)
        ev["evaluator"]["source_blob_id"] = "0" * 40
        ev = r.seal_record(ev)
        env = r.make_envelope(r.make_statement(rec))
        self.assertEqual(run(env, record=rec_from(ev)).code, "record_digest_mismatch")
        stmt = r.make_statement(rec)
        stmt["evaluator"] = dict(stmt["evaluator"], source_blob_id="1" * 40)
        self.assertEqual(run(r.make_envelope(stmt), record=rec_from(rec)).code, "evaluator_mismatch")
        self.assertEqual(run(record=Rec(False, "field_invalid", "", None, None)).code, "composition_record_invalid")

    def test_trust_snapshot(self):
        self.assertTrue(run().ok)  # default fixture sanity
        rep = v.verify_selection(sel_from(r.make_envelope()), CTX, None, r.FakeVerifier(), r.NOW)
        self.assertEqual((rep.code, rep.layers["trust_snapshot"]), ("trust_snapshot_missing", "refuse"))
        self.assertEqual(run(tr=trust(snapshot_id="")).code, "trust_snapshot_invalid")
        self.assertEqual(run(tr=trust(version=0)).code, "trust_snapshot_invalid")
        self.assertEqual(run(tr=trust(valid_until="tomorrow")).code, "trust_snapshot_invalid")
        self.assertEqual(run(tr=trust(issuers=(issuer(), issuer()))).code, "trust_snapshot_invalid")
        self.assertEqual(run(tr="not a snapshot").code, "trust_snapshot_invalid")
        self.assertEqual(run(tr=trust(valid_until="2026-10-25T12:00:00Z")).code, "trust_snapshot_expired")
        self.assertEqual(run(tr=trust(valid_until="2026-10-25T12:00:01Z")).ok, True)
        self.assertEqual(run(now=None).code, "time_unavailable")
        self.assertEqual(run(now=datetime.datetime(2026, 10, 25, 12)).code, "time_unavailable")  # naive time

    def test_authenticity(self):
        self.assertEqual(run(r.make_envelope(signed=False)).code, "signature_missing")
        env = r.make_envelope()
        env["signatures"][0]["alg"] = "rsa"
        self.assertEqual(run(env).code, "signature_algorithm_unsupported")
        env = r.make_envelope(key_id="key-unknown")
        self.assertEqual(run(env).code, "issuer_untrusted")
        self.assertEqual(run(tr=trust(revoked_key_ids=frozenset({"key-test-1"}))).code, "issuer_key_revoked")
        env = r.make_envelope()
        env["signatures"][0]["signature"] = "!!not base64!!"
        self.assertEqual(run(env).code, "signature_invalid")
        env = r.make_envelope()
        env["signatures"][0]["signature"] = r.fake_signature(b"other-key", b"msg")
        rep = run(env)
        self.assertEqual((rep.code, rep.authenticated, rep.layers["authenticity"]), ("signature_invalid", False, "refuse"))
        self.assertEqual(run(tr=trust(issuers=(issuer(alg="rsa"),))).code, "signature_invalid")

    def test_authority(self):
        other = v.AuthorityGrant("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test")
        rep = run(tr=trust(issuers=(issuer(grants=(other,)),)))
        self.assertEqual((rep.code, rep.layers["authority"], rep.layers["authenticity"]), ("issuer_not_authorized", "refuse", "pass"))
        rep = run(tr=trust(issuers=(issuer(grants=()),)))
        self.assertEqual(rep.code, "issuer_not_authorized")
        wild = v.AuthorityGrant("consumer-test", "*", "inst-a", "domain-a", "op-test")
        self.assertEqual(run(tr=trust(issuers=(issuer(grants=(wild,)),))).code, "trust_snapshot_invalid")  # tokens exclude '*'

    def test_authority_requires_authenticity(self):
        rep = run(verifier=None)
        self.assertEqual(rep.layers["authority"], "not_evaluated")

    def test_scope(self):
        self.assertEqual(run(ctx=c.ExpectedContext("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test")).code, "selection_consumer_mismatch")
        self.assertEqual(run(ctx=c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test")).code, "selection_scope_mismatch")
        self.assertEqual(run(ctx=c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test")).code, "selection_scope_mismatch")
        self.assertEqual(run(ctx=c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test")).code, "selection_scope_mismatch")
        self.assertEqual(run(ctx=c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")).code, "selection_operation_mismatch")
        self.assertEqual(run(ctx=None).code, "selection_scope_mismatch")

    def test_time_boundaries(self):
        def at(h, m=0, s=0, d=25):
            return datetime.datetime(2026, 10, d, h, m, s, tzinfo=UTC)
        self.assertEqual(run(now=datetime.datetime(2026, 10, 24, 23, 59, 59, tzinfo=UTC)).code, "selection_not_yet_effective")
        self.assertTrue(run(now=at(0)).ok)
        self.assertTrue(run(now=datetime.datetime(2026, 10, 25, 23, 59, 59, tzinfo=UTC)).ok)
        rep = run(now=at(0, d=26))
        self.assertEqual((rep.code, rep.layers["time"]), ("selection_expired", "refuse"))
        east = datetime.timezone(datetime.timedelta(hours=2))
        self.assertTrue(run(now=datetime.datetime(2026, 10, 25, 14, tzinfo=east)).ok)  # aware, non-UTC offset

    def test_revocation(self):
        rep = run(tr=trust(revoked_selections=frozenset({("sel-test-1", 1)})))
        self.assertEqual((rep.code, rep.layers["revocation"]), ("selection_revoked", "refuse"))
        self.assertTrue(run(tr=trust(revoked_selections=frozenset({("sel-test-1", 2)}))).ok)
        self.assertTrue(run(tr=trust(revoked_selections=frozenset({("sel-other", 1)}))).ok)
        self.assertEqual(run(tr=trust(revoked_selections=frozenset({"bad"}))).code, "trust_snapshot_invalid")

    def test_epoch_floor(self):
        env = r.make_envelope(r.make_statement(epoch=2))
        self.assertTrue(run(env, tr=trust(min_epochs=(("sel-test-1", 2),))).ok)
        rep = run(env, tr=trust(min_epochs=(("sel-test-1", 3),)))
        self.assertEqual((rep.code, rep.layers["epoch"]), ("selection_epoch_stale", "refuse"))
        self.assertTrue(run(env, tr=trust(min_epochs={"sel-test-1": 2})).ok)
        self.assertTrue(run(env, tr=trust(min_epochs={"sel-other": 9})).ok)  # no floor for this id
        self.assertEqual(run(env, tr=trust(min_epochs=(("sel-test-1", 0),))).code, "trust_snapshot_invalid")
        self.assertEqual(run(env, tr=trust(min_epochs=(("sel-test-1", 2), ("sel-test-1", 3)))).code, "trust_snapshot_invalid")


class Independence(unittest.TestCase):
    def test_layers_reported_independently(self):
        # wrong tenant AND expired AND revoked AND stale: every layer still reports its own failure.
        env = r.make_envelope(r.make_statement(epoch=1))
        rep = run(env, ctx=c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"),
                  tr=trust(revoked_selections=frozenset({("sel-test-1", 1)}), min_epochs=(("sel-test-1", 5),)),
                  now=datetime.datetime(2026, 10, 26, 12, tzinfo=UTC))
        self.assertEqual(rep.layers["scope"], "refuse")
        self.assertEqual(rep.layers["time"], "refuse")
        self.assertEqual(rep.layers["revocation"], "refuse")
        self.assertEqual(rep.layers["epoch"], "refuse")
        self.assertEqual(rep.layers["authenticity"], "pass")
        self.assertEqual(rep.code, "selection_scope_mismatch")  # first failing in documented order
        self.assertFalse(rep.ok)

    def test_first_failing_order(self):
        env = r.make_envelope()
        env["statement_digest"] = "sha256:" + "1" * 64
        rep = run(env, verifier=None)
        self.assertEqual(rep.code, "digest_mismatch")
        self.assertEqual(rep.layers["authenticity"], "refuse")


class DigestIsNotAuthentication(unittest.TestCase):
    def test_no_verifier_no_authentication(self):
        env = r.make_envelope()
        rep = run(env, verifier=None)
        self.assertEqual(rep.layers["integrity"], "pass")  # the digest matches
        self.assertEqual((rep.ok, rep.code, rep.authenticated), (False, "verifier_unavailable", False))
        self.assertIsNone(rep.issuer_id)

    def test_unsigned_with_matching_digest_is_not_authenticated(self):
        rep = run(r.make_envelope(signed=False))
        self.assertEqual(rep.layers["integrity"], "pass")
        self.assertFalse(rep.authenticated)
        self.assertFalse(rep.ok)

    def test_attacker_redigests_modified_statement_but_cannot_sign(self):
        good = r.make_envelope()
        stmt = copy.deepcopy(good["statement"])
        stmt["scope"]["tenant"] = "tenant-evil"
        forged = {"contract_version": c.CONTRACT_VERSION, "kind": "selection-envelope", "statement": stmt,
                  "statement_digest": c.digest(stmt), "signatures": good["signatures"]}  # copied signature
        rep = run(forged, ctx=c.ExpectedContext("consumer-test", "tenant-evil", "inst-a", "domain-a", "op-test"))
        self.assertEqual(rep.layers["integrity"], "pass")
        self.assertEqual(rep.layers["authenticity"], "refuse")
        self.assertEqual(rep.code, "signature_invalid")
        self.assertFalse(rep.authenticated)

    def test_verifier_raising_is_refusal(self):
        class Boom:
            def verify(self, *a):
                raise RuntimeError("boom")
        rep = run(verifier=Boom())
        self.assertEqual((rep.ok, rep.code, rep.authenticated), (False, "signature_invalid", False))

    def test_verifier_truthy_but_not_true_is_refusal(self):
        class Loose:
            def verify(self, *a):
                return "yes"
        self.assertEqual(run(verifier=Loose()).code, "signature_invalid")


class Robustness(unittest.TestCase):
    def test_garbage_inputs_never_raise_never_accept(self):
        for sel in (None, object(), 5, Sel(True, None, "", None, None, None, None), Sel(True, None, "", {}, {}, "x", "notalist")):
            for tr in (None, object(), trust()):
                for ctx in (None, CTX, object()):
                    rep = v.verify_selection(sel, ctx, tr, r.FakeVerifier(), r.NOW)
                    self.assertFalse(rep.ok)
                    self.assertFalse(rep.operationally_authorized)
                    self.assertIn(rep.code, c.CODES)

    def test_all_report_codes_are_closed(self):
        reps = [run(), run(verifier=None), run(r.make_envelope(signed=False)), run(now=None), run(tr=trust(snapshot_id=""))]
        for rep in reps:
            self.assertTrue(rep.code is None or rep.code in c.CODES)


if __name__ == "__main__":
    unittest.main()
