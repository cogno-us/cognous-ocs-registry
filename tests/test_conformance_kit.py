"""Tests for the EXT-S1-8 consumer activation / high-water conformance kit.

IMPLEMENTED / DEVELOPER-TESTED. Not independently qualified. Builder-authored.
"""

import ast
import copy
import glob
import json
import os
import random

import pytest

import registry_conformance as kit
from registry_conformance import highwater as hw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_FILES = sorted(glob.glob(os.path.join(ROOT, "registry_conformance", "vectors", "*.json")))


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


DOCS = {os.path.basename(p): _load(p) for p in VECTOR_FILES}
ALL = [(name, doc, v) for name, doc in DOCS.items() for v in doc["vectors"]]


def test_vector_corpus_shape():
    assert len(DOCS) >= 10
    ids = [v["id"] for _, _, v in ALL]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 100
    for d in DOCS.values():
        kit.validate_vector_set(d)
        assert d["label"] == "SYNTHETIC-TEST-ONLY"


@pytest.mark.parametrize("name,doc,vector", ALL, ids=[v["id"] for _, _, v in ALL])
def test_vector(name, doc, vector):
    assert kit.run_vector(doc, vector) == []


def test_identifier_and_digest_validation_is_full_match():
    assert hw._ident("key-1") and not hw._ident("key-1\n") and not hw._ident("")
    assert hw._sha("sha256:" + "a" * 64) and not hw._sha("sha256:" + "a" * 64 + "\n")


def test_verdict_vocabulary_is_closed():
    seen = set()
    for _, doc, v in ALL:
        for s in v["steps"]:
            if s["op"] == "advance":
                seen.add(s["expect"]["verdict"])
    assert seen == set(kit.VERDICTS) == {"ACCEPT", "REFUSE_STALE", "REFUSE", "UNKNOWN_FAIL_CLOSED"}


# ------------------------------------------------------------ malformed vectors


def _good():
    return copy.deepcopy(DOCS["01_selection_epoch.json"])


def _mut(fn):
    d = _good()
    fn(d)
    return d


MALFORMED = {
    "not_object": lambda d: [],
    "wrong_schema": lambda d: d.update(schema="x"),
    "missing_label": lambda d: d.pop("label"),
    "wrong_label": lambda d: d.update(label="PRODUCTION"),
    "extra_doc_key": lambda d: d.update(authorizes=True),
    "empty_vectors": lambda d: d.update(vectors=[]),
    "vectors_not_list": lambda d: d.update(vectors={}),
    "duplicate_id": lambda d: d["vectors"].append(copy.deepcopy(d["vectors"][0])),
    "missing_steps": lambda d: d["vectors"][0].pop("steps"),
    "empty_steps": lambda d: d["vectors"][0].update(steps=[]),
    "extra_vector_key": lambda d: d["vectors"][0].update(mint="grant"),
    "missing_cites": lambda d: d["vectors"][0].update(cites=[]),
    "unknown_op": lambda d: d["vectors"][0]["steps"].append({"op": "authorize"}),
    "advance_missing_expect": lambda d: d["vectors"][0]["steps"][0].pop("expect"),
    "bad_verdict": lambda d: d["vectors"][0]["steps"][0]["expect"].update(verdict="ALLOW"),
    "missing_code": lambda d: d["vectors"][0]["steps"][0]["expect"].pop("code"),
    "authorization_key_in_expect": lambda d: d["vectors"][0]["steps"][0]["expect"].update(authorization="grant"),
    "unknown_scope_label": lambda d: d["vectors"][0]["steps"][0]["obs"].update(scope="ZZ"),
    "bad_policy_state_expect": lambda d: d["vectors"][0]["steps"].append(
        {"op": "policy_state", "scope": "A", "now": 1, "expect": {"policy_state": "enabled"}}),
    "bad_tear": lambda d: d["vectors"][0]["steps"].append({"op": "tear", "kind": "melt", "scope": "A"}),
    "concurrent_one_observation": lambda d: d["vectors"][0]["steps"].append(
        {"op": "concurrent", "observations": [{"kind": "read"}], "expect": {"accepted_count": 1, "allowed_final": [{}]}}),
    "bad_check_key": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"enabled": True}}),
    "defaults_bad_kind": lambda d: d["defaults"].update(grant={"now": 1}),
    "check_unknown_label_row_absent": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"row_absent": ["typo"]}}),
    "check_unknown_label_row": lambda d: d["vectors"][0]["steps"].append(
        {"op": "check", "expect": {"row": {"typo": {"activation_state": "active", "epoch": 1}}}}),
    "check_unknown_label_high_water": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"high_water": {"typo": 1}}}),
    "check_unknown_label_ratchet": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"scope_required": ["typo"]}}),
    "check_wrong_container": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"row_absent": "A"}}),
    "check_log_length_not_int": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"log_length": "1"}}),
    "check_bad_store": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"store": "maybe"}}),
    "check_bad_revoked_pair": lambda d: d["vectors"][0]["steps"].append({"op": "check", "expect": {"revoked": [["sel-a"]]}}),
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_kit_refuses_malformed_vectors(name):
    d = _good()
    r = MALFORMED[name](d)
    if name == "not_object":
        d = []
    with pytest.raises(kit.MalformedVector):
        kit.run_vector_set(d)


