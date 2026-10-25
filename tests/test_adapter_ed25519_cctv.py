"""C2SP CCTV Ed25519 edge-case vectors through the Ed25519 adapter (PR #26, SECURITY-HELD).

Disposition rule (documented, not inferred from the adapter's output):

* A vector with NO flag is an ordinary prime-order key and R with a good signature: the adapter must ACCEPT it.
* A vector with ANY flag involves a low-order or mixed-order public key or R, or a non-canonical point encoding. The registry
  policy (strict, cofactorless, prime-order-subgroup public key; see docs/adapters/ed25519.md) REFUSES every one of them.
  This is stricter than RFC 8032, which accepts many of them; the adapter must never accept a flagged vector.

The corpus is almost entirely a refusal corpus (914 vectors, 1 unflagged): it shows what is refused and says little about
accepting legitimate signatures; that rests on the Wycheproof valid vectors, the RFC 8032 known answers and the honest
signature tests in tests/test_adapter_ed25519.py.

AI review artifact, not independent cryptographic approval: PR #26 stays SECURITY-HELD.
"""
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import pytest

import ed25519_oracle as oracle
from registry_adapters import ed25519_verifier as ev

try:
    import nacl.bindings  # noqa: F401
    HAVE_BACKEND = True
except ImportError:
    HAVE_BACKEND = False

CCTV_DIR = Path(__file__).resolve().parent / "vectors" / "cctv"
RAW = (CCTV_DIR / "ed25519vectors.json").read_bytes()
README_RAW = (CCTV_DIR / "UPSTREAM-README.md").read_bytes()
SOURCE = (CCTV_DIR / "SOURCE.md").read_text()
VECTORS = json.loads(RAW)
ALG = "ed25519"
UPSTREAM_COMMIT = "0fb2c3b5dc50437ce3272abcbec7567dde497047"  # C2SP/CCTV; the commit that last touched ed25519/ed25519vectors.json
LICENSE_SHA256 = "9fe727c21f00a770a683a4c8491bf24203ec839628bad09b026258c5afc17076"  # C2SP/CCTV ed25519/LICENSE (BSD-3-Clause)
KNOWN_FLAGS = {"low_order_A", "low_order_R", "low_order_component_A", "low_order_component_R", "low_order_residue",
               "non_canonical_A", "non_canonical_R", "reencoded_k"}
needs_backend = pytest.mark.skipif(not HAVE_BACKEND, reason="pynacl not installed (requirements-ed25519.lock.txt)")


def _row(t):
    return bytes.fromhex(t["key"]), t["msg"].encode("utf-8"), bytes.fromhex(t["sig"])


def _flags(t):
    return tuple(t.get("flags") or ())


def _expected_accept(t):
    return not _flags(t)


@pytest.fixture
def verifier():
    return ev.Ed25519Verifier()


def test_ci_runs_the_cctv_corpus_through_the_real_backend():
    """In CI (GitHub sets CI=true) the corpus must run, not skip: the workflow installs requirements-ed25519.lock.txt."""
    if os.environ.get("CI") == "true":
        assert HAVE_BACKEND, "CI must install requirements-ed25519.lock.txt"


def test_cctv_files_are_the_recorded_upstream_files():
    assert hashlib.sha256(RAW).hexdigest() == "b38e84caf3e7e89170ff520292dbeae421b0a794c27408ce5ce973018fe3d7f9"
    assert hashlib.sha256(RAW).hexdigest() in SOURCE and hashlib.sha256(README_RAW).hexdigest() in SOURCE
    # provenance and redistribution terms (resolved): exact upstream commit, preserved BSD-3-Clause LICENSE, attribution NOTICE
    assert UPSTREAM_COMMIT in SOURCE and "https://github.com/C2SP/CCTV" in SOURCE
    assert "License: BSD-3-Clause" in SOURCE and "not established" not in SOURCE
    license_raw = (CCTV_DIR / "LICENSE").read_bytes()
    assert hashlib.sha256(license_raw).hexdigest() == LICENSE_SHA256 and LICENSE_SHA256 in SOURCE
    assert license_raw.startswith(b"Copyright 2019 Google LLC\nCopyright 2022 Filippo Valsorda\n")
    assert b"Redistributions of source code must retain the above copyright" in license_raw
    notice = (CCTV_DIR / "NOTICE").read_text()
    assert "Google LLC" in notice and "Filippo Valsorda" in notice and UPSTREAM_COMMIT in notice and "BSD 3-Clause" in notice
    assert len(VECTORS) == 914 and [t["number"] for t in VECTORS] == list(range(914))
    assert all(set(t) == {"number", "key", "sig", "msg", "flags"} for t in VECTORS)
    assert all(len(bytes.fromhex(t["key"])) == 32 and len(bytes.fromhex(t["sig"])) == 64 for t in VECTORS)
    assert {f for t in VECTORS for f in _flags(t)} == KNOWN_FLAGS
    assert [t["number"] for t in VECTORS if _expected_accept(t)] == [305]


