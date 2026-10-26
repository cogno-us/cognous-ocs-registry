"""S01 test builders (test-only). r08-v2 selection envelopes, v1/v2 signing domains, trust snapshots.

BUILDER_TESTED, not independently qualified. `r08_support.FakeVerifier` is a deterministic double, not cryptography; the real-Ed25519
tests in test_s01_* use PyNaCl directly and the repository adapter.
"""
import copy
import datetime

import r08_support as r
from registry_successor import common as c
from registry_successor import verify as v

V1_DOMAIN = b"ocs-reg/r08-v1/selection\n"
V2_DOMAIN = b"ocs-reg/r08-v2/selection\n"
PK = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")  # RFC 8032 7.1 test 1 (synthetic)
KEY_ID = "key-test-1"
GRANT = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
NOW = r.NOW
UTC = datetime.timezone.utc


def trust(version=1, valid_until="2026-10-27T00:00:00Z", key_id=KEY_ID, pub=PK, **kw):
    return v.TrustSnapshot("snap-test-1", version, valid_until, (v.IssuerEntry(key_id, "issuer-test-1", "ed25519", pub, (GRANT,)),), **kw)


def select_statement(**over):
    stmt = r.make_statement()
    stmt["disposition"] = "select"
    stmt.update(over)
    return stmt


def withdraw_statement(select=None, **over):
    """A withdrawal at epoch 2 naming `select` (default: the standard epoch-1 select) exactly; no record pin."""
    select = select or select_statement()
    stmt = copy.deepcopy(select)
    stmt.update({
        "disposition": "withdraw", "epoch": select["epoch"] + 1, "record": None, "evaluator": None,
        "supersedes": {"selection_id": select["selection_id"], "epoch": select["epoch"], "statement_digest": c.digest(select),
                       "decision_ref": "decision-test-9"},
    })
    stmt.update(over)
    return stmt


def sign_fake(statement, domain=V2_DOMAIN, pub=PK):
    return r.fake_signature(pub, domain + c.canonical_bytes(statement))


def envelope(statement, domain=V2_DOMAIN, contract="r08-v2", key_id=KEY_ID, signed=True, signature=None, pub=PK, **over):
    sigs = []
    if signed:
        sigs = [{"alg": "ed25519", "key_id": key_id, "signature": signature if signature is not None else sign_fake(statement, domain, pub)}]
    env = {"contract_version": contract, "kind": "selection-envelope", "statement": statement,
           "statement_digest": c.digest(statement), "signatures": sigs}
    env.update(over)
    return env


def v1_statement(**over):
    return r.make_statement(**over)


def v1_envelope(statement=None, domain=V1_DOMAIN, **over):
    statement = statement or v1_statement()
    return envelope(statement, domain=domain, contract="r08-v1", **over)