# ------------------------------------------------------ purity / boundaries


def _kit_sources():
    base = os.path.join(ROOT, "registry_conformance")
    return {p: open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(base, "*.py"))}


def test_kit_is_pure_stdlib_no_io_no_clock_no_core_imports():
    banned_modules = {"os", "sys", "time", "datetime", "random", "socket", "subprocess", "pathlib", "shutil",
                      "urllib", "http", "sqlite3", "tempfile", "io", "threading", "asyncio", "requests"}
    banned_calls = {"open", "eval", "exec", "compile", "__import__", "input"}
    for path, src in _kit_sources().items():
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    top = a.name.split(".")[0]
                    assert top not in banned_modules, (path, a.name)
                    assert not top.startswith("registry_"), (path, a.name)
            if isinstance(node, ast.ImportFrom):
                top = (node.module or "").split(".")[0]
                assert top not in banned_modules, (path, node.module)
                assert not top.startswith("registry_") or top == "registry_conformance", (path, node.module)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls, (path, node.func.id)


def test_core_does_not_import_the_kit():
    for pkg in ("registry_successor", "registry_contract", "registry_consumer", "registry_records"):
        for p in glob.glob(os.path.join(ROOT, pkg, "**", "*.py"), recursive=True):
            assert "registry_conformance" not in open(p, encoding="utf-8").read(), p


def _seed():
    d = DOCS["02_revocation_withdrawal_replay.json"]
    v = [x for x in d["vectors"] if x["id"] == "RV-05-reversal-only-by-fresh-higher-epoch"][0]
    return d, v


def test_advance_does_not_mutate_inputs_and_is_deterministic():
    st = kit.empty_state()
    obs = {"kind": "select", "now": 200, "scope": {
        "selection_id": "sel-a", "consumer_id": "c", "tenant": "t", "institution": "i", "authority_domain": "d",
        "operation": "o", "family": "f"}, "epoch": 1, "selection_digest": "sha256:" + "a" * 64, "supersedes": None,
        "participation": "required", "valid_from": 100, "valid_until": 1000, "issuer_key_id": "k", "issuer_id": "i1", "verified": True,
        "record": {"record_id": "r", "record_version": 1, "record_digest": "sha256:" + "b" * 64}}
    st0, obs0 = copy.deepcopy(st), copy.deepcopy(obs)
    new1, v1 = kit.advance(st, obs)
    new2, v2 = kit.advance(st, obs)
    assert st == st0 and obs == obs0
    assert (new1, v1) == (new2, v2)
    assert v1["verdict"] == "ACCEPT" and new1 is not st
    new1["rows"].clear()
    assert st == st0


def test_verdict_never_carries_authorization():
    allowed = {"verdict", "code", "applied", "fallback", "fallback_reason", "activation_ref"}
    for _, doc, v in ALL:
        # the runner already fails on unknown verdict keys; assert the allowed set is what the docs promise
        assert kit.run_vector(doc, v) == []
    assert allowed == set(kit._ALLOWED_VERDICT_KEYS)


