"""S05 differential harness: historical LocalExecutionPolicy versus the registry-backed path (non-authorizing, builder-side).

Plan: OCS-REG-PLAN v1.1 S05 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2).
Constitution: cognous-engineering-constitution 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.
Specification: docs/s05-comparison-spec.md. Expected outcomes: tests/s05_expectations.json and tests/s05_oracle.py, frozen
before this file existed and pinned below by git blob id. This harness never computes an expected outcome from the S03
validator or the S04 consumer. It runs everything first, records every result (failures included), then asserts.

Set S05_RESULTS_DIR to a directory to have the raw results written there (deterministic JSON). Not run by default.

Attribution: the ExecutionOperation field values in operation() other than adapter, action and unit are the synthetic values
of the S01 fixture (tests/test_s01_baseline_local_policy.py), copied there from cognous-execution-runtime
tests/test_producer_contract.py at ec728da6dc301a664b331ac8986afd6e850a1273 (Apache-2.0).
"""
import dataclasses
import hashlib
import inspect
import json
import os
import platform
import sys
from pathlib import Path

import pytest

import s05_oracle as oracle
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
from registry_consumer import TrustConfig, apply_registry_overlay
from registry_contract.validator import validate_record_text

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
EXPECTATIONS_PATH = TESTS / "s05_expectations.json"

# Frozen before this harness existed (git blob ids). A change here or to the files is an amendment, not a fix.
FROZEN_FILES = {
    "tests/s05_expectations.json": "37a68275c8c2b932d7a47adac43c05ec802d0081",
    "tests/s05_oracle.py": "503851c4ffa989a213c7dfb4d8957d0d540cb73c",
}

EXP = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))
FROZEN = EXP["frozen"]
BLOB = FROZEN["baseline_safe_executor_blob"]
SHA = FROZEN["baseline_safe_executor_sha256"]
RUNTIME_SOURCE = ROOT / "baseline" / "execution-runtime" / "engine" / "safe_executor.py"
EVALUATOR_ID = "engine.safe_executor.LocalExecutionPolicy.check"
INSTITUTION = "urn:cognous:institution:demo"
DOMAIN = "customer-refunds"
MAX_FILE = 1024 * 1024

REASON_TO_CODE = {oracle.REASON[f]: oracle.CODE[f] for f in oracle.FIELDS}
FIELD_TO_OPKEY = oracle.OP_KEY
BASE_SETS = {
    "allowed_adapters": [oracle.VALUES["allowed_adapters"][0]],
    "allowed_actions": [oracle.VALUES["allowed_actions"][0]],
    "allowed_units": [oracle.VALUES["allowed_units"][0]],
}


# ------------------------------------------------------------------ helpers (independent of the code under test)

def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def sha256_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canon(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def seal(rec: dict) -> dict:
    rec["data_digest"] = sha256_of(canon(rec["data"]))
    rec["record_digest"] = sha256_of(canon({k: v for k, v in rec.items() if k != "record_digest"}))
    return rec


def make_record(sets: dict, version: int = 1, mutate=None, reseal: bool = True) -> dict:
    rec = {
        "record_type": "local-execution-allowlist",
        "contract_version": "s03-v1",
        "record_id": "lep.allowlist.s05",
        "record_version": version,
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
        "evaluator": {"evaluator_id": EVALUATOR_ID, "binding": "registered-code-reference",
                      "supplies": ["allowed_actions", "allowed_adapters", "allowed_units"]},
        "data": {f: sorted(sets[f]) for f in ("allowed_units", "allowed_adapters", "allowed_actions")},  # S03 requires sorted entries
        "data_digest": "",
        "provenance": {"decision_ref": "docs/decisions/2026-10-24-s05-authorization.md",
                       "authored_at": "2026-10-24T12:00:00Z", "authored_by": "synthetic S05 harness fixture"},
        "record_digest": "",
    }
    if version > 1:
        prev = make_record(sets, version - 1)
        rec["supersedes"] = {"record_id": rec["record_id"], "record_version": version - 1,
                             "record_digest": prev["record_digest"]}
    if mutate:
        mutate(rec)
    return seal(rec) if reseal else rec


def record_bytes(rec: dict) -> bytes:
    return (json.dumps(rec, indent=2) + "\n").encode("utf-8")


def make_manifest(rec: dict, raw: bytes, mutate=None) -> dict:
    manifest = {
        "manifest_type": "local-execution-allowlist-selection",
        "manifest_version": "s04-v1",
        "contract_version": "s03-v1",
        "record": {"record_id": rec["record_id"], "record_version": rec["record_version"],
                   "record_digest": rec["record_digest"], "file_sha256": sha256_of(raw)},
        "record_source": {"repository": "cogno-us/cognous-ocs-registry", "commit": "1" * 40,
                          "path": "registry_records/s05.record.json"},
        "evaluator": {"evaluator_id": EVALUATOR_ID, "binding": "registered-code-reference"},
        "runtime": {"source_blob_id": BLOB, "source_sha256": SHA},
    }
    if mutate:
        mutate(manifest)
    return manifest


def manifest_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, indent=2) + "\n").encode("utf-8")


