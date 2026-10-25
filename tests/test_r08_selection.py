"""Developer tests for registry_successor.selection (R08-S01 lane B). DEVELOPER-TESTED only; not independent qualification."""
import copy
import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from registry_successor import common as c
from registry_successor import selection as s
import r08_support as r

CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")


def parse(stmt=None, **over):
    return s.parse_selection_envelope(r.dumps(r.make_envelope(stmt, **over)))


def parse_env(env):
    return s.parse_selection_envelope(r.dumps(env))


def sel(**over):
    return parse(r.make_statement(**over))


class StructureTests(unittest.TestCase):
    def test_valid(self):
        res = parse()
        self.assertTrue(res.ok, res)
        self.assertEqual(res.statement["selection_id"], "sel-test-1")
        self.assertEqual(res.statement_digest, c.digest(res.statement))
        self.assertEqual(len(res.signatures), 1)

    def test_unsigned_is_structurally_valid(self):
        self.assertTrue(parse(signed=False).ok)

    def test_envelope_missing_and_unknown_fields(self):
        base = r.make_envelope()
        for f in s.ENVELOPE_FIELDS:
            env = copy.deepcopy(base)
            del env[f]
            self.assertEqual(parse_env(env).code, "field_missing", f)
        env = copy.deepcopy(base)
        env["extra"] = 1
        self.assertEqual(parse_env(env).code, "field_unknown")

    def test_statement_missing_and_unknown_fields(self):
        for f in s.STATEMENT_FIELDS:
            stmt = r.make_statement()
            del stmt[f]
            self.assertEqual(parse(stmt).code, "field_missing", f)
        stmt = r.make_statement()
        stmt["extra"] = 1
        self.assertEqual(parse(stmt).code, "field_unknown")

    def test_nested_missing_and_unknown(self):
        for name, fields in (("scope", s.SCOPE_FIELDS), ("record", s.RECORD_PIN_FIELDS),
                             ("evaluator", s.EVALUATOR_FIELDS), ("effective", s.EFFECTIVE_FIELDS)):
            for f in fields:
                stmt = r.make_statement()
                del stmt[name][f]
                self.assertEqual(parse(stmt).code, "field_missing", (name, f))
            stmt = r.make_statement()
            stmt[name]["extra"] = "x"
            self.assertEqual(parse(stmt).code, "field_unknown", name)

    def test_contract_and_kind(self):
        self.assertEqual(parse(contract_version="r08-v2").code, "contract_unsupported")
        self.assertEqual(parse(kind="record").code, "kind_unsupported")
        self.assertEqual(parse(r.make_statement(kind="record")).code, "kind_unsupported")
        self.assertEqual(parse(r.make_statement(family="other-family")).code, "family_unsupported")

    def test_types(self):
        for name in ("selection_id", "consumer_id", "operation", "revocation_ref", "selector_ref"):
            self.assertEqual(sel(**{name: 5}).code, "field_type_invalid", name)
            self.assertEqual(sel(**{name: "BAD ID"}).code, "field_invalid", name)
        self.assertEqual(sel(scope=[]).code, "field_type_invalid")
        stmt = r.make_statement()
        stmt["record"] = "x"
        self.assertEqual(parse(stmt).code, "field_type_invalid")
        self.assertEqual(sel(participation="mandatory").code, "field_invalid")
        self.assertEqual(sel(participation=1).code, "field_invalid")
        self.assertEqual(parse_env(r.make_envelope(statement="x")).code, "field_type_invalid")
        self.assertEqual(s.parse_selection_envelope("[]").code, "field_type_invalid")

    def test_epoch(self):
        self.assertEqual(sel(epoch=0).code, "field_invalid")
        self.assertEqual(sel(epoch=-1).code, "field_invalid")
        self.assertEqual(sel(epoch=True).code, "field_type_invalid")
        self.assertEqual(sel(epoch="1").code, "field_type_invalid")
        self.assertEqual(sel(epoch=c.MAX_INT + 1).code, "field_invalid")
        self.assertTrue(sel(epoch=c.MAX_INT).ok)

    def test_scope_tokens(self):
        for bad in ("", "a*b", "a b", "x" * 129, 7):
            stmt = r.make_statement()
            stmt["scope"]["tenant"] = bad
            self.assertEqual(parse(stmt).code, "field_invalid", repr(bad))

    def test_record_pin_and_evaluator(self):
        stmt = r.make_statement()
        stmt["record"]["record_digest"] = "sha256:zz"
        self.assertEqual(parse(stmt).code, "field_invalid")
        stmt = r.make_statement()
        stmt["record"]["record_version"] = 0
        self.assertEqual(parse(stmt).code, "field_invalid")
        stmt = r.make_statement()
        stmt["record"]["record_version"] = True
        self.assertEqual(parse(stmt).code, "field_invalid")
        stmt = r.make_statement()
        stmt["evaluator"]["evaluator_id"] = "other.evaluator"
        self.assertEqual(parse(stmt).code, "evaluator_unsupported")
        stmt = r.make_statement()
        stmt["evaluator"]["binding"] = "dynamic"
        self.assertEqual(parse(stmt).code, "evaluator_unsupported")
        stmt = r.make_statement()
        stmt["evaluator"]["source_blob_id"] = "abc"
        self.assertEqual(parse(stmt).code, "field_invalid")
        stmt = r.make_statement()
        stmt["evaluator"]["source_sha256"] = "deadbeef"
        self.assertEqual(parse(stmt).code, "field_invalid")

    def test_timestamps(self):
        for bad in ("2026-10-25", "2026-10-25T00:00:00", "2026-10-25T00:00:00+00:00", "2026-13-01T00:00:00Z", "", 5):
            stmt = r.make_statement()
            stmt["effective"]["valid_from"] = bad
            self.assertEqual(parse(stmt).code, "field_invalid", repr(bad))
        for bad in ("nope", "2026-10-24T00:00:00"):
            self.assertEqual(sel(issued_at=bad).code, "field_invalid")

    def test_interval_order(self):
        stmt = r.make_statement()
        stmt["effective"] = {"valid_from": "2026-10-26T00:00:00Z", "valid_until": "2026-10-25T00:00:00Z"}
        self.assertEqual(parse(stmt).code, "field_invalid")
        stmt["effective"] = {"valid_from": "2026-10-25T00:00:00Z", "valid_until": "2026-10-25T00:00:00Z"}
        self.assertEqual(parse(stmt).code, "field_invalid")

    def test_supersedes_variants(self):
        good = {"selection_id": "sel-test-1", "epoch": 1, "statement_digest": "sha256:" + "a" * 64, "decision_ref": "decision-2"}
        self.assertTrue(sel(epoch=2, supersedes=good).ok)
        variants = {
            "missing_field": {k: v for k, v in good.items() if k != "decision_ref"},
            "extra_field": dict(good, extra="x"),
            "other_selection": dict(good, selection_id="sel-other"),
            "same_epoch": dict(good, epoch=2),
            "higher_epoch": dict(good, epoch=3),
            "bad_digest": dict(good, statement_digest="sha256:short"),
            "bad_decision": dict(good, decision_ref="Bad Ref"),
            "epoch_bool": dict(good, epoch=True),
            "not_dict": "sel",
            "list": [],
        }
        for name, sup in variants.items():
            self.assertEqual(sel(epoch=2, supersedes=sup).code, "selection_supersession_invalid", name)

    def test_signatures(self):
        good = {"alg": "ed25519", "key_id": "key-test-1", "signature": "AAAA"}
        self.assertTrue(parse(signed=False, signatures=[good]).ok)
        self.assertTrue(parse(signed=False, signatures=[dict(good, alg="rsa-9999")]).ok)  # alg support is verify.py's job
        self.assertEqual(parse(signed=False, signatures="x").code, "field_type_invalid")
        self.assertEqual(parse(signed=False, signatures=[1]).code, "field_type_invalid")
        self.assertEqual(parse(signed=False, signatures=[{"alg": "ed25519"}]).code, "field_missing")
        self.assertEqual(parse(signed=False, signatures=[dict(good, extra=1)]).code, "field_unknown")
        self.assertEqual(parse(signed=False, signatures=[dict(good, alg="")]).code, "field_invalid")
        self.assertEqual(parse(signed=False, signatures=[dict(good, key_id="Bad Key")]).code, "field_invalid")
        self.assertEqual(parse(signed=False, signatures=[dict(good, signature="")]).code, "field_invalid")
        self.assertEqual(parse(signed=False, signatures=[dict(good, signature=5)]).code, "field_type_invalid")
        self.assertEqual(parse(signed=False, signatures=[good] * 9).code, "field_invalid")
        self.assertTrue(parse(signed=False, signatures=[good] * 8).ok)

    def test_digest_mismatch(self):
        env = r.make_envelope()
        env["statement_digest"] = "sha256:" + "0" * 64
        self.assertEqual(parse_env(env).code, "digest_mismatch")
        env = r.make_envelope()
        env["statement"]["epoch"] = 2  # altered after digest
        self.assertEqual(parse_env(env).code, "digest_mismatch")
        env = r.make_envelope()
        env["statement_digest"] = "nope"
        self.assertEqual(parse_env(env).code, "field_invalid")

    def test_parse_layer(self):
        self.assertEqual(s.parse_selection_envelope(None).code, "input_not_text")
        self.assertEqual(s.parse_selection_envelope(b"{}").code, "input_not_text")
        self.assertEqual(s.parse_selection_envelope("{").code, "json_malformed")
        self.assertEqual(s.parse_selection_envelope('{"a":1,"a":2}').code, "json_duplicate_key")
        self.assertEqual(s.parse_selection_envelope('{"a":1.5}').code, "json_number_unsupported")
        self.assertEqual(s.parse_selection_envelope("x" * (c.MAX_DOCUMENT_BYTES + 1)).code, "input_too_large")
        self.assertEqual(s.parse_selection_envelope("[" * 20 + "]" * 20).code, "json_nesting_too_deep")
        self.assertEqual(s.parse_selection_envelope("\ud800").code, "input_not_text")

    def test_duplicate_key_inside_statement(self):
        text = r.dumps(r.make_envelope()).replace('"epoch": 1', '"epoch": 1, "epoch": 2')
        self.assertEqual(s.parse_selection_envelope(text).code, "json_duplicate_key")

    def test_codes_are_closed(self):
        for res in (sel(epoch=0), parse(kind="x"), s.parse_selection_envelope("{")):
            self.assertIn(res.code, c.CODES)