def test_policy_state_has_no_authorizing_boolean():
    r = kit.policy_state(kit.empty_state(), {
        "selection_id": "s", "consumer_id": "c", "tenant": "t", "institution": "i", "authority_domain": "d",
        "operation": "o", "family": "f"}, 5)
    assert set(r) == {"policy_state", "required", "display"}
    assert all(not isinstance(v, bool) or k == "required" for k, v in r.items())


@pytest.mark.parametrize("ps", kit.highwater.POLICY_STATES)
def test_required_display_never_success_unless_active(ps):
    view = hw._view(ps, True)
    if ps == "active":
        assert view["display"] == "ENABLED"
    else:
        assert view["display"] == hw.REQUIRED_UNAVAILABLE
    opt = hw._view(ps, False)
    assert (opt["display"] == "ENABLED") == (ps == "active")
    assert (opt["display"] == "DISABLED") == (ps in ("withdrawn", "not_selected"))


# ------------------------------------------------------------- mutation tests


def _run_all():
    """Failures across all vectors; an exception from a mutated kit counts as detection."""
    fails = []
    for _, doc, v in ALL:
        try:
            fails.extend(kit.run_vector(doc, v))
        except Exception as exc:  # noqa: BLE001 - mutation harness
            fails.append("%s raised %r" % (v["id"], exc))
    return fails


SELECT_NAMES = [n for n, _ in hw._SELECT_CHECKS]
WITHDRAW_NAMES = [n for n, _ in hw._WITHDRAW_CHECKS]


@pytest.mark.parametrize("which,name", [("select", n) for n in SELECT_NAMES] + [("withdraw", n) for n in WITHDRAW_NAMES])
def test_mutation_disabling_one_refusal_is_caught(monkeypatch, which, name):
    attr = "_SELECT_CHECKS" if which == "select" else "_WITHDRAW_CHECKS"
    orig = getattr(hw, attr)
    mutated = tuple((n, (lambda st, o, ctx: None) if n == name else fn) for n, fn in orig)
    monkeypatch.setattr(hw, attr, mutated)
    assert _run_all() != [], "vectors did not detect disabling %s/%s" % (which, name)


def test_mutation_relaxation_refusal_is_caught(monkeypatch):
    orig = hw.advance

    def mutated(state, observation):
        if isinstance(observation, dict) and observation.get("kind") == "relax_scope_required":
            return orig(state, {"kind": "read", "now": observation.get("now", 0)})
        return orig(state, observation)

    monkeypatch.setattr(kit, "advance", mutated)
    assert _run_all() != []


def test_mutation_policy_state_precedence_is_caught(monkeypatch):
    orig = hw.policy_state

    def mutated(state, scope, now, known_selection=None, epoch=None):
        r = orig(state, scope, now, known_selection, epoch)
        if r["policy_state"] == "revoked":
            return hw._view("withdrawn", r["required"])
        return r

    monkeypatch.setattr(kit, "policy_state", mutated)
    assert _run_all() != []


# ----------------------------------------------------- randomized invariants


def _scope(i):
    return {"selection_id": "sel-%d" % (i % 2), "consumer_id": "c", "tenant": "t", "institution": "i",
            "authority_domain": "d", "operation": "op%d" % (i % 2), "family": "f"}


