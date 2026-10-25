"""S04 acceptance battery for the registry overlay consumer (non-authorizing, synthetic, builder-side).

Written before registry_consumer/ existed, from the required negative-case list in the adopted S04 authorization
(docs/decisions/2026-10-24-s04-preconditions-and-authorization.md). All manifests, records and digests are built by
helpers in this module, not by the consumer, so the checks are not circular. The builder wrote this battery and does
not certify its own Tier 1 migration: the designated independent technical review is Copilot on the exact final head
(P3 as amended), which is not independent qualification.

Plan: OCS-REG-PLAN v1.1 S04 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2).
Constitution: cognous-engineering-constitution 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.

Attribution: the ExecutionOperation field values in _operation() are the synthetic values used by the S01 fixture
(tests/test_s01_baseline_local_policy.py), which copies them from cognous-execution-runtime tests/test_producer_contract.py
at ec728da6dc301a664b331ac8986afd6e850a1273 (Apache-2.0).
"""
import ast
import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from engine.safe_executor import (
    EXECUTION_ENVELOPE_VERSION,
    ExecutionEnvelope,
    ExecutionOperation,
    LocalExecutionPolicy,
    commitment,
    snapshot_envelope,
)
from registry_consumer import CONSUMER_REASON_CODES, OverlayResult, TrustConfig, apply_registry_overlay
from registry_contract.validator import validate_record_text

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SOURCE = ROOT / "baseline" / "execution-runtime" / "engine" / "safe_executor.py"
CONSUMER_DIR = ROOT / "registry_consumer"
FIXTURES = ROOT / "registry_records"

BLOB = "2fc880dae37eac76e5074533435740ce0684209d"
SHA = "sha256:940e781934542a7acd7bbe2f6833f9d329325d94b49425afd9d2bedcf23c5b68"
EVALUATOR_ID = "engine.safe_executor.LocalExecutionPolicy.check"
ADAPTER = "urn:cognous:adapter:synthetic-refund"
FIELDS = ("allowed_actions", "allowed_adapters", "allowed_units")

# Frozen S03 files (git blob ids at main 1ec246d): S04 must not change them.
FROZEN_S03 = {
    "registry_contract/validator.py": "afee88b37197ca4aa3842b228fbc348f585b937a",
    "registry_contract/__init__.py": "5d8e9e69697fae3bc027666541a36379ce299d9f",
}


# ------------------------------------------------------------------ independent builders

def sha256_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canon(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def seal(rec: dict) -> dict:
    rec["data_digest"] = sha256_of(canon(rec["data"]))
    rec["record_digest"] = sha256_of(canon({k: v for k, v in rec.items() if k != "record_digest"}))
    return rec


def make_record(units=("USD",), adapters=(ADAPTER,), actions=("refund.issue",), mutate=None) -> dict:
    rec = {
        "record_type": "local-execution-allowlist",
        "contract_version": "s03-v1",
        "record_id": "lep.allowlist.synthetic",
        "record_version": 1,
        "status": "active",
        "non_authorizing": True,
        "supersedes": None,
        "source": {
            "repository": "cogno-us/cognous-execution-runtime",
            "commit": "ec728da6dc301a664b331ac8986afd6e850a1273",
            "path": "engine/safe_executor.py",
            "blob_id": BLOB,
            "sha256": SHA,
            "field_lines": "358-372",
            "check_lines": "417-424",
        },
        "applicability": {"runtime_source_blob_id": BLOB},
        "evaluator": {"evaluator_id": EVALUATOR_ID, "binding": "registered-code-reference", "supplies": list(FIELDS)},
        "data": {
            "allowed_units": sorted(units),
            "allowed_adapters": sorted(adapters),
            "allowed_actions": sorted(actions),
        },
        "data_digest": "",
        "provenance": {
            "decision_ref": "docs/decisions/2026-10-24-s04-preconditions-and-authorization.md",
            "authored_at": "2026-10-24T12:00:00Z",
            "authored_by": "synthetic S04 test fixture",
        },
        "record_digest": "",
    }
    if mutate:
        mutate(rec)
    return seal(rec)


def record_bytes(rec: dict) -> bytes:
    return (json.dumps(rec, indent=2) + "\n").encode("utf-8")


def make_manifest(rec: dict, raw: bytes, mutate=None) -> dict:
    manifest = {
        "manifest_type": "local-execution-allowlist-selection",
        "manifest_version": "s04-v1",
        "contract_version": "s03-v1",
        "record": {
            "record_id": rec["record_id"],
            "record_version": rec["record_version"],
            "record_digest": rec["record_digest"],
            "file_sha256": sha256_of(raw),
        },
        "record_source": {
            "repository": "cogno-us/cognous-ocs-registry",
            "commit": "1" * 40,
            "path": "registry_records/synthetic.record.json",
        },
        "evaluator": {"evaluator_id": EVALUATOR_ID, "binding": "registered-code-reference"},
        "runtime": {"source_blob_id": BLOB, "source_sha256": SHA},
    }
    if mutate:
        mutate(manifest)
    return manifest


def manifest_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, indent=2) + "\n").encode("utf-8")