class SigningInputTests(unittest.TestCase):
    def test_deterministic_and_domain_separated(self):
        stmt = r.make_statement()
        a = s.signing_input(stmt)
        self.assertEqual(a, s.signing_input(copy.deepcopy(stmt)))
        self.assertTrue(a.startswith(b"ocs-reg/r08-v1/selection\n"))
        self.assertEqual(a, b"ocs-reg/r08-v1/selection\n" + c.canonical_bytes(stmt))
        self.assertNotEqual(a, c.canonical_bytes(stmt))
        self.assertNotEqual(a, s.signing_input(r.make_statement(epoch=2)))

    def test_key_order_does_not_matter(self):
        stmt = r.make_statement()
        reordered = dict(reversed(list(stmt.items())))
        self.assertEqual(s.signing_input(stmt), s.signing_input(reordered))


def sup_ref(older, decision="decision-2"):
    st = older.statement
    return {"selection_id": st["selection_id"], "epoch": st["epoch"], "statement_digest": older.statement_digest, "decision_ref": decision}


class ResolveTests(unittest.TestCase):
    def test_none(self):
        res = s.resolve_effective([], CTX, r.NOW)
        self.assertEqual((res.ok, res.code, res.selected), (False, "selection_missing", None))

    def test_one(self):
        a = sel()
        res = s.resolve_effective([a], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertIs(res.selected, a)

    def test_invalid_candidates_ignored(self):
        bad = parse(epoch=0)
        a = sel()
        res = s.resolve_effective([bad, a, "junk", None], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertEqual(s.resolve_effective([bad], CTX, r.NOW).code, "selection_missing")

    def test_window(self):
        a = sel()
        before = r.NOW - datetime.timedelta(days=2)
        end = datetime.datetime(2026, 10, 26, 0, 0, 0, tzinfo=datetime.timezone.utc)
        start = datetime.datetime(2026, 10, 25, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self.assertEqual(s.resolve_effective([a], CTX, before).code, "selection_missing")
        self.assertEqual(s.resolve_effective([a], CTX, end).code, "selection_missing")  # until is exclusive
        self.assertTrue(s.resolve_effective([a], CTX, start).ok)  # from is inclusive
        self.assertTrue(s.resolve_effective([a], CTX, end - datetime.timedelta(seconds=1)).ok)

    def test_context_mismatches(self):
        a = sel()
        for ctx in (c.ExpectedContext("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test"),
                    c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"),
                    c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"),
                    c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"),
                    c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")):
            self.assertEqual(s.resolve_effective([a], ctx, r.NOW).code, "selection_missing", ctx)

    def test_now_unavailable(self):
        a = sel()
        self.assertEqual(s.resolve_effective([a], CTX, None).code, "time_unavailable")
        self.assertEqual(s.resolve_effective([a], CTX, datetime.datetime(2026, 10, 25, 12)).code, "time_unavailable")
        tz = datetime.timezone(datetime.timedelta(hours=2))
        self.assertEqual(s.resolve_effective([a], CTX, datetime.datetime(2026, 10, 25, 12, tzinfo=tz)).code, "time_unavailable")
        self.assertEqual(s.resolve_effective([a], CTX, "2026-10-25").code, "time_unavailable")

    def test_bad_context(self):
        self.assertEqual(s.resolve_effective([sel()], None, r.NOW).code, "selection_missing")
        self.assertEqual(s.resolve_effective("abc", CTX, r.NOW).code, "selection_missing")
        self.assertEqual(s.resolve_effective(5, CTX, r.NOW).code, "selection_missing")

    def test_higher_epoch_without_supersession_conflicts(self):
        a = sel(epoch=1)
        b = sel(epoch=2)
        res = s.resolve_effective([a, b], CTX, r.NOW)
        self.assertEqual((res.ok, res.code, res.selected), (False, "selection_conflict", None))
        self.assertEqual(s.resolve_effective([b, a], CTX, r.NOW).code, "selection_conflict")

    def test_explicit_supersession_chain(self):
        a = sel(epoch=1)
        b = sel(epoch=2, supersedes=sup_ref(a))
        res = s.resolve_effective([a, b], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertIs(res.selected, b)
        self.assertIs(s.resolve_effective([b, a], CTX, r.NOW).selected, b)

    def test_three_link_chain(self):
        a = sel(epoch=1)
        b = sel(epoch=2, supersedes=sup_ref(a))
        d = sel(epoch=3, supersedes=sup_ref(b, "decision-3"))
        res = s.resolve_effective([a, d, b], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertIs(res.selected, d)

    def test_chain_skipping_a_link_conflicts(self):
        a = sel(epoch=1)
        b = sel(epoch=2, supersedes=sup_ref(a))
        e = sel(epoch=3)  # no supersedes at all
        self.assertEqual(s.resolve_effective([a, b, e], CTX, r.NOW).code, "selection_conflict")

    def test_broken_chain_wrong_digest(self):
        a = sel(epoch=1)
        ref = sup_ref(a)
        ref["statement_digest"] = "sha256:" + "f" * 64
        b = sel(epoch=2, supersedes=ref)
        self.assertEqual(s.resolve_effective([a, b], CTX, r.NOW).code, "selection_conflict")

    def test_broken_chain_wrong_epoch(self):
        a = sel(epoch=1)
        z = sel(epoch=2)
        ref = sup_ref(a)
        ref["epoch"] = 2  # names epoch 2 of the same id, which is not a candidate with that digest
        c3 = sel(epoch=3, supersedes=ref)
        self.assertEqual(s.resolve_effective([a, z, c3], CTX, r.NOW).code, "selection_conflict")

    def test_same_epoch_two_digests_conflict(self):
        a = sel(epoch=1)
        b = sel(epoch=1, selector_ref="selector-test-2")
        self.assertNotEqual(a.statement_digest, b.statement_digest)
        self.assertEqual(s.resolve_effective([a, b], CTX, r.NOW).code, "selection_conflict")

    def test_duplicate_identical_candidates_are_one(self):
        a = sel()
        a2 = sel()
        res = s.resolve_effective([a, a2], CTX, r.NOW)
        self.assertTrue(res.ok)

    def test_different_selection_ids_conflict(self):
        a = sel(selection_id="sel-test-1")
        b = sel(selection_id="sel-test-2")
        self.assertEqual(s.resolve_effective([a, b], CTX, r.NOW).code, "selection_conflict")

    def test_out_of_window_older_does_not_conflict(self):
        old = sel(epoch=1, effective={"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-02T00:00:00Z"})
        cur = sel(epoch=2)
        res = s.resolve_effective([old, cur], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertIs(res.selected, cur)

    def test_superseding_references_expired_older_alone(self):
        old = sel(epoch=1, effective={"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-02T00:00:00Z"})
        cur = sel(epoch=2, supersedes=sup_ref(old))
        res = s.resolve_effective([old, cur], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertIs(res.selected, cur)

    def test_other_context_candidates_do_not_conflict(self):
        a = sel()
        other = sel(consumer_id="consumer-other")
        res = s.resolve_effective([a, other], CTX, r.NOW)
        self.assertTrue(res.ok)
        self.assertIs(res.selected, a)

    def test_participation_is_not_a_discriminator(self):
        a = sel(participation="required")
        b = sel(participation="optional")
        self.assertEqual(s.resolve_effective([a, b], CTX, r.NOW).code, "selection_conflict")


if __name__ == "__main__":
    unittest.main()
