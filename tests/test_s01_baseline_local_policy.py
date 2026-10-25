"""S01 behavioural fixture for the imported v0.1 baseline (non-authorizing, synthetic, builder-side).

Runs the real decision path of the imported Runtime source (validate_snapshot -> LocalExecutionPolicy.check ->
SQLite destination commit, via LocalDestinationExecutor.execute_snapshot) at the pinned historical revision.
It characterises what the baseline does today. It extracts no rule, populates no registry and qualifies nothing.

Attribution: the ExecutionOperation field values in _operation() (actor, principal, institution_id, authority_domain,
manifest_*, proposal_commitment, action_id, adapter_id, target, requested_permissions, amount, unit, effects, the
authority/requirement/grant ids, effective_max_effects) are copied from the synthetic operation in
cognous-execution-runtime tests/test_producer_contract.py at ec728da6dc301a664b331ac8986afd6e850a1273
(Apache-2.0, Copyright 2026 Cognous; see baseline/execution-runtime/NOTICE and engine/LICENSE). The payload text, the
policy construction, the run helpers and all test functions are newly written for S01.
"""
import dataclasses
import hashlib
from pathlib import Path

import pytest

from engine.safe_executor import (
    EXECUTION_ENVELOPE_VERSION,
    DurableRefundDestination,
    ExecutionEnvelope,
    ExecutionOperation,
    LocalDestinationExecutor,
    LocalExecutionPolicy,
    commitment,
    snapshot_envelope,
)

IMPORTED = Path(__file__).resolve().parent.parent / "baseline" / "execution-runtime"

# Git blob ids at cogno-us/cognous-execution-runtime ec728da6dc301a664b331ac8986afd6e850a1273
PINNED_BLOBS = {
    "engine/__init__.py": "9013e21fc7b3726aa9b65ddc381bfcb8310f2ccf",
    "engine/safe_executor.py": "2fc880dae37eac76e5074533435740ce0684209d",
    "engine/LICENSE": "d645695673349e3947e8e5ae42332d0ac3164cd7",
    "LICENSE": "f7b526698bb7ed2d26d96c49f2f32234c88f69bc",
    "LICENSE-APACHE-2.0": "d645695673349e3947e8e5ae42332d0ac3164cd7",
    "NOTICE": "f2e9d127dbe54f68791e28cb6d1614909caf2d19",
}