def operation() -> ExecutionOperation:
    payload = {"refund_reason": "s04-overlay-fixture"}
    return ExecutionOperation(
        actor="urn:cognous:identity:agent-1",
        principal="urn:cognous:principal:service",
        institution_id="urn:cognous:institution:demo",
        authority_domain="customer-refunds",
        manifest_id="refund-integration-v1-1",
        manifest_version="1.1",
        manifest_digest="sha256:" + "a" * 64,
        proposal_commitment="sha256:" + "b" * 64,
        action_id="refund.issue",
        adapter_id=ADAPTER,
        target="urn:cognous:synthetic-account:customer-1",
        payload=payload,
        payload_commitment=commitment(payload),
        requested_permissions=("refund.issue",),
        amount=50.0,
        unit="USD",
        effects=1,
        authority_context_id="urn:cognous:authority-context:refund-demo",
        requirement_id="urn:cognous:requirement:refund-t1",
        grant_id="urn:cognous:grant:refund-1",
        grant_revision="1",
        effective_max_effects=1,
    )


def frozen_op():
    envelope = ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", "effect-1", operation())
    return snapshot_envelope(envelope).operation


def caller_policy(**changes) -> LocalExecutionPolicy:
    op = operation()
    args = dict(
        allowed_institutions=frozenset({op.institution_id}),
        allowed_authority_domains=frozenset({op.authority_domain}),
        allowed_adapters=frozenset({ADAPTER}),
        allowed_actions=frozenset({"refund.issue"}),
        allowed_target_prefixes=("urn:cognous:synthetic-account:",),
        allowed_units=frozenset({"USD"}),
        max_amount=1000.0,
        max_effects=1,
    )
    args.update(changes)
    return LocalExecutionPolicy(**args)


class Scenario:
    """A trusted-host layout in tmp_path: untrusted record file, manifest file, and the operator's trusted pin."""

    def __init__(self, tmp_path, rec=None, manifest_mutate=None):
        self.dir = tmp_path
        self.rec = rec or make_record()
        self.raw = record_bytes(self.rec)
        self.record_path = tmp_path / "record.json"
        self.record_path.write_bytes(self.raw)
        self.manifest = make_manifest(self.rec, self.raw, manifest_mutate)
        self.manifest_raw = manifest_bytes(self.manifest)
        self.manifest_path = tmp_path / "manifest.json"
        self.manifest_path.write_bytes(self.manifest_raw)
        self.trust = TrustConfig(manifest_sha256=sha256_of(self.manifest_raw), runtime_source_blob_id=BLOB,
                                 runtime_source_sha256=SHA)

    def run(self, policy=None, trust=None, manifest_path=None, record_path=None):
        policy = policy or caller_policy()
        result = apply_registry_overlay(policy, trust or self.trust, manifest_path or self.manifest_path,
                                        record_path or self.record_path)
        return policy, result


def refused(result: OverlayResult, policy, reason, validator_reason=None):
    assert (result.disposition, result.reason) == ("REFUSE", reason), result
    assert result.overlay_applied is False
    assert result.policy is policy, "refusal must leave the caller-constructed policy exactly as constructed"
    assert result.validator_reason == validator_reason
    assert result.narrowed_fields == ()


# ------------------------------------------------------------------ positive and semantics