class Scenario:
    """Trusted-host layout. The harness plays the operator for synthetic scenarios: it computes the pin from the manifest
    it generates. Pin independence from checked files is exercised separately by the PIN cases and by R09, R14, R24, R31."""

    def __init__(self, directory: Path, sets=None, rec=None, raw=None, manifest_mutate=None):
        directory.mkdir(parents=True, exist_ok=True)
        self.dir = directory
        self.rec = rec if rec is not None else make_record(sets or BASE_SETS)
        self.raw = raw if raw is not None else record_bytes(self.rec)
        self.record_path = directory / "record.json"
        self.record_path.write_bytes(self.raw)
        self.manifest_path = directory / "manifest.json"
        self.set_manifest(make_manifest(self.rec, self.raw, manifest_mutate))

    def set_manifest(self, manifest: dict, raw: bytes = None):
        self.manifest = manifest
        self.manifest_raw = raw if raw is not None else manifest_bytes(manifest)
        self.manifest_path.write_bytes(self.manifest_raw)
        self.trust = TrustConfig(manifest_sha256=sha256_of(self.manifest_raw), runtime_source_blob_id=BLOB,
                                 runtime_source_sha256=SHA)

    def approve(self, raw: bytes, rec: dict = None, manifest_mutate=None):
        """Deliver `raw` as the record and have the pinned manifest approve exactly those bytes."""
        self.raw = raw
        self.record_path.write_bytes(raw)
        self.set_manifest(make_manifest(rec if rec is not None else self.rec, raw, manifest_mutate))


def policy_from(sets: dict, **changes) -> LocalExecutionPolicy:
    args = dict(
        allowed_institutions=frozenset({INSTITUTION}),
        allowed_authority_domains=frozenset({DOMAIN}),
        allowed_adapters=frozenset(sets["allowed_adapters"]),
        allowed_actions=frozenset(sets["allowed_actions"]),
        allowed_target_prefixes=("urn:cognous:synthetic-account:",),
        allowed_units=frozenset(sets["allowed_units"]),
        max_amount=1000.0,
        max_effects=1,
    )
    args.update(changes)
    return LocalExecutionPolicy(**args)


def operation(adapter: str, action: str, unit: str) -> ExecutionOperation:
    payload = {"refund_reason": "s05-differential"}
    return ExecutionOperation(
        actor="urn:cognous:identity:agent-1", principal="urn:cognous:principal:service",
        institution_id=INSTITUTION, authority_domain=DOMAIN,
        manifest_id="refund-integration-v1-1", manifest_version="1.1", manifest_digest="sha256:" + "a" * 64,
        proposal_commitment="sha256:" + "b" * 64, action_id=action, adapter_id=adapter,
        target="urn:cognous:synthetic-account:customer-1", payload=payload, payload_commitment=commitment(payload),
        requested_permissions=(action,), amount=50.0, unit=unit, effects=1,
        authority_context_id="urn:cognous:authority-context:refund-demo",
        requirement_id="urn:cognous:requirement:refund-t1", grant_id="urn:cognous:grant:refund-1",
        grant_revision="1", effective_max_effects=1,
    )


_FROZEN_OPS = {}


def frozen_op(adapter: str, action: str, unit: str):
    key = (adapter, action, unit)
    if key not in _FROZEN_OPS:
        env = ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", "effect-1", operation(adapter, action, unit))
        _FROZEN_OPS[key] = snapshot_envelope(env).operation
    return _FROZEN_OPS[key]


def op_of(op: dict):
    return frozen_op(op["adapter"], op["action"], op["unit"])


def code_of(policy, op: dict) -> str:
    """"A" admitted; a/x/u the first failing allow-list; "?" any other refusal; "!" any other exception."""
    try:
        policy.check(op_of(op))
        return oracle.ADMIT
    except PermissionError as exc:
        return REASON_TO_CODE.get(str(exc), "?")
    except Exception:  # noqa: BLE001 - recorded as a failure by the caller
        return "!"


def mask(universe, chosen) -> str:
    return "".join("1" if v in chosen else "0" for v in universe)


def masks(sets: dict, size: int) -> str:
    return "|".join(mask(oracle.VALUES[f][:size], sets[f]) for f in oracle.FIELDS)


def _sets_dict(policy) -> dict:
    return {f: sorted(getattr(policy, f)) for f in oracle.FIELDS}


# ------------------------------------------------------------------ results sink