def _git_blob_id(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _operation() -> ExecutionOperation:
    payload = {"refund_reason": "s01-baseline-fixture"}
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
        adapter_id="urn:cognous:adapter:synthetic-refund",
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


def _policy(op: ExecutionOperation, **changes) -> LocalExecutionPolicy:
    base = dict(
        allowed_institutions=frozenset({op.institution_id}),
        allowed_authority_domains=frozenset({op.authority_domain}),
        allowed_adapters=frozenset({op.adapter_id}),
        allowed_actions=frozenset({op.action_id}),
        allowed_target_prefixes=("urn:cognous:synthetic-account:",),
        allowed_units=frozenset({"USD"}),
        max_amount=1000.0,
        max_effects=1,
    )
    base.update(changes)
    return LocalExecutionPolicy(**base)


def _run(tmp_path, op, policy):
    destination = DurableRefundDestination(tmp_path / "state")
    envelope = ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", "effect-1", op)
    executor = LocalDestinationExecutor(destination, policy)
    return destination, executor, snapshot_envelope(envelope)


def test_imported_files_are_byte_identical_to_the_pinned_revision():
    for rel, blob in PINNED_BLOBS.items():
        assert _git_blob_id(IMPORTED / rel) == blob, rel


def test_positive_case_executes_and_commits_one_synthetic_effect(tmp_path):
    op = _operation()
    destination, executor, snapshot = _run(tmp_path, op, _policy(op))
    result = executor.execute_snapshot(snapshot)
    assert result.status == "executed"
    assert result.attempted is True and result.acknowledged is True and result.newly_executed is True
    assert result.observation["state"] == "applied"
    assert destination.effect_count(op.grant_id) == 1
    assert destination.failure_history("effect-1") == []


def test_refusal_case_target_outside_policy_is_refused_before_any_effect(tmp_path):
    op = dataclasses.replace(_operation(), target="urn:other:prefix:customer-1")
    destination, executor, snapshot = _run(tmp_path, op, _policy(op))
    with pytest.raises(PermissionError, match="^local target restriction$"):
        executor.execute_snapshot(snapshot)
    assert destination.effect_count(op.grant_id) == 0
    history = destination.failure_history("effect-1")
    assert [(r["failure_class"], r["reason_code"], r["stage"]) for r in history] == [
        ("policy_denial", "local_policy_rejected", "pre_dispatch")
    ]


# One refusal per local restriction, in the order the baseline checks them (record of current behaviour only).
REFUSALS = [
    ("institution_id", "urn:cognous:institution:other", "local institution restriction"),
    ("authority_domain", "other-domain", "local authority-domain restriction"),
    ("adapter_id", "urn:cognous:adapter:other", "local adapter restriction"),
    ("action_id", "refund.other", "local action restriction"),
    ("unit", "EUR", "local unit restriction"),
    ("amount", 1000.01, "local amount restriction"),
    ("effective_max_effects", 2, "local effect-count restriction"),
]


@pytest.mark.parametrize("field,value,reason", REFUSALS)
def test_each_local_restriction_refuses_with_its_stable_reason(tmp_path, field, value, reason):
    op = dataclasses.replace(_operation(), **{field: value})
    # The policy is built from the unmodified operation so that only the changed field falls outside it.
    destination, executor, snapshot = _run(tmp_path, op, _policy(_operation()))
    with pytest.raises(PermissionError) as info:
        executor.execute_snapshot(snapshot)
    assert str(info.value) == reason
    assert destination.effect_count(op.grant_id) == 0


def test_effects_other_than_one_is_refused_by_validation_before_the_policy_text(tmp_path):
    # Finding: "local adapter supports exactly one effect" (LocalExecutionPolicy.check) is not reachable through the
    # real path, because snapshot_envelope and validate_snapshot refuse effects != 1 first with a ValueError.
    op = dataclasses.replace(_operation(), effects=2, effective_max_effects=2)
    envelope = ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", "effect-1", op)
    with pytest.raises(ValueError, match="^effects must equal exactly 1$"):
        snapshot_envelope(envelope)
    destination, executor, snapshot = _run(tmp_path, _operation(), _policy(_operation(), max_effects=2))
    forged = dataclasses.replace(snapshot, operation=dataclasses.replace(snapshot.operation, effects=2))
    with pytest.raises(ValueError, match="^effects must equal exactly 1$"):
        executor.execute_snapshot(forged)
    assert destination.effect_count(op.grant_id) == 0
    assert [r["reason_code"] for r in destination.failure_history("effect-1")] == ["local_policy_rejected"]


def test_segment_aware_target_matching_through_execute_snapshot(tmp_path):
    entry = ("urn:cognous:synthetic-account",)  # no trailing separator
    spill = dataclasses.replace(_operation(), target="urn:cognous:synthetic-accountX")
    inside = dataclasses.replace(_operation(), target="urn:cognous:synthetic-account:customer-1")
    d1, e1, s1 = _run(tmp_path / "a", spill, _policy(spill, allowed_target_prefixes=entry))
    with pytest.raises(PermissionError, match="^local target restriction$"):
        e1.execute_snapshot(s1)
    assert d1.effect_count(spill.grant_id) == 0
    d2, e2, s2 = _run(tmp_path / "b", inside, _policy(inside, allowed_target_prefixes=entry))
    assert e2.execute_snapshot(s2).status == "executed"
    d3, e3, s3 = _run(tmp_path / "c", spill, _policy(spill, allowed_target_prefixes=entry, target_match="legacy-prefix"))
    assert e3.execute_snapshot(s3).status == "executed" and d3.effect_count(spill.grant_id) == 1


def test_default_target_match_is_segment_aware_and_legacy_prefix_is_an_explicit_opt_in(tmp_path):
    entry = ("urn:cognous:synthetic-account",)  # no trailing separator
    inside = dataclasses.replace(_operation(), target="urn:cognous:synthetic-account:customer-1")
    spill = dataclasses.replace(_operation(), target="urn:cognous:synthetic-accountX")
    assert _policy(inside, allowed_target_prefixes=entry).target_match == "segment"
    segment = _policy(inside, allowed_target_prefixes=entry)
    assert segment._target_allowed(inside.target) is True
    assert segment._target_allowed(spill.target) is False
    legacy = _policy(inside, allowed_target_prefixes=entry, target_match="legacy-prefix")
    assert legacy._target_allowed(spill.target) is True


# --- S01 review-round additions: boundary, ordering and exact-mode controls (characterisation only) ---


def test_amount_exactly_at_max_is_allowed(tmp_path):
    op = dataclasses.replace(_operation(), amount=1000.0)
    destination, executor, snapshot = _run(tmp_path, op, _policy(op))
    assert executor.execute_snapshot(snapshot).status == "executed"
    assert destination.effect_count(op.grant_id) == 1


def test_effective_max_effects_equal_to_policy_max_is_allowed(tmp_path):
    op = dataclasses.replace(_operation(), effective_max_effects=2)
    destination, executor, snapshot = _run(tmp_path, op, _policy(op, max_effects=2))
    assert executor.execute_snapshot(snapshot).status == "executed"


def test_first_failing_check_in_documented_order_wins(tmp_path):
    # Violate institution AND authority domain: institution is reported (checked first).
    op = _operation()
    policy = _policy(
        op,
        allowed_institutions=frozenset({"urn:cognous:institution:other"}),
        allowed_authority_domains=frozenset({"other-domain"}),
    )
    destination, executor, snapshot = _run(tmp_path, op, policy)
    with pytest.raises(PermissionError, match="^local institution restriction$"):
        executor.execute_snapshot(snapshot)


def test_exact_target_match_mode_allows_only_the_exact_target(tmp_path):
    op = _operation()
    ok = _policy(op, allowed_target_prefixes=(op.target,), target_match="exact")
    destination, executor, snapshot = _run(tmp_path, op, ok)
    assert executor.execute_snapshot(snapshot).status == "executed"
    longer = dataclasses.replace(op, target=op.target + "-x")
    destination2, executor2, snapshot2 = _run(tmp_path / "b", longer, ok)
    with pytest.raises(PermissionError, match="^local target restriction$"):
        executor2.execute_snapshot(snapshot2)


# --- S01 independent-review-round additions: target well-formedness and boundary characterisation ---
# These call the policy's target matcher directly (characterisation of current behaviour; the real-path
# refusal for one malformed target is asserted separately below).

PREFIX = "urn:cognous:synthetic-account:"
MALFORMED = [
    "",
    PREFIX + "a\x00b",              # NUL (Cc)
    PREFIX + "a\nb",                # control character (Cc)
    PREFIX + "a​b",            # zero-width space (Cf)
    PREFIX + "a b",            # line separator (Zl)
    PREFIX + "a b",            # paragraph separator (Zp)
    PREFIX + "a\ud800b",            # lone surrogate (Cs)
    PREFIX + "..",                  # dot-segment
    PREFIX + "a/../b",
    PREFIX + "a/./b",
    PREFIX + "a\\..\\b",            # backslash-separated dot-segment
    PREFIX + "a:..:b",              # colon-separated dot-segment
]


@pytest.mark.parametrize("mode", ["segment", "legacy-prefix", "exact"])
@pytest.mark.parametrize("target", MALFORMED)
def test_malformed_targets_are_refused_in_every_match_mode(mode, target):
    op = _operation()
    entries = (PREFIX, target) if (mode == "exact" and target) else (PREFIX,)  # empty entries are invalid policy
    policy = _policy(op, allowed_target_prefixes=entries, target_match=mode)
    assert policy._target_allowed(target) is False


def test_non_string_target_is_refused():
    policy = _policy(_operation())
    assert policy._target_allowed(None) is False
    assert policy._target_allowed(123) is False


@pytest.mark.parametrize(
    "prefix,target,expected",
    [
        ("urn:a", "urn:a", True),            # equal to entry
        ("urn:a", "urn:a:x", True),          # ":" boundary
        ("urn:a", "urn:a/x", True),          # "/" boundary
        ("urn:a", "urn:ax", False),          # spill, not on a boundary
        ("urn:a/", "urn:a/x", True),         # entry ends in separator
        ("urn:a:", "urn:a:x", True),
        ("urn:a", "urn:b", False),
    ],
)
def test_segment_boundary_rules(prefix, target, expected):
    policy = _policy(_operation(), allowed_target_prefixes=(prefix,))
    assert policy._target_allowed(target) is expected


def test_any_allowed_entry_may_match():
    policy = _policy(_operation(), allowed_target_prefixes=("urn:a", "urn:b"))
    assert policy._target_allowed("urn:b:x") is True


def test_dot_segment_target_is_refused_through_the_real_path(tmp_path):
    op = dataclasses.replace(_operation(), target=PREFIX + "customer-1/../customer-2")
    destination, executor, snapshot = _run(tmp_path, op, _policy(op))
    with pytest.raises(PermissionError, match="^local target restriction$"):
        executor.execute_snapshot(snapshot)
    assert destination.effect_count(op.grant_id) == 0