def test_P1_accept_with_matching_record_applies_overlay_and_keeps_other_fields(tmp_path):
    policy, result = Scenario(tmp_path).run()
    assert (result.disposition, result.reason, result.overlay_applied) == ("ACCEPT", None, True)
    assert result.validator_reason is None
    eff = result.policy
    for name in ("allowed_institutions", "allowed_authority_domains", "allowed_target_prefixes", "target_match",
                 "max_amount", "max_effects"):
        assert getattr(eff, name) == getattr(policy, name), name
    assert eff.allowed_units == policy.allowed_units
    assert eff.allowed_adapters == policy.allowed_adapters
    assert eff.allowed_actions == policy.allowed_actions
    assert result.narrowed_fields == ()
    eff.check(frozen_op())  # the baseline evaluator still admits the baseline operation


def test_P2_registry_values_exceeding_caller_permissions_never_widen(tmp_path):
    rec = make_record(units=("EUR", "GBP", "USD"), adapters=(ADAPTER, "urn:other"), actions=("refund.issue", "x.other"))
    policy, result = Scenario(tmp_path, rec).run(caller_policy())
    assert result.disposition == "ACCEPT"
    assert result.policy.allowed_units == frozenset({"USD"})
    assert result.policy.allowed_adapters == frozenset({ADAPTER})
    assert result.policy.allowed_actions == frozenset({"refund.issue"})
    assert result.narrowed_fields == ()


def test_P3_registry_narrows_caller_and_baseline_check_denies_removed_value(tmp_path):
    rec = make_record(units=("EUR",))
    caller = caller_policy(allowed_units=frozenset({"USD", "EUR"}))
    policy, result = Scenario(tmp_path, rec).run(caller)
    assert result.disposition == "ACCEPT"
    assert result.policy.allowed_units == frozenset({"EUR"})
    assert result.narrowed_fields == ("allowed_units",)
    caller.check(frozen_op())  # caller alone would have allowed USD
    with pytest.raises(PermissionError, match="local unit restriction"):
        result.policy.check(frozen_op())
    assert caller.allowed_units == frozenset({"USD", "EUR"}), "caller policy object must not be mutated"


@pytest.mark.parametrize("field,record_kwargs,message", [
    ("allowed_units", {"units": ("EUR",)}, "local unit restriction"),
    ("allowed_adapters", {"adapters": ("urn:other",)}, "local adapter restriction"),
    ("allowed_actions", {"actions": ("x.other",)}, "local action restriction"),
])
def test_P4_disjoint_sets_give_empty_intersection_and_deny(tmp_path, field, record_kwargs, message):
    policy, result = Scenario(tmp_path, make_record(**record_kwargs)).run()
    assert result.disposition == "ACCEPT"
    assert getattr(result.policy, field) == frozenset()
    assert result.narrowed_fields == (field,)
    with pytest.raises(PermissionError, match=message):
        result.policy.check(frozen_op())


def test_P5_empty_caller_set_stays_empty(tmp_path):
    policy, result = Scenario(tmp_path).run(caller_policy(allowed_actions=frozenset()))
    assert result.disposition == "ACCEPT"
    assert result.policy.allowed_actions == frozenset()
    assert result.narrowed_fields == ()


def test_P6_check_order_is_unchanged_by_the_overlay(tmp_path):
    policy, result = Scenario(tmp_path).run(caller_policy(allowed_institutions=frozenset({"urn:other"}),
                                                          allowed_adapters=frozenset({"urn:other-adapter"})))
    assert result.disposition == "ACCEPT"
    with pytest.raises(PermissionError, match="local institution restriction"):
        result.policy.check(frozen_op())


def test_P7_committed_synthetic_fixtures_are_accepted_under_a_test_supplied_pin():
    manifest_path = FIXTURES / "local-execution-allowlist.synthetic.manifest.json"
    record_path = FIXTURES / "local-execution-allowlist.synthetic.record.json"
    pin = sha256_of(manifest_path.read_bytes())  # the test plays the operator; this is NOT an approved pin
    trust = TrustConfig(manifest_sha256=pin, runtime_source_blob_id=BLOB, runtime_source_sha256=SHA)
    policy = caller_policy()
    result = apply_registry_overlay(policy, trust, manifest_path, record_path)
    assert (result.disposition, result.reason) == ("ACCEPT", None), result
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert manifest["runtime"] == {"source_blob_id": BLOB, "source_sha256": SHA}
    assert manifest["record"]["record_digest"] == record["record_digest"]
    assert manifest["record"]["file_sha256"] == sha256_of(record_path.read_bytes())
    assert record["status"] == "active" and record["non_authorizing"] is True
    assert "synthetic" in record["provenance"]["authored_by"]