@pytest.fixture(scope="module")
def sink():
    data = {
        "spec_version": EXP["spec_version"],
        "identities": {
            "base_commit": FROZEN["main_at_start"],
            "plan_blob": blob_id((ROOT / "docs" / "plans" / "PROJECT_PLAN-v1.1.md").read_bytes()),
            "baseline_safe_executor_blob": blob_id(RUNTIME_SOURCE.read_bytes()),
            "baseline_safe_executor_sha256": sha256_of(RUNTIME_SOURCE.read_bytes()),
            "s03_validator_blob": blob_id((ROOT / "registry_contract" / "validator.py").read_bytes()),
            "s03_package_init_blob": blob_id((ROOT / "registry_contract" / "__init__.py").read_bytes()),
            "s04_consumer_blob": blob_id((ROOT / "registry_consumer" / "consumer.py").read_bytes()),
            "frozen_expectations_blob": blob_id(EXPECTATIONS_PATH.read_bytes()),
            "frozen_oracle_blob": blob_id((TESTS / "s05_oracle.py").read_bytes()),
        },
        "configuration": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "system": platform.system(),
            "pytest": pytest.__version__,
            "consumer_limits": {"max_file_bytes": MAX_FILE},
        },
        "groups": {},
    }
    yield data
    out = os.environ.get("S05_RESULTS_DIR")
    if out:
        data["groups_present"] = sorted(data["groups"])
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "differential-raw.json").write_text(
            json.dumps(data, indent=1, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ G1 and G2 (A, B, D)

def _run_pair(caller_sets, registry_scenario, registry_sets, ops, size):
    caller = policy_from(caller_sets)
    before = _sets_dict(caller)
    result = apply_registry_overlay(caller, registry_scenario.trust, registry_scenario.manifest_path,
                                    registry_scenario.record_path)
    eff_sets = oracle.effective(caller_sets, registry_sets)
    direct = policy_from({f: eff_sets[f] for f in oracle.FIELDS})  # historical reference, built directly
    row = {"c": masks(caller_sets, size), "r": masks(registry_sets, size), "e": masks(eff_sets, size),
           "consumer": result.disposition}
    oracle_codes = "".join(oracle.code(o, eff_sets) for o in ops)
    direct_codes = "".join(code_of(direct, o) for o in ops)
    reg_codes = "".join(code_of(result.policy, o) for o in ops)
    caller_codes = "".join(code_of(caller, o) for o in ops)
    caller_oracle = "".join(oracle.code(o, {f: frozenset(caller_sets[f]) for f in oracle.FIELDS}) for o in ops)
    row.update(oracle=oracle_codes, direct=direct_codes, registry=reg_codes, caller=caller_codes)
    problems = []
    if result.disposition != "ACCEPT":
        problems.append("consumer did not accept a valid grid record: %s/%s" % (result.disposition, result.reason))
    if not (oracle_codes == direct_codes == reg_codes):
        problems.append("A: oracle/direct/registry codes differ")
    if caller_codes != caller_oracle:
        problems.append("oracle disagrees with the historical caller policy")
    widened = [i for i, (c, r) in enumerate(zip(caller_codes, reg_codes)) if c != oracle.ADMIT and r == oracle.ADMIT]
    if widened:
        problems.append("B: widening at operation indexes %s" % widened)
    if any(ch in "?!" for ch in reg_codes + direct_codes + caller_codes):
        problems.append("unexpected refusal or exception")
    if _sets_dict(caller) != before:
        problems.append("caller policy object was mutated")
    row["problems"] = problems
    return row


def _scenario_cache(tmp_path_factory, label):
    cache = {}

    def get(sets):
        key = tuple((f, tuple(sets[f])) for f in oracle.FIELDS)
        if key not in cache:
            cache[key] = Scenario(tmp_path_factory.mktemp("%s%03d" % (label, len(cache))), sets=sets)
        return cache[key]
    return get


@pytest.fixture(scope="module")
def g1(sink, tmp_path_factory):
    get = _scenario_cache(tmp_path_factory, "g1")
    ops = oracle.g1_operations()
    rows = [_run_pair(c, get(r), r, ops, 2) for c in oracle.g1_caller_policies() for r in oracle.g1_registry_records()]
    sink["groups"]["G1"] = {"operations": len(ops), "legend": "masks per field in order adapters|actions|units over the 2 universe values; "
                            "operation order is the oracle's g1_operations(); codes: A admitted, a adapter, x action, u unit",
                            "rows": rows}
    return rows


@pytest.fixture(scope="module")
def g2(sink, tmp_path_factory):
    get = _scenario_cache(tmp_path_factory, "g2")
    result = {}
    for field in oracle.FIELDS:
        ops = oracle.g2_operations(field)
        result[field] = [_run_pair(c, get(r), r, ops, 3) for c, r in oracle.g2_pairs(field)]
    sink["groups"]["G2"] = {"legend": "masks per field in order adapters|actions|units over the 3 universe values; "
                            "operations are g2_operations(field)", "rows": result}
    return result


def test_G1_exhaustive_equivalence_nonwidening_and_ordering(g1):
    spec = EXP["grids"]["G1"]
    assert len(g1) == spec["pairs"]
    assert len(g1) * spec["operations"] == spec["comparisons"]
    failures = [r for r in g1 if r["problems"]]
    assert not failures, "%d of %d G1 pairs failed; first: %s" % (len(failures), len(g1), failures[0])


def test_G1_grid_actually_exercises_each_outcome_class(g1):
    seen = set("".join(r["registry"] for r in g1))
    assert seen == {"A", "a", "x", "u"}
    narrowing = [r for r in g1 if r["e"] != r["c"]]
    assert narrowing and any("A" in r["caller"] and r["registry"] != r["caller"] for r in g1)
    assert any(set(r["e"].split("|")) == {"00"} for r in g1), "empty intersections must occur"


def test_G2_per_field_exhaustive(g2):
    spec = EXP["grids"]["G2"]
    total_pairs = sum(len(v) for v in g2.values())
    assert total_pairs == spec["pairs_per_field"] * spec["fields"]
    assert total_pairs * spec["operations_per_field"] == spec["comparisons"]
    failures = [r for rows in g2.values() for r in rows if r["problems"]]
    assert not failures, "%d G2 pairs failed; first: %s" % (len(failures), failures[0])


# ------------------------------------------------------------------ C and D: refusal cases R01-R34

def _tampered_source_copy(directory: Path, data: bytes) -> Path:
    path = directory / "safe_executor_copy.py"
    path.write_bytes(data)
    return path


def _approved_variant(s: Scenario, mutate, version: int = 1, reseal: bool = True, manifest_mutate=None):
    rec = make_record(BASE_SETS, version=version, mutate=mutate, reseal=reseal)
    s.approve(record_bytes(rec), rec, manifest_mutate)
    return rec


def _recipe(name: str, s: Scenario):
    """Apply the named recipe to a scenario; return (policy, trust, manifest_path, record_path)."""
    policy = policy_from(BASE_SETS)
    trust, manifest_path, record_path = s.trust, s.manifest_path, s.record_path
    base_raw = s.raw

    if name == "record_file_absent":
        s.record_path.unlink()
    elif name == "manifest_file_absent":
        s.manifest_path.unlink()
    elif name == "record_duplicate_key_approved":
        s.approve((json.dumps(s.rec)[:-1] + ', "status": "withdrawn"}').encode("utf-8"))
    elif name == "record_trailing_garbage_approved":
        s.approve(base_raw + b"garbage")
    elif name == "record_contract_version_unsupported_approved":
        _approved_variant(s, lambda r: r.update(contract_version="s03-v2"))
    elif name == "record_type_unsupported_approved":
        _approved_variant(s, lambda r: r.update(record_type="other-family"))
    elif name == "record_widened_and_redigested_not_approved":
        widened = make_record({**BASE_SETS, "allowed_units": ["EUR", "USD"], "allowed_actions": ["act.extra", BASE_SETS["allowed_actions"][0]]})
        s.record_path.write_bytes(record_bytes(widened))
    elif name == "record_single_byte_appended":
        s.record_path.write_bytes(base_raw + b" ")
    elif name == "manifest_replaced_by_self_consistent_attacker_manifest":
        attacker = make_record({**BASE_SETS, "allowed_units": ["EUR", "USD"]})
        araw = record_bytes(attacker)
        s.record_path.write_bytes(araw)
        s.manifest_path.write_bytes(manifest_bytes(make_manifest(attacker, araw)))  # pin left unchanged
    elif name == "record_data_altered_without_redigest_approved":
        rec = make_record(BASE_SETS)
        altered = json.loads(json.dumps(rec))
        altered["data"]["allowed_units"] = ["EUR", "USD"]
        s.approve(record_bytes(altered), rec)
    elif name == "manifest_selects_v2_record_is_v1":
        s.set_manifest(make_manifest(s.rec, s.raw, lambda m: m["record"].update(record_version=2)))
    elif name == "record_v2_manifest_selects_v1":
        rec2 = make_record(BASE_SETS, version=2)
        s.approve(record_bytes(rec2), rec2, lambda m: m["record"].update(record_version=1))
    elif name == "record_applicability_other_runtime_approved":
        _approved_variant(s, lambda r: r["applicability"].update(runtime_source_blob_id="0" * 40))
    elif name == "manifest_runtime_identity_differs_from_trusted":
        s.set_manifest(make_manifest(s.rec, s.raw, lambda m: m["runtime"].update(source_blob_id="0" * 40)))
    elif name == "record_source_sha256_differs_approved":
        _approved_variant(s, lambda r: r["source"].update(sha256="sha256:" + "0" * 64))
    elif name == "installed_evaluator_source_modified":
        copy = _tampered_source_copy(s.dir, RUNTIME_SOURCE.read_bytes() + b"\n# modified\n")
        trust = dataclasses.replace(s.trust, runtime_source_path=copy)
    elif name == "record_status_withdrawn_approved":
        _approved_variant(s, lambda r: r.update(status="withdrawn"))
    elif name == "record_status_proposed_approved":
        _approved_variant(s, lambda r: r.update(status="proposed"))
    elif name == "record_evaluator_binding_wrong_approved":
        _approved_variant(s, lambda r: r["evaluator"].update(binding="script"))
    elif name == "record_supplies_widened_approved":
        _approved_variant(s, lambda r: r["evaluator"].update(
            supplies=["allowed_actions", "allowed_adapters", "allowed_units", "max_amount"]))
    elif name == "record_non_authorizing_false_approved":
        _approved_variant(s, lambda r: r.update(non_authorizing=False))
    elif name == "manifest_record_id_differs":
        s.set_manifest(make_manifest(s.rec, s.raw, lambda m: m["record"].update(record_id="lep.allowlist.other")))
    elif name == "manifest_record_digest_differs":
        s.set_manifest(make_manifest(s.rec, s.raw, lambda m: m["record"].update(record_digest="sha256:" + "0" * 64)))
    elif name == "manifest_unknown_field":
        s.set_manifest(make_manifest(s.rec, s.raw, lambda m: m.update(extra=1)))
    elif name == "trust_pin_malformed":
        trust = dataclasses.replace(s.trust, manifest_sha256="not-a-pin")
    elif name == "caller_policy_subclass_with_replaced_check":
        @dataclasses.dataclass(frozen=True)
        class Weak(LocalExecutionPolicy):
            def check(self, op):
                return None
        policy = Weak(**{f.name: getattr(policy, f.name) for f in dataclasses.fields(LocalExecutionPolicy)})
    elif name == "record_oversized_approved":
        s.approve(base_raw + b" " * MAX_FILE)
    elif name == "record_path_is_fifo":
        fifo = s.dir / "fifo"
        os.mkfifo(fifo)
        record_path = fifo
    elif name == "record_extra_field_approved":
        rec = make_record(BASE_SETS)
        extra = json.loads(json.dumps(rec))
        extra["extra"] = 1
        s.approve(record_bytes(extra), rec)
    elif name == "record_required_field_missing_approved":
        rec = make_record(BASE_SETS)
        missing = json.loads(json.dumps(rec))
        del missing["status"]
        s.approve(record_bytes(missing), rec)
    elif name == "manifest_oversized_pinned":
        s.set_manifest(s.manifest, s.manifest_raw + b" " * MAX_FILE)
    elif name == "trust_absent":
        trust = None
    elif name == "record_v2_bad_supersedes_approved":
        rec2 = make_record(BASE_SETS, version=2, mutate=lambda r: r["supersedes"].update(record_id="lep.allowlist.other"))
        s.approve(record_bytes(rec2), rec2)
    elif name == "installed_evaluator_source_unreadable":
        trust = dataclasses.replace(s.trust, runtime_source_path=s.dir / "does-not-exist.py")
    else:
        raise AssertionError("unknown recipe " + name)
    if name not in ("installed_evaluator_source_modified", "trust_pin_malformed", "trust_absent",
                    "installed_evaluator_source_unreadable"):
        trust = s.trust
    if name == "record_path_is_fifo":
        record_path = s.dir / "fifo"
    else:
        record_path = s.record_path
    return policy, trust, s.manifest_path, record_path


def _thread_call(fn, timeout=10.0):
    import threading
    box = {}
    thread = threading.Thread(target=lambda: box.update(result=fn()), daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    return box["result"]


@pytest.fixture(scope="module")
def refusal(sink, tmp_path_factory):
    g1_ops = oracle.g1_operations()
    rows = []
    for case in EXP["refusal_cases"]:
        s = Scenario(tmp_path_factory.mktemp(case["id"].lower()))
        policy, trust, manifest_path, record_path = _recipe(case["recipe"], s)
        before = _sets_dict(policy) if type(policy) is LocalExecutionPolicy else None
        result = _thread_call(lambda: apply_registry_overlay(policy, trust, manifest_path, record_path))
        row = {"id": case["id"], "recipe": case["recipe"], "expected": case["expected"]}
        if result is None:
            row.update(actual="BLOCKED (consumer did not return within 10 s)", problems=["consumer blocked"])
            rows.append(row)
            continue
        actual = {"disposition": result.disposition, "reason": result.reason, "validator_reason": result.validator_reason}
        problems = []
        if actual != case["expected"]:
            problems.append("C: outcome differs from the frozen expectation")
        if result.overlay_applied is not False or result.narrowed_fields != ():
            problems.append("overlay reported applied or narrowed on a refusal")
        if result.policy is not policy:
            problems.append("refusal did not return the caller's policy object")
        if before is not None:
            if _sets_dict(policy) != before:
                problems.append("caller policy was modified")
            caller_sets = {f: frozenset(before[f]) for f in oracle.FIELDS}
            observed = "".join(code_of(result.policy, o) for o in g1_ops)
            expected_codes = "".join(oracle.code(o, caller_sets) for o in g1_ops)
            row["behavior_equals_historical_over_g1_ops"] = observed == expected_codes
            if observed != expected_codes:
                problems.append("policy behavior after refusal differs from the historical caller policy")
        else:
            row["behavior_check"] = "not applicable: caller policy is the deliberately weak subclass (its own check replaced)"
        row.update(actual=actual, problems=problems)
        rows.append(row)
    sink["groups"]["refusal"] = rows
    return rows


def test_C_refusal_cases_match_frozen_expectations_and_leave_caller_policy_in_force(refusal):
    assert len(refusal) == len(EXP["refusal_cases"]) == 34
    failures = [r for r in refusal if r["problems"]]
    assert not failures, "%d refusal cases failed; first: %s" % (len(failures), failures[0])


def test_C_refusal_reason_coverage_is_broad(refusal):
    reasons = {r["expected"]["reason"] for r in refusal}
    validator = {r["expected"]["validator_reason"] for r in refusal if r["expected"]["validator_reason"]}
    assert {"record_missing", "manifest_missing", "manifest_pin_mismatch", "manifest_invalid", "manifest_runtime_mismatch",
            "record_file_mismatch", "record_refused", "record_identity_mismatch", "runtime_source_unverified",
            "trust_config_invalid", "caller_policy_invalid"} <= reasons
    assert {"record_malformed", "contract_unsupported", "digest_mismatch", "version_not_latest", "not_applicable",
            "source_mismatch", "status_not_active", "evaluator_unsupported", "record_invalid",
            "supersession_invalid"} <= validator


# ------------------------------------------------------------------ E: representation coverage

def _class_list(cls):
    if "list" in cls:
        return list(cls["list"])
    if "list_length" in cls:
        return ["e%04d" % i for i in range(cls["list_length"])]
    return sorted(cls["values"])


def _historical_accepts(field: str, entries) -> bool:
    try:
        policy_from({**{f: BASE_SETS[f] for f in oracle.FIELDS}, field: entries})
        return True
    except ValueError:
        return False


@pytest.fixture(scope="module")
def representation(sink, tmp_path_factory):
    rows = []
    for cls in EXP["representation_classes"]:
        for field in oracle.FIELDS:
            entries = _class_list(cls)
            row = {"id": cls["id"], "field": field, "classification_expected": cls["classification"]}
            problems = []
            sets = {**BASE_SETS, field: entries}
            rec = make_record(sets)
            s = Scenario(tmp_path_factory.mktemp("%s-%s" % (cls["id"].lower(), field[8:])), rec=rec)
            ctx = {"runtime_source_blob_id": BLOB, "runtime_source_sha256": SHA, "latest_known_version": 1}
            s03 = validate_record_text(s.raw, ctx)
            if (s03.outcome, s03.reason) != ("REFUSE", cls["expected_s03_reason"]):
                problems.append("S03 outcome %s/%s differs from frozen %s" % (s03.outcome, s03.reason, cls["expected_s03_reason"]))
            caller_ok = _historical_accepts(field, entries)
            if caller_ok != cls["historical_constructor_accepts"]:
                problems.append("historical constructor acceptance differs from frozen expectation")
            base_policy = policy_from(BASE_SETS)
            res = apply_registry_overlay(base_policy, s.trust, s.manifest_path, s.record_path)
            actual = {"disposition": res.disposition, "reason": res.reason, "validator_reason": res.validator_reason}
            if actual != cls["expected_consumer"] or res.policy is not base_policy or res.overlay_applied:
                problems.append("consumer outcome differs from frozen expectation")
            row.update(s03=[s03.outcome, s03.reason], consumer=actual, historical_constructor_accepts=caller_ok)
            if caller_ok and entries:
                v = entries[0]
                caller_sets = {**BASE_SETS, field: set(entries)}
                caller = policy_from(caller_sets)
                op = {oracle.OP_KEY[f]: BASE_SETS[f][0] for f in oracle.FIELDS}
                op[oracle.OP_KEY[field]] = v
                # unsupported representation: the record is refused, the caller policy governs, behavior equals historical
                refused_res = apply_registry_overlay(caller, s.trust, s.manifest_path, s.record_path)
                hist_code, reg_code = code_of(caller, op), code_of(refused_res.policy, op)
                row["under_refusal"] = {"historical": hist_code, "registry_backed": reg_code}
                try:
                    op_of(op)
                    exercisable = True
                except Exception as exc:  # noqa: BLE001 - recorded, not hidden
                    exercisable = False
                    row["not_exercisable"] = "baseline snapshot_envelope cannot represent this value: %s" % type(exc).__name__
                if not exercisable:
                    # Neither path can evaluate an operation carrying this value; both fail identically before check().
                    if not (hist_code == reg_code == "!" and refused_res.policy is caller):
                        problems.append("behavior under refusal differs from historical")
                elif not (hist_code == reg_code == oracle.ADMIT and refused_res.policy is caller):
                    problems.append("behavior under refusal differs from historical")
                # designed narrowing: a representable record applied to a caller that lists the unsupported value
                narrow_caller = policy_from({**BASE_SETS, field: set(entries) | set(BASE_SETS[field])})
                good = Scenario(tmp_path_factory.mktemp("%s-%s-ok" % (cls["id"].lower(), field[8:])))
                narrowed = apply_registry_overlay(narrow_caller, good.trust, good.manifest_path, good.record_path)
                h2, r2 = code_of(narrow_caller, op), code_of(narrowed.policy, op)
                row["designed_narrowing"] = {"historical_caller": h2, "registry_backed": r2}
                expected_removed = oracle.CODE[field]
                if not exercisable:
                    if not (narrowed.disposition == "ACCEPT" and h2 == r2 == "!"):
                        problems.append("designed narrowing did not behave as the intersection specifies")
                elif not (narrowed.disposition == "ACCEPT" and h2 == oracle.ADMIT and r2 == expected_removed):
                    problems.append("designed narrowing did not behave as the intersection specifies")
            row["problems"] = problems
            rows.append(row)
    sink["groups"]["representation"] = rows
    return rows


def test_E_unsupported_classes_are_refused_by_s03_and_consumer_and_behave_as_historical_under_refusal(representation):
    assert len(representation) == len(EXP["representation_classes"]) * 3 == 60
    failures = [r for r in representation if r["problems"]]
    assert not failures, "%d representation cases failed; first: %s" % (len(failures), failures[0])


def test_E_classification_is_reported_per_class(representation):
    by_class = {}
    for r in representation:
        by_class.setdefault(r["id"], r["classification_expected"])
    assert by_class["E20"] == "historically_invalid_also_refused"
    assert [k for k, v in by_class.items() if v == "unsupported_representation"] == ["E%02d" % i for i in range(1, 20)]


@pytest.fixture(scope="module")
def boundaries(sink, tmp_path_factory):
    rows = []
    for b in EXP["representable_boundaries"]:
        for field in oracle.FIELDS:
            entries = ["e%04d" % i for i in range(b["list_length"])] if "list_length" in b else sorted(b["values"])
            sets = {**BASE_SETS, field: entries}
            s = Scenario(tmp_path_factory.mktemp("%s-%s" % (b["id"].lower(), field[8:])), sets=sets)
            caller = policy_from({**BASE_SETS, field: set(entries)})
            res = apply_registry_overlay(caller, s.trust, s.manifest_path, s.record_path)
            op = {oracle.OP_KEY[f]: BASE_SETS[f][0] for f in oracle.FIELDS}
            op[oracle.OP_KEY[field]] = entries[0]
            eff = oracle.effective({f: getattr(caller, f) for f in oracle.FIELDS}, {f: sets[f] for f in oracle.FIELDS})
            direct = policy_from(eff)
            problems = []
            if res.disposition != "ACCEPT":
                problems.append("representable boundary was refused: %s/%s" % (res.reason, res.validator_reason))
            if code_of(res.policy, op) != code_of(direct, op) or code_of(res.policy, op) != oracle.ADMIT:
                problems.append("behavior differs from the direct historical policy")
            if res.policy.allowed_units != direct.allowed_units or res.policy.allowed_adapters != direct.allowed_adapters \
                    or res.policy.allowed_actions != direct.allowed_actions:
                problems.append("effective sets differ")
            rows.append({"id": b["id"], "field": field, "consumer": res.disposition, "problems": problems})
    sink["groups"]["boundaries"] = rows
    return rows


def test_E_representable_boundaries_are_accepted_and_equivalent(boundaries):
    assert len(boundaries) == len(EXP["representable_boundaries"]) * 3 == 15
    failures = [r for r in boundaries if r["problems"]]
    assert not failures, "%d boundary cases failed; first: %s" % (len(failures), failures[0])


# ------------------------------------------------------------------ end to end through the baseline executor

def _execute(tmp: Path, name: str, policy, op: dict) -> dict:
    destination = DurableRefundDestination(tmp / name / "state")
    executor = LocalDestinationExecutor(destination, policy)
    operation_obj = operation(op["adapter"], op["action"], op["unit"])
    snapshot = snapshot_envelope(ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", "effect-1", operation_obj))
    try:
        res = executor.execute_snapshot(snapshot)
        return {"admitted": res.status == "executed", "error": None, "status": res.status,
                "effect_count": destination.effect_count(operation_obj.grant_id)}
    except PermissionError as exc:
        return {"admitted": False, "error": str(exc), "status": "raised",
                "effect_count": destination.effect_count(operation_obj.grant_id)}


@pytest.fixture(scope="module")
def e2e(sink, tmp_path_factory):
    rows = []
    for case in EXP["e2e_cases"]:
        tmp = tmp_path_factory.mktemp(case["id"].lower())
        caller_sets = {f: case["caller"][f] for f in oracle.FIELDS}
        registry_sets = {f: sorted(case["registry"][f]) for f in oracle.FIELDS}
        caller = policy_from(caller_sets)
        s = Scenario(tmp / "scn", sets=registry_sets)
        if "refusal_recipe" in case:
            assert case["refusal_recipe"] == "record_single_byte_appended"
            s.record_path.write_bytes(s.raw + b" ")
        res = apply_registry_overlay(caller, s.trust, s.manifest_path, s.record_path)
        if "refusal_recipe" in case:
            historical = caller  # the historical policy is the caller's own
        else:
            eff = oracle.effective({f: set(caller_sets[f]) for f in oracle.FIELDS}, {f: set(registry_sets[f]) for f in oracle.FIELDS})
            historical = policy_from(eff)
        h = _execute(tmp, "historical", historical, case["op"])
        r = _execute(tmp, "registry", res.policy, case["op"])
        problems = []
        exp = case["expected"]
        for label, got in (("historical", h), ("registry-backed", r)):
            if (got["admitted"], got["error"], got["effect_count"]) != (exp["admitted"], exp["error"], exp["effect_count"]):
                problems.append("%s result differs from the frozen expectation" % label)
        if h != r:
            problems.append("historical and registry-backed results differ")
        if ("refusal_recipe" in case) == (res.disposition == "ACCEPT"):
            problems.append("overlay disposition not as the case specifies")
        rows.append({"id": case["id"], "expected": exp, "historical": h, "registry_backed": r,
                     "overlay": res.disposition, "problems": problems})
    sink["groups"]["e2e"] = rows
    return rows


def test_X_end_to_end_results_equal_frozen_expectations_and_each_other(e2e):
    assert len(e2e) == len(EXP["e2e_cases"]) == 11
    failures = [r for r in e2e if r["problems"]]
    assert not failures, "%d end-to-end cases failed; first: %s" % (len(failures), failures[0])


# ------------------------------------------------------------------ PIN and LIM

FIXTURES = ROOT / "registry_records"
FIXTURE_MANIFEST = FIXTURES / "local-execution-allowlist.synthetic.manifest.json"
FIXTURE_RECORD = FIXTURES / "local-execution-allowlist.synthetic.record.json"


def _fixture_caller():
    return policy_from({"allowed_adapters": ["urn:cognous:adapter:synthetic-refund"],
                        "allowed_actions": ["refund.issue"], "allowed_units": ["USD"]})


@pytest.fixture(scope="module")
def pins(sink):
    frozen_pin = FROZEN["s04_candidate_manifest_digest"]
    rows = []
    trust = TrustConfig(manifest_sha256=frozen_pin, runtime_source_blob_id=BLOB, runtime_source_sha256=SHA)
    caller = _fixture_caller()
    res = apply_registry_overlay(caller, trust, FIXTURE_MANIFEST, FIXTURE_RECORD)
    rows.append({"id": "PIN-1", "actual": [res.disposition, res.reason],
                 "problems": [] if (res.disposition, res.reason) == ("ACCEPT", None) else ["frozen pin literal did not accept the committed fixtures"]})
    altered = frozen_pin[:-1] + ("0" if frozen_pin[-1] != "0" else "1")
    res2 = apply_registry_overlay(caller, dataclasses.replace(trust, manifest_sha256=altered), FIXTURE_MANIFEST, FIXTURE_RECORD)
    rows.append({"id": "PIN-2", "actual": [res2.disposition, res2.reason],
                 "problems": [] if (res2.disposition, res2.reason) == ("REFUSE", "manifest_pin_mismatch") else ["altered pin was not refused"]})
    params = list(inspect.signature(apply_registry_overlay).parameters)
    fields = [f.name for f in dataclasses.fields(TrustConfig)]
    ok = params == EXP["pin_cases"][2]["expected"]["parameters"] and fields == [
        "manifest_sha256", "runtime_source_blob_id", "runtime_source_sha256", "runtime_source_path"]
    rows.append({"id": "PIN-3", "actual": {"parameters": params, "trust_fields": fields},
                 "problems": [] if ok else ["API offers another way to supply or derive the pin"]})
    sink["groups"]["pin"] = rows
    return rows


def test_PIN_frozen_pin_literal_accepts_altered_pin_refuses_and_api_has_no_derivation_path(pins):
    assert [r["id"] for r in pins] == [c["id"] for c in EXP["pin_cases"]]
    failures = [r for r in pins if r["problems"]]
    assert not failures, failures


def test_PIN_frozen_candidate_digest_matches_committed_fixture_bytes():
    assert sha256_of(FIXTURE_MANIFEST.read_bytes()) == FROZEN["s04_candidate_manifest_digest"]


@pytest.fixture(scope="module")
def limitations(sink, tmp_path_factory):
    rows = []
    # LIM-1: loaded-code tampering is not detected
    s = Scenario(tmp_path_factory.mktemp("lim1"))
    original = LocalExecutionPolicy.check
    try:
        LocalExecutionPolicy.check = lambda self, op: None  # simulates in-process replacement of the loaded code object
        caller = policy_from(BASE_SETS)
        res = apply_registry_overlay(caller, s.trust, s.manifest_path, s.record_path)
        outside = {"adapter": oracle.OUTSIDE["allowed_adapters"], "action": oracle.OUTSIDE["allowed_actions"],
                   "unit": oracle.OUTSIDE["allowed_units"]}
        admits_outside = code_of(res.policy, outside) == oracle.ADMIT
    finally:
        LocalExecutionPolicy.check = original
    rows.append({"id": "LIM-1", "actual": {"disposition": res.disposition, "tampered_check_admits_everything": admits_outside},
                 "problems": [] if (res.disposition == "ACCEPT" and admits_outside) else ["limitation no longer reproduces; re-assess the claim"]})
    # LIM-2: S03 alone does not authenticate
    s2 = Scenario(tmp := tmp_path_factory.mktemp("lim2"))
    widened = make_record({**BASE_SETS, "allowed_units": ["EUR", "USD"]})
    s2.record_path.write_bytes(record_bytes(widened))
    ctx = {"runtime_source_blob_id": BLOB, "runtime_source_sha256": SHA, "latest_known_version": 1}
    s03 = validate_record_text(s2.record_path.read_bytes(), ctx)
    res2 = apply_registry_overlay(policy_from(BASE_SETS), s2.trust, s2.manifest_path, s2.record_path)
    rows.append({"id": "LIM-2", "actual": {"s03_outcome": s03.outcome, "consumer_reason": res2.reason},
                 "problems": [] if (s03.outcome, res2.reason) == ("ACCEPT", "record_file_mismatch") else ["limitation no longer reproduces"]})
    # LIM-3: record_source is unverified provenance
    s3 = Scenario(tmp_path_factory.mktemp("lim3"), manifest_mutate=lambda m: m["record_source"].update(commit="f" * 40))
    res3 = apply_registry_overlay(policy_from(BASE_SETS), s3.trust, s3.manifest_path, s3.record_path)
    rows.append({"id": "LIM-3", "actual": {"disposition": res3.disposition},
                 "problems": [] if res3.disposition == "ACCEPT" else ["limitation no longer reproduces"]})
    sink["groups"]["limitations"] = rows
    return rows


def test_LIM_documented_trust_limitations_reproduce_as_stated(limitations):
    assert [r["id"] for r in limitations] == [c["id"] for c in EXP["limitation_cases"]]
    failures = [r for r in limitations if r["problems"]]
    assert not failures, failures


# ------------------------------------------------------------------ frozen inputs and totals

def test_Z1_frozen_expectation_files_are_unchanged():
    for rel, blob in FROZEN_FILES.items():
        assert blob_id((ROOT / rel).read_bytes()) == blob, "frozen file changed: " + rel
    spec = (ROOT / "docs" / "s05-comparison-spec.md").read_text(encoding="utf-8")
    for blob in FROZEN_FILES.values():
        assert blob in spec


def test_Z2_subject_files_match_their_frozen_identities():
    expected = {
        "docs/plans/PROJECT_PLAN-v1.1.md": FROZEN["plan_blob"],
        "baseline/execution-runtime/engine/safe_executor.py": FROZEN["baseline_safe_executor_blob"],
        "registry_contract/validator.py": FROZEN["s03_validator_blob"],
        "registry_contract/__init__.py": FROZEN["s03_package_init_blob"],
        "registry_consumer/consumer.py": FROZEN["s04_consumer_blob"],
    }
    for rel, blob in expected.items():
        assert blob_id((ROOT / rel).read_bytes()) == blob, rel
    assert sha256_of(RUNTIME_SOURCE.read_bytes()) == FROZEN["baseline_safe_executor_sha256"]


def test_Z3_oracle_imports_nothing_from_the_code_under_test():
    import ast
    tree = ast.parse((TESTS / "s05_oracle.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"itertools"}, imported


def test_Z4_totals_are_recorded(sink, g1, g2, refusal, representation, boundaries, e2e, pins, limitations):
    groups = sink["groups"]
    failing = {k: sum(1 for r in (v["rows"] if isinstance(v, dict) and "rows" in v else v)
                      if isinstance(r, dict) and r.get("problems")) for k, v in groups.items() if k not in ("G2",)}
    failing["G2"] = sum(1 for rows in groups["G2"]["rows"].values() for r in rows if r["problems"])
    sink["totals"] = {
        "cases": {"G1_pairs": len(g1), "G1_comparisons": len(g1) * EXP["grids"]["G1"]["operations"],
                  "G2_pairs": sum(len(v) for v in g2.values()),
                  "G2_comparisons": sum(len(v) for v in g2.values()) * EXP["grids"]["G2"]["operations_per_field"],
                  "refusal": len(refusal), "representation": len(representation), "boundaries": len(boundaries),
                  "e2e": len(e2e), "pin": len(pins), "limitations": len(limitations)},
        "failing_cases_by_group": failing,
        "skipped": 0,
    }
    assert sum(failing.values()) == 0, failing
