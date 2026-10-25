"""Shared builders for R08-S01 developer tests. Test-only. Not part of the contract.

`FakeVerifier` is a deterministic test double, NOT cryptography: it exists only to exercise the layer separation
without a real Ed25519 implementation. It never ships and never appears in `registry_successor`.
"""
import base64
import copy
import datetime
import hashlib
import json

from registry_successor import common as c

BLOB = "2fc880dae37eac76e5074533435740ce0684209d"
SHA = "sha256:940e781934542a7acd7bbe2f6833f9d329325d94b49425afd9d2bedcf23c5b68"
NOW = datetime.datetime(2026, 10, 25, 12, 0, 0, tzinfo=datetime.timezone.utc)
EVALUATOR = {"evaluator_id": c.EVALUATOR_ID, "binding": c.EVALUATOR_BINDING, "source_blob_id": BLOB, "source_sha256": SHA}


def make_record(**over):
    body = {
        "contract_version": c.CONTRACT_VERSION, "kind": "record", "family": c.FAMILY_F1A,
        "record_id": "f1a-test-record", "record_version": 1, "non_authorizing": True, "supersedes": None,
        "evaluator": dict(EVALUATOR),
        "source": {"repository": "cogno-us/cognous-execution-runtime", "commit": "ec728da6dc301a664b331ac8986afd6e850a1273",
                   "path": "engine/safe_executor.py", "blob_id": BLOB, "sha256": SHA},
        "payload": {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a", "unit-b"]},
        "provenance": {"decision_ref": "decision-test-1", "authored_at": "2026-10-25T00:00:00Z", "authored_by": "test-author"},
    }
    body.update(over)
    return seal_record(body)


def seal_record(body):
    body = copy.deepcopy(body)
    body["payload_digest"] = c.digest(body["payload"])
    body["record_digest"] = c.digest({k: v for k, v in body.items() if k != "record_digest"})
    return body


def make_statement(record=None, **over):
    record = record or make_record()
    stmt = {
        "kind": "selection", "selection_id": "sel-test-1", "epoch": 1, "consumer_id": "consumer-test",
        "scope": {"tenant": "tenant-a", "institution": "inst-a", "authority_domain": "domain-a"},
        "operation": "op-test", "participation": "required", "family": c.FAMILY_F1A,
        "record": {"record_id": record["record_id"], "record_version": record["record_version"], "record_digest": record["record_digest"]},
        "evaluator": dict(EVALUATOR),
        "effective": {"valid_from": "2026-10-25T00:00:00Z", "valid_until": "2026-10-26T00:00:00Z"},
        "supersedes": None, "revocation_ref": "revocation-test-1", "selector_ref": "selector-test-1",
        "issued_at": "2026-10-24T00:00:00Z",
    }
    stmt.update(over)
    return stmt


def fake_signature_bytes(public_key: bytes, message: bytes) -> bytes:
    return hashlib.sha256(b"fake-signature|" + public_key + b"|" + message).digest()


def fake_signature(public_key: bytes, message: bytes) -> str:
    return base64.b64encode(fake_signature_bytes(public_key, message)).decode("ascii")


def make_envelope(statement=None, key_id="key-test-1", public_key=b"public-key-test-1", signed=True, **over):
    from registry_successor.selection import signing_input
    statement = statement or make_statement()
    sigs = []
    if signed:
        sigs = [{"alg": "ed25519", "key_id": key_id, "signature": fake_signature(public_key, signing_input(statement))}]
    env = {"contract_version": c.CONTRACT_VERSION, "kind": "selection-envelope", "statement": statement,
           "statement_digest": c.digest(statement), "signatures": sigs}
    env.update(over)
    return env


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True)


class FakeVerifier:
    """Deterministic test double standing in for an Ed25519 verifier. Not cryptography."""

    def verify(self, alg, public_key, message, signature):
        return alg == "ed25519" and signature == fake_signature_bytes(public_key, message)