# ------------------------------------------------------------------ trust boundary and negatives

def test_N1_record_modified_and_redigested_is_refused_even_though_s03_alone_accepts_it(tmp_path):
    s = Scenario(tmp_path)
    widened = make_record(units=("EUR", "USD"), actions=("attacker.action", "refund.issue"))
    s.record_path.write_bytes(record_bytes(widened))
    ctx = {"runtime_source_blob_id": BLOB, "runtime_source_sha256": SHA, "latest_known_version": 1}
    assert validate_record_text(s.record_path.read_bytes(), ctx).outcome == "ACCEPT"  # S03 limitation L1
    policy, result = s.run()
    refused(result, policy, "record_file_mismatch")


def test_N2_wrong_approved_file_hash_in_manifest(tmp_path):
    s = Scenario(tmp_path, manifest_mutate=lambda m: m["record"].update(file_sha256="sha256:" + "0" * 64))
    policy, result = s.run()
    refused(result, policy, "record_file_mismatch")


def test_N3_wrong_approved_record_digest_in_manifest(tmp_path):
    s = Scenario(tmp_path, manifest_mutate=lambda m: m["record"].update(record_digest="sha256:" + "0" * 64))
    policy, result = s.run()
    refused(result, policy, "record_identity_mismatch")


def test_N4_wrong_approved_record_id_in_manifest(tmp_path):
    s = Scenario(tmp_path, manifest_mutate=lambda m: m["record"].update(record_id="lep.allowlist.other"))
    policy, result = s.run()
    refused(result, policy, "record_identity_mismatch")


def test_N5_unauthorized_manifest_replacement_is_refused_by_the_trusted_pin(tmp_path):
    s = Scenario(tmp_path)
    attacker_record = make_record(units=("EUR", "USD"))
    attacker_raw = record_bytes(attacker_record)
    s.record_path.write_bytes(attacker_raw)
    s.manifest_path.write_bytes(manifest_bytes(make_manifest(attacker_record, attacker_raw)))  # self-consistent
    policy, result = s.run()
    refused(result, policy, "manifest_pin_mismatch")


def test_N6_manifest_cannot_pin_itself_from_untrusted_content(tmp_path):
    s = Scenario(tmp_path)
    s.manifest_path.write_bytes(s.manifest_raw + b" ")
    policy, result = s.run()
    refused(result, policy, "manifest_pin_mismatch")


@pytest.mark.parametrize("selected", [2, 3])
def test_N7_incorrect_selected_version(tmp_path, selected):
    s = Scenario(tmp_path, manifest_mutate=lambda m: m["record"].update(record_version=selected))
    policy, result = s.run()
    refused(result, policy, "record_refused", "version_not_latest")


def test_N8_installed_runtime_source_modified(tmp_path):
    tampered = tmp_path / "safe_executor.py"
    tampered.write_bytes(RUNTIME_SOURCE.read_bytes() + b"\n# tampered\n")
    s = Scenario(tmp_path)
    trust = dataclasses.replace(s.trust, runtime_source_path=tampered)
    policy, result = s.run(trust=trust)
    refused(result, policy, "runtime_source_unverified")


def test_N9_unreadable_installed_runtime_source(tmp_path):
    s = Scenario(tmp_path)
    policy, result = s.run(trust=dataclasses.replace(s.trust, runtime_source_path=tmp_path / "nope.py"))
    refused(result, policy, "runtime_source_unverified")


@pytest.mark.parametrize("field,value", [("runtime_source_blob_id", "0" * 40), ("runtime_source_sha256", "sha256:" + "0" * 64)])
def test_N10_trusted_expectations_disagree_with_installed_bytes(tmp_path, field, value):
    s = Scenario(tmp_path)
    policy, result = s.run(trust=dataclasses.replace(s.trust, **{field: value}))
    refused(result, policy, "runtime_source_unverified")


