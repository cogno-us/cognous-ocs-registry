"""Golden vectors for Amendment 2 (canonical base64 signature spelling for r08-v2 envelopes).

The vector data file is NOT under tests/golden (that directory is the frozen r08-v1 corpus). Its sha256 is pinned here and in
docs/r08-v2-contract-amendment-2.md. Exercised against canonical_b64.py directly, through the r08-v2 entry point, and
against the frozen r08-v1 path (which must keep the plain standard-library rule).
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import selection, verify  # noqa: E402
from registry_successor.canonical_b64 import decode_canonical_base64  # noqa: E402

VECTORS_PATH = Path(__file__).resolve().parent / "vectors" / "r08_v2_canonical_base64_vectors.json"
VECTORS_SHA256 = "964fba696968fb5509c596c78fd04a17d2e090565595749cf8b36df2465fbd28"
DOC = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
VECTORS = DOC["vectors"]
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
KEY = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")


class AcceptAnyBytes:
    """Verifier double that accepts every signature: any refusal seen is therefore caused by the textual spelling alone."""

    def __init__(self):
        self.seen = []

    def verify(self, alg, public_key, message, signature):
        self.seen.append(signature)
        return True


def _run(text, entry):
    if entry is verify.verify_selection_v2:  # the r08-v2 entry takes a real r08-v2 selection (v2 statement, v2 parser)
        stmt = r.make_statement_v2()
        env = r.make_envelope_v2(stmt, key_id="key-test-1", public_key=b"x", signed=False)
        env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": text}]
        sel = r.parse_v2(r.dumps(env))
    else:
        stmt = r.make_statement()
        env = r.make_envelope(stmt, key_id="key-test-1", public_key=b"x", signed=False)
        env["signatures"] = [{"alg": "ed25519", "key_id": "key-test-1", "signature": text}]
        sel = selection.parse_selection_envelope(r.dumps(env))
    assert sel.ok, sel.code
    grant = verify.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
    trust = verify.TrustSnapshot("trust-snap-test-1", 1, "2026-12-31T00:00:00Z",
                                 (verify.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", KEY, (grant,)),))
    v = AcceptAnyBytes()
    return entry(sel, CTX, trust, v, r.NOW), v


def test_vector_file_is_pinned_and_has_the_expected_shape():
    assert hashlib.sha256(VECTORS_PATH.read_bytes()).hexdigest() == VECTORS_SHA256
    assert DOC["format"] == "r08-v2-canonical-base64-vectors/1"
    assert len({v["id"] for v in VECTORS}) == len(VECTORS)
    accepts = [v for v in VECTORS if v["expect"] == "accept"]
    rejects = [v for v in VECTORS if v["expect"] == "reject"]
    assert len(accepts) >= 12 and len(rejects) >= 150
    assert any(v["stdlib_validate_decodes"] for v in rejects) and any(not v["stdlib_validate_decodes"] for v in rejects)
    # advertised lengths are real (review): every pos-lenN encodes exactly N bytes, every neg-lenN family derives from N bytes, and the padding model fits N % 3
    for v in VECTORS:
        head = v["id"].split("-")
        if len(head) >= 2 and head[1].startswith("len"):
            n = int(head[1][3:])
            if v["expect"] == "accept":
                assert head[0] == "pos" and len(bytes.fromhex(v["decoded_hex"])) == n and len(base64.b64decode(v["text"], validate=True)) == n
                assert v["text"].count("=") == (3 - n % 3) % 3 and len(v["text"]) == 4 * ((n + 2) // 3)
            elif "-padbits-" in v["id"]:  # the alternate spellings of the SAME bytes (other negatives may decode to other lengths on purpose)
                assert len(bytes.fromhex(v["decodes_to_hex"])) == n
    assert {int(v["id"].split("-")[1][3:]) for v in accepts} == {1, 2, 3, 4, 5, 31, 32, 33, 63, 64, 65, 96}
    # every vector is independently re-derivable: an accept is exactly the stdlib canonical encoding of its bytes
    for v in accepts:
        assert base64.b64encode(bytes.fromhex(v["decoded_hex"])).decode("ascii") == v["text"]
    # every alternate spelling that the stdlib validate=True decoder accepts is an alternate text of some accept vector's bytes class
    for v in rejects:
        if v["stdlib_validate_decodes"]:
            assert base64.b64decode(v["text"], validate=True).hex() == v["decodes_to_hex"]
            assert base64.b64encode(bytes.fromhex(v["decodes_to_hex"])).decode("ascii") != v["text"]


@pytest.mark.parametrize("vec", VECTORS, ids=[v["id"] for v in VECTORS])
def test_canonical_b64_module_against_vectors(vec):
    got = decode_canonical_base64(vec["text"])
    if vec["expect"] == "accept":
        assert got == bytes.fromhex(vec["decoded_hex"])
    else:
        assert got is None


@pytest.mark.parametrize("vec", VECTORS, ids=[v["id"] for v in VECTORS])
def test_r08_v2_path_against_vectors(vec):
    rep, verifier = _run(vec["text"], verify.verify_selection_v2)
    if vec["expect"] == "accept":
        assert rep.ok is True and verifier.seen == [bytes.fromhex(vec["decoded_hex"])]
    else:
        assert rep.ok is False and rep.code == "signature_invalid" and verifier.seen == []
        assert rep.detail == ("signature is not canonical base64" if vec["stdlib_validate_decodes"] else "signature is not valid base64")


@pytest.mark.parametrize("vec", VECTORS, ids=[v["id"] for v in VECTORS])
def test_r08_v1_path_is_frozen_and_keeps_the_plain_stdlib_rule(vec):
    rep, verifier = _run(vec["text"], verify.verify_selection)  # legacy default: contract_version "r08-v1"
    if vec["stdlib_validate_decodes"] or vec["expect"] == "accept":
        assert rep.ok is True and len(verifier.seen) == 1
        assert verifier.seen[0] == base64.b64decode(vec["text"], validate=True)
    else:
        assert rep.ok is False and rep.code == "signature_invalid" and rep.detail == "signature is not valid base64"


def test_amendment_2_is_anchored_to_the_unedited_frozen_contracts_and_the_vector_file():
    root = Path(__file__).resolve().parent.parent
    amendment = (root / "docs" / "r08-v2-contract-amendment-2.md").read_text(encoding="utf-8")
    for rel, sha, blob in (("docs/r08-v2-contract.md", "64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01", "ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f"),
                           ("docs/r08-s01-contract.md", "da24154e85d803c6c904d650ddad3dda2ef9f7283f37506e7bbae984d16e5541", "d8cf632a5f1ba09c38cfb95cecd84e7b4a7e0452")):
        data = (root / rel).read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha and sha in amendment and blob in amendment
        assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == blob
    assert "standard base64 text" in (root / "docs" / "r08-s01-contract.md").read_text(encoding="utf-8")
    assert VECTORS_SHA256 in amendment
    n_reject = sum(1 for v in VECTORS if v["expect"] == "reject")
    n_decodable = sum(1 for v in VECTORS if v["expect"] == "reject" and v["stdlib_validate_decodes"])
    assert f"{len(VECTORS)} vectors: {sum(1 for v in VECTORS if v['expect'] == 'accept')} positive" in amendment
    assert f"{n_reject} negative" in amendment and f"{n_decodable} of the negatives" in amendment