@needs_backend
@pytest.mark.parametrize("t", VECTORS, ids=lambda t: f"cctv{t['number']}")
def test_cctv_vector_through_adapter_follows_the_documented_disposition(verifier, t):
    got = verifier.verify(ALG, *_row(t))
    assert got is _expected_accept(t), f"vector {t['number']} flags={_flags(t)}"
    if _flags(t):
        # every flagged vector is refused by the adapter; none may be accepted by dropping to the equation alone
        assert got is False


@needs_backend
def test_cctv_aggregate_adapter_accepts_exactly_the_single_unflagged_control(verifier):
    accepted = [t["number"] for t in VECTORS if verifier.verify(ALG, *_row(t))]
    assert accepted == [305]
    refused_by_flag = Counter(f for t in VECTORS if not verifier.verify(ALG, *_row(t)) for f in _flags(t))
    accepted_by_flag = Counter(f for t in VECTORS if verifier.verify(ALG, *_row(t)) for f in _flags(t))
    assert not accepted_by_flag
    assert set(refused_by_flag) == KNOWN_FLAGS


@pytest.mark.parametrize("t", VECTORS, ids=lambda t: f"cctv{t['number']}")
def test_cctv_vector_through_policy_oracle(t):
    """The executable specification (tests/ed25519_oracle.py, an unreviewed instrument) agrees on every vector."""
    assert oracle.policy_verify(*_row(t)) is _expected_accept(t)


@needs_backend
def test_cctv_key_policy_refuses_every_vector_whose_key_is_flagged(verifier):
    for t in VECTORS:
        key = bytes.fromhex(t["key"])
        flagged_key = any(f in _flags(t) for f in ("low_order_A", "non_canonical_A"))
        if flagged_key:
            assert verifier.acceptable_public_key(key) is False, t["number"]


# ---- mutation checks: dropping the refusal logic must be caught by this corpus --------------------------------------
def _accepted_numbers(verifier):
    return [t["number"] for t in VECTORS if verifier.verify(ALG, *_row(t))]


@needs_backend
def test_mutant_dropping_the_public_key_policy_is_caught_by_cctv(verifier):
    verifier._is_valid_point = lambda pk: True  # mutant: no key policy; only libsodium's own signature checks remain
    accepted = _accepted_numbers(verifier)
    assert accepted != [305] and len(accepted) > 1, "CCTV does not notice dropping the public-key policy"


@needs_backend
def test_mutant_dropping_the_signature_call_is_caught_by_cctv(verifier):
    verifier._sign_open = lambda signed, pk: None  # mutant: the signature is never checked
    accepted = _accepted_numbers(verifier)
    assert len(accepted) > 1 or accepted != [305]


@needs_backend
def test_mutant_always_refusing_is_caught_by_the_unflagged_control(verifier):
    verifier._sign_open = lambda signed, pk: (_ for _ in ()).throw(ValueError("refused"))
    assert 305 not in _accepted_numbers(verifier)


@needs_backend
@pytest.mark.parametrize("drop", [("A_small_order",), ("A_subgroup",), ("R_small_order",)],
                         ids=lambda d: "drop-" + "+".join(d))
def test_mutant_policy_checks_are_caught_by_cctv(verifier, drop):
    """Executable-policy mutants (as in tests/test_adapter_ed25519.py): CCTV must accept something it should refuse."""
    verifier._is_valid_point = lambda pk: True

    def weak_open(signed, pk):
        if not oracle.policy_verify(pk, signed[64:], signed[:64], drop=drop):
            raise ValueError("refused")

    verifier._sign_open = weak_open
    accepted = _accepted_numbers(verifier)
    assert set(accepted) - {305}, f"CCTV does not notice dropping {drop}"