@pytest.mark.parametrize("key,value", [("source_blob_id", "0" * 40), ("source_sha256", "sha256:" + "0" * 64)])
def test_N11_manifest_runtime_identity_differs_from_trusted_context(tmp_path, key, value):
    s = Scenario(tmp_path, manifest_mutate=lambda m: m["runtime"].update({key: value}))
    policy, result = s.run()
    refused(result, policy, "manifest_runtime_mismatch")


@pytest.mark.parametrize("path,value", [
    (("evaluator", "evaluator_id"), "engine.safe_executor.Other.check"),
    (("evaluator", "binding"), "script"),
    (("contract_version",), "s03-v2"),
    (("manifest_type",), "other"),
    (("manifest_version",), "s04-v2"),
])
def test_N12_manifest_evaluator_or_version_constants_wrong(tmp_path, path, value):
    def mutate(m):
        node = m
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    policy, result = Scenario(tmp_path, manifest_mutate=mutate).run()
    refused(result, policy, "manifest_invalid")


def test_N13_record_evaluator_binding_wrong_even_if_approved_by_manifest(tmp_path):
    rec = make_record(mutate=lambda r: r["evaluator"].update(binding="script"))
    policy, result = Scenario(tmp_path, rec).run()
    refused(result, policy, "record_refused", "evaluator_unsupported")


@pytest.mark.parametrize("name,mutate,expected", [
    ("withdrawn", lambda r: r.update(status="withdrawn"), "status_not_active"),
    ("unsupported_version", lambda r: r.update(contract_version="s03-v2"), "contract_unsupported"),
    ("not_authorizing_false", lambda r: r.update(non_authorizing=False), "record_invalid"),
    ("other_runtime", lambda r: r["applicability"].update(runtime_source_blob_id="0" * 40), "not_applicable"),
])
def test_N14_invalid_or_unsupported_record_approved_by_manifest(tmp_path, name, mutate, expected):
    policy, result = Scenario(tmp_path, make_record(mutate=mutate)).run()
    refused(result, policy, "record_refused", expected)


def test_N15_malformed_record_text_approved_by_manifest(tmp_path):
    s = Scenario(tmp_path)
    raw = b'{"record_type": "local-execution-allowlist", "record_type": "x"}'
    s.record_path.write_bytes(raw)
    manifest = make_manifest(s.rec, raw)
    s.manifest_path.write_bytes(manifest_bytes(manifest))
    trust = dataclasses.replace(s.trust, manifest_sha256=sha256_of(s.manifest_path.read_bytes()))
    policy, result = s.run(trust=trust)
    refused(result, policy, "record_refused", "record_malformed")


def test_N16_missing_approved_selection(tmp_path):
    s = Scenario(tmp_path)
    policy, result = s.run(manifest_path=tmp_path / "absent.json")
    refused(result, policy, "manifest_missing")
    policy, result = s.run(manifest_path=None)
    refused(result, policy, "manifest_missing")
    policy, result = s.run(manifest_path=tmp_path)  # a directory
    refused(result, policy, "manifest_missing")


def test_N17_missing_record_file(tmp_path):
    s = Scenario(tmp_path)
    policy, result = s.run(record_path=tmp_path / "absent.json")
    refused(result, policy, "record_missing")
    policy, result = s.run(record_path=None)
    refused(result, policy, "record_missing")


@pytest.mark.parametrize("bad", [
    None,
    "sha256:abc",
    {"manifest_sha256": "x"},
])
def test_N18_trust_config_missing_or_wrong_type(tmp_path, bad):
    s = Scenario(tmp_path)
    policy, result = s.run(trust=bad)
    refused(result, policy, "trust_config_invalid")


@pytest.mark.parametrize("field,value", [
    ("manifest_sha256", None),
    ("manifest_sha256", "ABC"),
    ("manifest_sha256", "sha256:" + "A" * 64),
    ("runtime_source_blob_id", "xyz"),
    ("runtime_source_blob_id", None),
    ("runtime_source_sha256", 5),
    ("runtime_source_sha256", "0" * 64),
    ("runtime_source_path", 12),
])
def test_N19_malformed_trusted_context(tmp_path, field, value):
    s = Scenario(tmp_path)
    policy, result = s.run(trust=dataclasses.replace(s.trust, **{field: value}))
    refused(result, policy, "trust_config_invalid")