def _rand_obs(rng, state):
    sc = _scope(rng.randrange(2))
    e = rng.randrange(1, 6)
    dig = lambda x: "sha256:" + ("%064x" % x)
    row = state["rows"].get(hw.scope_key(sc)) if not hw._shape_problem(state) else None
    sup = None
    if row and rng.random() < 0.8:
        sup = {"selection_id": sc["selection_id"], "epoch": row["epoch"], "statement_digest": row["selection_digest"]}
    k = rng.choice(["select", "select", "withdraw", "sync", "sync", "read", "external_floor", "guard", "relax_scope_required", "rebaseline", "lose_state"])
    if k == "lose_state" and rng.random() < 0.85:
        k = "read"  # loss is permanent in the kit (no recovery), keep most sequences alive
    now = rng.choice([150, 200, 999, 1000])
    if k == "select":
        return {"kind": k, "now": now, "scope": sc, "epoch": e, "selection_digest": dig(rng.randrange(8)), "supersedes": sup,
                "participation": rng.choice(["required", "optional"]), "valid_from": 100, "valid_until": 1000,
                "issuer_key_id": rng.choice(["k1", "k2"]), "issuer_id": rng.choice(["i1", "i2"]), "verified": rng.random() < 0.9,
                "record": {"record_id": "r", "record_version": 1, "record_digest": dig(9)}}
    if k == "withdraw":
        return {"kind": k, "now": now, "scope": sc, "epoch": e, "selection_digest": dig(rng.randrange(8)), "supersedes": sup,
                "participation": rng.choice(["required", "optional"]), "issuer_key_id": "k1", "issuer_id": "i1", "verified": True}
    if k == "sync":
        rev = [["sel-%d" % rng.randrange(2), rng.randrange(1, 6)] for _ in range(rng.randrange(3))]
        rev = [list(x) for x in {tuple(x) for x in rev}]
        return {"kind": k, "now": now, "snapshot": {"version": rng.randrange(1, 6), "fingerprint": dig(rng.randrange(3)),
                "valid_until": 5000, "revoked_selections": rev, "revoked_key_ids": rng.choice([[], ["k1"]]),
                "min_epochs": rng.choice([[], [["sel-0", 2]]]),
                "revoked_records": rng.choice([[], [["r", 1]]]), "revoked_issuers": rng.choice([[], ["i2"]])}}
    if k == "external_floor":
        return {"kind": k, "now": now, "min_trust_snapshot_version": rng.randrange(0, 4)}
    if k == "guard":
        return {"kind": k, "now": now, "claim": {"scope": sc, "binding": None}}
    if k == "relax_scope_required":
        return {"kind": k, "now": now, "scope": sc}
    if k == "rebaseline":
        return {"kind": k, "now": now, "authorized": True, "decision_ref": "op-r"}
    if k == "lose_state":
        return {"kind": k, "now": now}
    return {"kind": "read", "now": now}


@pytest.mark.parametrize("seed", range(40))
def test_random_sequences_keep_monotonic_invariants(seed):
    rng = random.Random(seed)
    state = kit.empty_state()
    for _ in range(30):
        obs = _rand_obs(rng, state)
        new, verdict = kit.advance(state, obs)
        assert kit._invariants(obs["kind"], state, new, verdict) == [], (seed, obs, verdict)
        if new["store"] == "known":
            assert kit.verify_state(new) is None
        state = new
    assert state["store"] == "unknown" or kit.verify_state(state) is None