@pytest.mark.parametrize("bad_policy", [None, {"allowed_units": ["USD"]}, "policy", 5])
def test_N20_caller_policy_must_be_a_local_execution_policy(tmp_path, bad_policy):
    s = Scenario(tmp_path)
    result = apply_registry_overlay(bad_policy, s.trust, s.manifest_path, s.record_path)
    assert (result.disposition, result.reason, result.overlay_applied) == ("REFUSE", "caller_policy_invalid", False)
    assert result.policy is bad_policy


@pytest.mark.parametrize("text", [
    b'{"a": 1, "a": 2}', b"NaN", b"", b"[]", b"null", b"not json", b'{"manifest_type": NaN}',
])
def test_N21_malformed_manifest_text_even_when_pinned(tmp_path, text):
    s = Scenario(tmp_path)
    s.manifest_path.write_bytes(text)
    trust = dataclasses.replace(s.trust, manifest_sha256=sha256_of(text))
    policy, result = s.run(trust=trust)
    refused(result, policy, "manifest_invalid")


@pytest.mark.parametrize("name,mutate", [
    ("unknown_top", lambda m: m.update(extra=1)),
    ("unknown_record", lambda m: m["record"].update(extra=1)),
    ("unknown_runtime", lambda m: m["runtime"].update(extra=1)),
    ("unknown_evaluator", lambda m: m["evaluator"].update(extra=1)),
    ("unknown_source", lambda m: m["record_source"].update(extra=1)),
    ("missing_record", lambda m: m.pop("record")),
    ("missing_runtime", lambda m: m.pop("runtime")),
    ("version_string", lambda m: m["record"].update(record_version="1")),
    ("version_bool", lambda m: m["record"].update(record_version=True)),
    ("version_zero", lambda m: m["record"].update(record_version=0)),
    ("bad_digest_format", lambda m: m["record"].update(record_digest="abc")),
    ("bad_file_hash_format", lambda m: m["record"].update(file_sha256="sha256:XYZ")),
    ("bad_blob_format", lambda m: m["runtime"].update(source_blob_id="xyz")),
    ("bad_commit", lambda m: m["record_source"].update(commit="abc")),
    ("record_as_list", lambda m: m.update(record=[])),
])
def test_N22_manifest_shape_is_strict(tmp_path, name, mutate):
    policy, result = Scenario(tmp_path, manifest_mutate=mutate).run()
    refused(result, policy, "manifest_invalid")


def test_N23_oversized_files_are_refused(tmp_path):
    s = Scenario(tmp_path)
    big = b" " * (1024 * 1024 + 1)
    s.manifest_path.write_bytes(big)
    policy, result = s.run(trust=dataclasses.replace(s.trust, manifest_sha256=sha256_of(big)))
    refused(result, policy, "manifest_invalid")
    (tmp_path / "second").mkdir()
    s2 = Scenario(tmp_path / "second")
    s2.record_path.write_bytes(big)
    policy, result = s2.run()
    refused(result, policy, "record_file_mismatch")


# ------------------------------------------------------------------ representation coverage (S05 hand-off)

@pytest.mark.parametrize("name,mutate", [
    ("empty_list", lambda r: r["data"].update(allowed_units=[])),
    ("whitespace_entry", lambda r: r["data"].update(allowed_actions=["has space"])),
    ("wildcard_entry", lambda r: r["data"].update(allowed_actions=["refund.*"])),
    ("zero_width_entry", lambda r: r["data"].update(allowed_adapters=["a​b"])),
    ("oversized_list", lambda r: r["data"].update(allowed_units=["e%04d" % i for i in range(257)])),
    ("oversized_entry", lambda r: r["data"].update(allowed_units=["x" * 129])),
])
def test_R1_unrepresentable_policy_classes_are_refused_and_leave_caller_policy_in_force(tmp_path, name, mutate):
    policy, result = Scenario(tmp_path, make_record(mutate=mutate)).run()
    refused(result, policy, "record_refused", "record_invalid")
    policy.check(frozen_op())  # the caller policy still governs exactly as before


# ------------------------------------------------------------------ failure containment

def test_F1_unexpected_consumer_exception_is_a_refusal_without_narrowing_or_activation_claim(tmp_path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("injected fault")

    monkeypatch.setattr("registry_consumer.consumer.validate_record_text", boom)
    policy, result = Scenario(tmp_path).run()
    refused(result, policy, "consumer_error")


def test_F2_policy_construction_failure_is_contained(tmp_path, monkeypatch):
    import registry_consumer.consumer as consumer

    def boom(*_args, **_kwargs):
        raise ValueError("injected fault")

    monkeypatch.setattr(consumer.dataclasses, "replace", boom)
    policy, result = Scenario(tmp_path).run()
    refused(result, policy, "consumer_error")


def test_F3_refusal_never_touches_the_caller_policy_object(tmp_path):
    s = Scenario(tmp_path)
    caller = caller_policy()
    before = dataclasses.asdict(caller)
    s.record_path.write_bytes(b"{}")
    _, result = s.run(caller)
    assert result.disposition == "REFUSE"
    assert dataclasses.asdict(caller) == before


# ------------------------------------------------------------------ order, closed set, frozen inputs

def test_O1_reason_codes_are_the_closed_ordered_set():
    assert CONSUMER_REASON_CODES == (
        "caller_policy_invalid", "trust_config_invalid", "runtime_source_unverified", "manifest_missing",
        "manifest_pin_mismatch", "manifest_invalid", "manifest_runtime_mismatch", "record_missing",
        "record_file_mismatch", "record_refused", "record_identity_mismatch", "consumer_error",
    )


def test_O2_first_failing_check_wins(tmp_path):
    s = Scenario(tmp_path)
    tampered = tmp_path / "safe_executor.py"
    tampered.write_bytes(RUNTIME_SOURCE.read_bytes() + b"x")
    # bad runtime source beats a missing manifest
    trust = dataclasses.replace(s.trust, runtime_source_path=tampered)
    policy, result = s.run(trust=trust, manifest_path=tmp_path / "absent.json")
    refused(result, policy, "runtime_source_unverified")
    # malformed trust beats bad runtime source
    policy, result = s.run(trust=dataclasses.replace(trust, manifest_sha256="x"))
    refused(result, policy, "trust_config_invalid")
    # missing manifest beats a missing record
    policy, result = s.run(manifest_path=tmp_path / "absent.json", record_path=tmp_path / "absent2.json")
    refused(result, policy, "manifest_missing")
    # pin mismatch beats invalid manifest content
    s.manifest_path.write_bytes(b"not json")
    policy, result = s.run()
    refused(result, policy, "manifest_pin_mismatch")


def test_O3_result_is_frozen_and_deterministic(tmp_path):
    s = Scenario(tmp_path)
    _, first = s.run()
    _, second = s.run()
    assert (first.disposition, first.reason, first.narrowed_fields) == (second.disposition, second.reason, second.narrowed_fields)
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.disposition = "REFUSE"


# ------------------------------------------------------------------ preserved boundaries

def test_B1_s03_validator_and_baseline_are_unchanged():
    for rel, blob in FROZEN_S03.items():
        data = (ROOT / rel).read_bytes()
        assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == blob, rel
    data = RUNTIME_SOURCE.read_bytes()
    assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == BLOB
    assert sha256_of(data) == SHA


def test_B2_consumer_has_no_discovery_network_process_or_dynamic_code():
    banned_modules = {"os", "subprocess", "socket", "importlib", "glob", "shutil", "urllib", "http", "requests"}
    banned_attrs = {"glob", "iglob", "rglob", "listdir", "scandir", "walk", "iterdir", "system", "popen"}
    banned_calls = {"eval", "exec", "compile", "__import__"}
    files = sorted(CONSUMER_DIR.glob("*.py"))
    assert files
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {a.name.split(".")[0] for a in node.names} & banned_modules, path
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in banned_modules, path
            if isinstance(node, ast.Attribute):
                assert node.attr not in banned_attrs, (path, node.attr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls, path


def test_B3_consumer_never_imports_policy_internals_it_must_not_change():
    for path in CONSUMER_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in ("max_amount", "max_effects", "allowed_target_prefixes", "target_match", "allowed_institutions",
                     "allowed_authority_domains", "_target_allowed", "_strict_finite_number"):
            assert name not in text, (path, name)