def test_monotonicity_survives_random_restore_and_loss():
    rng = random.Random(7)
    state = kit.empty_state()
    snaps = []
    for _ in range(40):
        snaps.append(copy.deepcopy(state))
        obs = _rand_obs(rng, state)
        state, _ = kit.advance(state, obs)
    before = copy.deepcopy(state)
    new, verdict = kit.advance(state, {"kind": "restore", "now": 300, "backup": snaps[len(snaps) // 3]})
    assert kit._invariants("restore", before, new, verdict) == []
    for k, v in before["floors"]["high_water"].items():
        assert new["floors"]["high_water"].get(k, 0) >= v
    assert all(p in new["floors"]["revoked"] for p in before["floors"]["revoked"])


# ------------------------------------------------ architect rulings R1-R4


def _verdict_codes():
    out = {}
    for _, _, v in ALL:
        for s in v["steps"]:
            if s["op"] == "advance":
                out.setdefault(s["expect"]["code"], set()).add(s["expect"]["verdict"])
    return out


def test_r1_each_verdict_has_its_own_vector_and_codes_do_not_straddle_classes():
    doc = DOCS["11_verdict_semantics.json"]
    per = {}
    for v in doc["vectors"]:
        per[v["id"]] = {s["expect"]["verdict"] for s in v["steps"] if s["op"] == "advance"}
    assert per["VD-01-accept-means-valid-under-authority-and-state"] == {"ACCEPT"}
    assert "REFUSE" in per["VD-02-refuse-is-definitive-invalidity-or-authority-violation"]
    assert per["VD-03-refuse-stale-is-definitive-stale-replay-or-rollback"] >= {"REFUSE_STALE"}
    assert per["VD-04-unknown-fail-closed-authority-or-state-indeterminate"] >= {"UNKNOWN_FAIL_CLOSED"}
    # a cause code names one verdict class; the only documented dual code is trust_snapshot_expired
    # (REFUSE for a delivered expired snapshot, UNKNOWN_FAIL_CLOSED for an expired current snapshot at the guard)
    dual = {c for c, vs in _verdict_codes().items() if len(vs) > 1}
    assert dual <= {"trust_snapshot_expired"}, dual
    assert not any("UNKNOWN_FAIL_CLOSED" in vs and "ACCEPT" in vs for vs in _verdict_codes().values())


def test_r2_revocation_scopes_are_checked_and_never_cleared():
    names = {n for n, _ in hw._SELECT_CHECKS}
    assert {"revoked_pair", "revoked_key", "revoked_record", "revoked_issuer"} <= names
    assert {"revoked_key", "revoked_issuer"} <= {n for n, _ in hw._WITHDRAW_CHECKS}


def test_r3_known_unactivated_epoch_never_changes_the_row_view():
    d = DOCS["07_policy_state.json"]
    v = [x for x in d["vectors"] if x["id"] == "PS-11-higher-unactivated-epoch-does-not-supersede"][0]
    assert kit.run_vector(d, v) == []
    import inspect
    src = inspect.getsource(hw.policy_state)
    assert 'ks.get("epoch"' not in src and 'known_selection.get("epoch"' not in src


def test_r3_mutation_unactivated_epoch_supersedes_is_caught(monkeypatch):
    orig = hw.policy_state

    def mutated(state, scope, now, known_selection=None, epoch=None):
        r = orig(state, scope, now, known_selection, epoch)
        if known_selection and r["policy_state"] == "active":
            return hw._view("superseded", r["required"])
        return r

    monkeypatch.setattr(kit, "policy_state", mutated)
    assert _run_all() != []


def test_r4_no_rebaseline_state_or_entry_type_and_closed_vocabulary():
    st = kit.empty_state()
    assert "rebaselines" not in st
    assert "rebaseline" not in hw._replay.__code__.co_consts
    for e in ("activate", "withdraw", "revoke", "sync"):
        assert e in hw._replay_unsafe.__code__.co_consts
    assert "rebaseline" in hw.KINDS  # an input kind only, always refused


@pytest.mark.parametrize("authorized", [True, False])
@pytest.mark.parametrize("lost", [True, False])
def test_r4_rebaseline_never_accepts_and_never_changes_store(authorized, lost):
    st, v = kit.advance(kit.empty_state(), {"kind": "lose_state", "now": 5}) if lost else (kit.empty_state(), None)
    before = copy.deepcopy(st)
    new, verdict = kit.advance(st, {"kind": "rebaseline", "now": 6, "authorized": authorized, "decision_ref": "op-1"})
    assert verdict["verdict"] == "REFUSE" and verdict["code"] == "rebaseline_not_authorized_v1"
    assert new["store"] == before["store"] and new["anchor"] == before["anchor"]
    assert new["log"] == before["log"] and new["rows"] == before["rows"]


def test_r4_unknown_store_is_never_made_known_by_restore():
    st = kit.empty_state()
    good = copy.deepcopy(st)
    lost, _ = kit.advance(st, {"kind": "lose_state", "now": 5})
    for backup in (good, copy.deepcopy(lost)):
        new, verdict = kit.advance(lost, {"kind": "restore", "now": 6, "backup": backup})
        assert verdict["verdict"] == "UNKNOWN_FAIL_CLOSED" and new["store"] == "unknown"


def test_r4_mutation_automatic_rebaseline_is_caught(monkeypatch):
    def accepting(st, o):
        st["store"] = "known"
        st["unknown_reason"] = None
        return st, hw._verdict(hw.ACCEPT, "rebaselined")

    monkeypatch.setattr(hw, "_do_rebaseline", accepting)
    assert _run_all() != []


def test_r4_mutation_restore_recovering_unknown_store_is_caught(monkeypatch):
    orig = hw._do_restore

    def recovering(st, o):
        if st["store"] == "unknown":
            st = {**st, "store": "known", "unknown_reason": None}
        return orig(st, o)

    monkeypatch.setattr(hw, "_do_restore", recovering)
    assert _run_all() != []
